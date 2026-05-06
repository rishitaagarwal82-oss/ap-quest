import streamlit as st

buttons = ["AP Calculus AB", "AP Calculus BC", "AP Statistics", "AP Computer Science A", "AP Computer Science Principles", "AP Biology", "AP Chemistry", "AP Physics 1", "AP Physics 2", "AP Physics C: Mechanics", "AP Environmental Science", "AP U.S. History", "AP World History: Modern", "AP European History", "AP Psychology", "AP U.S. Government and Politics", "AP English Language and Composition", "AP English Literature and Composition", "AP Spanish Language and Culture", "AP French Language and Culture"]
if "ap" not in st.session_state:
    st.session_state.ap = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if st.session_state.page =="home":
    st.title("Welcome to **AP Quest!**")
    st.header("What would you like to practice today?")
    for ap in buttons:
        if st.button(ap):
            st.session_state.page = "quiz"
            st.session_state.ap = ap
            st.rerun()
if st.session_state.page == "quiz":
    st.title( st.session_state.ap + " style questions")            
    if st.button("Back"):
        st.session_state.page = "home"
        st.rerun()
