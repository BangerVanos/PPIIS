from model import DBWorker
from typing import Literal
import streamlit as st
from enum import StrEnum
import os
import json
from streamlit_extras.stateful_button import button


class AppStates(StrEnum):
    PRE_AUTH = 'pre_auth'
    AUTH = 'auth'
    AUTHENTICATED = 'authenticated'


class AuthenticationStatus(StrEnum):
    NON_EXISTENT_USER = 'user_not_exist'
    WRONG_PASSWORD = 'wrong_password'
    SUCCESS = 'success'
    ADMIN_FAILURE = 'admin_failure'
    OTHER = 'other'


class App:

    def __init__(self) -> None:
        self._db = DBWorker()
        if not 'authenticated_person' in st.session_state:
            st.session_state['authenticated_person'] = None
        if not 'user_type' in st.session_state:
            st.session_state['user_type'] = None
        if not 'state' in st.session_state:
            st.session_state['state'] = AppStates.PRE_AUTH
        if not 'placeholder' in st.session_state:
            st.session_state['placeholder'] = st.empty()
        if not 'render_stop' in st.session_state:
            st.session_state['render_stop'] = False        
        self._container = st.session_state['placeholder']
    
    def run(self) -> None:
        self._render_main_layout()
    
    def _app_state(self, state: AppStates):
        st.session_state['state'] = state
    
    def _authenticated_person(self, user_type: Literal['admin', 'user', 'guest'] | None) -> None:
        st.session_state['authenticated_person'] = user_type

    @property
    def _user_type(self) -> Literal['admin', 'user', 'guest'] | None:
        return st.session_state['user_type']   
    
    @_user_type.setter
    def _user_type(self, user_type: Literal['admin', 'user', 'guest'] | None) -> None:
        st.session_state['user_type'] = user_type    

    @property
    def placeholder(self):
        return st.session_state['placeholder']
    
    @property
    def render_stop(self):
        return st.session_state['render_stop']
    
    @render_stop.setter
    def render_stop(self, value: bool):
        st.session_state['render_stop'] = value

    def _render_main_layout(self) -> None:               
        if st.session_state['state'] == AppStates.PRE_AUTH:            
            self._render_non_authenticated_layout()            
        elif st.session_state['state'] == AppStates.AUTH:            
            self._render_authentication_layout(st.session_state['user_type'])            
        elif st.session_state['state'] == AppStates.AUTHENTICATED:            
            self._render_authenticated_layout(st.session_state['authenticated_person'])            
    
    def _render_non_authenticated_layout(self) -> None:
        self._app_state(AppStates.PRE_AUTH)
        self._container.empty()        
        with self._container.container():
            st.header('Выберите режим работы с программой')
            guest = st.button('Остаться как гость', key='guest_btn', use_container_width=True,
                              on_click=self._submit_authentication,
                              args=('guest',))                           
            user = st.button('Войти как пользователь', key='user_btn', use_container_width=True,
                             on_click=self._authentication_process_run,
                             args=('user',))                            
            admin = st.button('Войти как администратор', key='admin_btn', use_container_width=True,
                              on_click=self._authentication_process_run,
                              args=('admin',))

    def _authentication_process_run(self, user_type: Literal['admin', 'user', 'guest']) -> None:
        self._app_state(AppStates.AUTH)               
        self._user_type = user_type
    
    def _submit_authentication(self, user_type: Literal['admin', 'user', 'guest']) -> None:
        self._app_state(AppStates.AUTHENTICATED)               
        self._user_type = user_type
        self._authenticated_person(user_type)
    
    def _reset_app(self) -> None:
        self._app_state(AppStates.PRE_AUTH)
        self._user_type = None
        self._authenticated_person(None)

    def _render_authentication_layout(self, user_type: Literal['admin', 'user', 'guest']) -> None:        
        self._container.empty()                                
        with self._container.container():
            st.header('Вход в аккаунт')
            with st.form(f'authentication_form'):                
                login = st.text_input(label='Введите идентификатор (логин)', key='login_field')
                password = st.text_input(label='Введите пароль', key='password_field',
                                         type='password')
                log_col, back_col = st.columns([1, 1])
                with log_col:
                    log_btn = st.form_submit_button('Войти', use_container_width=True)
                if log_btn:                                       
                    authentication_status = self._authenticate(user_type, (login, password))                    
                    if authentication_status == AuthenticationStatus.NON_EXISTENT_USER:
                        st.error('Пользователя с таким идентификатором не существует!')
                    elif authentication_status == AuthenticationStatus.WRONG_PASSWORD:
                        st.error('Введённый пароль неправильный!')
                    elif authentication_status == AuthenticationStatus.ADMIN_FAILURE:
                        st.error('Не выдавайте себя за администратора!')
                    elif authentication_status == AuthenticationStatus.OTHER:
                        st.error('Возникла непредвиденная проблема! В процессе поиска решения...')
                    elif authentication_status == AuthenticationStatus.SUCCESS:                                                                  
                        self._submit_authentication(user_type)
                with back_col:
                    back_btn = st.form_submit_button(label='Назад', on_click=self._reset_app,
                                                     use_container_width=True)        
            

    def _render_authenticated_layout(self, user_type: Literal['admin', 'user', 'guest']) -> None:
        self._authenticated_person(user_type)
        
        self._container.empty()       
        with self._container.container():
            st.header('Выберите возможную функцию')
            amount_btn = st.button('Узнать количество учащихся', key='amount_btn')
            if amount_btn:
                self._get_students_amount()
            if st.session_state['authenticated_person'] == 'user':
                student_list_btn = st.button('Получить список всех студентов', key='student_list_btn')
                if student_list_btn:
                    self._get_students()
            elif st.session_state['authenticated_person'] == 'admin':
                student_list_btn = st.button('Получить список всех студентов', key='student_list_btn')
                if student_list_btn:
                    self._get_students()
                add_student_btn = st.button('Добавить нового студента', key='add_student_btn')
                if add_student_btn:
                    st.header('Добавить нового студента')
                    with st.form('add_student'):
                        first_name = st.text_input('Имя', key='first_name_field')
                        last_name = st.text_input('Фамилия', key='last_name_field')
                        group = st.text_input('Группа', key='group_field')
                        add_student_btn = st.form_submit_button('Добавить нового студента')
                        if add_student_btn:
                            self._create_student(first_name, last_name, group)
                delete_db_btn = st.button('Удалить базу данных', key='delete_db_btn',
                                          on_click=self._delete_database)
            log_out_btn = st.button('Выйти из аккаунта', key='log_out_btn', on_click=self._reset_app)

    def _authenticate(self, user_type: Literal['admin', 'user', 'guest'],
                      credentials: tuple[str, str]) -> AuthenticationStatus:        
        if user_type == 'admin':
            return self._authenticate_admin(credentials)
        elif user_type == 'user':
            return self._authenticate_user(credentials)        
    
    def _authenticate_admin(self, credentials: tuple[str, str]) -> AuthenticationStatus:
        admin_login = os.getenv('ADMIN_LOGIN')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if admin_login == credentials[0] and admin_password == credentials[1]:
            self._submit_authentication('admin')
            return AuthenticationStatus.SUCCESS
        return AuthenticationStatus.ADMIN_FAILURE
    
    def _authenticate_user(self, credentials: tuple[str, str]) -> AuthenticationStatus:
        with open('users.json', encoding='utf-8') as file:
            users: dict[str, str] = json.load(file)
        if credentials[0] not in users:
            return AuthenticationStatus.NON_EXISTENT_USER
        elif users.get(credentials[0]) != credentials[1]:
            return AuthenticationStatus.WRONG_PASSWORD
        return AuthenticationStatus.SUCCESS
    
    def _get_students_amount(self) -> None:        
        try:       
            students_amount = self._db.get_students_amount()
            st.toast(f'Количество учащихся: {students_amount}')       
            st.info(f'Количество учащихся: {students_amount}')
        except Exception as e:
            print('DB is empty!')
            st.error('Ошибка во время получения количества студентов')
            st.toast('Ошибка во время получения количества студентов')
    
    def _get_students(self) -> None:        
        try:       
            students = self._db.get_students()        
            for student in students:
                st.write(student)
        except Exception as e:
            print('DB is empty!')
            st.error(f'Ошибка во время получения списка студентов: {e}')
            st.toast(f'Ошибка во время получения списка студентов: база данных отсутствует!')    
   
    def _delete_database(self) -> None:
        self._db.delete_database()
        st.toast('База данных успешно удалена!')
    
    def _create_student(self, first_name: str, last_name: str, group: str) -> None:
        print(first_name, last_name, group)
        try:                    
            self._db.create_student(first_name, last_name, int(group))
        except Exception as e:
            print(f'Error: {e}')                    
            st.error(f'Ошибка во время добавления студента: {e}')
            st.toast(f'Ошибка во время добавления студента: {e}')
        else:
            st.toast('Студент успешно добавлен в базу данных!')
            st.success('Студент успешно добавлен в базу данных!')


if __name__ == '__main__':
    app = App()
    app.run()
