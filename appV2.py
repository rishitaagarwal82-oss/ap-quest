
import os
import secrets
from urllib.parse import urlencode

import requests
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


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
GOOGLE_SCOPE = "openid email profile"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def get_google_auth_url():
    state = secrets.token_urlsafe(16)
    st.session_state.google_oauth_state = state
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code):
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    return response.json() if response.ok else None


def get_google_userinfo(access_token):
    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json() if response.ok else None


def handle_google_login(userinfo):
    email = userinfo.get("email")
    if not email:
        return None

    username = email
    existing = get_user_data(username)
    if not existing:
        create_user(username, secrets.token_urlsafe(32))

    return username


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
    "frq_answer": "",
    "google_oauth_state": None
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

query_params = st.query_params
if "code" in query_params:
    code = query_params["code"]
    state = query_params.get("state", "")

    if state != st.session_state.google_oauth_state:
        st.error("Google sign-in failed due to invalid state.")
    else:
        token_data = exchange_google_code(code)
        if token_data and "access_token" in token_data:
            userinfo = get_google_userinfo(token_data["access_token"])
            username = handle_google_login(userinfo)
            if username:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "dashboard"
                st.experimental_set_query_params()
                st.experimental_rerun()
            else:
                st.error("Unable to read Google account information.")
        else:
            st.error("Google sign-in failed. Please try again.")

# =========================
# LOGIN PAGE
# =========================

if st.session_state.page == "login":

    st.markdown("""
    <div class='hero'>
        <h1> 5score</h1>
        <h3>Fun AP Exam Practice</h3>
        <p>Level up your AP skills and earn XP.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Welcome Back")

        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_clicked = st.form_submit_button("Login")

            if login_clicked:
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    user = login_user(username, password)

                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Check your username and password.")

    with tab2:
        st.subheader("Create Account")

        with st.form("signup_form"):
            new_user = st.text_input("Create Username", key="signup_username")
            new_pass = st.text_input("Create Password", type="password", key="signup_password")
            signup_clicked = st.form_submit_button("Create Account")

            if signup_clicked:
                if not new_user or not new_pass:
                    st.warning("Please enter both a username and password.")
                else:
                    try:
                        create_user(new_user, new_pass)
                        st.success("Account created. You are now logged in.")
                        st.session_state.logged_in = True
                        st.session_state.username = new_user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists. Choose a different one.")
                    except Exception:
                        st.error("Unable to create account. Please try again.")

    st.markdown("<div style='margin: 1rem 0; text-align:center; color:#94a3b8;'>or</div>", unsafe_allow_html=True)

    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        google_auth_url = get_google_auth_url()
        st.markdown(
            f"<div style='text-align:center;'>"
            f"<a href='{google_auth_url}' style='text-decoration:none;'>"
            f"<button style='width:100%; padding:0.75rem 1rem; border:none; border-radius:15px; background:#4285F4; color:white; font-weight:bold; cursor:pointer;'>"
            f"Continue with Google"
            f"</button>"
            f"</a>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables.")

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
