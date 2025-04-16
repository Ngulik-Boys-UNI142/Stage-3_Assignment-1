import streamlit as st
import logging
from detection import DetectionPage
from chat import ChatPage
from dashboard import DashboardPage

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

        if 'selected_page' not in st.session_state:
            st.session_state['selected_page'] = 'Dashboard'

        self.pages = {
            'Dashboard': DashboardPage(),
            'Detection': DetectionPage(),
            'Chat': ChatPage(),
        }

        st.set_page_config(page_title=st.session_state['selected_page'])

    def __show_sidebar(self):
        with st.sidebar:
            st.title('Menu')
            for page in self.pages.keys():
                if st.button(page, use_container_width=True):
                    st.session_state['selected_page'] = page
                    st.rerun()  

    def run(self):
        self.__show_sidebar()
        self.pages[st.session_state['selected_page']].show()

if __name__ == '__main__':
    main = Main()
    main.run()
