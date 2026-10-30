# Ai Course Generator

A Streamlit app that uses the Groq API to generate a course outline, full lesson content and a five-question quiz for each lesson. Quizzes are graded locally in Python.

## Features

- Enter a course topic, choose a difficulty (Beginner / Intermediate / Advanced) and a lesson count (2-5).
- Generate a validated course outline with titles, objectives and summaries.
- Generate full lesson content: introduction, 2-4 sections, summary and 2 exercises with hints.
- Generate a 5-question multiple-choice quiz per lesson, graded locally, with retake support.
- All model output is validated with Pydantic before it is shown.

## Requirements

- Python 3.11 or compatible
- A Groq API key

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in the same window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and set your real key:

```
GROQ_API_KEY=your_real_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit `.env`. It is already listed in `.gitignore`.

## Run

Check the Groq connection first:

```powershell
python connection_test.py
```

Start the app:

```powershell
python -m streamlit run app.py
```

Run the local checks (no API key needed):

```powershell
python test_local.py
```

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface and session state |
| `generator.py` | Outline, lesson and quiz generation with validation and retry |
| `models.py` | Pydantic schemas |
| `grading.py` | Local quiz grading |
| `llm_client.py` | Groq client and error handling |
| `connection_test.py` | Groq connection test |
| `test_local.py` | Local logic checks |
| `.env.example` | Environment variable template |

## Scope

This is the Week 1 version. PDF processing, embeddings, RAG, a chatbot and permanent storage are planned for later weeks.
