import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = "student_helper.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
    
    def get_cursor(self):
        return self.conn.cursor()
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

# Student operations
def get_student(db: Database, student_id: int) -> Optional[Dict]:
    cursor = db.get_cursor()
    cursor.execute("SELECT * FROM student WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_student_courses(db: Database, student_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT c.* FROM course c
        JOIN student_course sc ON c.id = sc.course_id
        WHERE sc.student_id = ?
    """, (student_id,))
    return [dict(row) for row in cursor.fetchall()]

# Course operations
def get_course(db: Database, course_id: int) -> Optional[Dict]:
    cursor = db.get_cursor()
    cursor.execute("SELECT * FROM course WHERE id = ?", (course_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_course_exercises(db: Database, course_id: int, student_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT e.*, 
               (SELECT score FROM exercise_log el 
                WHERE el.exercise_id = e.id AND el.student_id = ? 
                ORDER BY created DESC LIMIT 1) as last_score
        FROM exercise e
        WHERE e.course_id = ?
        ORDER BY e.created DESC
    """, (student_id, course_id))
    return [dict(row) for row in cursor.fetchall()]

def get_course_labels(db: Database, course_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("SELECT * FROM labels WHERE course_id = ?", (course_id,))
    return [dict(row) for row in cursor.fetchall()]

# Exercise operations
def create_exercise(db: Database, course_id: int, text: str, solution: str, 
                   difficulty: int, exercise_type: str) -> int:
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT INTO exercise (course_id, text, solution, difficulty, created, type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (course_id, text, solution, difficulty, datetime.now().isoformat(), exercise_type))
    db.commit()
    return cursor.lastrowid

def add_exercise_labels(db: Database, exercise_id: int, label_ids: List[int]):
    cursor = db.get_cursor()
    for label_id in label_ids:
        cursor.execute("""
            INSERT OR IGNORE INTO exercise_label (exercise_id, label_id)
            VALUES (?, ?)
        """, (exercise_id, label_id))
    db.commit()

def get_exercise(db: Database, exercise_id: int) -> Optional[Dict]:
    cursor = db.get_cursor()
    cursor.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_exercise_labels(db: Database, exercise_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT l.* FROM labels l
        JOIN exercise_label el ON l.id = el.label_id
        WHERE el.exercise_id = ?
    """, (exercise_id,))
    return [dict(row) for row in cursor.fetchall()]

# Exercise log operations
def log_exercise_attempt(db: Database, exercise_id: int, student_id: int, 
                        execution_type: str, score: float):
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT INTO exercise_log (exercise_id, student_id, execution_type, created, score)
        VALUES (?, ?, ?, ?, ?)
    """, (exercise_id, student_id, execution_type, datetime.now().isoformat(), score))
    db.commit()

def get_student_exercise_logs(db: Database, student_id: int, label_id: Optional[int] = None) -> List[Dict]:
    cursor = db.get_cursor()
    if label_id:
        cursor.execute("""
            SELECT el.*, e.text, e.type, e.difficulty, e.created as exercise_created,
                   GROUP_CONCAT(l.name) as labels
            FROM exercise_log el
            JOIN exercise e ON el.exercise_id = e.id
            JOIN exercise_label exl ON e.id = exl.exercise_id
            JOIN labels l ON exl.label_id = l.id
            WHERE el.student_id = ? AND l.id = ?
            GROUP BY el.id
            ORDER BY el.created DESC
        """, (student_id, label_id))
    else:
        cursor.execute("""
            SELECT el.*, e.text, e.type, e.difficulty, e.created as exercise_created,
                   GROUP_CONCAT(l.name) as labels
            FROM exercise_log el
            JOIN exercise e ON el.exercise_id = e.id
            JOIN exercise_label exl ON e.id = exl.exercise_id
            JOIN labels l ON exl.label_id = l.id
            WHERE el.student_id = ?
            GROUP BY el.id
            ORDER BY el.created DESC
        """, (student_id,))
    return [dict(row) for row in cursor.fetchall()]

# Label strength operations
def upsert_label_strength(db: Database, student_id: int, label_id: int, 
                          score: float, trend: str, reasoning: str):
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO label_strength 
        (student_id, label_id, score, trend, llm_reasoning, updated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, label_id, score, trend, reasoning, datetime.now().isoformat()))
    db.commit()

def get_label_strengths(db: Database, student_id: int, course_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT ls.*, l.name as label_name
        FROM label_strength ls
        JOIN labels l ON ls.label_id = l.id
        WHERE ls.student_id = ? AND l.course_id = ?
    """, (student_id, course_id))
    return [dict(row) for row in cursor.fetchall()]

# Study plan operations
def create_study_plan(db: Database, course_id: int, student_id: int) -> int:
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT INTO study_plan (course_id, student_id, created)
        VALUES (?, ?, ?)
    """, (course_id, student_id, datetime.now().isoformat()))
    db.commit()
    return cursor.lastrowid

def create_study_block(db: Database, study_plan_id: int, block_order: int, topic_id: int) -> int:
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT INTO study_block (study_plan_id, block_order, topic_id)
        VALUES (?, ?, ?)
    """, (study_plan_id, block_order, topic_id))
    db.commit()
    return cursor.lastrowid

def add_exercise_to_block(db: Database, study_block_id: int, exercise_id: int):
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO study_block_exercise (study_block_id, exercise_id)
        VALUES (?, ?)
    """, (study_block_id, exercise_id))
    db.commit()

def get_latest_study_plan(db: Database, student_id: int, course_id: int) -> Optional[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT sp.* FROM study_plan sp
        WHERE sp.student_id = ? AND sp.course_id = ?
        ORDER BY sp.created DESC LIMIT 1
    """, (student_id, course_id))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_study_plan_blocks(db: Database, study_plan_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT sb.*, l.name as topic_name
        FROM study_block sb
        JOIN labels l ON sb.topic_id = l.id
        WHERE sb.study_plan_id = ?
        ORDER BY sb.block_order
    """, (study_plan_id,))
    return [dict(row) for row in cursor.fetchall()]

def get_block_exercises(db: Database, study_block_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT e.* FROM exercise e
        JOIN study_block_exercise sbe ON e.id = sbe.exercise_id
        WHERE sbe.study_block_id = ?
    """, (study_block_id,))
    return [dict(row) for row in cursor.fetchall()]

# Label operations
def create_label(db: Database, name: str, course_id: int) -> int:
    cursor = db.get_cursor()
    cursor.execute("""
        INSERT INTO labels (name, course_id)
        VALUES (?, ?)
    """, (name, course_id))
    db.commit()
    return cursor.lastrowid

def get_all_labels(db: Database, course_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("SELECT * FROM labels WHERE course_id = ?", (course_id,))
    return [dict(row) for row in cursor.fetchall()]

# Exam operations
def get_exam_exercises(db: Database, course_id: int) -> List[Dict]:
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT e.* FROM exercise e
        WHERE e.course_id = ? AND e.type = 'exam'
        ORDER BY e.created DESC
    """, (course_id,))
    return [dict(row) for row in cursor.fetchall()]
