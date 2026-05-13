from typing import List, Dict
from database import Database, get_student_exercise_logs, get_course_labels, upsert_label_strength, get_label_strengths
from llm_service import LLMService

class TraceIndexer:
    """Parses and indexes the student's learning history"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_student_history(self, student_id: int, course_id: int) -> Dict:
        """Retrieve and structure the student's complete learning history"""
        labels = get_course_labels(self.db, course_id)
        history = {}
        
        for label in labels:
            logs = get_student_exercise_logs(self.db, student_id, label["id"])
            history[label["name"]] = {
                "label_id": label["id"],
                "logs": logs,
                "total_attempts": len(logs),
                "last_attempt": logs[0]["created"] if logs else None
            }
        
        return history

class GapDetector:
    """Identifies weak, avoided, or decaying concepts from the trace"""
    
    def __init__(self, db: Database, llm_service: LLMService):
        self.db = db
        self.llm = llm_service
    
    def detect_gaps(self, student_id: int, course_id: int) -> List[Dict]:
        """Compute label strengths using LLM analysis"""
        # Get student's exercise history
        labels = get_course_labels(self.db, course_id)
        all_logs = get_student_exercise_logs(self.db, student_id)
        
        # Use LLM to compute label strengths
        label_strengths = self.llm.compute_label_strengths(all_logs, labels)
        
        # Store in database
        for strength in label_strengths:
            label_id = strength.get("label_id")
            if label_id:
                upsert_label_strength(
                    self.db,
                    student_id,
                    label_id,
                    strength.get("score", 0),
                    strength.get("trend", "unknown"),
                    strength.get("llm_reasoning", "")
                )
        
        return label_strengths

class NudgeEngine:
    """Generates direct, actionable provocations"""
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    def generate_nudge(self, study_plan: List[Dict], label_strengths: List[Dict]) -> str:
        """Generate an actionable nudge based on study plan and strengths"""
        return self.llm.generate_nudge(study_plan, label_strengths)
