#include <Arduino.h>
#include <WiFiNINA.h>
#include <WiFiUdp.h>

// --- CONFIGURATION ---
#include "secrets.h"  // defines WIFI_SSID and WIFI_PASSWORD (not committed, see include/secrets.example.h)
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const int udpPort = 9002;                

// --- HARDWARE PINS ---
const int BUTTON_PIN = 2; // Grove Button on D2
const int MOTOR_PIN = 4;  // Vibration Motor on D4

// --- SYSTEM VARIABLES ---
WiFiUDP udp;
char packetBuffer[255];
String lastMessage = "STOPPED OR GONE"; 
String smoothedState = "STOPPED OR GONE"; 

bool systemActive = false; 
bool lastButtonState = LOW;
unsigned long lastDangerTime = 0; 

// --- PATTERN VARIABLES (SYNCED WITH WATCH) ---
String currentActivePattern = "STOPPED OR GONE";
unsigned long lastPatternTime = 0;
int patternStep = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(BUTTON_PIN, INPUT); 
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW); // Ensure motor is off at startup

  // 1. Connect to Wi-Fi immediately
  Serial.println("\n[+] Waking up... Connecting to Hotspot");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n[+] Wi-Fi Connected!");
  Serial.print("[*] Cane IP Address: ");
  Serial.println(WiFi.localIP());

  // 2. Start listening
  udp.begin(udpPort);
  Serial.println("[*] Listening on Port 9002.");
  Serial.println("[!] Cane is ASLEEP. Press the Grove button to activate the motor!");
}

void loop() {
  bool currentButtonReading = digitalRead(BUTTON_PIN);
  
  // If the pin spikes HIGH, check it carefully
  if (currentButtonReading == HIGH && lastButtonState == LOW) { 
    delay(50); // Wait 50ms to let electrical noise pass
    
    // Check again! Is the button STILL being pressed by a real human?
    if (digitalRead(BUTTON_PIN) == HIGH) {
      systemActive = !systemActive; // Flip the state
      
      if (systemActive) {
        // SYSTEM TURNED ON: 2 Quick Buzzes
        Serial.println("\n[>>>] CANE ACTIVATED! Motor is now live.");
        for (int i = 0; i < 2; i++) {
          digitalWrite(MOTOR_PIN, HIGH);
          delay(150);
          digitalWrite(MOTOR_PIN, LOW);
          delay(150);
        }
      } else {
        // SYSTEM TURNED OFF: 3 Quick Buzzes
        Serial.println("\n[zzz] Cane Asleep. Motor disabled.");
        smoothedState = "STOPPED OR GONE"; 
        currentActivePattern = ""; // Reset pattern
        
        for (int i = 0; i < 3; i++) {
          digitalWrite(MOTOR_PIN, HIGH);
          delay(150);
          digitalWrite(MOTOR_PIN, LOW);
          delay(150);
        }
      }
      delay(300); // Prevent rapid double-clicks
    }
  }
  lastButtonState = currentButtonReading;

  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = 0; 
    }
    lastMessage = String(packetBuffer); 
    lastMessage.trim(); 

    Serial.print("[UDP] AI says: ");
    Serial.println(lastMessage);

    // AI GLITCH FILTER LOGIC
    if (lastMessage == "< 15M AWAY" || lastMessage == "15-30M AWAY" || lastMessage == "> 30M AWAY") {
      smoothedState = lastMessage;
      lastDangerTime = millis(); // Reset the 1.5 second memory timer
    } 
    else {
      // Only believe it if 1.5 seconds have passed since the last vehicle detection
      if (millis() - lastDangerTime > 1500) {
        smoothedState = lastMessage; 
      }
    }
  }

  if (systemActive) {
    
    // If the AI zone changes, reset our timing sequence
    if (smoothedState != currentActivePattern) {
      currentActivePattern = smoothedState;
      patternStep = 0;
      lastPatternTime = millis();
      digitalWrite(MOTOR_PIN, LOW); // Clean slate for the new pattern
    }

    unsigned long elapsed = millis() - lastPatternTime;

    if (smoothedState == "< 15M AWAY") {
      // RED: Fast Emergency Pulse (ON 200, OFF 50)
      if (patternStep == 0) {
        digitalWrite(MOTOR_PIN, HIGH);
        if (elapsed >= 200) { patternStep = 1; lastPatternTime = millis(); }
      } else if (patternStep == 1) {
        digitalWrite(MOTOR_PIN, LOW);
        if (elapsed >= 50) { patternStep = 0; lastPatternTime = millis(); }
      }
    } 
    else if (smoothedState == "15-30M AWAY") {
      // ORANGE: Double Tap (ON 200, OFF 200, ON 200, OFF 800)
      if (patternStep == 0) {
        digitalWrite(MOTOR_PIN, HIGH);
        if (elapsed >= 200) { patternStep = 1; lastPatternTime = millis(); }
      } else if (patternStep == 1) {
        digitalWrite(MOTOR_PIN, LOW);
        if (elapsed >= 200) { patternStep = 2; lastPatternTime = millis(); }
      } else if (patternStep == 2) {
        digitalWrite(MOTOR_PIN, HIGH);
        if (elapsed >= 200) { patternStep = 3; lastPatternTime = millis(); }
      } else if (patternStep == 3) {
        digitalWrite(MOTOR_PIN, LOW);
        if (elapsed >= 800) { patternStep = 0; lastPatternTime = millis(); }
      }
    }
    else if (smoothedState == "> 30M AWAY") {
      // YELLOW: Relaxed Radar Ping (ON 200, OFF 2000)
      if (patternStep == 0) {
        digitalWrite(MOTOR_PIN, HIGH);
        if (elapsed >= 200) { patternStep = 1; lastPatternTime = millis(); }
      } else if (patternStep == 1) {
        digitalWrite(MOTOR_PIN, LOW);
        if (elapsed >= 2000) { patternStep = 0; lastPatternTime = millis(); }
      }
    }
    else {
      // SAFE TO CROSS / STOPPED
      digitalWrite(MOTOR_PIN, LOW);
    }
    
  } else {
    // If system is asleep, forcefully keep the motor off
    digitalWrite(MOTOR_PIN, LOW); 
  }
}