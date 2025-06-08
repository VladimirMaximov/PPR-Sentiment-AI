import streamlit as st
from menu import menu

def connection_page():
    st.title("Соединение с базой данных")
    st.markdown("### Информация о соединении")

    # Две колонки: слева поля ввода, справа статус
    col1, col2 = st.columns([2, 1])

    with col1:
        # Поля ввода
        host = st.text_input("PG_HOST", value="", placeholder="Введите адрес хоста")
        port = st.text_input("PG_PORT", value="", placeholder="Введите порт")
        user = st.text_input("PG_USER", value="", placeholder="Введите имя пользователя")
        password = st.text_input("PG_PASSWORD", value="", type="password", placeholder="Введите пароль")

        # Кнопка подключения
        if st.button("Подключить"):
            # Здесь будет реальная логика подключения
            # Например:
            # try:
            #     conn = psycopg2.connect(host=host, port=port, user=user, password=password)
            #     st.session_state.connected = True
            #     st.session_state.conn_info = (host, port, user, password)
            # except Exception as e:
            #     st.session_state.connected = False
            #     st.session_state.error = str(e)
            st.session_state.connected = False
            st.session_state.error = "Заглушка: подключение не выполнено"

    with col2:
        # Блок статуса
        st.markdown("#### Статус подключения")
        connected = st.session_state.get("connected", False)
        if connected:
            st.success("Подключено")
        else:
            st.error("Не подключено")

        # Вывод введённых значений
        st.text(f"PG_HOST: {st.session_state.get('conn_info', ['', '', '', ''])[0] if connected else host or 'None'}")
        st.text(f"PG_PORT: {st.session_state.get('conn_info', ['', '', '', ''])[1] if connected else port or 'None'}")
        st.text(f"PG_USER: {st.session_state.get('conn_info', ['', '', '', ''])[2] if connected else user or 'None'}")
        st.text(f"PG_PASSWORD: {st.session_state.get('conn_info', ['', '', '', ''])[3] if connected else ('*' * len(password) if password else 'None')}")

    # Информация о базе данных (заглушка)
    st.markdown("### Информация о базе данных")
    st.info("Здесь позже будет отображаться информация о структуре и содержимом БД")
    # Можно зарезервировать место:
    st.empty()

menu()
connection_page()