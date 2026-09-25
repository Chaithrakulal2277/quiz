import streamlit as st
from pypdf import PdfReader
import pandas as pd
import re
import sqlite3
import hashlib
from collections import Counter
from urllib.parse import quote_plus


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="StatLearn AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# DATABASE
# ==========================================================

DB_NAME = "learning_platform.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            login_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER PRIMARY KEY,
            quiz_score INTEGER DEFAULT 0,
            progress INTEGER DEFAULT 0,
            mistakes TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


create_database()


# ==========================================================
# PASSWORD HASHING
# ==========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# ==========================================================
# SESSION STATE
# ==========================================================

defaults = {

    "logged_in": False,
    "user_id": None,
    "username": "",

    "pdf_text": "",
    "pdf_name": "",

    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_score": 0,
    "quiz_completed": False,

    "mistakes": Counter(),

    "learning_progress": 0,

    "chat_history": [],

    "decision_score": 0,

    "show_answer": {},

    "quiz_feedback": [],

    "language": "English"
}


for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================================
# TOPIC DATABASE
# ==========================================================

TOPICS = {

    "Mean": [
        "mean",
        "average",
        "arithmetic mean"
    ],

    "Median": [
        "median",
        "middle value"
    ],

    "Mode": [
        "mode",
        "most frequent"
    ],

    "Probability": [
        "probability",
        "random",
        "event",
        "sample space"
    ],

    "Statistics": [
        "statistics",
        "statistical",
        "data analysis"
    ],

    "Data Quality": [
        "missing data",
        "duplicate",
        "inconsistent",
        "data quality",
        "validation"
    ],

    "Sampling": [
        "sampling",
        "sample",
        "population",
        "random sampling"
    ],

    "Correlation": [
        "correlation",
        "relationship",
        "pearson"
    ],

    "Regression": [
        "regression",
        "linear regression",
        "prediction"
    ]
}


# ==========================================================
# PDF FUNCTIONS
# ==========================================================

def extract_pdf_text(uploaded_file):

    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def detect_topics(text):

    detected = []

    text_lower = text.lower()

    for topic, keywords in TOPICS.items():

        for keyword in keywords:

            if keyword.lower() in text_lower:

                detected.append(topic)

                break

    return detected


def search_document(text, keyword):

    results = []

    for line in text.split("\n"):

        if keyword.lower() in line.lower():

            if line.strip():

                results.append(line.strip())

    return results[:30]


# ==========================================================
# QUIZ GENERATOR
# ==========================================================

def generate_questions(text):

    questions = []

    detected = detect_topics(text)

    if "Mean" in detected:

        questions.append({

            "question": "What is the arithmetic mean?",

            "options": [
                "The middle value",
                "The most frequent value",
                "The sum of values divided by the number of values",
                "The largest value"
            ],

            "answer":
                "The sum of values divided by the number of values",

            "topic": "Mean",

            "feedback":
                "Mean is calculated by adding all values and dividing by the total number of values."

        })


    if "Median" in detected:

        questions.append({

            "question": "What does the median represent?",

            "options": [
                "Most frequent value",
                "Middle value after arranging data",
                "Average of all values",
                "Largest value"
            ],

            "answer":
                "Middle value after arranging data",

            "topic": "Median",

            "feedback":
                "Median is the middle value after arranging observations in order."

        })


    if "Mode" in detected:

        questions.append({

            "question": "What is the mode?",

            "options": [
                "Middle value",
                "Average value",
                "Most frequently occurring value",
                "Smallest value"
            ],

            "answer":
                "Most frequently occurring value",

            "topic": "Mode",

            "feedback":
                "Mode is the observation that occurs most frequently."

        })


    if "Probability" in detected:

        questions.append({

            "question": "What does probability measure?",

            "options": [
                "Data size",
                "Likelihood of an event",
                "Average",
                "Data storage"
            ],

            "answer":
                "Likelihood of an event",

            "topic": "Probability",

            "feedback":
                "Probability measures how likely an event is to occur."

        })


    if "Sampling" in detected:

        questions.append({

            "question": "What is a sample in statistics?",

            "options": [
                "The entire population",
                "A subset of the population",
                "Only incorrect data",
                "A graph"
            ],

            "answer":
                "A subset of the population",

            "topic": "Sampling",

            "feedback":
                "A sample is a selected subset used to study a larger population."

        })


    if "Correlation" in detected:

        questions.append({

            "question": "What does correlation describe?",

            "options": [
                "A relationship between variables",
                "Only missing values",
                "Data duplication",
                "A type of database"
            ],

            "answer":
                "A relationship between variables",

            "topic": "Correlation",

            "feedback":
                "Correlation describes the strength and direction of a relationship between variables."

        })


    # Default questions

    if not questions:

        questions = [

            {
                "question": "What is statistics?",

                "options": [
                    "The study and analysis of data",
                    "A programming language",
                    "A database",
                    "An operating system"
                ],

                "answer":
                    "The study and analysis of data",

                "topic": "Statistics",

                "feedback":
                    "Statistics deals with collecting, analyzing, interpreting and presenting data."
            },

            {
                "question": "What is data?",

                "options": [
                    "Collected facts or observations",
                    "Only numbers",
                    "Only text",
                    "Only graphs"
                ],

                "answer":
                    "Collected facts or observations",

                "topic": "Statistics",

                "feedback":
                    "Data consists of collected facts, observations or measurements."
            }
        ]

    return questions


# ==========================================================
# AI ASSISTANT
# ==========================================================

def assistant_answer(question):

    q = question.lower()

    answers = {

        "mean":
            "Mean is the average of a set of values. Add all values and divide the total by the number of values.",

        "median":
            "Median is the middle value after arranging the observations in ascending or descending order.",

        "mode":
            "Mode is the value that occurs most frequently in a dataset.",

        "probability":
            "Probability represents the likelihood of an event occurring. It ranges from 0 to 1.",

        "correlation":
            "Correlation measures the strength and direction of the relationship between two variables.",

        "sampling":
            "Sampling means selecting a smaller group from a larger population for statistical analysis.",

        "data quality":
            "Data quality describes how accurate, complete, consistent and valid a dataset is."
    }

    for keyword, answer in answers.items():

        if keyword in q:

            return answer

    return (
        "I can explain statistical concepts such as "
        "mean, median, mode, probability, sampling, "
        "correlation and data quality."
    )


# ==========================================================
# DATABASE PROGRESS
# ==========================================================

def save_progress():

    if not st.session_state.logged_in:
        return

    conn = get_connection()
    cursor = conn.cursor()

    mistakes_text = ",".join(
        f"{k}:{v}"
        for k, v in st.session_state.mistakes.items()
    )

    cursor.execute("""
        INSERT OR REPLACE INTO progress
        (user_id, quiz_score, progress, mistakes)
        VALUES (?, ?, ?, ?)
    """, (
        st.session_state.user_id,
        st.session_state.quiz_score,
        st.session_state.learning_progress,
        mistakes_text
    ))

    conn.commit()
    conn.close()


def load_progress():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quiz_score, progress, mistakes
        FROM progress
        WHERE user_id=?
    """, (
        st.session_state.user_id,
    ))

    row = cursor.fetchone()

    conn.close()

    if row:

        st.session_state.quiz_score = row[0] or 0

        st.session_state.learning_progress = row[1] or 0

        st.session_state.mistakes = Counter()

        if row[2]:

            for item in row[2].split(","):

                if ":" in item:

                    topic, count = item.rsplit(":", 1)

                    try:

                        st.session_state.mistakes[
                            topic
                        ] = int(count)

                    except ValueError:

                        pass


# ==========================================================
# LOGIN PAGE
# ==========================================================

def login_page():

    st.markdown("""
    <style>

    .login-box {
        max-width: 500px;
        margin: 60px auto;
        padding: 35px;
        border-radius: 20px;
        background: white;
        box-shadow: 0px 5px 25px rgba(0,0,0,0.10);
    }

    .login-title {
        text-align: center;
        font-size: 40px;
        font-weight: 700;
    }

    .login-subtitle {
        text-align: center;
        color: #666666;
        margin-bottom: 30px;
    }

    </style>
    """, unsafe_allow_html=True)


    st.markdown(
        '<div class="login-title">📊 StatLearn AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">'
        'AI-Enabled Learning Platform for Statistical Capacity Building'
        '</div>',
        unsafe_allow_html=True
    )


    tab1, tab2 = st.tabs([
        "🔐 Login",
        "📝 Create Account"
    ])


    # ======================================================
    # LOGIN
    # ======================================================

    with tab1:

        st.subheader("Welcome Back 👋")

        login_id = st.text_input(
            "Email or Phone Number",
            key="login_id"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )


        if st.button(
            "🔓 Login",
            use_container_width=True
        ):

            if not login_id.strip() or not password:

                st.warning(
                    "Please enter your email/phone number and password."
                )

            else:

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, username, password
                    FROM users
                    WHERE LOWER(TRIM(login_id)) =
                          LOWER(TRIM(?))
                    """,
                    (login_id,)
                )

                user = cursor.fetchone()

                conn.close()


                if user is not None:

                    stored_password = user[2]

                    if stored_password == hash_password(password):

                        # Login success

                        st.session_state.logged_in = True

                        st.session_state.user_id = user[0]

                        st.session_state.username = user[1]

                        # Load saved progress

                        load_progress()

                        st.success(
                            f"Welcome back, {user[1]}! 🎉"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "❌ Incorrect password."
                        )

                else:

                    st.error(
                        "❌ Account not found."
                    )

                    st.info(
                        "Please check your email/phone number "
                        "or create an account first."
                    )


    # ======================================================
    # CREATE ACCOUNT
    # ======================================================

    with tab2:

        st.subheader("Create Your LearnAI Account 🚀")

        username = st.text_input(
            "Student Name",
            key="register_name"
        )

        register_id = st.text_input(
            "Email or Phone Number",
            key="register_id"
        )

        register_password = st.text_input(
            "Create Password",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_password"
        )


        if st.button(
            "✨ Create Account",
            use_container_width=True
        ):

            username = username.strip()

            register_id = register_id.strip()


            # Validation

            if not username:

                st.warning(
                    "Please enter your name."
                )

            elif not register_id:

                st.warning(
                    "Please enter your email or phone number."
                )

            elif not register_password:

                st.warning(
                    "Please create a password."
                )

            elif register_password != confirm_password:

                st.error(
                    "❌ Passwords do not match."
                )

            else:

                conn = get_connection()
                cursor = conn.cursor()


                # Check existing account

                cursor.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(TRIM(login_id)) =
                          LOWER(TRIM(?))
                    """,
                    (register_id,)
                )

                existing_user = cursor.fetchone()


                if existing_user:

                    conn.close()

                    st.error(
                        "⚠️ This email/phone number is already registered."
                    )

                    st.info(
                        "Go to the Login tab and use your existing password."
                    )

                else:

                    # Save user

                    cursor.execute(
                        """
                        INSERT INTO users
                        (username, login_id, password)
                        VALUES (?, ?, ?)
                        """,
                        (
                            username,
                            register_id,
                            hash_password(register_password)
                        )
                    )


                    user_id = cursor.lastrowid


                    # Create progress record

                    cursor.execute(
                        """
                        INSERT INTO progress
                        (user_id, quiz_score, progress, mistakes)
                        VALUES (?, 0, 0, '')
                        """,
                        (user_id,)
                    )


                    conn.commit()

                    conn.close()


                    st.success(
                        "🎉 Account created successfully!"
                    )

                    st.info(
                        "Your account has been saved. "
                        "Now open the Login tab and sign in."
                    )


# ==========================================================
# SHOW LOGIN
# ==========================================================

if not st.session_state.logged_in:

    login_page()

    st.stop()


# ==========================================================
# CUSTOM CSS
# ==========================================================

st.markdown("""
<style>

.main-title {
    font-size: 40px;
    font-weight: 700;
}

.subtitle {
    font-size: 18px;
    color: #666666;
}

.feature-card {
    padding: 20px;
    border-radius: 15px;
    background: #f7f9fc;
    border: 1px solid #e5e7eb;
    margin-bottom: 15px;
}

.section-title {
    font-size: 28px;
    font-weight: 700;
    margin-top: 10px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    f"""
    <div class="main-title">
        📊 StatLearn AI
    </div>

    <div class="subtitle">
        Personalized Statistical Learning Platform
    </div>
    """,
    unsafe_allow_html=True
)

st.write(
    f"Welcome, **{st.session_state.username}** 👋"
)

st.divider()


# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.title("📚 Learning Platform")

st.sidebar.write(
    f"👤 {st.session_state.username}"
)


menu = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Dashboard",
        "📄 PDF Learning",
        "🔎 Search & Topics",
        "🤖 AI Assistant",
        "📝 Interactive Quiz",
        "📚 Study Notes",
        "🎯 Skill Gap",
        "🛣️ Learning Path",
        "📊 Data Quality",
        "🎮 Decision Simulator",
        "❌ Mistake Tracking",
        "🌐 Multilingual",
        "🎥 Related Videos",
        "📈 Progress Dashboard"
    ]
)


st.sidebar.divider()


if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):

    # Save progress before logout

    save_progress()

    st.session_state.logged_in = False

    st.session_state.user_id = None

    st.session_state.username = ""

    st.session_state.pdf_text = ""

    st.session_state.pdf_name = ""

    st.session_state.quiz_questions = []

    st.session_state.quiz_answers = {}

    st.session_state.quiz_feedback = []

    st.session_state.quiz_completed = False

    st.session_state.chat_history = []

    st.rerun()


# ==========================================================
# DASHBOARD
# ==========================================================

if menu == "🏠 Dashboard":

    st.header("🏠 Student Dashboard")


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "📚 Topics",
            len(
                detect_topics(
                    st.session_state.pdf_text
                )
            )
        )


    with col2:

        st.metric(
            "📝 Quiz Score",
            f"{st.session_state.quiz_score}%"
        )


    with col3:

        st.metric(
            "❌ Mistakes",
            sum(
                st.session_state.mistakes.values()
            )
        )


    with col4:

        st.metric(
            "📈 Progress",
            f"{st.session_state.learning_progress}%"
        )


    st.divider()

    st.subheader("🚀 Learning Modules")


    features = [

        (
            "📄",
            "PDF Learning",
            "Upload and analyze statistical learning material."
        ),

        (
            "🤖",
            "AI Personal Assistant",
            "Ask questions and get simple explanations."
        ),

        (
            "📝",
            "Interactive Quiz",
            "Practice MCQs and receive instant feedback."
        ),

        (
            "🎯",
            "Skill Gap Detection",
            "Identify weak statistical concepts."
        ),

        (
            "🛣️",
            "Personalized Learning Path",
            "Follow a learning path based on performance."
        ),

        (
            "📊",
            "Data Quality Checker",
            "Find missing, duplicate and inconsistent data."
        ),

        (
            "🎮",
            "Decision Simulator",
            "Practice real-world statistical decisions."
        ),

        (
            "🌐",
            "Multilingual Learning",
            "Learn concepts in English, Kannada and Hindi."
        )

    ]


    for icon, title, description in features:

        st.markdown(
            f"""
            <div class="feature-card">

                <h3>{icon} {title}</h3>

                <p>{description}</p>

            </div>
            """,
            unsafe_allow_html=True
        )


# ==========================================================
# PDF LEARNING
# ==========================================================

elif menu == "📄 PDF Learning":

    st.header("📄 PDF Learning")

    st.write(
        "Upload your statistical learning material."
    )


    uploaded_file = st.file_uploader(
        "Choose PDF",
        type=["pdf"]
    )


    if uploaded_file:

        if st.button(
            "🔍 Analyze PDF",
            use_container_width=True
        ):

            try:

                text = extract_pdf_text(
                    uploaded_file
                )

                st.session_state.pdf_text = text

                st.session_state.pdf_name = uploaded_file.name

                st.session_state.quiz_questions = []

                st.session_state.quiz_completed = False

                st.success(
                    "PDF analyzed successfully!"
                )

            except Exception as e:

                st.error(
                    f"Error reading PDF: {e}"
                )


    if st.session_state.pdf_text:

        st.divider()

        st.subheader("📋 Document Information")


        col1, col2 = st.columns(2)


        with col1:

            st.info(
                f"📄 File: {st.session_state.pdf_name}"
            )


        with col2:

            st.info(
                f"📝 Characters: {len(st.session_state.pdf_text)}"
            )


        detected = detect_topics(
            st.session_state.pdf_text
        )


        st.subheader("🧠 Detected Topics")


        if detected:

            cols = st.columns(3)


            for i, topic in enumerate(detected):

                cols[i % 3].success(
                    f"📌 {topic}"
                )

        else:

            st.warning(
                "No predefined topics detected."
            )


        st.subheader("📖 Extracted Content")


        st.text_area(
            "Document text",
            st.session_state.pdf_text[:15000],
            height=350
        )


# ==========================================================
# SEARCH & TOPICS
# ==========================================================

elif menu == "🔎 Search & Topics":

    st.header("🔎 Search & Topics")


    if not st.session_state.pdf_text:

        st.warning(
            "Upload a PDF first."
        )

    else:

        st.subheader("🧠 Detected Topics")


        detected = detect_topics(
            st.session_state.pdf_text
        )


        for topic in detected:

            st.write(
                f"📌 **{topic}**"
            )


        st.divider()


        keyword = st.text_input(
            "🔎 Search for a word or concept"
        )


        if keyword:

            results = search_document(
                st.session_state.pdf_text,
                keyword
            )


            if results:

                st.subheader(
                    f"Found {len(results)} result(s)"
                )


                for result in results:

                    st.info(result)

            else:

                st.warning(
                    "No matching content found."
                )


# ==========================================================
# AI ASSISTANT
# ==========================================================

elif menu == "🤖 AI Assistant":

    st.header(
        "🤖 AI Personal Learning Assistant"
    )


    st.write(
        "Ask questions about statistical concepts."
    )


    question = st.text_input(
        "💬 Your question"
    )


    if st.button(
        "💡 Ask AI",
        use_container_width=True
    ):

        if question:

            answer = assistant_answer(
                question
            )


            st.session_state.chat_history.append(
                (question, answer)
            )


    if st.session_state.chat_history:

        st.subheader("💬 Conversation")


        for q, a in st.session_state.chat_history:

            st.markdown(
                f"**You:** {q}"
            )

            st.success(
                f"AI: {a}"
            )


# ==========================================================
# INTERACTIVE QUIZ
# ==========================================================

elif menu == "📝 Interactive Quiz":

    st.header("📝 Interactive MCQ Quiz")


    if not st.session_state.pdf_text:

        st.warning(
            "Upload a PDF first."
        )

    else:

        if st.button(
            "🤖 Generate Quiz",
            use_container_width=True
        ):

            st.session_state.quiz_questions = (
                generate_questions(
                    st.session_state.pdf_text
                )
            )

            st.session_state.quiz_answers = {}

            st.session_state.quiz_feedback = []

            st.session_state.quiz_completed = False

            st.session_state.quiz_score = 0

            st.session_state.show_answer = {}


        questions = st.session_state.quiz_questions


        if questions:

            st.info(
                f"📚 {len(questions)} questions generated."
            )


            for i, q in enumerate(questions):

                st.divider()

                st.subheader(
                    f"Question {i + 1}"
                )


                st.write(
                    f"**Topic:** {q['topic']}"
                )


                st.write(
                    f"### {q['question']}"
                )


                # ------------------------------------------
                # ANSWER BUTTON
                # ------------------------------------------

                if not st.session_state.show_answer.get(
                    i,
                    False
                ):

                    if st.button(
                        "🟢 Answer",
                        key=f"answer_button_{i}"
                    ):

                        st.session_state.show_answer[i] = True

                        st.rerun()


                # ------------------------------------------
                # OPTIONS
                # ------------------------------------------

                if st.session_state.show_answer.get(
                    i,
                    False
                ):

                    answer = st.radio(
                        "Select your answer:",
                        q["options"],
                        key=f"option_{i}"
                    )


                    st.session_state.quiz_answers[
                        i
                    ] = answer


            st.divider()


            if st.button(
                "✅ Submit Quiz",
                use_container_width=True
            ):

                score = 0

                feedback = []


                for i, q in enumerate(questions):

                    selected = (
                        st.session_state.quiz_answers.get(
                            i
                        )
                    )


                    if selected == q["answer"]:

                        score += 1


                        feedback.append({

                            "number": i + 1,

                            "question":
                                q["question"],

                            "selected":
                                selected,

                            "correct":
                                q["answer"],

                            "status":
                                "Correct",

                            "feedback":
                                q["feedback"],

                            "topic":
                                q["topic"]

                        })


                    else:

                        st.session_state.mistakes[
                            q["topic"]
                        ] += 1


                        feedback.append({

                            "number": i + 1,

                            "question":
                                q["question"],

                            "selected":
                                selected if selected
                                else "Not answered",

                            "correct":
                                q["answer"],

                            "status":
                                "Wrong",

                            "feedback":
                                q["feedback"],

                            "topic":
                                q["topic"]

                        })


                st.session_state.quiz_score = int(
                    score / len(questions) * 100
                )


                st.session_state.quiz_feedback = feedback

                st.session_state.quiz_completed = True


                st.session_state.learning_progress = min(
                    100,
                    st.session_state.learning_progress + 10
                )


                save_progress()

                st.rerun()


            # ------------------------------------------
            # RESULT
            # ------------------------------------------

            if st.session_state.quiz_completed:

                st.divider()

                st.subheader("📊 Quiz Result")


                score = st.session_state.quiz_score


                if score >= 80:

                    st.success(
                        f"🎉 Excellent! Score: {score}%"
                    )

                elif score >= 50:

                    st.warning(
                        f"👍 Good effort! Score: {score}%"
                    )

                else:

                    st.error(
                        f"📚 More practice recommended. Score: {score}%"
                    )


                st.progress(
                    score / 100
                )


                st.subheader(
                    "📝 Answer Review & Feedback"
                )


                for item in st.session_state.quiz_feedback:

                    if item["status"] == "Correct":

                        st.success(
                            f"Q{item['number']} ✅ Correct"
                        )

                        st.write(
                            f"Your answer: {item['selected']}"
                        )

                    else:

                        st.error(
                            f"Q{item['number']} ❌ Wrong"
                        )

                        st.write(
                            f"Your answer: {item['selected']}"
                        )

                        st.write(
                            f"Correct answer: "
                            f"**{item['correct']}**"
                        )


                    st.info(
                        f"💡 Feedback: {item['feedback']}"
                    )


# ==========================================================
# STUDY NOTES
# ==========================================================

elif menu == "📚 Study Notes":

    st.header("📚 Study Notes")


    if not st.session_state.pdf_text:

        st.warning(
            "Upload a PDF first."
        )

    else:

        detected = detect_topics(
            st.session_state.pdf_text
        )


        st.write(
            "Select a topic to view quick study notes."
        )


        if detected:

            topic = st.selectbox(
                "Choose topic",
                detected
            )


            notes = {

                "Mean":
                    "Mean = Sum of all observations / Number of observations.",

                "Median":
                    "Median is the middle value after arranging observations.",

                "Mode":
                    "Mode is the most frequently occurring observation.",

                "Probability":
                    "Probability measures the likelihood of an event.",

                "Sampling":
                    "Sampling selects a subset from a larger population.",

                "Correlation":
                    "Correlation measures the relationship between variables.",

                "Regression":
                    "Regression is used to study relationships and make predictions.",

                "Data Quality":
                    "Good data should be accurate, complete, consistent, valid and reliable.",

                "Statistics":
                    "Statistics involves collecting, analyzing, interpreting and presenting data."
            }


            st.success(
                notes.get(
                    topic,
                    "Study the uploaded document for this topic."
                )
            )


# ==========================================================
# SKILL GAP
# ==========================================================

elif menu == "🎯 Skill Gap":

    st.header("🎯 AI Skill-Gap Detection")


    if not st.session_state.quiz_questions:

        st.info(
            "Complete a quiz first."
        )

    else:

        detected = detect_topics(
            st.session_state.pdf_text
        )


        for topic in detected:

            mistakes = st.session_state.mistakes.get(
                topic,
                0
            )


            if mistakes == 0:

                st.success(
                    f"🟢 {topic} — Good understanding"
                )

            elif mistakes == 1:

                st.warning(
                    f"🟡 {topic} — Needs revision"
                )

            else:

                st.error(
                    f"🔴 {topic} — Weak area"
                )


        st.divider()


        st.subheader(
            "🎯 Recommended Improvement"
        )


        for topic, count in st.session_state.mistakes.items():

            if count > 0:

                st.write(
                    f"📚 Practice **{topic}** "
                    f"with additional MCQs and study notes."
                )


# ==========================================================
# LEARNING PATH
# ==========================================================

elif menu == "🛣️ Learning Path":

    st.header("🛣️ Personalized Learning Path")


    st.write(
        "Your learning path changes according to your performance."
    )


    weak_topics = [

        topic

        for topic, count
        in st.session_state.mistakes.items()

        if count > 0
    ]


    if weak_topics:

        steps = [

            "📖 Review study notes",

            "🤖 Ask the AI assistant",

            "🎥 Watch a related video",

            "📝 Practice MCQs",

            "🔁 Retake the quiz"

        ]


        for topic in weak_topics:

            st.subheader(
                f"🎯 Improve: {topic}"
            )


            for step in steps:

                st.write(
                    f"→ {step}"
                )


            st.divider()


    else:

        st.success(
            "No major skill gaps detected yet."
        )


# ==========================================================
# DATA QUALITY
# ==========================================================

elif menu == "📊 Data Quality":

    st.header(
        "📊 AI Data-Quality Checker ⭐"
    )


    st.write(
        "Upload sample CSV data to identify common data-quality problems."
    )


    uploaded_csv = st.file_uploader(
        "Upload CSV",
        type=["csv"]
    )


    if uploaded_csv:

        try:

            df = pd.read_csv(
                uploaded_csv
            )


            st.subheader("📋 Dataset")


            st.dataframe(
                df,
                use_container_width=True
            )


            st.divider()


            # Missing values

            st.subheader(
                "1️⃣ Missing Values"
            )


            missing = df.isnull().sum()


            if missing.sum() == 0:

                st.success(
                    "No missing values found."
                )

            else:

                st.warning(
                    "Missing values detected."
                )


                st.dataframe(
                    missing[missing > 0]
                )


            # Duplicate

            st.subheader(
                "2️⃣ Duplicate Records"
            )


            duplicate_count = df.duplicated().sum()


            if duplicate_count == 0:

                st.success(
                    "No duplicate rows found."
                )

            else:

                st.warning(
                    f"{duplicate_count} duplicate rows found."
                )


            # Inconsistent

            st.subheader(
                "3️⃣ Possible Inconsistencies"
            )


            found = False


            for column in df.columns:

                if df[column].dtype == "object":

                    values = (
                        df[column]
                        .dropna()
                        .astype(str)
                    )


                    normalized = {}


                    for value in values:

                        key = re.sub(
                            r"\s+",
                            " ",
                            value.strip().lower()
                        )


                        normalized.setdefault(
                            key,
                            []
                        ).append(value)


                    for key, variants in normalized.items():

                        if len(set(variants)) > 1:

                            found = True


                            st.warning(
                                f"{column}: "
                                f"{list(set(variants))}"
                            )


            if not found:

                st.success(
                    "No obvious text inconsistencies found."
                )


            st.divider()


            st.subheader(
                "🤖 Explanation"
            )


            st.info(
                "Missing values reduce completeness. "
                "Duplicate records can affect statistical results. "
                "Inconsistent spellings or formats can cause incorrect "
                "grouping and analysis."
            )


        except Exception as e:

            st.error(
                f"Could not analyze the CSV: {e}"
            )


# ==========================================================
# DECISION SIMULATOR
# ==========================================================

elif menu == "🎮 Decision Simulator":

    st.header(
        "🎮 Statistical Decision Simulator ⭐"
    )


    st.subheader(
        "Scenario"
    )


    st.write(
        "A government survey contains data from several districts. "
        "Some districts have very few responses."
    )


    st.write(
        "You need to prepare the dataset before analysis."
    )


    decision = st.radio(
        "What should you do first?",
        [
            "Delete the small districts",
            "Check data quality and sample sizes",
            "Ignore the problem",
            "Duplicate records"
        ]
    )


    if st.button(
        "Evaluate Decision",
        use_container_width=True
    ):

        if decision == "Check data quality and sample sizes":

            st.success(
                "✅ Good decision!"
            )

            st.info(
                "Before analysis, data quality, sample size and "
                "representativeness should be checked."
            )

            st.session_state.decision_score = 1

        else:

            st.warning(
                "⚠️ Review the decision."
            )

            st.info(
                "Statistical analysis should begin by checking "
                "data quality and sample characteristics."
            )


# ==========================================================
# MISTAKE TRACKING
# ==========================================================

elif menu == "❌ Mistake Tracking":

    st.header(
        "❌ Mistake Tracking & Improvement"
    )


    if not st.session_state.mistakes:

        st.success(
            "🎉 No mistakes recorded yet."
        )

    else:

        for topic, count in st.session_state.mistakes.items():

            st.write(
                f"**{topic}** → {count} mistake(s)"
            )


            if count >= 2:

                st.error(
                    "🔴 Repeated mistake — targeted practice recommended."
                )

            else:

                st.warning(
                    "🟡 Review this topic once more."
                )


# ==========================================================
# MULTILINGUAL
# ==========================================================

elif menu == "🌐 Multilingual":

    st.header(
        "🌐 Multilingual Learning"
    )


    language = st.selectbox(
        "Select language",
        [
            "English",
            "Kannada",
            "Hindi"
        ]
    )


    concept = st.selectbox(
        "Select concept",
        [
            "Mean",
            "Median",
            "Mode",
            "Probability"
        ]
    )


    explanations = {

        "English": {

            "Mean":
                "Mean is the average of a set of numbers.",

            "Median":
                "Median is the middle value after arranging the data.",

            "Mode":
                "Mode is the most frequently occurring value.",

            "Probability":
                "Probability tells us how likely an event is."

        },


        "Kannada": {

            "Mean":
                "Mean ಅಂದರೆ ಸಂಖ್ಯೆಗಳ ಸರಾಸರಿ.",

            "Median":
                "Median ಅಂದರೆ ಕ್ರಮವಾಗಿ ಜೋಡಿಸಿದ ದತ್ತಾಂಶದ ಮಧ್ಯದ ಮೌಲ್ಯ.",

            "Mode":
                "Mode ಅಂದರೆ ಹೆಚ್ಚು ಬಾರಿ ಕಾಣಿಸಿಕೊಳ್ಳುವ ಮೌಲ್ಯ.",

            "Probability":
                "Probability ಅಂದರೆ ಒಂದು ಘಟನೆ ಸಂಭವಿಸುವ ಸಾಧ್ಯತೆ."

        },


        "Hindi": {

            "Mean":
                "Mean संख्याओं का औसत होता है।",

            "Median":
                "Median व्यवस्थित डेटा का मध्य मान होता है।",

            "Mode":
                "Mode वह मान है जो सबसे अधिक बार आता है।",

            "Probability":
                "Probability किसी घटना के होने की संभावना बताती है।"

        }

    }


    st.success(
        explanations[language][concept]
    )


# ==========================================================
# RELATED VIDEOS
# ==========================================================

elif menu == "🎥 Related Videos":

    st.header(
        "🎥 Related Learning Videos"
    )


    st.write(
        "Select a topic to find educational videos."
    )


    topic = st.selectbox(
        "Choose topic",
        [
            "Statistics",
            "Mean",
            "Median",
            "Probability",
            "Sampling",
            "Correlation",
            "Regression",
            "Data Quality"
        ]
    )


    search_query = quote_plus(
        f"{topic} statistics tutorial"
    )


    youtube_url = (
        "https://www.youtube.com/results?search_query="
        + search_query
    )


    st.link_button(
        "▶️ Find Videos on YouTube",
        youtube_url,
        use_container_width=True
    )


    st.info(
        f"Recommended search: {topic} statistics tutorial"
    )


# ==========================================================
# PROGRESS DASHBOARD
# ==========================================================

elif menu == "📈 Progress Dashboard":

    st.header(
        "📈 Learning Progress Dashboard"
    )


    st.subheader(
        "Overall Learning Progress"
    )


    progress = (
        st.session_state.learning_progress
    )


    st.progress(
        progress / 100
    )


    st.write(
        f"### {progress}% completed"
    )


    st.divider()


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Quiz Score",
            f"{st.session_state.quiz_score}%"
        )


    with col2:

        st.metric(
            "Mistakes",
            sum(
                st.session_state.mistakes.values()
            )
        )


    with col3:

        st.metric(
            "Topics",
            len(
                detect_topics(
                    st.session_state.pdf_text
                )
            )
        )


    with col4:

        st.metric(
            "Questions",
            len(
                st.session_state.quiz_questions
            )
        )


    st.divider()


    st.subheader(
        "📚 Weak Areas"
    )


    if st.session_state.mistakes:

        for topic, count in st.session_state.mistakes.items():

            st.write(
                f"🔴 {topic}: {count} mistake(s)"
            )

    else:

        st.success(
            "No weak areas recorded."
        )


    st.divider()


    st.subheader(
        "🚀 Recommended Next Topics"
    )


    detected = detect_topics(
        st.session_state.pdf_text
    )


    for topic in detected:

        if topic not in st.session_state.mistakes:

            st.write(
                f"➡️ Continue learning **{topic}**"
            )