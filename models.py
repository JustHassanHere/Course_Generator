from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]



class Lesson(BaseModel):
    title: NonEmptyStr
    objectives: list[NonEmptyStr] = Field(min_length=1)
    summary: NonEmptyStr


class Course(BaseModel):
    title: NonEmptyStr
    description: NonEmptyStr
    objectives: list[NonEmptyStr] = Field(min_length=1)
    lessons: list[Lesson] = Field(min_length=1)


class Section(BaseModel):
    heading: NonEmptyStr
    explanation: NonEmptyStr
    example: NonEmptyStr


class Exercise(BaseModel):
    task: NonEmptyStr
    hint: NonEmptyStr


class LessonContent(BaseModel):
    introduction: NonEmptyStr
    sections: list[Section] = Field(min_length=2, max_length=4)
    summary: NonEmptyStr
    exercises: list[Exercise] = Field(min_length=2, max_length=2)


class QuizQuestion(BaseModel):
    question: NonEmptyStr
    options: list[NonEmptyStr] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)  # exactly one correct option
    explanation: NonEmptyStr

    @model_validator(mode="after")
    def options_must_be_distinct(self):
        lowered = [option.lower() for option in self.options]
        if len(set(lowered)) != len(lowered):
            raise ValueError("Answer options must be distinct.")
        return self


class Quiz(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=5, max_length=5)
