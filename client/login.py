import streamlit as st
import requests

def show_login_page():
    st.title('Login')

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'chat_id' not in st.session_state:
        st.session_state['chat_id'] = ""
    if 'pot_ids' not in st.session_state:
        st.session_state['pot_ids'] = []
    if 'login_error' not in st.session_state:
        st.session_state['login_error'] = ""

    chat_id = st.text_input(
        'Enter you Chat ID',
        value=st.session_state['chat_id'],
        placeholder='Telegram Chat ID (contoh: 1111)',
        key='chat_id_input'
    )

    if st.button('Login'):
        if chat_id:
            st.session_state['chat_id'] = chat_id
            st.session_state['login_error'] = ""
            try:
                api_url = f"https://api-smart-plant.vercel.app/find/pot/{chat_id}"
                response = requests.get(api_url)
                response.raise_for_status()

                data = response.json()

                fetched_pot_ids = None

                if isinstance(data, dict) and 'pot_ids' in data and isinstance(data['pot_ids'], list):
                    fetched_pot_ids = data['pot_ids']
                elif isinstance(data, list):
                    fetched_pot_ids = data
                if fetched_pot_ids:
                    st.session_state['pot_ids'] = fetched_pot_ids
                    st.session_state['logged_in'] = True
                    st.session_state['selected_page'] = 'Dashboard'
                    st.success('Login successful!')
                    st.rerun()
                else:
                    st.warning('No pot IDs found for the provided Chat ID.')
            except requests.exceptions.RequestException as e:
                st.session_state['login_error'] = f"API Error: Could not connect or fetch data. {e}"
                st.warning(f'Error: {e}')
            except Exception as e:
                st.session_state['login_error'] = f"An unexpected error occurred: {e}"
                st.warning(f'Error: {e}')
        else:
            st.warning('Please enter your Chat ID.')

    if st.session_state['login_error']:
        st.warning(st.session_state['login_error'])
