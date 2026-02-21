#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>

// --- ตั้งค่า WiFi ---
const char* ssid = "gaybank";
const char* password = "12345678";

// --- ตั้งค่า Server (เปลี่ยนเป็น IP ของคอมพิวเตอร์คุณ) ---
const char* websockets_server_host = "10.254.139.106"; 
const uint16_t websockets_server_port = 8000; // Port ของ FastAPI

using namespace websockets;
WebsocketsClient client;

// ฟังก์ชันดึง MAC Address แบบไม่มีเครื่องหมาย :
String getMacAddress() {
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  return mac;
}

void setup() {
  Serial.begin(115200);

  // --- 1. ตั้งค่ากล้อง ESP32-CAM (AI-Thinker) ---
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5; config.pin_d1 = 18; config.pin_d2 = 19; config.pin_d3 = 21;
  config.pin_d4 = 36; config.pin_d5 = 39; config.pin_d6 = 34; config.pin_d7 = 35;
  config.pin_xclk = 0; config.pin_pclk = 22; config.pin_vsync = 25;
  config.pin_href = 23; config.pin_sscb_sda = 26; config.pin_sscb_scl = 27;
  config.pin_pwdn = 32; config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // ปรับคุณภาพและขนาดภาพ (ยิ่งเล็กยิ่งลื่น)
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA; // 640x480
    config.jpeg_quality = 12; // 0-63 (น้อยคือชัดมาก)
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // --- 2. เชื่อมต่อ WiFi ---
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  // --- 3. เชื่อมต่อ WebSocket ---
  String serverUrl = "ws://" + String(websockets_server_host) + ":" + String(websockets_server_port) + "/ws/images/camera/" + getMacAddress();
  Serial.println("Connecting to: " + serverUrl);
  
  bool connected = client.connect(serverUrl);
  if(connected) {
      Serial.println("Connected to Server!");
  } else {
      Serial.println("Connection Failed!");
  }
}

void loop() {
  if (client.available()) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      return;
    }

    // ส่งข้อมูลภาพแบบ Binary
    client.sendBinary((const char*)fb->buf, fb->len);
    
    // คืนค่า memory กล้อง
    esp_camera_fb_return(fb);
    
    // หน่วงเวลาเล็กน้อยเพื่อคุม Frame Rate
    // delay(50); 
  } else {
    // พยายามเชื่อมต่อใหม่หากหลุด
    Serial.println("Connection lost. Reconnecting...");
    delay(5000);
    client.connect("ws://" + String(websockets_server_host) + ":" + String(websockets_server_port) + "/ws/images/camera/" + getMacAddress());
  }
}
