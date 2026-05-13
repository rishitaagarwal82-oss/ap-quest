# 5score — Gamified AP Practice Platform

## Project Structure

```text
5score/
│
├── app.py
├── questions.csv
├── users.db
├── requirements.txt
├── images/
│   ├── yuh.png
│   └── banner.webp
│
└── styles.css
```

---

# FULL APP CODE (app.py)

```python
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import random
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="5score",
    page_icon="🔥",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================

st.markdown("""
<style>

#MainMenu {
    visibility:hidden;
}

footer {
    visibility:hidden;
}

header {
    visibility:hidden;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(to bottom right, #0f172a, #111827);
    color: white;
}

.hero {
    padding: 2rem;
    border-radius: 25px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    margin-bottom: 2rem;
}

.subject-card {
    background: #1e293b;
    padding: 1rem;
    border-radius: 18px;
    text-align: center;
    border: 1px solid #334155;
}

.xp-box {
    background: #1d4ed8;
    padding: 1rem;
    border-radius: 18px;
    text-align:center;
}

.stButton button {
    width: 100%;
    border-radius: 15px;
    height: 3em;
    border: none;
    background: linear-gradient(90deg,#3b82f6,#8b5cf6);
    color: white;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================
# DATABASE SETUP
# =========================

conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT,
    xp INTEGER,
    streak INTEGER,
    joined TEXT
)
''')

conn.commit()

# =========================
# HELPER FUNCTIONS
# =========================


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    hashed = hash_password(password)

    c.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
        (username, hashed, 0, 0, str(datetime.now()))
    )

    conn.commit()


def login_user(username, password):
    hashed = hash_password(password)

    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hashed)
    )

    return c.fetchone()


def get_user_data(username):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()


def add_xp(username, amount):
    c.execute(
        "UPDATE users SET xp = xp + ? WHERE username=?",
        (amount, username)
    )

    conn.commit()


# =========================
# LOAD QUESTIONS
# =========================

try:
    df = pd.read_csv("questions.csv")
except:
    st.error("questions.csv not found")
    st.stop()

# =========================
# SESSION STATE
# =========================

DEFAULTS = {
    "logged_in": False,
    "username": None,
    "page": "login",
    "subject": None,
    "q_index": 0,
    "correct": 0,
    "answered": 0,
    "submitted": False,
    "iscorrect": None,
    "frq_answer": ""
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================
# LOGIN PAGE
# =========================

if st.session_state.page == "login":

    st.markdown("""
    <div class='hero'>
        <h1>🔥 5score</h1>
        <h3>Gamified AP Exam Practice</h3>
        <p>Level up your AP skills and earn XP.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Welcome Back")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username, password)

            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        st.subheader("Create Account")

        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password", type="password")

        if st.button("Create Account"):
            try:
                create_user(new_user, new_pass)
                st.success("Account created")
            except:
                st.error("Username already exists")

# =========================
# DASHBOARD
# =========================

if st.session_state.page == "dashboard":

    user_data = get_user_data(st.session_state.username)

    xp = user_data[2]
    streak = user_data[3]
    level = xp // 100

    st.markdown(f"""
    <div class='hero'>
        <h1>Welcome back, {st.session_state.username} 👋</h1>
        <h3>Level {level}</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class='xp-box'>
            <h2>{xp}</h2>
            <p>Total XP</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='xp-box'>
            <h2>{streak}</h2>
            <p>Current Streak</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='xp-box'>
            <h2>{level}</h2>
            <p>Level</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.header("Choose a Subject")

    subjects = [
        "AP Biology",
        "AP Chemistry",
        "AP Psychology",
        "AP Calculus AB",
        "AP Computer Science A",
        "AP World History"
    ]

    cols = st.columns(3)

    for i, subject in enumerate(subjects):
        with cols[i % 3]:
            st.markdown("<div class='subject-card'>", unsafe_allow_html=True)

            st.subheader(subject)

            if st.button(f"Practice {subject}"):
                st.session_state.subject = subject
                st.session_state.page = "quiz"
                st.session_state.q_index = 0
                st.session_state.correct = 0
                st.session_state.answered = 0
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("FRQ Practice"):
        st.session_state.page = "frq"
        st.rerun()

# =========================
# QUIZ PAGE
# =========================

if st.session_state.page == "quiz":

    st.title(f"📚 {st.session_state.subject}")

    subject_df = df[df["ap"] == st.session_state.subject]

    if len(subject_df) == 0:
        st.warning("No questions found")
        st.stop()

    question = subject_df.iloc[st.session_state.q_index]

    progress = st.session_state.q_index / len(subject_df)

    st.progress(progress)

    st.subheader(question["question"])

    answer = st.radio(
        "Choose an answer",
        [
            f"A. {question['choice_a']}",
            f"B. {question['choice_b']}",
            f"C. {question['choice_c']}",
            f"D. {question['choice_d']}"
        ]
    )

    if st.button("Submit"):

        selected = answer[0]

        if selected == question["correct_answer"]:
            st.success("Correct! +10 XP")
            st.session_state.correct += 1

            add_xp(st.session_state.username, 10)

        else:
            st.error("Incorrect")

        st.write(question["explanation"])

        st.session_state.answered += 1

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Next Question"):

            if st.session_state.q_index < len(subject_df) - 1:
                st.session_state.q_index += 1
                st.rerun()

    with col2:
        if st.button("Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

# =========================
# FRQ PAGE
# =========================

if st.session_state.page == "frq":

    st.title("✍️ FRQ Practice")

    prompts = [
        "Explain how natural selection contributes to evolution.",
        "Describe ONE cause of the Great Depression.",
        "Explain polymorphism in object-oriented programming."
    ]

    prompt = random.choice(prompts)

    st.info(prompt)

    response = st.text_area(
        "Write your FRQ response",
        height=300
    )

    if st.button("Submit FRQ"):

        word_count = len(response.split())

        st.success("FRQ Submitted")

        st.write(f"Word Count: {word_count}")

        if word_count > 150:
            st.success("Strong depth of explanation")
        elif word_count > 80:
            st.warning("Decent response but could use more detail")
        else:
            st.error("Response likely too short")

        add_xp(st.session_state.username, 25)

        st.balloons()

    if st.button("Return Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
