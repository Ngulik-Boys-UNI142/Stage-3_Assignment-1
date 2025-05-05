import streamlit as st
import pandas as pd
import requests
import time

class DashboardPage:
    def __init__(self, pot_ids):
        self.title = 'Dashboard'
        self.__url = 'https://api-smart-plant.vercel.app/find/data/'
        self.__placeholders = {}
        self.__pot_ids = pot_ids if pot_ids else []
        self.__notified = {}

    def show(self):
        current_pot_ids = st.session_state.get('pot_ids', self.__pot_ids)

        st.title('Dashboard Overview 📈')
        st.write('Selamat datang di 😎 **SMART PLANT** 🌱')
        st.markdown("Tekan tombol 'Pemantauan' untuk melihat data.")

        start_monitoring = st.button('Pemantauan 👀')



        if not current_pot_ids:
            st.warning("No pots associated with your account.")
            return

        self.__placeholders = {}
        pots_per_row = 3
        num_pots = len(current_pot_ids)

        for i in range(0, num_pots, pots_per_row):
            row_pot_ids = current_pot_ids[i : i + pots_per_row]
            cols = st.columns(len(row_pot_ids))

            for j, pot_id in enumerate(row_pot_ids):
                with cols[j]:
                    st.subheader(f"Pot: {pot_id}")
                    metric_cols = st.columns(2)
                    with metric_cols[0]:
                        ph_placeholder = st.empty()
                    with metric_cols[1]:
                        soil_placeholder = st.empty()
                    chart_placeholder = st.empty()
                    notify_placeholder = st.empty()

                    self.__placeholders[pot_id] = {
                        'ph': ph_placeholder,
                        'soil': soil_placeholder,
                        'chart': chart_placeholder,
                        'notify': notify_placeholder
                    }
                    if not start_monitoring:
                         ph_placeholder.info("pH: -")
                         soil_placeholder.info("Soil: -")
                         chart_placeholder.info("Chart: -")
                         notify_placeholder.empty()

            if i + pots_per_row < num_pots:
                 st.divider()

        if start_monitoring:
            self.__update_data(current_pot_ids)
            if 'last_refresh' in st.session_state:
                del st.session_state['last_refresh']

    def __update_data(self, pot_ids):

        PH_ASAM_THRESHOLD = 5
        PH_BASA_THRESHOLD = 8
        SOIL_THRESHOLD = 20

        while True:
            for pot_id in pot_ids:
                if pot_id not in self.__placeholders:
                    continue
                url = self.__url + str(pot_id)
                ph_placeholder = None
                soil_placeholder = None
                chart_placeholder = None
                notify_placeholder = None

                try:
                    if pot_id not in self.__placeholders or not isinstance(self.__placeholders[pot_id], dict):
                        time.sleep(1)
                        return

                    ph_placeholder = self.__placeholders[pot_id].get('ph')
                    soil_placeholder = self.__placeholders[pot_id].get('soil')
                    chart_placeholder = self.__placeholders[pot_id].get('chart')
                    notify_placeholder = self.__placeholders[pot_id].get('notify')

                    if not ph_placeholder or not soil_placeholder or not chart_placeholder:
                        time.sleep(1)
                        return

                    response = requests.get(url, timeout=7)
                    response.raise_for_status()

                    data = response.json()

                    if data and isinstance(data, list) and len(data) >= 1:
                        last_data = data[-1]
                        ph = last_data.get('ph', 'N/A')
                        soil = last_data.get('soil', 'N/A')

                        delta_ph_label = "N/A"
                        delta_soil_label = "N/A"

                        if len(data) >= 2:
                            delta_data = data[-2]
                            prev_ph = delta_data.get('ph', 'N/A')
                            prev_soil = delta_data.get('soil', 'N/A')

                            if isinstance(ph, (int, float)) and isinstance(prev_ph, (int, float)):
                                delta_ph = ph - prev_ph
                                delta_ph_label = f'{delta_ph:+.2f}'
                            else:
                                delta_ph_label = "N/A"

                            if isinstance(soil, (int, float)) and isinstance(prev_soil, (int, float)):
                                delta_soil = soil - prev_soil
                                delta_soil_label = f'{delta_soil:+.2f}'
                            else:
                                delta_soil_label = "N/A"

                        ph_placeholder.metric('pH Level 🌱', f'{ph}', delta_ph_label)
                        soil_placeholder.metric('Soil Level 🌍', f'{soil}', delta_soil_label)

                        placeholder_text = []
                        notify_message = "⚠️  []. Harap periksa pot Anda."

                        if isinstance(ph, (int, float)) and ph < PH_ASAM_THRESHOLD:
                            placeholder_text.append('Tanah terlalu asam')
                        if isinstance(ph, (int, float)) and ph > PH_BASA_THRESHOLD:
                            placeholder_text.append('Tanah terlalu basa')
                        if isinstance(soil, (int, float)) and soil <= SOIL_THRESHOLD:
                            placeholder_text.append('Tanah terlalu kering')

                        if placeholder_text:
                            new_message = notify_message.replace('[]', ' & '.join(placeholder_text))
                            notify_message = str(new_message)
                            notify_placeholder.warning(notify_message)
                            self.__notified[pot_id] = True
                        else:
                            notify_placeholder.empty()
                            self.__notified[pot_id] = False
                            placeholder_text = []

                        df = pd.DataFrame(data)

                        chart_cols = []
                        if 'ph' in df.columns:
                            df['ph'] = pd.to_numeric(df['ph'], errors='coerce')
                            chart_cols.append('ph')
                        if 'soil' in df.columns:
                            df['soil'] = pd.to_numeric(df['soil'], errors='coerce')
                            chart_cols.append('soil')

                        if chart_cols:
                            df_to_plot = df[chart_cols].dropna()
                            if not df_to_plot.empty:
                                chart_placeholder.line_chart(df_to_plot)
                            else:
                                chart_placeholder.info("No valid chart data points.")
                        else:
                            chart_placeholder.info("No chart data available.")

                    else:
                        ph_placeholder.metric('pH Level 🌱', 'N/A', 'N/A')
                        soil_placeholder.metric('Soil Level 🌍', 'N/A', 'N/A')
                        chart_placeholder.info("No data received for this pot.")
                        if notify_placeholder:
                            notify_placeholder.empty()
                        self.__notified[pot_id] = False
                        placeholder_text = []
                except requests.exceptions.RequestException as e:
                    ph_placeholder.metric('pH Level 🌱', 'N/A', 'N/A')
                    soil_placeholder.metric('Soil Level 🌍', 'N/A', 'N/A')
                    chart_placeholder.info(f"Data belum ada😓.")
                    if notify_placeholder:
                        notify_placeholder.empty()
                    self.__notified[pot_id] = False
                    placeholder_text = []
                except requests.exceptions.Timeout:
                    if chart_placeholder:
                        chart_placeholder.info("Request timed out.")
                    if notify_placeholder:
                        notify_placeholder.empty()
                    self.__notified[pot_id] = False
                    placeholder_text = []
                except Exception as e:
                    chart_placeholder.info(f"An unexpected error occurred: {e}")
                    if notify_placeholder:
                        notify_placeholder.empty()
                    self.__notified[pot_id] = False
                    placeholder_text = []
