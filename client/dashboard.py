import streamlit as st
import pandas as pd
import requests
import time

class DashboardPage:
    def __init__(self):
        self.title = 'Dashboard'
        self.__url = 'https://api-smart-plant.vercel.app/find/data'

    def show(self):
        st.title('Dashboard Overview 📈')
        st.write('Selamat datang di 😎 **SMART PLANT** 🌱')
        st.markdown("Tekan tombol 'Pemantauan' untuk melihat data.")

        if st.button('Pemantauan 👀'):
            col1, col2 = st.columns(2)

            with col1:
                self.__ph = st.empty()

            with col2:
                self.__soil = st.empty()

            self.__chart_placeholder = st.empty()
            
            self.__update_data()

    def __update_data(self):
        while True:
            try:
                response = requests.get(self.__url)
                data = response.json()

                if data and len(data) >= 2:
                    delta_data = data[-2]
                    last_data = data[-1]

                    ph = last_data.get('ph', 'N/A')
                    soil = last_data.get('soil', 'N/A')
                    prev_ph = delta_data.get('ph', 'N/A')
                    prev_soil = delta_data.get('soil', 'N/A')

                    if isinstance(ph, (int, float)) and isinstance(prev_ph, (int, float)):
                        delta_ph = ph - prev_ph
                        delta_ph_label = f'{delta_ph:.2f}'
                    else:
                        delta_ph_label = "N/A"

                    if isinstance(soil, (int, float)) and isinstance(prev_soil, (int, float)):
                        delta_soil = soil - prev_soil
                        delta_soil_label = f'{delta_soil:.2f}'
                    else:
                        delta_soil_label = "N/A"

                    self.__ph.metric('pH Level 🌱', f'{ph}', delta_ph_label)
                    self.__soil.metric('Soil Level 🌍', f'{soil}', delta_soil_label)

                    df = pd.DataFrame(data)
                    self.__chart_placeholder.line_chart(df[['ph', 'soil']])

            except Exception as e:
                st.error(f'Error fetching data: {e}')

            time.sleep(10)