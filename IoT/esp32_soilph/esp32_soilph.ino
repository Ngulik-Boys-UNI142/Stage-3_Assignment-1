#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiManager.h>
#include "FS.h"
#include "LittleFS.h"

#define POT_ID 941

// Pin definitions
#define MOISTURE_PIN 33
#define PH_PIN 35
#define RELAY_PIN1 26
#define RELAY_PIN2 27

// Threshold values
#define DRY_THRESHOLD 30 
#define WET_THRESHOLD 70
#define PH_LOW_THRESHOLD 5.5   // pH below this is too acidic
#define PH_HIGH_THRESHOLD 6.5  // Target pH level
#define MAX_PUMP_TIME 10000
#define DRY_VALUE 3200    // Value when sensor is in dry air
#define WET_VALUE 1532    // Value when sensor is in water
#define MOISTURE_CHANGE_THRESHOLD 2
#define PH_CHANGE_THRESHOLD 0.2

// File paths
#define WIFI_CONFIG_FILE "/wifi_config.txt"

// Ubidots configuration
#define UBIDOTS_TOKEN "BBUS-reJzd1NY4DgL646T8huuohOVENRTrY"
#define DEVICE_LABEL "soil-sensor" 
#define MOISTURE_VARIABLE "moisture"
#define PH_VARIABLE "ph"
#define UBIDOTS_HTTP_ENDPOINT "http://industrial.api.ubidots.com/api/v1.6/devices/"

// Flask API 
const String FLASK_API_ENDPOINT = "https://api-smart-plant.vercel.app/insert/data/" + String(POT_ID);

// Global variables for sensor data
int moisturePercent = 0;
int lastSentMoisturePercent = -MOISTURE_CHANGE_THRESHOLD - 1;
float pH = 0;
float lastSentPH = -PH_CHANGE_THRESHOLD - 1;
bool newDataAvailable = false;

// Pump control variables
bool pumpRunning1 = false;
bool pumpRunning2 = false;
unsigned long pumpStartTime1 = 0;
unsigned long pumpStartTime2 = 0;

// Timing variables
unsigned long lastSensorReadTime = 0;
unsigned long lastUbidotsSendTime = 0;
unsigned long lastWiFiCheckTime = 0;
unsigned long lastPumpCheckTime = 0;
unsigned long lastFlaskSendTime = 0;

// WiFi Manager callback
void saveWiFiManagerParamsCallback() {
  saveWiFiCredentials(WiFi.SSID(), WiFi.psk());
}

bool loadWIFiCredentials(String &ssid, String &password) {
  File file = LittleFS.open(WIFI_CONFIG_FILE, "r");
  if (!file) return false;
  
  ssid = file.readStringUntil('\n'); ssid.trim();
  password = file.readStringUntil('\n'); password.trim();
  file.close();
  
  return (ssid.length() > 0);
}

void saveWiFiCredentials(const String &ssid, const String &password) {
  File file = LittleFS.open(WIFI_CONFIG_FILE, "w");
  if (!file) return;
  
  file.println(ssid);
  file.println(password);
  file.close();
}

bool sendDataToUbidots(int moistureValue, float phValue) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(String(UBIDOTS_HTTP_ENDPOINT) + String(DEVICE_LABEL));
  http.addHeader(F("Content-Type"), F("application/json"));
  http.addHeader(F("X-Auth-Token"), UBIDOTS_TOKEN);
  
  String payload = "{\"" + String(MOISTURE_VARIABLE) + "\":" + String(moistureValue) + 
                   ",\"" + String(PH_VARIABLE) + "\":" + String(phValue, 2) + "}";
  int httpResponseCode = http.POST(payload);
  
  bool success = (httpResponseCode > 0);
  http.end();
  return success;
}

bool sendDataToFlaskAPI(int moistureValue, float phValue) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(FLASK_API_ENDPOINT.c_str());
  http.addHeader(F("Content-Type"), F("application/json"));
  
  StaticJsonDocument<200> doc;
  doc["ph"] = phValue;
  doc["soil"] = moistureValue;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpResponseCode = http.POST(payload);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print(F("Flask API Response: "));
    Serial.println(response);
    return true;
  } else {
    Serial.print(F("Flask API Error: "));
    Serial.println(httpResponseCode);
    return false;
  }
  
  http.end();
}

void initLittleFS() {
  if (!LittleFS.begin(true)) {
    Serial.println(F("ERROR: LittleFS Mount Failed"));
  }
}

void setupWiFi() {
  initLittleFS();
  
  String ssid, password;
  bool credentialsLoaded = loadWIFiCredentials(ssid, password);
  
  WiFiManager wm;
  wm.setSaveConfigCallback(saveWiFiManagerParamsCallback);
  
  if (credentialsLoaded) {
    WiFi.begin(ssid.c_str(), password.c_str());
    
    unsigned long startTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < 10000) {
      delay(500);
      Serial.print(F("."));
    }
    Serial.println();
    
    if (WiFi.status() != WL_CONNECTED) {
      if (!wm.autoConnect("ESP32-Sensor", "12345678")) {
        ESP.restart();
      }
    }
  } else {
    if (!wm.autoConnect("ESP32-Sensor", "12345678")) {
      ESP.restart();
    }
  }
}

// control pump for soil
void controlWaterPump() {
  if (!pumpRunning1 && moisturePercent < DRY_THRESHOLD) {
    digitalWrite(RELAY_PIN1, LOW);
    pumpRunning1 = true;
    pumpStartTime1 = millis();
    Serial.println(F("Soil too dry! Activating water pump"));
  } else if (pumpRunning1 && (moisturePercent >= WET_THRESHOLD || (millis() - pumpStartTime1 > MAX_PUMP_TIME))) {
    digitalWrite(RELAY_PIN1, HIGH);
    pumpRunning1 = false;
    
    if (moisturePercent >= WET_THRESHOLD) {
      Serial.println(F("Deactivating water pump - Soil moisture adequate"));
    } else {
      Serial.println(F("Deactivating water pump - Maximum pump time reached"));
    }
  }
}

// control pump for ph
void controlPHPump() {
  if (!pumpRunning2 && pH < PH_LOW_THRESHOLD) {
    digitalWrite(RELAY_PIN2, LOW);
    pumpRunning2 = true;
    pumpStartTime2 = millis();
    Serial.println(F("Soil too acidic! Activating pH adjustment pump"));
  } else if (pumpRunning2 && (pH >= PH_HIGH_THRESHOLD || (millis() - pumpStartTime2 > MAX_PUMP_TIME))) {
    digitalWrite(RELAY_PIN2, HIGH);
    pumpRunning2 = false;
    
    if (pH >= PH_HIGH_THRESHOLD) {
      Serial.println(F("Deactivating pH pump - Soil pH adequate"));
    } else {
      Serial.println(F("Deactivating pH pump - Maximum pump time reached"));
    }
  }
}

float readPHSensor() {
  int pH_value = analogRead(PH_PIN);
  float voltage = pH_value * (3.3 / 4095.0);
  float pH = 7 + (2.5 - voltage) * 3.5;
  
  // Serial.print(F("pH ADC: "));
  // Serial.print(pH_value);
  // Serial.print(F(" | Voltage: "));
  // Serial.print(voltage, 2);
  // Serial.print(F(" V | pH: "));
  // Serial.println(pH, 2);
  
  return pH;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println(F("\n--- Moisture $ pH Sensor Project ---"));
  
  analogSetAttenuation(ADC_11db);
  analogReadResolution(12);
  
  pinMode(RELAY_PIN1, OUTPUT);
  pinMode(RELAY_PIN2, OUTPUT);
  digitalWrite(RELAY_PIN1, HIGH);
  digitalWrite(RELAY_PIN2, HIGH);

  setupWiFi();
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Read sensor (every 2 seconds)
  if (currentMillis - lastSensorReadTime >= 2000) {
    int rawValue = analogRead(MOISTURE_PIN);
    moisturePercent = constrain(map(rawValue, DRY_VALUE, WET_VALUE, 0, 100), 0, 100);

    pH = readPHSensor();
    
    if (abs(moisturePercent - lastSentMoisturePercent) >= MOISTURE_CHANGE_THRESHOLD || abs(pH - lastSentPH) >= PH_CHANGE_THRESHOLD) {
      newDataAvailable = true;
    }
    
    // Serial.print(F("Moisture: "));
    // Serial.print(rawValue);
    // Serial.print(F(" raw, "));
    // Serial.print(moisturePercent);
    // Serial.println(F("%"));
    
    lastSensorReadTime = currentMillis;
  }
  
  if (currentMillis - lastPumpCheckTime >= ((pumpRunning1 || pumpRunning2) ? 1000 : 5000)) {
    // Serial.print(F("Moisture: "));
    // Serial.print(moisturePercent);
    // Serial.print(F("%, Threshold: "));
    // Serial.println(DRY_THRESHOLD);
    // Serial.print(F(" | pH: "));
    // Serial.print(pH, 2);
    // Serial.print(F(", Threshold: "));
    // Serial.println(PH_LOW_THRESHOLD);
    
    controlWaterPump();
    controlPHPump();
    
    lastPumpCheckTime = currentMillis;
  }

  if (currentMillis - lastWiFiCheckTime >= 10000) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println(F("WiFi disconnected, reconnecting..."));
      
      String ssid, password;
      if (loadWIFiCredentials(ssid, password)) {
        WiFi.begin(ssid.c_str(), password.c_str());
      }
    }
    lastWiFiCheckTime = currentMillis;
  }

  // if (newDataAvailable && WiFi.status() == WL_CONNECTED && 
  //     currentMillis - lastUbidotsSendTime >= 1000) {
    
  //   if (sendDataToUbidots(moisturePercent, pH)) {
  //     lastSentMoisturePercent = moisturePercent;
  //     newDataAvailable = false;
  //     Serial.println(F("Data sent to Ubidots"));
  //   }
    
  //   lastUbidotsSendTime = currentMillis;
  // }
  
  if ( WiFi.status() == WL_CONNECTED && 
      currentMillis - lastFlaskSendTime >= 5000) {
    
    if (sendDataToFlaskAPI(moisturePercent, pH)) {
      lastSentMoisturePercent = moisturePercent;
      lastSentPH = pH;
      newDataAvailable = false;
      Serial.println(F("Data sent to Flask API for MongoDB storage"));
    }
    
    lastFlaskSendTime = currentMillis;
  }
  delay(10);
}