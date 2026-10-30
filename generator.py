import json
import re

from pydantic import ValidationError

from llm_client import GenerationError, ask_model
from models import Course, Lesson, LessonContent, Quiz

MAX_ATTEMPTS = 2 

SYSTEM_PROMPT = (
    "You are an expert curriculum designer. Respond with a single JSON object "
    "only. Do not use markdown code fences and do not add any text before or "
    "after the JSON."
)


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the response.")
    return json.loads(cleaned[start : end + 1])


def _generate(user_prompt: str, build, label: str):
    """Call the model, parse and validate; retry once if the output is invalid."""
    last_error = ""
    for _ in range(MAX_ATTEMPTS):
        prompt = user_prompt
        if last_error:
            prompt += (
                f"\n\nYour previous answer was rejected: {last_error}\n"
                "Return a corrected JSON object only."
            )
        raw = ask_model(SYSTEM_PROMPT, prompt)
        try:
            return build(_extract_json(raw))
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)[:300]
    raise GenerationError(
        f"The model did not return a valid {label} after {MAX_ATTEMPTS} attempts. "
        "Please try again."
    )



def generate_course(topic: str, difficulty: str, lesson_count: int) -> Course:
    prompt = f"""Create a course outline.
Topic: {topic}
Difficulty: {difficulty}
Number of lessons: exactly {lesson_count}

Return JSON in exactly this shape:
{{
  "title": "course title",
  "description": "short course description",
  "objectives": ["course objective"],
  "lessons": [
    {{"title": "lesson title", "objectives": ["lesson learning objective"], "summary": "short lesson summary"}}
  ]
}}
The "lessons" array must contain exactly {lesson_count} items."""

    def build(data: dict) -> Course:
        course = Course.model_validate(data)
        if len(course.lessons) != lesson_count:
            raise ValueError(
                f"Expected exactly {lesson_count} lessons but got {len(course.lessons)}."
            )
        return course

    return _generate(prompt, build, "course outline")


def generate_lesson(
    topic: str, difficulty: str, course_title: str, lesson: Lesson
) -> LessonContent:
    objectives = "\n".join(f"- {o}" for o in lesson.objectives)
    prompt = f"""Write the full content of one lesson.
Course topic: {topic}
Course title: {course_title}
Difficulty: {difficulty}
Lesson title: {lesson.title}
Lesson summary: {lesson.summary}
Lesson objectives:
{objectives}

Return JSON in exactly this shape:
{{
  "introduction": "...",
  "sections": [{{"heading": "...", "explanation": "...", "example": "..."}}],
  "summary": "...",
  "exercises": [{{"task": "...", "hint": "..."}}]
}}
Rules: 2 to 4 sections; exactly 2 exercises; every exercise has a hint."""
    return _generate(prompt, LessonContent.model_validate, "lesson")



def generate_quiz(
    topic: str,
    difficulty: str,
    course_title: str,
    lesson: Lesson,
    content: LessonContent | None = None,
) -> Quiz:
    objectives = "\n".join(f"- {o}" for o in lesson.objectives)
    covered = ""
    if content is not None:
        headings = ", ".join(s.heading for s in content.sections)
        covered = f"\nSections covered in the lesson: {headings}"
    prompt = f"""Write a multiple-choice quiz for one lesson.
Course topic: {topic}
Course title: {course_title}
Difficulty: {difficulty}
Lesson title: {lesson.title}
Lesson summary: {lesson.summary}
Lesson objectives:
{objectives}{covered}

Return JSON in exactly this shape:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "why the correct option is right"
    }}
  ]
}}
Rules: exactly 5 questions; each has exactly 4 distinct options; "correct_index" is
the zero-based index (0-3) of the single correct option; vary the position of the
correct option across questions."""
    return _generate(prompt, Quiz.model_validate, "quiz")
