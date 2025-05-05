import streamlit as st
import requests
import time
from datetime import datetime

class DetectionPage:
    def __init__(self):
        self.__base_url = 'https://api-smart-plant.vercel.app/get/image/'
        self.__placeholders = {}
        current_pot_ids = st.session_state.get('pot_ids', [])
        for pot_id in current_pot_ids:
            if f'detected_image_{pot_id}' not in st.session_state:
                st.session_state[f'detected_image_{pot_id}'] = None

    def show(self):
        current_pot_ids = st.session_state.get('pot_ids', [])

        st.title('Camera Detection 📸')
        st.markdown("Tekan tombol 'Start Detection' untuk melihat kamera.")

        start_detection = st.button('Start Detection 👀')

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
                    image_placeholder = st.empty()
                    button_placeholder = st.empty()

                    self.__placeholders[pot_id] = {
                        'image': image_placeholder,
                        'button': button_placeholder
                    }
                    if not start_detection:
                         image_placeholder.info("Camera: -")
                         button_placeholder.empty()

                    image_bytes = st.session_state.get(f'detected_image_{pot_id}', None)

                    if image_bytes:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_name = f"detection_pot_{pot_id}_{timestamp}.png"
                        self.__placeholders[pot_id]['button'].download_button(
                            label="Unduh Gambar 💾",
                            data=image_bytes,
                            file_name=file_name,
                            mime="image/png",
                            key=f"download_{pot_id}_{timestamp}"
                        )
                    else:
                         self.__placeholders[pot_id]['button'].empty()


            if i + pots_per_row < num_pots:
                 st.divider()

        if start_detection:
            for pot_id in current_pot_ids:
                 if f'detected_image_{pot_id}' not in st.session_state:
                     st.session_state[f'detected_image_{pot_id}'] = None
            self.__update_detection_view(current_pot_ids)


    def __update_detection_view(self, pot_ids):
        """Loops through pots and updates their camera views."""
        while True:
            active_pots = st.session_state.get('pot_ids', [])
            if not active_pots:
                 st.warning("No active pots found. Stopping detection.")
                 break

            pots_to_process = [pid for pid in pot_ids if pid in active_pots and pid in self.__placeholders]
            if not pots_to_process:
                 time.sleep(1)
                 continue

            for pot_id in pots_to_process:
                placeholder = self.__placeholders[pot_id].get('image')
                if not placeholder:
                    continue

                image_url = self.__base_url + str(pot_id)
                self.__process_and_display_image(pot_id, image_url, placeholder)

            for pot_id in pots_to_process:
                 image_bytes = st.session_state.get(f'detected_image_{pot_id}', None)
                 button_placeholder = self.__placeholders[pot_id].get('button')
                 if button_placeholder:
                     if image_bytes:
                         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                         file_name = f"detection_pot_{pot_id}_{timestamp}.png"
                         button_placeholder.download_button(
                             label="Unduh Gambar 💾",
                             data=image_bytes,
                             file_name=file_name,
                             mime="image/png",
                             key=f"download_{pot_id}_{timestamp}"
                         )
                     else:
                         button_placeholder.empty()

            time.sleep(2)

    def __process_and_display_image(self, pot_id, image_url, placeholder):
        """Fetches and displays image for a single pot directly from API."""
        try:
            response = requests.get(image_url, stream=True, timeout=7)
            response.raise_for_status()

            content_type = response.headers.get('content-type')
            if not content_type or not content_type.startswith('image/'):
                 placeholder.warning(f"No valid image feed from camera.")
                 st.session_state[f'detected_image_{pot_id}'] = None
                 return

            image_bytes = response.content

            if not image_bytes:
                placeholder.warning("Received empty image data.")
                st.session_state[f'detected_image_{pot_id}'] = None
                return


            st.session_state[f'detected_image_{pot_id}'] = image_bytes
            placeholder.image(image_bytes)


        except requests.exceptions.Timeout:
             st.session_state[f'detected_image_{pot_id}'] = None
             placeholder.warning("Request timed out ⏳.")
        except requests.exceptions.RequestException as e:
            st.session_state[f'detected_image_{pot_id}'] = None
            placeholder.warning(f"Kamera sedang tidak aktif 😞.")
        except Exception as e:
            st.session_state[f'detected_image_{pot_id}'] = None
            placeholder.error(f"Error processing image: {e} 😞.")
