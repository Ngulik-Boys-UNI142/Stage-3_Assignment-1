import streamlit as st
from model_genai import ModelGenai

class ChatPage:
    def __init__(self):
        self.__model = ModelGenai()
        if 'last_message' not in st.session_state:
            st.session_state['last_message'] = None

    def show(self):
        st.title('Asisten Ahli Tanaman 🌿')
        st.markdown('Tanyakan apa saja tentang tanaman. Aku tidak bisa mengingat pertanyaan sebelumnya.')

        question = st.text_input('Pertanyaan Anda:')

        if st.button('Tanya') and question.strip():
            self.__handle_question(question)
        elif not st.session_state['last_message']:
            st.info("Masukkan pertanyaan lalu klik tombol 'Tanya'.")
        elif st.session_state['last_message']:
            st.info(f'Pertanyaan terakhir Anda: {st.session_state['last_message']['question']}')
            st.markdown(f'**Jawaban terakhir:** {st.session_state['last_message']['answer']}')

    def __handle_question(self, question):
        with st.spinner('Menjawab...'):
            try:
                answer_stream = self.__model.chain.stream({'input': question})
                response_container = st.empty()
                output = ''

                for chunk in answer_stream:
                    content = getattr(chunk, 'content', str(chunk))
                    output += content
                    response_container.markdown(output + '▌')

                response_container.markdown(output)
                st.success('✅ Jawaban diberikan.')
                st.session_state['last_message'] = {'question': question, 'answer': output}
            except Exception as e:
                st.error('❌ Terjadi kesalahan. Mungkin kuota API habis.')
