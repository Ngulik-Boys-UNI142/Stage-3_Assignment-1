from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
# from dotenv import load_dotenv
from langchain_core.runnables import RunnableMap, RunnablePassthrough
# import os
import streamlit as st

class ModelGenai():
    def __init__(self):
        self.__GOOGLE_API_KEY = st.secrets['GOOGLE_API_KEY']
        self.__model = 'gemini-1.5-pro'
        
        self.__system_template = 'Kamu adalah asisten ahli tanaman dan juga teman saya. Jangan memberikan pertanyaan di akhir karena kamu tidak bisa mengingat'
        self.__human_template = '{input}'
        
        self.__prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.__system_template),
            HumanMessagePromptTemplate.from_template(self.__human_template)
        ])

        self.__llm = ChatGoogleGenerativeAI(
            api_key=self.__GOOGLE_API_KEY,
            model=self.__model,
            streaming=True
        )

        self.chain = self.__prompt_template | self.__llm
        

