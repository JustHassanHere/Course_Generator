from models import Quiz


def grade_quiz(quiz: Quiz, answers: list[int | None]) -> dict:
    """Return the score (0-5) and per-question results for the chosen option indexes."""
    if len(answers) != len(quiz.questions):
        raise ValueError("One answer is required for every question.")
    if any(answer is None for answer in answers):
        raise ValueError("All questions must be answered before grading.")

    correct = [answer == q.correct_index for answer, q in zip(answers, quiz.questions)]
    return {"score": sum(correct), "answers": list(answers), "correct": correct}
