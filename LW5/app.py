import streamlit as st
import psutil
from cryptography.fernet import Fernet
import tracemalloc
from dataclasses import dataclass


tracemalloc.start()


@dataclass
class Data:
    data: str
    is_confidential: bool


st.set_page_config(page_title='Работа с ОЗУ', layout='wide')

if not 'memory' in st.session_state:
    st.session_state['memory'] = {}
memory: dict[str, Data] = st.session_state['memory']

if not 'encryption_key' in st.session_state:
    st.session_state['encryption_key'] = Fernet.generate_key()
encryption_key = st.session_state['encryption_key']

if not 'cipher' in st.session_state:
    st.session_state['cipher'] = Fernet(encryption_key)
cipher: Fernet = st.session_state['cipher']

if not 'step' in st.session_state:
    st.session_state['step'] = 'Запуск системы'
step = st.session_state['step']

if not 'last_snapshot' in st.session_state:
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    st.session_state['last_snapshot'] = snapshot
    tracemalloc.stop()


def upload_data(_id: str, data: str, confidential: bool = False) -> None:
    if not get_data(_id) is None:
        raise KeyError('Данные по данному идентификатору уже существуют!')
    if confidential:
        data = cipher.encrypt(data.encode()).decode()
    st.session_state['memory'][_id] = Data(data, confidential)

def get_data(_id: str) -> str | None:
    data: Data | None = st.session_state['memory'].get(_id)
    if data is None:
        return None
    if data.is_confidential:
        return cipher.decrypt(data.data.encode()).decode()
    return data.data

def update_data(_id: str, data: str, confidential: bool = False) -> None:
    if get_data(_id) is None:
        raise KeyError('Данных по данному адресу не существует!')
    if confidential:
        data = cipher.encrypt(data.encode()).decode()
    st.session_state['memory'][_id] = Data(data, confidential)

def delete_data(_id: str) -> None:
    if get_data(_id) is None:
        raise KeyError('Данных по данному адресу не существует!')
    del st.session_state['memory'][_id]

def dump_memory(step: str):
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    st.write(f"Дамп памяти ({step}):")
    top_diffs = snapshot.compare_to(st.session_state['last_snapshot'], 'lineno')
    top_stats = snapshot.statistics('lineno')
    st.session_state['last_snapshot'] = snapshot    
    tracemalloc.stop()
    result = [f"{'=' * 5} TOP STATS {'=' * 5}"]
    result.extend(list(map(str, top_stats[:10])))
    result.append(f"{'=' * 5} TOP DIFFS {'=' * 5}")
    result.extend(list(map(str, top_diffs[:10])))
    return result

def system_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    cpu_times = process.cpu_times()
    return (
        f"Использование ОЗУ: {memory_info.rss / 1024 ** 2:.2f} MB\n\n"
        f"Процессорное время (пользователь): {cpu_times.user:.2f} s\n\n"
        f"Процессорное время (система): {cpu_times.system:.2f} s"
    )    

def choise_format_func(option: str) -> str:
    return {
        'upload': 'Добавить данные',
        'get': 'Получить данные',
        'update': 'Изменить данные',
        'delete': 'Удалить данные'
    }[option]

def main_view() -> None:
    data_col, memory_col = st.columns([2, 3])    
    with data_col:
        choise = st.selectbox(label='Выберите действие', key='choise',
                              format_func=choise_format_func,
                              options=['upload', 'get', 'update', 'delete'])
        match choise:
            case 'upload':
                render_upload()
            case 'get':
                render_get()
            case 'update':
                render_update()
            case 'delete':
                render_delete()
    with memory_col:
        with st.empty().container(height=700):
            st.write('\n\n'.join(dump_memory(step)))
            st.divider()
            st.write(system_usage())

def render_upload() -> None:    
    with st.form('upload_form'):
        st.header('Загрузить данные')
        _id = st.text_input('Адрес в памяти', key='key_input')
        data = st.text_input('Значение данных', key='data')
        confidential = st.checkbox('Конфиденциальные данные?',
                                   key='confidential')
        submit_btn = st.form_submit_button('Загрузить данные')
        if submit_btn:
            try:
                upload_data(_id, data, confidential)
            except KeyError as e:
                st.error(e)
            else:
                st.session_state['step'] = 'Загрузка данных'
                st.success('Данные загружены')

def render_update() -> None:
    with st.form('update_form'):
        st.header('Обновить данные')
        _id = st.text_input('Адрес в памяти', key='key_input')
        data = st.text_input('Новое значение данных', key='data')
        confidential = st.checkbox('Конфиденциальные данные?',
                                   key='confidential')
        submit_btn = st.form_submit_button('Обновить данные')
        if submit_btn:
            try:
                update_data(_id, data, confidential)
            except KeyError as e:
                st.error(e)
            else:
                st.session_state['step'] = 'Обновление данных'
                st.success('Данные обновлены')

def render_get() -> None:
    with st.form('get_form'):
        st.header('Получить данные')
        _id = st.text_input('Адрес в памяти', key='key_input')        
        submit_btn = st.form_submit_button('Получить данные')
        if submit_btn:            
            result = get_data(_id)            
            st.session_state['step'] = 'Получение данных'
            if result is None:
                st.error('По данному адресу данных не существует!')
            else:
                st.write(f'Полученные данные по адресу {_id}: {result}')

def render_delete() -> None:
    with st.form('delete_form'):
        st.header('Удалить данные')
        _id = st.text_input('Адрес в памяти', key='key_input')        
        submit_btn = st.form_submit_button('Удалить данные')
        if submit_btn:
            try:
                delete_data(_id)
            except KeyError as e:
                st.error(e)
            else:
                st.session_state['step'] = 'Удаление данных'
                st.success('Данные удалены')


main_view()
