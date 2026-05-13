# AI Student Helper

An MVP AI-powered student learning assistant that analyzes learning profiles and nudges students toward exercises.

## Architecture

The system consists of 3 main components:

1. **Trace Indexer**: Parses and indexes the student's learning history
2. **Gap Detector**: Identifies weak, avoided, or decaying concepts from the trace
3. **Nudge Engine**: Generates direct, actionable provocations

## Tech Stack

- **Frontend**: HTML + Tailwind CSS (via CDN)
- **Backend**: Python + FastAPI + SQLite
- **LLM**: Google Gemini

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the server:
```bash
python main.py
```

The server will start on `http://localhost:8000`

## Usage

### Student Flow

1. Go to `/` - Login page (click "Student Login")
2. `/home` - View enrolled courses
3. `/course/{id}` - View course exercises and generate study plan
4. `/study_plan` - Complete exercises from the study plan

### Professor Flow

1. Go to `/` - Login page (click "Professor Login")
2. `/creation` - Create new exercises with LLM-suggested labels
3. `/grade` - Grade student exam submissions

## API Endpoints

- `POST /api/suggest-labels` - Get LLM-suggested labels for an exercise
- `POST /api/create-exercise` - Create a new exercise
- `POST /api/submit-labels` - Submit labels for an exercise
- `POST /api/grade-exercise` - Grade an exam exercise
- `POST /api/submit-solution` - Submit a student solution
- `POST /api/generate-study-plan/{course_id}` - Generate a new study plan
- `GET /api/label-strengths/{course_id}` - Get label strengths for a student
- `GET /api/exercise/{exercise_id}` - Get exercise details

## Database Schema

The system uses SQLite with the following tables:
- student
- course
- student_course
- labels
- exam
- exercise
- exam_exercise
- exercise_label
- exercise_log
- label_strength
- study_plan
- study_block
- study_block_exercise

## Notes

- This is an MVP with hardcoded student_id = 1
- The system uses Gemini Pro for LLM operations
- Tailwind CSS is loaded via CDN for simplicity
