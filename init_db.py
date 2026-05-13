import sqlite3
import os

DB_PATH = "student_helper.db"

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # STUDENT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created TEXT NOT NULL
        )
    """)
    
    # COURSE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            professor TEXT
        )
    """)
    
    # student_course
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_course (
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES student(id),
            FOREIGN KEY (course_id) REFERENCES course(id)
        )
    """)
    
    # LABELS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES course(id)
        )
    """)
    
    # EXAM
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            created TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES course(id)
        )
    """)
    
    # EXERCISE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            solution TEXT,
            difficulty INTEGER,
            created TEXT NOT NULL,
            type TEXT CHECK(type IN ('exam', 'quiz')),
            FOREIGN KEY (course_id) REFERENCES course(id)
        )
    """)
    
    # exam_exercise
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_exercise (
            exam_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            PRIMARY KEY (exam_id, exercise_id),
            FOREIGN KEY (exam_id) REFERENCES exam(id),
            FOREIGN KEY (exercise_id) REFERENCES exercise(id)
        )
    """)
    
    # exercise_label
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_label (
            exercise_id INTEGER NOT NULL,
            label_id INTEGER NOT NULL,
            PRIMARY KEY (exercise_id, label_id),
            FOREIGN KEY (exercise_id) REFERENCES exercise(id),
            FOREIGN KEY (label_id) REFERENCES labels(id)
        )
    """)
    
    # EXERCISE LOG
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_log (
            id INTEGER PRIMARY KEY,
            exercise_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            execution_type TEXT CHECK(execution_type IN ('exam', 'individual')),
            created TEXT NOT NULL,
            score REAL,
            FOREIGN KEY (exercise_id) REFERENCES exercise(id),
            FOREIGN KEY (student_id) REFERENCES student(id)
        )
    """)
    
    # LABEL STRENGTH
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS label_strength (
            id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            label_id INTEGER NOT NULL,
            score REAL,
            trend REAL,
            llm_reasoning TEXT,
            updated TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES student(id),
            FOREIGN KEY (label_id) REFERENCES labels(id)
        )
    """)
    
    # STUDY PLAN
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_plan (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            created TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES course(id),
            FOREIGN KEY (student_id) REFERENCES student(id)
        )
    """)
    
    # STUDY BLOCK
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_block (
            id INTEGER PRIMARY KEY,
            study_plan_id INTEGER NOT NULL,
            block_order INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            FOREIGN KEY (study_plan_id) REFERENCES study_plan(id),
            FOREIGN KEY (topic_id) REFERENCES labels(id)
        )
    """)
    
    # study_block_exercise
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_block_exercise (
            study_block_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            PRIMARY KEY (study_block_id, exercise_id),
            FOREIGN KEY (study_block_id) REFERENCES study_block(id),
            FOREIGN KEY (exercise_id) REFERENCES exercise(id)
        )
    """)
    
    # Insert sample data
    from datetime import datetime
    
    # Insert student
    cursor.execute("INSERT OR IGNORE INTO student (id, name, email, created) VALUES (?, ?, ?, ?)",
                  (1, "John Doe", "john@example.com", datetime.now().isoformat()))
    
    # Insert courses
    cursor.execute("INSERT OR IGNORE INTO course (id, name, professor) VALUES (?, ?, ?)",
                  (1, "Mathematics 101", "Dr. Smith"))
    cursor.execute("INSERT OR IGNORE INTO course (id, name, professor) VALUES (?, ?, ?)",
                  (2, "Physics 101", "Dr. Johnson"))
    
    # Enroll student in courses
    cursor.execute("INSERT OR IGNORE INTO student_course (student_id, course_id) VALUES (?, ?)",
                  (1, 1))
    cursor.execute("INSERT OR IGNORE INTO student_course (student_id, course_id) VALUES (?, ?)",
                  (1, 2))
    
    # Insert labels for Mathematics
    cursor.execute("INSERT OR IGNORE INTO labels (id, name, course_id) VALUES (?, ?, ?)",
                  (1, "Addition", 1))
    cursor.execute("INSERT OR IGNORE INTO labels (id, name, course_id) VALUES (?, ?, ?)",
                  (2, "Subtraction", 1))
    cursor.execute("INSERT OR IGNORE INTO labels (id, name, course_id) VALUES (?, ?, ?)",
                  (3, "Multiplication", 1))
    cursor.execute("INSERT OR IGNORE INTO labels (id, name, course_id) VALUES (?, ?, ?)",
                  (4, "Division", 1))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
