# Smart Plant IoT System

![ESP32-CAM and System Overview](images/esp32-cam.jpg)

## Overview

Smart Plant is an IoT-based system designed to monitor and manage plant health using a combination of sensors, an ESP32-CAM for image capture, and a cloud-based dashboard for real-time data visualization and AI-powered plant analysis. The system collects soil moisture, pH, and plant images, sending them to a Flask backend for storage and further processing. A Streamlit client provides an interactive dashboard and AI chat assistant for plant care.

## Features

- **Real-time Monitoring:** Collects soil moisture, pH, and plant images.
- **Remote Image Capture:** Uses ESP32-CAM to capture and send plant images to the server.
- **Data Visualization:** Streamlit dashboard displays historical and real-time sensor data.
- **AI Plant Assistant:** Integrated AI chat for plant care advice (using Gemini/Google Generative AI).
- **Object Detection:** YOLO-based model for plant and disease detection from images.
- **Cloud Backend:** Flask server for data and image storage, accessible via REST API.
- **Easy Setup:** WiFiManager for ESP32-CAM configuration.

## Hardware Used

- **ESP32-CAM** (for image capture)
- **ESP32 Dev Board** (for sensor data collection)
- **Soil Moisture Sensor**
- **pH Sensor**
- **Relay Module**
- **Water Pump(s)**
- **9V Battery** (or suitable power supply)
- **Jumper wires, breadboard, etc.**

### Hardware Setup

| <img src="images/esp32-cam-alone.jpg" alt="ESP32-CAM Module" width="150"> | <img src="images/system-wiring.jpg" alt="Full System Wiring" width="400"> |
|:-----------------------------------------:|:-----------------------------------------------:|
| ESP32-CAM Module                          | Full System Wiring (Sensors, Relays, Pumps, etc.)|

## Software Architecture

- **IoT Firmware:** Arduino code for ESP32-CAM and ESP32 (located in `/IoT/`).
- **Backend Server:** Flask app for receiving images and sensor data (`/server/`).
- **Client Dashboard:** Streamlit app for visualization and AI chat (`/client/`).

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Smart-Plant.git
cd Smart-Plant
```

### 2. Hardware Assembly
- Connect the sensors, relays, and ESP32 boards as shown in the wiring diagram above.
- Flash the ESP32-CAM and ESP32 with the provided Arduino sketches in `/IoT/`.

### 3. Backend Setup (Flask)

```bash
cd server
pip install -r requirements.txt
python main.py
```

### 4. Client Setup (Streamlit)

```bash
cd client
pip install -r requirements.txt
streamlit run main.py
```

**Note:** For YOLO and OpenCV, ensure you have the necessary system dependencies. See `client/packages.txt` for Linux packages if deploying on Linux.

### 5. ESP32-CAM WiFi Setup
- On first boot, ESP32-CAM will create a WiFi AP for configuration.
- Connect to the AP and set your WiFi credentials via the captive portal.

## Usage

- **Dashboard:** Access the Streamlit dashboard to view real-time sensor data and historical trends.
- **Detection:** Use the "Deteksi Objek" page to capture and analyze plant images.
- **AI Chat:** Ask plant care questions to the AI assistant.
- **Backend:** The Flask server exposes endpoints for image and data upload/retrieval.

## API Endpoints

- `POST /post/image` — Upload image (from ESP32-CAM)
- `GET /get/image` — Retrieve latest image
- `POST /insert/data` — Upload sensor data (pH, soil moisture)
- `GET /find/data` — Retrieve all sensor data

## File Structure

```plaintext
Smart-Plant/
│
├── AI/
│   └── training_model_iot_smart_plant.ipynb
│
├── IoT/
│   ├── esp32cam.ino
│   └── esp32_soilph.ino
│
├── server/
│   ├── main.py
│   ├── controller.py
│   ├── model.py
│   └── requirements.txt
│
├── client/
│   ├── main.py
│   ├── dashboard.py
│   ├── detection.py
│   ├── model_genai.py
│   ├── best.pt
│   └── requirements.txt
│
└── README.md
```

## Credits

- **Hardware:** ESP32, various sensors
- **Software:** Arduino, Flask, Streamlit, YOLO, Google Generative AI

## License

This project is licensed under the MIT License.

## Gallery

### ESP32-CAM Module
![ESP32-CAM Module](images/esp32-cam-alone.jpg)

### Full System Wiring
![Full System Wiring](images/system-wiring.jpg)

For questions or contributions, please open an issue or pull request!
