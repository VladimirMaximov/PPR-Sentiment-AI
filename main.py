import streamlit as st
from menu import menu
from pages.connection_page import connection_page
from pages.parsing_page import parsing_page

def main():
    st.set_page_config(
        page_title="Sentiment AI",
        layout="wide",
    )

    st.session_state.page = "Соединение с БД"

    menu()
    
    if st.session_state.page == "Соединение с БД":
        connection_page()
    elif st.session_state.page == "Парсинг":
        pass
    elif st.session_state.page == "Аналитика":
        pass
    elif st.session_state.page == "SQL запросы":
        pass
    elif st.session_state.page == "Дополнительно":
        pass

if __name__ == "__main__":
    main()