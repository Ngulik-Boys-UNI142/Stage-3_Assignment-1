#include <WiFiManager.h>
#include "esp_camera.h"
#include <WebServer.h>
#include <HTTPClient.h>
#include "FS.h"
#include "LittleFS.h"

#define TRIGGER_PIN 13

#define WIFI_CONFIG_FILE "/wifi_config.txt"

bool wm_nonblocking = false;
WiFiManager wm;
const char* flask_url = "https://api-smart-plant.vercel.app/post/image";

void saveWiFiManagerParamsCallback() {
  saveWiFiCredentials(WiFi.SSID(), WiFi.psk());
}

bool loadWiFiCredentials(String &ssid, String &password) {
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

void initLittleFS() {
  if (!LittleFS.begin(true)) {
    Serial.println(F("ERROR: LittleFS Mount Failed"));
  }
}

void setupWiFi() {
  initLittleFS();
  
  String ssid, password;
  bool credentialsLoaded = loadWiFiCredentials(ssid, password);
  
  if (wm_nonblocking) wm.setConfigPortalBlocking(false);
  
  std::vector<const char *> menu = {"wifi", "info", "param", "sep", "restart", "exit"};
  wm.setMenu(menu);
  wm.setClass("invert");
  wm.setSaveConfigCallback(saveWiFiManagerParamsCallback);
  
  if (credentialsLoaded) {
    Serial.println("Using saved WiFi credentials");
    WiFi.begin(ssid.c_str(), password.c_str());
    
    unsigned long startTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < 10000) {
      delay(500);
      Serial.print(".");
    }
    Serial.println();
    
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("Failed to connect with saved credentials, starting config portal");
      if (!wm.autoConnect("ESP32CAM_AP", "password")) {
        Serial.println("Failed to connect or hit timeout");
        ESP.restart();
      }
    } else {
      Serial.println("Connected with saved credentials");
    }
  } else {
    Serial.println("No saved credentials, starting config portal");
    if (!wm.autoConnect("ESP32CAM_AP", "12345678")) {
      Serial.println("Failed to connect or hit timeout");
      ESP.restart();
    }
  }
  
  Serial.println("Connected... yeey :)");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  delay(3000);
  Serial.println("\nStarting");
  
  WiFi.mode(WIFI_STA);
  
  pinMode(TRIGGER_PIN, INPUT);
  
  #ifdef BOARD_HAS_PSRAM
    Serial.println("PSRAM is enabled in build flags");
  #else
    Serial.println("PSRAM is not enabled in build flags");
  #endif
  
  if (psramInit()) {
    Serial.println("PSRAM initialized successfully");
  } else {
    Serial.println("PSRAM initialization failed");
  }
  
  if (psramFound()) {
    Serial.println("PSRAM found and available");
    Serial.printf("Free PSRAM: %d bytes\n", ESP.getFreePsram());
  } else {
    Serial.println("No PSRAM detected or not properly initialized");
  }
  
  setupWiFi();
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  config.frame_size = FRAMESIZE_UXGA;
  config.jpeg_quality = 10;
  config.fb_count = 1;
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    Serial.println("Try connecting GPIO 0 to GND briefly while resetting to enter flash mode");
    return;
  }
  
  Serial.println("Camera initialized successfully");
  
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    s->set_framesize(s, FRAMESIZE_UXGA);
    s->set_quality(s, 10);
    s->set_brightness(s, 0);
    s->set_contrast(s, 0);
    s->set_saturation(s, 0);
    s->set_special_effect(s, 0);
    s->set_wb_mode(s, 0);
  }
}

unsigned long lastWiFiCheckTime = 0;
const unsigned long wifiCheckInterval = 30000;

void loop() {
  if (wm_nonblocking) wm.process();
  
  unsigned long currentMillis = millis();
  if (currentMillis - lastWiFiCheckTime >= wifiCheckInterval) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected, reconnecting...");
      
      String ssid, password;
      if (loadWiFiCredentials(ssid, password)) {
        WiFi.begin(ssid.c_str(), password.c_str());
        
        unsigned long startTime = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - startTime < 10000) {
          delay(500);
          Serial.print(".");
        }
        Serial.println();
        
        if (WiFi.status() == WL_CONNECTED) {
          Serial.println("Reconnected to WiFi");
        } else {
          Serial.println("Failed to reconnect with saved credentials");
        }
      }
    }
    lastWiFiCheckTime = currentMillis;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Capturing image...");
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      delay(2000);
      return;
    }
    
    Serial.printf("Image captured - Size: %d bytes\n", fb->len);
    
    HTTPClient http;
    http.begin(flask_url);
    http.addHeader("Content-Type", "image/jpeg");
    
    Serial.println("Sending image to server...");
    int httpResponseCode = http.POST(fb->buf, fb->len);
    
    if (httpResponseCode > 0) {
      Serial.printf("Image sent. Status code: %d\n", httpResponseCode);
      String response = http.getString();
      Serial.println("Server response: " + response);
    } else {
      Serial.printf("Failed to send image. Error: %s\n", http.errorToString(httpResponseCode).c_str());
    }
    
    http.end();
    esp_camera_fb_return(fb);
    
    Serial.println("Waiting before next capture...");
    delay(5000);
  } else {
    Serial.println("WiFi not connected, skipping image capture");
    delay(2000);
  }
}