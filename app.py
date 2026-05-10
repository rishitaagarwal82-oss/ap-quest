import streamlit as st
st.set_page_config(
    page_title="AP Quest",
    page_icon="🎓"
)
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
import pandas as pd
df= pd.read_csv("questions.csv", on_bad_lines="skip")
buttons = ["AP Calculus AB", "AP Calculus BC", "AP Statistics", "AP Computer Science A", "AP Computer Science Principles", "AP Biology", "AP Chemistry", "AP Physics 1", "AP Physics 2", "AP Physics C: Mechanics", "AP Environmental Science", "AP U.S. History", "AP World History: Modern", "AP European History", "AP Psychology", "AP U.S. Government and Politics", "AP English Language and Composition", "AP English Literature and Composition", "AP Spanish Language and Culture", "AP French Language and Culture"]

# DEFINE VARIABLES
if "answered_index" not in st.session_state:
    st.session_state.answered_index= set()
if "correct_items" not in st.session_state:
    st.session_state.correct_items = 0
if "questions_answered" not in st.session_state:
    st.session_state.questions_answered = 0
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "iscorrect" not in st.session_state:
    st.session_state.iscorrect = None
if "ap" not in st.session_state:
    st.session_state.ap = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "last_ap" not in st.session_state:
    st.session_state.last_ap = None
if "correct_index" not in st.session_state:
    st.session_state.correct_index = set()
if "first_try" not in st.session_state:
    st.session_state.first_try = {}
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
# HOME AND QUIZ PAGES

if st.session_state.page =="home":
    st.title("Welcome to **AP Quest!**")
    st.header("What would you like to practice today?")

# RENDER AP BUTTONS

    for ap in buttons:
        if st.button(ap):
            st.session_state.page = "quiz"
            st.session_state.ap = ap
            st.rerun()
    
# RENDER CSV DATA

if st.session_state.page == "quiz":
    disabled = st.session_state.submitted and st.session_state.iscorrect is True
    st.title( st.session_state.ap + " style questions")     
    ap_questions = df[df["ap"] == st.session_state.ap]
    
    total = len(ap_questions)

    if  st.session_state.q_index>=total:
        if st.session_state.questions_answered > 0:
            score = st.session_state.correct_items / st.session_state.questions_answered
        else:
            score = 0

        st.success(f"🎉 You finished! Your score is {score * 100:.1f}%!")
        st.session_state.q_index = 0
        st.session_state.correct_items= 0
        st.session_state.questions_answered = 0
        st.stop()

    def current_question():
        return ap_questions.iloc[st.session_state.q_index] 
    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.session_state.q_index = 0
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.correct_items= 0
        st.session_state.questions_answered = 0
        st.rerun()
    
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

    if st.button("Submit",disabled=st.session_state.submitted) and not st.session_state.submitted:
        st.session_state.submitted = True
        is_correct = selected_letter == current_question()["correct_answer"]
        if st.session_state.q_index not in st.session_state.first_try:
            st.session_state.first_try[st.session_state.q_index] = is_correct
            if is_correct:
                st.session_state.correct_items+=1
        st.session_state.iscorrect = is_correct
        if st.session_state.q_index not in st.session_state.answered_index: 
            st.session_state.questions_answered +=1 
            st.session_state.answered_index.add(st.session_state.q_index)
            st.rerun()
 # RESULTS
    if st.session_state.submitted:
        if st.session_state.iscorrect == True:
            st.success("Correct✅")        
            st.write("Explanation:", current_question()["explanation"])
            if st.session_state.q_index not in st.session_state.correct_index:
                st.session_state.correct_index.add(st.session_state.q_index)
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
        st.write("Questions Answered:", st.session_state.questions_answered)
        
        

 # RESET AND CHANGE QUIZZES
    
    if st.session_state.last_ap != st.session_state.ap:
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.last_ap = st.session_state.ap


   
    
 
           
    