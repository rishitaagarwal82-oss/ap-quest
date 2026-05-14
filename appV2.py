
import os
import secrets
from urllib.parse import urlencode

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
    page_icon="🎓",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Zen+Dots&display=swap" rel="stylesheet">

<style>
html, body, .stApp, button, input, textarea {
    font-family: 'Zen Dots', sans-serif !important;
}

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
    font-family: 'Zen Dots', sans-serif !important;
}

.stApp {
    background: black;
    color: white;
}

.hero {
    padding: 2rem;
    border-radius: 25px;
    background:#6FBF83;
    margin-bottom: 2rem;
}

.subject-card {
    background: #6AB6BA;
    padding: 1rem;
    border-radius: 18px;
    text-align: center;
    border: 1px solid #334155;
}

.xp-box {
    background: #A700BD;
    padding: 1rem;
    border-radius: 18px;
    text-align:center;
}
            
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

h1, h2, h3, p {
    color: white !important;
    font-family: 'Zen Dots', sans-serif !important;
}

h1 {
    font-size: 70px !important;
    font-family: 'Zen Dots', sans-serif !important;
}

.stApp {
    background: black;
}

.stButton button {
    background: black !important;
    color: white !important;
    border-radius: 15px;
    border-color: #334155 !important;
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
    if hasattr(st, "secrets") and name in st.secrets and st.secrets[name]:
        return st.secrets[name]
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
    "submitted": False,
    "iscorrect": None,
    "frq_answer": "",
    "google_oauth_state": None,
    "guest_mode": False,
    "questions_answered": 0,
    "correct_items": 0,
    "first_try": {},
    "last_q": None,
    "ap": None
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

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

    st.markdown("""
    <div class='hero'>
        <img src="IMG_1779.webp"width="120">
        <h1>🎓 5score</h1>
        <h3> AP Exam Practice, free forever.</h3>
        
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

if st.session_state.page == "dashboard":

    if st.session_state.logged_in:
        user_data = get_user_data(st.session_state.username)
        if user_data:
            xp = user_data[2]
            streak = user_data[3]
            level = xp // 100
        else:
            xp = 0
            streak = 0
            level = 0
    else:
        xp = 0
        streak = 0
        level = 0

    st.markdown(f"""
    <div class='hero'>
        <h1>Welcome back, {st.session_state.username} 👋</h1>
        <h3>Level {level}</h3>
    </div>
    """, unsafe_allow_html=True)

    if is_guest():
        st.warning("Guest mode is active. Progress will not be saved.")

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
                st.session_state.ap = subject
                st.session_state.page = "quiz"
                st.session_state.q_index = 0
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("FRQ Practice"):
        st.session_state.page = "selectap"
        st.rerun()
    if st.session_state.page == "selectap":
        colsFRQ = st.columns(3)

        for i, subject in enumerate(subjects):
            with colsFRQ[i % 3]:
                st.markdown("<div class='subject-card'>", unsafe_allow_html=True)

                st.subheader(subject)
                if st.button(f"Practice {subject} FRQs"):
                    st.session_state.ap = subject
                    st.session_state.page = "frq"
                    st.rerun()
# =========================
# QUIZ PAGE
# =========================

if st.session_state.page == "quiz":
    disabled = st.session_state.submitted and st.session_state.iscorrect is True
    st.title( st.session_state.ap + " style questions")     
    ap_questions = df[df["ap"] == st.session_state.ap]
    
    total = len(ap_questions)

    if total == 0:
        st.warning("No questions available for this AP subject. Return home to choose a different quiz.")
        
    progress = (st.session_state.questions_answered / total) 
    st.write(f"Question {st.session_state.questions_answered} of {total}")
    st.progress(progress, text=f"{int(progress * 100)}%")
    if progress > 1:
        st.progress(1.0, text="100%")


    if  st.session_state.q_index>=total:
        st.balloons()
        if st.session_state.questions_answered > 0:
           
            

            score = st.session_state.correct_items / st.session_state.questions_answered
        else:
            score = 0

        st.success(f"🎉 You finished! Your score is {score * 100:.1f}%!")
        
        if st.button("Return Home"):
            st.session_state.q_index = 0
            st.session_state.correct_items = 0
            st.session_state.questions_answered = 0
            st.session_state.first_try = {}
            st.session_state.page = "dashboard"
        st.stop()

    def current_question():
        return ap_questions.iloc[st.session_state.q_index] 
    if st.button("⬅ Back"):
        st.session_state.page = "dashboard"
        st.session_state.q_index = 0
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.correct_items = 0
        st.session_state.questions_answered = 0
        st.session_state.first_try = {}
        st.rerun()
    
    if "last_q" not in st.session_state:
        st.session_state.last_q = None
    if st.session_state.q_index != st.session_state.last_q:
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.last_q = st.session_state.q_index
    
    
    
    st.header(current_question()["question"], divider = "blue")


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

    if st.button("Submit",disabled=st.session_state.submitted) and not st.session_state.submitted:
        st.session_state.submitted = True
        is_correct = selected_letter == current_question()["correct_answer"]
        if st.session_state.q_index not in st.session_state.first_try:
            st.session_state.first_try[st.session_state.q_index] = is_correct
            st.session_state.questions_answered += 1
            if is_correct:
                st.session_state.correct_items += 1
                if st.session_state.logged_in:
                    add_xp(st.session_state.username, 10)
        st.session_state.iscorrect = is_correct
        
            
        st.rerun()
 # RESULTS
    if st.session_state.submitted:
        
        if st.session_state.iscorrect == True:
            st.success("Correct✅")        
            st.write("Explanation:", current_question()["explanation"])
           
            if st.button("Next"):
                st.session_state.q_index +=1
                st.session_state.iscorrect = None
                st.session_state.submitted = False
                st.rerun()
        elif st.session_state.iscorrect == False:
            st.error("Incorrect❌")

            if st.button("Try again"):
                st.session_state.submitted = False
                st.session_state.iscorrect = None
                st.rerun()
                st.write("Correct questions:", st.session_state.correct_items)

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

        if st.session_state.logged_in:
            add_xp(st.session_state.username, 25)
        else:
            st.info("Guest mode: progress will not be saved.")
