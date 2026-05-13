from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from database import (
    Database, get_student, get_student_courses, get_course, get_course_exercises,
    get_course_labels, create_exercise, add_exercise_labels, get_exercise,
    get_exercise_labels, log_exercise_attempt, get_student_exercise_logs,
    upsert_label_strength, get_label_strengths, create_study_plan,
    create_study_block, add_exercise_to_block, get_latest_study_plan,
    get_study_plan_blocks, get_block_exercises, create_label, get_all_labels,
    get_exam_exercises
)
from llm_service import LLMService
from components import TraceIndexer, GapDetector, NudgeEngine

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database and services
db = Database()
llm_service = LLMService()
trace_indexer = TraceIndexer(db)
gap_detector = GapDetector(db, llm_service)
nudge_engine = NudgeEngine(llm_service)

# Pydantic models
class ExerciseCreate(BaseModel):
    course_id: int
    text: str
    solution: str
    difficulty: int
    type: str

class LabelSubmit(BaseModel):
    exercise_id: int
    labels: List[str]

class ExerciseSubmission(BaseModel):
    exercise_id: int
    solution: str

class GradeSubmission(BaseModel):
    exercise_id: int
    score: float

# ==================== Frontend Routes ====================

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    courses = get_student_courses(db, 1)  # Hardcoded student_id = 1
    return templates.TemplateResponse("home.html", {"request": request, "courses": courses})

@app.get("/course/{course_id}", response_class=HTMLResponse)
async def course_page(request: Request, course_id: int):
    course = get_course(db, course_id)
    exercises = get_course_exercises(db, course_id, 1)  # Hardcoded student_id = 1
    return templates.TemplateResponse("course.html", {
        "request": request,
        "course": course,
        "exercises": exercises
    })

@app.get("/study_plan", response_class=HTMLResponse)
async def study_plan_page(request: Request, course_id: int):
    course = get_course(db, course_id)
    study_plan = get_latest_study_plan(db, 1, course_id)  # Hardcoded student_id = 1
    
    blocks = []
    current_exercise = None
    
    if study_plan:
        blocks = get_study_plan_blocks(db, study_plan["id"])
        if blocks:
            # Get exercises from first block as current exercise
            block_exercises = get_block_exercises(db, blocks[0]["id"])
            if block_exercises:
                current_exercise = block_exercises[0]
    
    return templates.TemplateResponse("study_plan.html", {
        "request": request,
        "course": course,
        "study_plan": study_plan,
        "blocks": blocks,
        "current_exercise": current_exercise
    })

@app.get("/creation", response_class=HTMLResponse)
async def creation_page(request: Request):
    courses = get_student_courses(db, 1)  # Reuse for professor
    return templates.TemplateResponse("creation.html", {"request": request, "courses": courses})

@app.get("/grade", response_class=HTMLResponse)
async def grade_page(request: Request):
    courses = get_student_courses(db, 1)  # Reuse for professor
    exam_exercises = []
    for course in courses:
        exam_exercises.extend(get_exam_exercises(db, course["id"]))
    return templates.TemplateResponse("grade.html", {
        "request": request,
        "exam_exercises": exam_exercises
    })

# ==================== API Routes ====================

@app.post("/api/suggest-labels")
async def suggest_labels(exercise: ExerciseCreate):
    """LLM suggests labels for a new exercise"""
    existing_labels = [l["name"] for l in get_all_labels(db, exercise.course_id)]
    suggested = llm_service.suggest_labels(exercise.text, existing_labels)
    return {"suggested_labels": suggested}

@app.post("/api/create-exercise")
async def create_exercise_endpoint(data: ExerciseCreate):
    """Create a new exercise"""
    exercise_id = create_exercise(
        db, data.course_id, data.text, data.solution, 
        data.difficulty, data.type
    )
    return {"exercise_id": exercise_id}

@app.post("/api/submit-labels")
async def submit_labels(data: LabelSubmit):
    """Submit labels for an exercise"""
    # Get or create labels
    exercise = get_exercise(db, data.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    label_ids = []
    for label_name in data.labels:
        labels = get_all_labels(db, exercise["course_id"])
        existing = next((l for l in labels if l["name"] == label_name), None)
        if existing:
            label_ids.append(existing["id"])
        else:
            new_id = create_label(db, label_name, exercise["course_id"])
            label_ids.append(new_id)
    
    add_exercise_labels(db, data.exercise_id, label_ids)
    return {"success": True}

@app.post("/api/grade-exercise")
async def grade_exercise(data: GradeSubmission):
    """Professor grades an exam exercise"""
    exercise = get_exercise(db, data.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    log_exercise_attempt(db, data.exercise_id, 1, "exam", data.score)
    return {"success": True}

@app.post("/api/submit-solution")
async def submit_solution(data: ExerciseSubmission):
    """Student submits a solution"""
    exercise = get_exercise(db, data.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Compare with solution
    is_correct = data.solution.strip().lower() == exercise["solution"].strip().lower()
    score = 100.0 if is_correct else 0.0
    
    log_exercise_attempt(db, data.exercise_id, 1, "individual", score)
    
    return {"correct": is_correct, "score": score}

@app.post("/api/generate-study-plan/{course_id}")
async def generate_study_plan(course_id: int):
    """Generate a new study plan using the 3-component system"""
    student_id = 1  # Hardcoded
    
    # Step 1: Trace Indexer - get student history
    history = trace_indexer.get_student_history(student_id, course_id)
    
    # Step 2: Gap Detector - compute label strengths
    label_strengths = gap_detector.detect_gaps(student_id, course_id)
    
    # Step 3: Generate study plan using LLM
    all_exercises = get_course_exercises(db, course_id, student_id)
    study_plan_blocks = llm_service.generate_study_plan(label_strengths, all_exercises)
    
    # Step 4: Store study plan in database
    plan_id = create_study_plan(db, course_id, student_id)
    
    for block_data in study_plan_blocks:
        block_id = create_study_block(
            db, plan_id, 
            block_data["block_order"], 
            block_data["topic_id"]
        )
        for exercise_id in block_data.get("exercise_ids", []):
            add_exercise_to_block(db, block_id, exercise_id)
    
    # Step 5: Nudge Engine - generate actionable nudge
    nudge = nudge_engine.generate_nudge(study_plan_blocks, label_strengths)
    
    return {
        "study_plan_id": plan_id,
        "nudge": nudge,
        "label_strengths": label_strengths
    }

@app.get("/api/label-strengths/{course_id}")
async def get_label_strengths_endpoint(course_id: int):
    """Get current label strengths for a student"""
    strengths = get_label_strengths(db, 1, course_id)  # Hardcoded student_id = 1
    return {"strengths": strengths}

@app.get("/api/exercise/{exercise_id}")
async def get_exercise_endpoint(exercise_id: int):
    """Get exercise details"""
    exercise = get_exercise(db, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    labels = get_exercise_labels(db, exercise_id)
    return {"exercise": exercise, "labels": labels}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
