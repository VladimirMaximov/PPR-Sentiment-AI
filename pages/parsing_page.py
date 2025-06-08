import streamlit as st
from menu import menu

def parsing_page():
    st.title("Сбор отзывов")
    st.markdown("### Информация о результирующей таблице")
    st.write("")  # небольшое разделение

    # Первая секция: создание новой таблицы
    with st.expander("Создать новую таблицу"):
        table_name = st.text_input(
            label="Название таблицы:",
            placeholder="Введите имя новой таблицы"
        )

        start_date = st.date_input(
            label="С какой даты собирать отзывы:"
        )

        end_date = st.date_input(
            label="По какую дату собирать отзывы:"
        )

        st.markdown("**С каких сервисов собирать отзывы:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            yandex = st.checkbox("Яндекс")
        with col2:
            gis2 = st.checkbox("2ГИС")
        with col3:
            google = st.checkbox("Google")

        # Кнопка создания (если нужна логика – допишем позже)
        if st.button("Создать таблицу"):
            # здесь будет ваша логика создания
            st.success(f"Таблица `{table_name}` запланирована к созданию.\n"
                       f"Период: {start_date} — {end_date}\n"
                       f"Сервисы: {', '.join([n for n, v in [('Яндекс', yandex), ('2ГИС', gis2), ('Google', google)] if v]) or 'не выбраны'}")

    # Вторая секция: изменение существующей таблицы (пока пустая)
    with st.expander("Изменить существующую таблицу"):
        st.write("Здесь будет интерфейс для выбора и изменения уже созданных таблиц")

menu()
parsing_page()
