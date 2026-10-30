import streamlit as st

from generator import generate_course, generate_lesson, generate_quiz
from grading import grade_quiz
from llm_client import GenerationError
from models import Course, LessonContent, Quiz

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
LESSON_COUNTS = [2, 3, 4, 5]

st.set_page_config(page_title="Mini ClassBuild", layout="wide")


def init_state() -> None:
    """Create every session-state key once; never overwrite existing values."""
    defaults = {
        "course_settings": None,  
        "outline": None,  
        "course_id": 0,  
        "selected_lesson": 0,
        "lessons": {},  
        "quizzes": {},  
        "quiz_attempts": {},  
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def handle_generate(topic: str, difficulty: str, lesson_count: int) -> None:
    topic = topic.strip()
    if not topic:
        st.warning("Please enter a course topic before generating an outline.")
        return

    try:
        with st.spinner("Generating course outline..."):
            course = generate_course(topic, difficulty, lesson_count)
    except GenerationError as exc:
        st.error(str(exc))  
        return

   
    st.session_state.course_id += 1
    st.session_state.course_settings = {
        "topic": topic,
        "difficulty": difficulty,
        "lesson_count": lesson_count,
    }
    st.session_state.outline = course
    st.session_state.lessons = {}
    st.session_state.quizzes = {}
    st.session_state.quiz_attempts = {}
    st.session_state.selected_lesson = 0
    st.session_state.pop("lesson_picker", None)


def render_outline(course: Course) -> None:
    st.subheader(course.title)
    st.write(course.description)
    st.markdown("**Course objectives**")
    for objective in course.objectives:
        st.markdown(f"- {objective}")
    st.markdown("**Lessons**")
    for number, lesson in enumerate(course.lessons, start=1):
        with st.expander(f"Lesson {number}: {lesson.title}"):
            st.write(lesson.summary)
            st.markdown("Learning objectives")
            for objective in lesson.objectives:
                st.markdown(f"- {objective}")


def render_lesson_content(content: LessonContent) -> None:
    st.markdown("#### Introduction")
    st.write(content.introduction)
    for number, section in enumerate(content.sections, start=1):
        st.markdown(f"#### {number}. {section.heading}")
        st.write(section.explanation)
        st.markdown("**Example**")
        st.write(section.example)
    st.markdown("#### Summary")
    st.write(content.summary)
    st.markdown("#### Exercises")
    for number, exercise in enumerate(content.exercises, start=1):
        st.markdown(f"**Exercise {number}.** {exercise.task}")
        with st.expander("Show hint"):
            st.write(exercise.hint)


def render_quiz(quiz: Quiz, key: tuple[int, int]) -> None:
    course_id, lesson_index = key
    attempt = st.session_state.quiz_attempts.setdefault(
        key, {"attempt": 0, "result": None}
    )

    if attempt["result"] is None:
        form_id = f"quiz_form_{course_id}_{lesson_index}_{attempt['attempt']}"
        with st.form(form_id):
            choices = []
            for number, question in enumerate(quiz.questions, start=1):
                choice = st.radio(
                    f"{number}. {question.question}",
                    options=list(range(len(question.options))),
                    format_func=lambda i, q=question: q.options[i],
                    index=None,
                    key=f"{form_id}_q{number}",
                )
                choices.append(choice)
            submitted = st.form_submit_button("Submit answers")
        if submitted:
            if any(choice is None for choice in choices):
                st.warning("Please answer all 5 questions before submitting.")
            else:
                attempt["result"] = grade_quiz(quiz, choices)  # local grading
                st.rerun()
        return

    result = attempt["result"]
    st.metric("Score", f"{result['score']} / {len(quiz.questions)}")
    for number, question in enumerate(quiz.questions, start=1):
        chosen = result["answers"][number - 1]
        is_correct = result["correct"][number - 1]
        st.markdown(f"**{number}. {question.question}**")
        st.write(f"Your answer: {question.options[chosen]}")
        if is_correct:
            st.success("Correct.")
        else:
            st.error(f"Incorrect. Correct answer: {question.options[question.correct_index]}")
        st.caption(question.explanation)
    if st.button("Retake quiz", key=f"retake_{course_id}_{lesson_index}"):
        attempt["attempt"] += 1  
        attempt["result"] = None
        st.rerun()



def render_lesson_section(course: Course, settings: dict) -> None:
    course_id = st.session_state.course_id
    index = st.selectbox(
        "Select a lesson",
        options=list(range(len(course.lessons))),
        format_func=lambda i: f"Lesson {i + 1}: {course.lessons[i].title}",
        key="lesson_picker",
    )
    st.session_state.selected_lesson = index
    key = (course_id, index)
    lesson = course.lessons[index]

   
    content = st.session_state.lessons.get(key)
    if content is None:
        if st.button("Generate Lesson Content", key=f"gen_lesson_{course_id}_{index}"):
            try:
                with st.spinner("Generating lesson..."):
                    content = generate_lesson(
                        settings["topic"], settings["difficulty"], course.title, lesson
                    )
                st.session_state.lessons[key] = content
            except GenerationError as exc:
                st.error(str(exc))
        else:
            st.info("This lesson has not been generated yet.")
    if content is not None:
        render_lesson_content(content)

    st.divider()

   
    st.markdown("### Quiz")
    quiz = st.session_state.quizzes.get(key)
    if quiz is None:
        if st.button("Generate Quiz", key=f"gen_quiz_{course_id}_{index}"):
            try:
                with st.spinner("Generating quiz..."):
                    quiz = generate_quiz(
                        settings["topic"],
                        settings["difficulty"],
                        course.title,
                        lesson,
                        content,
                    )
                st.session_state.quizzes[key] = quiz
            except GenerationError as exc:
                st.error(str(exc))
        else:
            st.info("Generate a five-question quiz for this lesson.")
    if quiz is not None:
        render_quiz(quiz, key)



init_state()

st.title("Mini ClassBuild")
st.write(
    "Enter a topic, choose a difficulty and a lesson count. Mini ClassBuild "
    "generates a course outline, full lessons and a five-question quiz for each lesson."
)

col_topic, col_difficulty, col_count = st.columns([3, 1, 1])
with col_topic:
    topic_input = st.text_input(
        "Course Topic",
        key="topic_input",
        placeholder="For example: Introduction to Python",
    )
with col_difficulty:
    difficulty_input = st.selectbox("Difficulty", DIFFICULTIES, key="difficulty_input")
with col_count:
    count_input = st.selectbox("Number of lessons", LESSON_COUNTS, key="count_input")

if st.button("Generate Course Outline", type="primary"):
    handle_generate(topic_input, difficulty_input, count_input)

st.divider()

outline = st.session_state.outline
if outline is None:
    st.info("No course yet. Enter a topic above and select Generate Course Outline.")
else:
    settings = st.session_state.course_settings
    st.caption(
        f"{settings['topic']} | {settings['difficulty']} | "
        f"{settings['lesson_count']} lessons"
    )
    render_outline(outline)
    st.divider()
    st.header("Lesson")
    render_lesson_section(outline, settings)
