 import streamlit as st
 import pandas as pd
 df= pd.read_csv("questions.csv")
buttons = ["AP Calculus AB", "AP Calculus BC", "AP Statistics", "AP Computer Science A", "AP Computer Science Principles", "AP Biology", "AP Chemistry", "AP Physics 1", "AP Physics 2", "AP Physics C: Mechanics", "AP Environmental Science", "AP U.S. History", "AP World History: Modern", "AP European History", "AP Psychology", "AP U.S. Government and Politics", "AP English Language and Composition", "AP English Literature and Composition", "AP Spanish Language and Culture", "AP French Language and Culture"]

# DEFINE VARIABLES

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

# FUNCTIONS

def iscorrect():
    st.session_state.iscorrect = True
    st.badge("Correct ✅", color = "green")        
    st.write("Explanation:", current_question["explanation"])
    st.session_state.correct_items+=1

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
    
    st.title( st.session_state.ap + " style questions")     
    ap_questions = df[df["ap"] == st.session_state.ap]
    if "q_index" not in st.session_state:
        st.session_state.q_index = 0
    current_question = ap_questions.iloc[st.session_state.q_index]  
    disabled = st.session_state.submitted
    st.write(current_question["question"])  
    st.write("A:",current_question["choice_a"])   
    st.write("B:",current_question["choice_b"])  
    st.write("C:",current_question["choice_c"])  
    st.write("D:",current_question["choice_d"]) 
    answer = st.radio(
        "choose an answer:",
        ["A","B","C","D"],
        disabled=disabled
    ) 
 
 # SUBMISSION

    if st.button("submit"):
        st.session_state.submitted = True
        st.session_state.questions_answered +=1
        st.write("Questions answered:", st.session_state.questions_answered)
 
 # RESULTS

        if answer == current_question["answer"]:
            iscorrect()
        else:
            st.session_state.iscorrect = False
            st.badge("Incorrect ❌", color = "red")
        st.write("Correct questions:", st.session_state.correct_items)

 # RETRY

    if st.session_state.submitted and st.session_state.iscorrect is False:
        if st.button("Try again"):
                st.session_state.submitted = False
                st.session_state.iscorrect = None
                st.rerun()

 # RESET AND CHANGE QUIZZES
    
    if st.session_state.last_ap != st.session_state.ap:
        st.session_state.submitted = False
        st.session_state.iscorrect = None
        st.session_state.last_ap = st.session_state.ap
        
 # BACK BUTTON

    if st.button("Back"):
        st.session_state.page = "home"
        st.rerun()

 
           
    