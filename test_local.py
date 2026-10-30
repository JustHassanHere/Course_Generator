import copy
import json
import os
from unittest.mock import patch

from pydantic import ValidationError

import generator
import llm_client
from grading import grade_quiz
from llm_client import ConfigError, GenerationError
from models import Course, LessonContent, Quiz


def course_data(n):
    return {
        "title": "Intro",
        "description": "d",
        "objectives": ["o"],
        "lessons": [
            {"title": f"L{i}", "objectives": ["x"], "summary": "s"} for i in range(n)
        ],
    }


def lesson_data():
    return {
        "introduction": "i",
        "sections": [{"heading": "h", "explanation": "e", "example": "x"}] * 2,
        "summary": "s",
        "exercises": [{"task": "t", "hint": "h"}] * 2,
    }


def quiz_data():
    return {
        "questions": [
            {
                "question": f"q{i}",
                "options": ["a", "b", "c", "d"],
                "correct_index": i % 4,
                "explanation": "e",
            }
            for i in range(5)
        ]
    }


def raises(exc_type, fn, *args):
    try:
        fn(*args)
    except exc_type:
        return True
    return False


def run_with_replies(replies, fn, *args):
    calls = []

    def fake(system, user, temperature=0.4):
        calls.append(user)
        return replies[min(len(calls) - 1, len(replies) - 1)]

    with patch.object(generator, "ask_model", fake):
        try:
            return fn(*args), len(calls)
        except GenerationError:
            return "ERROR", len(calls)


def main():

    for n in (2, 3, 5):
        course, calls = run_with_replies([json.dumps(course_data(n))], generator.generate_course, "Python", "Beginner", n)
        assert len(course.lessons) == n and calls == 1, n
    bad = course_data(2)
    del bad["title"]
    assert raises(ValidationError, Course.model_validate, bad)
    result, calls = run_with_replies([json.dumps(bad)], generator.generate_course, "Python", "Beginner", 2)
    assert result == "ERROR" and calls == generator.MAX_ATTEMPTS
    result, calls = run_with_replies([json.dumps(course_data(4))], generator.generate_course, "Python", "Beginner", 3)
    assert result == "ERROR"  
    result, calls = run_with_replies(["not json", json.dumps(course_data(3))], generator.generate_course, "Python", "Beginner", 3)
    assert result != "ERROR" and calls == 2  
    fenced = "```json\n" + json.dumps(course_data(2)) + "\n```"
    result, _ = run_with_replies([fenced], generator.generate_course, "Python", "Beginner", 2)
    assert result != "ERROR"

    lesson = LessonContent.model_validate(lesson_data())
    assert len(lesson.exercises) == 2
    bad = lesson_data(); bad["sections"] = bad["sections"][:1]
    assert raises(ValidationError, LessonContent.model_validate, bad)
    bad = lesson_data(); bad["sections"] = bad["sections"] * 3
    assert raises(ValidationError, LessonContent.model_validate, bad)
    bad = lesson_data(); bad["exercises"] = bad["exercises"][:1]
    assert raises(ValidationError, LessonContent.model_validate, bad)
    bad = lesson_data(); bad["exercises"][0] = {"task": "t"}
    assert raises(ValidationError, LessonContent.model_validate, bad)

    
    quiz = Quiz.model_validate(quiz_data())
    bad = quiz_data(); bad["questions"] = bad["questions"][:4]
    assert raises(ValidationError, Quiz.model_validate, bad)
    bad = quiz_data(); bad["questions"][0]["options"] = ["a", "b", "c"]
    assert raises(ValidationError, Quiz.model_validate, bad)
    bad = quiz_data(); bad["questions"][0]["correct_index"] = 4
    assert raises(ValidationError, Quiz.model_validate, bad)
    bad = quiz_data(); bad["questions"][0]["options"] = ["a", "a", "c", "d"]
    assert raises(ValidationError, Quiz.model_validate, bad)

    perfect = [q.correct_index for q in quiz.questions]
    assert grade_quiz(quiz, perfect)["score"] == 5
    wrong = [(q.correct_index + 1) % 4 for q in quiz.questions]
    assert grade_quiz(quiz, wrong)["score"] == 0
    mixed = copy.copy(perfect); mixed[0] = (mixed[0] + 1) % 4
    assert grade_quiz(quiz, mixed)["score"] == 4
    assert raises(ValueError, grade_quiz, quiz, [0, 1, None, 0, 1])

    
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GROQ_API_KEY", None)
        assert raises(ConfigError, llm_client.get_client)

    print("All local checks passed (no Groq request was made).")


if __name__ == "__main__":
    main()
