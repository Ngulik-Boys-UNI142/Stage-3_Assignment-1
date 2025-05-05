import streamlit as st
import logging
from detection import DetectionPage
from chat import ChatPage
from dashboard import DashboardPage
from login import show_login_page

class Main:
    def __init__(self):
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.getLogger('tenacity').setLevel(logging.WARNING)
        logging.getLogger('langchain').setLevel(logging.ERROR)
        logging.getLogger('langchain_google_genai').setLevel(logging.ERROR)
        logging.getLogger('httpx').setLevel(logging.ERROR)

        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
        if 'pot_ids' not in st.session_state:
            st.session_state['pot_ids'] = []

        if 'selected_page' not in st.session_state:
            st.session_state['selected_page'] = 'Dashboard'

        self.pages = {}

        if st.session_state['logged_in']:
            self.pages = {
                'Dashboard': DashboardPage(st.session_state.get('pot_ids', [])),
                'Detection': DetectionPage(),
                'Chat': ChatPage(),
            }

        page_title = "Login"
        if st.session_state['logged_in'] and 'selected_page' in st.session_state:
             page_title = st.session_state['selected_page']
        st.set_page_config(page_title=page_title)

    def __show_sidebar(self):
        if st.session_state['logged_in'] and self.pages:
            with st.sidebar:
                st.title('Menu')
                if st.button("Logout", use_container_width=True):
                    st.session_state['logged_in'] = False
                    st.session_state['chat_id'] = ""
                    st.session_state['pot_ids'] = []
                    if 'selected_page' in st.session_state:
                         del st.session_state['selected_page']
                    if 'monitoring_active' in st.session_state:
                         del st.session_state['monitoring_active']
                    st.rerun()

                st.divider()

                for page_name in self.pages.keys():
                    if st.button(page_name, use_container_width=True):
                        st.session_state['selected_page'] = page_name
                        st.rerun()

    def run(self):
        if not st.session_state['logged_in']:
            show_login_page()
        elif 'selected_page' in st.session_state and st.session_state['selected_page'] in self.pages:
            self.__show_sidebar()
            self.pages[st.session_state['selected_page']].show()
        else:
            show_login_page()

if __name__ == '__main__':
    main = Main()
    main.run()
