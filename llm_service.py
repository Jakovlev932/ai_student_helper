import os
import json
from typing import List, Dict, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        #api_key = os.getenv("GEMINI_API_KEY")
        api_key = "FAKE KEY"
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'
    
    def suggest_labels(self, exercise_text: str, existing_labels: List[str]) -> List[str]:
        prompt = f"""
You are an educational content analyzer. Given an exercise, suggest appropriate topic labels.

Exercise text:
{exercise_text}

Existing labels in the course:
{', '.join(existing_labels)}

Analyze the exercise and suggest 1-3 labels that best describe the topics covered.
If there's a good match among existing labels, suggest it. Otherwise, suggest new labels.

Return ONLY a JSON array of label names, e.g.:
["Addition", "Fractions"]
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = response.text.strip()
            # Try to parse JSON from response
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            labels = json.loads(result)
            return labels if isinstance(labels, list) else [labels]
        except Exception as e:
            print(f"Error suggesting labels: {e}")
            return []
    
    def compute_label_strengths(self, exercise_logs: List[Dict], labels: List[Dict]) -> List[Dict]:
        logs_json = json.dumps(exercise_logs, indent=2, default=str)
        labels_json = json.dumps([{"id": l["id"], "name": l["name"]} for l in labels], indent=2)
        
        prompt = f"""
You are a learning analytics expert. Analyze a student's exercise history and compute label strengths.

Exercise logs (student's history):
{logs_json}

Labels to analyze:
{labels_json}

For each label, compute:
- score: 0-100 (0 = very weak, 100 = excellent)
- trend: "improving", "declining", "stable", or "unknown"
- reasoning: brief explanation for the score and trend

Rules:
- Exam questions are more important than practice
- Recent scores have more impact
- Topics with no exercises should have score 0
- Consider frequency of attempts and success rate
- Look for patterns in recent performance

Return ONLY a JSON array with this structure:
[
  {{
    "label_id": 1,
    "label_name": "Addition",
    "score": 30,
    "trend": "declining",
    "llm_reasoning": "Student failed recent exercises on this topic"
  }}
]
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = response.text.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            strengths = json.loads(result)
            return strengths if isinstance(strengths, list) else []
        except Exception as e:
            print(f"Error computing label strengths: {e}")
            return []
    
    def generate_study_plan(self, label_strengths: List[Dict], all_exercises: List[Dict]) -> List[Dict]:
        strengths_json = json.dumps(label_strengths, indent=2)
        exercises_json = json.dumps(all_exercises, indent=2, default=str)
        
        prompt = f"""
You are a personalized learning planner. Create a study plan based on student's label strengths.

Label strengths:
{strengths_json}

Available exercises:
{exercises_json}

Create a study plan with 3-5 study blocks. Each block focuses on one topic.
Prioritize:
1. Topics with lowest scores
2. Topics with declining trends
3. Don't overload with topics recently practiced

For each block, select 2-4 relevant exercises.

Return ONLY a JSON array with this structure:
[
  {{
    "block_order": 1,
    "topic_id": 1,
    "topic_name": "Addition",
    "exercise_ids": [1, 2, 3]
  }}
]
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = response.text.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            plan = json.loads(result)
            return plan if isinstance(plan, list) else []
        except Exception as e:
            print(f"Error generating study plan: {e}")
            return []
    
    def generate_nudge(self, study_plan: List[Dict], label_strengths: List[Dict]) -> str:
        plan_json = json.dumps(study_plan, indent=2)
        strengths_json = json.dumps(label_strengths, indent=2)
        
        prompt = f"""
You are a motivational learning assistant. Generate a direct, actionable nudge for a student.

Study plan:
{plan_json}

Label strengths:
{strengths_json}

Generate a short, direct provocation (max 2 sentences) that:
- Identifies the weakest topic
- Urges action without explaining why
- Provides no solutions
- Is actionable and motivating

Return ONLY the nudge text, nothing else.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            nudge = response.text.strip()
            # Remove any markdown formatting
            nudge = nudge.replace('"', '').replace('*', '')
            return nudge
        except Exception as e:
            print(f"Error generating nudge: {e}")
            return "Time to practice your weakest topic!"
