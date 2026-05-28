
import os
import secrets
from urllib.parse import urlencode
import base64

import requests
import streamlit as st
import streamlit.components.v1 as components
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
    page_icon="🍃",
    layout="wide"
)

# =========================
# HELPER FOR BASE64 IMAGES
# =========================
def get_base64_of_bin_file(bin_file):
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
    except:
        pass
    return ""

img_base64 = get_base64_of_bin_file('images/IMG_1779.webp')

# =========================
# CUSTOM CSS (CUTE INDIE STYLE)
# =========================
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@300;400;700&family=Quicksand:wght@300;400;700&display=swap" rel="stylesheet">

<style>
/* Base Styles */
html, body, .stApp, button, input, textarea {{
    font-family: 'Quicksand', sans-serif !important;
    color: #434343 !important;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Comfortaa', cursive !important;
    color: #434343 !important;
}}

#MainMenu {{
    visibility:hidden;
}}

footer {{
    visibility:hidden;
}}

header {{
    visibility:hidden;
}}

.stApp {{
    background-color: #FCF8F1; /* Cream Background */
}}

/* Hero Section */
.hero {{
    padding: 3rem;
    border-radius: 35px;
    background: #E2B3B3; /* Dusty Rose */
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 8px 8px 0px #D6C9B0; /* Sticker effect shadow */
    border: 3px solid #434343;
}}

.hero h1 {{
    font-size: 65px !important;
    margin-bottom: 10px;
    letter-spacing: -2px;
}}

.logo-container {{
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}}

.logo-img {{
    width: 150px;
    height: auto;
    border-radius: 20px;
    border: 2px solid #434343;
    background: white;
    padding: 10px;
    box-shadow: 4px 4px 0px #434343;
}}

/* Subject Cards */
.subject-card {{
    background: #F3E5AB;
    padding: 2rem;
    border-radius: 30px;
    text-align: center;
    border: 3px solid #434343;
    box-shadow: 6px 6px 0px #D6C9B0;
    margin-bottom: 1.5rem;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}

.subject-card:hover {{
    transform: scale(1.02) rotate(-1deg);
}}

/* XP & Stats Boxes */
.xp-box {{
    background: #9CAF88; /* Sage Green */
    padding: 1.5rem;
    border-radius: 25px;
    text-align: center;
    border: 3px solid #434343;
    box-shadow: 4px 4px 0px #D6C9B0;
}}

.xp-box h2, .xp-box p {{
    color: white !important;
}}

/* Buttons */
.stButton button {{
    background-color: #9CAF88 !important;
    color: white !important;
    border-radius: 25px !important;
    border: 3px solid #434343 !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 700 !important;
    box-shadow: 3px 3px 0px #434343 !important;
    text-transform: lowercase;
}}

.stButton button:hover {{
    background-color: #E2B3B3 !important;
    transform: translateY(-2px);
    box-shadow: 5px 5px 0px #434343 !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 15px;
    background-color: transparent;
}}

.stTabs [data-baseweb="tab"] {{
    background-color: #D6C9B0;
    border-radius: 20px 20px 0 0;
    padding: 12px 25px;
    color: #434343;
    font-weight: bold;
}}

.stTabs [aria-selected="true"] {{
    background-color: #E2B3B3 !important;
    color: #434343 !important;
}}

/* Input Fields */
.stTextInput input, .stTextArea textarea {{
    border-radius: 20px !important;
    border: 3px solid #D6C9B0 !important;
    background-color: white !important;
    padding: 15px !important;
}}

/* Divider */
hr {{
    border: 0;
    height: 3px;
    background: #D6C9B0;
    margin: 2.5rem 0;
    border-radius: 10px;
}}

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
    if not username or username == "Guest":
        return

    c.execute(
        "UPDATE users SET xp = xp + ? WHERE username=?",
        (amount, username)
    )

    conn.commit()


def get_config_value(name, default=""):
    env_value = os.getenv(name)
    if env_value:
        return env_value
    try:
        if hasattr(st, "secrets") and name in st.secrets and st.secrets[name]:
            return st.secrets[name]
    except:
        pass
    return default


def is_guest():
    return st.session_state.get("guest_mode", False)


def get_google_redirect_uri():
    configured = get_config_value("GOOGLE_REDIRECT_URI", "")
    if configured:
        return configured
    return st.session_state.get("host_url", "")


def ensure_host_url():
    if "host_url" in st.session_state:
        return

    params = st.query_params
    if "host_url" in params:
        st.session_state.host_url = params["host_url"][0]
        st.query_params.clear()
        st.rerun()

    components.html(
        """
        <script>
        const origin = window.location.origin;
        const search = window.location.search;
        const delim = search.includes('?') ? '&' : '?';
        window.location.replace(window.location.pathname + search + delim + 'host_url=' + encodeURIComponent(origin));
        </script>
        """,
        height=0,
    )


GOOGLE_CLIENT_ID = get_config_value("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_config_value("GOOGLE_CLIENT_SECRET")
GOOGLE_SCOPE = "openid email profile"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def get_google_auth_url():
    state = secrets.token_urlsafe(16)
    st.session_state.google_oauth_state = state
    redirect_uri = get_google_redirect_uri()
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code):
    redirect_uri = get_google_redirect_uri()
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
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
    name = userinfo.get("name", "")
    if not email:
        return None

    # Use name as username if available, otherwise use email
    username = name if name else email
    existing = get_user_data(username)
    if not existing:
        create_user(username, secrets.token_urlsafe(32))

    return username


# =========================
# LOAD QUESTIONS
# =========================

try:
    if os.path.exists("questions.csv"):
        df = pd.read_csv("questions.csv")
    else:
        df = pd.DataFrame([
            {"ap": "AP Biology", "question": "What produces ATP?", "choice_a": "Mitochondria", "choice_b": "Nucleus", "choice_c": "Ribosome", "choice_d": "Golgi apparatus", "correct_answer": "A", "explanation": "Mitochondria are the powerhouse of the cell.", "created_by": "System"},
            {"ap": "AP Calculus AB", "question": "Derivative of x^2?", "choice_a": "x", "choice_b": "2x", "choice_c": "x^2", "choice_d": "2", "correct_answer": "B", "explanation": "Power rule: d/dx x^n = n*x^(n-1)", "created_by": "System"}
        ])

    if os.path.exists("frqs.csv"):
        frq_df = pd.read_csv("frqs.csv")
    else:
        frq_df = pd.DataFrame([
            {"ap": "AP Biology", "frq": "Explain natural selection.", "sample_answer": "Natural selection is the process where organisms better adapted to their environment tend to survive and produce more offspring."}
        ])
except Exception as e:
    st.error(f"Error loading data: {e}")
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
    "submitted": False,
    "iscorrect": None,
    "frq_answer": "",
    "google_oauth_state": None,
    "guest_mode": False,
    "questions_answered": 0,
    "correct_items": 0,
    "first_try": {},
    "last_q": None,
    "ap": None,
    "mode": "mcq",
    "frq_answered": 0
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Initialize XP and streak if not present
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0

query_params = st.query_params
if "code" in query_params:
    code = query_params["code"][0] if isinstance(query_params["code"], list) else query_params["code"]
    state = query_params.get("state", [""])[0]

    if state != st.session_state.google_oauth_state:
        st.warning("Google sign-in state mismatch (possibly due to page refresh). Proceeding anyway for deployed apps.")
        # Continue instead of failing

    token_data = exchange_google_code(code)
    if token_data and "access_token" in token_data:
        userinfo = get_google_userinfo(token_data["access_token"])
        username = handle_google_login(userinfo)
        if username:
            st.session_state.logged_in = True
            st.session_state.guest_mode = False
            st.session_state.username = username
            # Load user XP from database
            user_data = get_user_data(username)
            if user_data:
                st.session_state.xp = user_data[2]
                st.session_state.streak = user_data[3]
            st.session_state.page = "dashboard"
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Unable to read Google account information.")
    else:
        st.error("Google sign-in failed. Please try again.")

# =========================
# LOGIN PAGE
# =========================

if st.session_state.page == "login":

    if not get_config_value("GOOGLE_REDIRECT_URI", ""):
        ensure_host_url()

    logo_html = f"<img src='data:image/webp;base64,{img_base64}' class='logo-img'>" if img_base64 else "🎓"

    st.markdown(f"""
    <div class='hero'>
        <div class='logo-container'>
            {logo_html}
        </div>
        <h1>hello, friend! 🍃</h1>
        <h3>Welcome to 5score, your cozy place to study for AP exams.</h3>
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
                        st.session_state.guest_mode = False
                        st.session_state.username = username
                        # Load user XP from database
                        st.session_state.xp = user[2]
                        st.session_state.streak = user[3]
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
                        st.session_state.guest_mode = False
                        st.session_state.username = new_user
                        # Load user XP from database (will be 0 for new users)
                        st.session_state.xp = 0
                        st.session_state.streak = 0
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
        st.info(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables "
            "or add them to .streamlit/secrets.toml."
        )

    if st.button("Continue as Guest"):
        st.session_state.logged_in = False
        st.session_state.guest_mode = True
        st.session_state.username = "Guest"
        st.session_state.page = "dashboard"
        st.rerun()

# =========================
# DASHBOARD
# =========================

subjects = sorted(list(df["ap"].unique()))

if st.session_state.page == "dashboard":

    if st.session_state.logged_in:
        # Use XP from session state (loaded at login)
        xp = st.session_state.get("xp", 0)
        streak = st.session_state.get("streak", 0)
        level = xp // 100
    else:
        xp = 0
        streak = 0
        level = 0

    logo_html = f"<img src='data:image/webp;base64,{img_base64}' class='logo-img'>" if img_base64 else "✨"

    st.markdown(f"""
    <div class='hero'>
        <div class='logo-container'>
            {logo_html}
        </div>
        <h1>ready to study, {st.session_state.username}?</h1>
        <h3>Level {level} explorer</h3>
    </div>
    """, unsafe_allow_html=True)

    if is_guest():
        st.warning("Guest mode is active. Progress will not be saved.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class='xp-box'>
            <h2>{xp}</h2>
            <p>Knowledge Gained (XP)</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='xp-box'>
            <h2>{streak}</h2>
            <p>Day Streak</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='xp-box'>
            <h2>{level}</h2>
            <p>Study Level</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.header("pick your path")

    cols = st.columns(3)

    for i, subject in enumerate(subjects):
        with cols[i % 3]:
            st.markdown("<div class='subject-card'>", unsafe_allow_html=True)

            st.subheader(subject)

            if st.button(f"Start MCQs", key=f"mcq_{subject}"):
                st.session_state.mode = "mcq"
                st.session_state.subject = subject
                st.session_state.ap = subject
                st.session_state.page = "quiz"
                st.session_state.q_index = 0
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("Practice FRQs", key="frq_nav"):
        st.session_state.mode = "frq"
        st.session_state.q_index = 0
        st.session_state.page = "selectap"
        st.rerun()

# =========================
# SELECT AP FOR FRQ
# =========================

if st.session_state.page == "selectap":
    st.title("Select AP Subject for FRQ Practice")
    frq_subjects = sorted(list(frq_df["ap"].unique()))
    colsFRQ = st.columns(3)
    for i, subject in enumerate(frq_subjects):
        with colsFRQ[i % 3]:
            st.markdown("<div class='subject-card'>", unsafe_allow_html=True)
            st.subheader(subject)
            if st.button(f"Select FRQs", key=f"frq_sel_{subject}"):
                st.session_state.ap = subject
                st.session_state.q_index = 0
                st.session_state.submitted = False
                st.session_state.frq_answered = 0
                st.session_state.page = "frq"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅ Back to Dashboard", key="back_from_frq_sel"):
        st.session_state.page = "dashboard"
        st.rerun()

# =========================
# QUIZ PAGE
# =========================

if st.session_state.page == "quiz":
    disabled = st.session_state.submitted and st.session_state.iscorrect is True
    st.title("🍃 " + st.session_state.ap)
    ap_questions = df[df["ap"] == st.session_state.ap]

    total = len(ap_questions)

    if total == 0:
        st.warning("No questions available for this AP subject. Return home to choose a different quiz.")

    progress = (st.session_state.questions_answered / total) if total > 0 else 0
    st.write(f"Question {st.session_state.questions_answered} of {total}")
    st.progress(min(progress, 1.0))

    if  st.session_state.q_index>=total:
        if st.session_state.questions_answered > 0:
            score = st.session_state.correct_items / st.session_state.questions_answered
        else:
            score = 0

        st.balloons()
        st.success(f"🎉 You finished! Your score is {score * 100:.1f}%!")

        if st.button("Return Home"):
            st.session_state.q_index = 0
            st.session_state.correct_items = 0
            st.session_state.questions_answered = 0
            st.session_state.first_try = {}
            st.session_state.page = "dashboard"
            st.rerun()
        st.stop()

    def current_question():
        return ap_questions.iloc[st.session_state.q_index]
    def reset_quiz():
        st.session_state.q_index = 0
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.correct_items = 0
        st.session_state.questions_answered = 0
        st.session_state.first_try = {}
        st.rerun()
    def go_back():
        st.session_state.page = "dashboard"
        reset_quiz()
    if st.button("⬅ Back to Dashboard"):
        go_back()

    if "last_q" not in st.session_state:
        st.session_state.last_q = None
    if st.session_state.q_index != st.session_state.last_q:
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.last_q = st.session_state.q_index



    st.header(current_question()["question"])


    answer = st.radio(
    "Choose an answer:",
    [
        f"A — {current_question()['choice_a']}",
        f"B — {current_question()['choice_b']}",
        f"C — {current_question()['choice_c']}",
        f"D — {current_question()['choice_d']}",
    ],
    disabled=st.session_state.submitted,
    key=f"q_{st.session_state.q_index}"
    )
    selected_letter = answer[0]



 # SUBMISSION

    if st.button("Submit Answer",disabled=st.session_state.submitted) and not st.session_state.submitted:
        st.session_state.submitted = True
        is_correct = selected_letter == current_question()["correct_answer"]
        if st.session_state.q_index not in st.session_state.first_try:
            st.session_state.first_try[st.session_state.q_index] = is_correct
            st.session_state.questions_answered += 1
            if is_correct:
                st.session_state.correct_items += 1
                if st.session_state.logged_in:
                    add_xp(st.session_state.username, 10)
                    st.session_state.xp += 10
        st.session_state.iscorrect = is_correct


        st.rerun()
 # RESULTS
    if st.session_state.submitted:

        if st.session_state.iscorrect == True:
            st.success("You got it! ✅")
            st.write("**Explanation:**", current_question()["explanation"])

            if st.button("Next Question"):
                st.session_state.q_index +=1
                st.session_state.iscorrect = None
                st.session_state.submitted = False
                st.rerun()
        elif st.session_state.iscorrect == False:
            st.error("Not quite right... ❌")

            if st.button("Try again"):
                st.session_state.submitted = False
                st.session_state.iscorrect = None
                st.rerun()
        st.write("Correct so far:", st.session_state.correct_items)

# =========================
# FRQ PAGE
# =========================
if st.session_state.page == "frq":

    st.title("🍂 " + st.session_state.ap + " FRQ practice")
    filtered_frq = frq_df[frq_df["ap"] == st.session_state.ap]
    total = len(filtered_frq)
    if st.session_state.q_index >= total:
        st.success("FRQ set complete 🎉")
        if st.button("Return Home"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.stop()

    progress = 0
    if total > 0:
        progress = st.session_state.frq_answered / total

    st.write(f"FRQs completed: {st.session_state.frq_answered} / {total}")
    st.progress(min(progress, 1.0))
    def current_frq():
        return filtered_frq.iloc[st.session_state.q_index]


    st.info(current_frq()["frq"])

    response = st.text_area(
        "Write your response here...",
        height=300,
        key="frq_answer"
    )

    if st.button("Submit FRQ", disabled=st.session_state.submitted):
        st.session_state.submitted = True
        word_count = len(response.split())

        st.success("FRQ Submitted")
        st.session_state.frq_answered += 1
        st.write("**Sample High-Scoring Response:**", current_frq()["sample_answer"])
        st.write(f"Word Count: {word_count}")

        if word_count > 150:
            st.success("Strong depth of explanation")
        elif word_count > 80:
            st.warning("Decent response but could use more detail")
        else:
            st.error("Response likely too short")

        if st.session_state.logged_in:
            add_xp(st.session_state.username, 25)
            st.session_state.xp += 25
        else:
            st.info("Guest mode: progress will not be saved.")
    if st.button("Next FRQ", disabled=not st.session_state.submitted):
        st.session_state.q_index += 1
        st.session_state.submitted = False
        st.rerun()
    if st.button("⬅ Back to Dashboard", key="back_from_frq"):
        st.session_state.page = "dashboard"
        st.rerun()
