import streamlit as st

def menu():
    st.sidebar.page_link("pages/connection_page.py", label="Соединение с БД")
    st.sidebar.page_link("pages/parsing_page.py", label="Парсинг")