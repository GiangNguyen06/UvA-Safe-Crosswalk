// #include <Arduino.h>
// #include "Ultrasonic.h"

// Ultrasonic ultrasonic(4);
// const int vibePin = 6;    

// void setup() {
//   pinMode(vibePin, OUTPUT);
//   Serial.begin(9600);
//   delay(2000);
// }

// void loop() {

//   long distance = ultrasonic.MeasureInCentimeters();
  
//   Serial.print("Car Distance: ");
//   Serial.print(distance);
//   Serial.println(" cm");
//   if (distance > 150 || distance <= 0) {
//     Serial.println("Status: SAFE - SILENT");
//     analogWrite(vibePin, 0); 
//     delay(250); 
//   }
  
  
//   else if (distance < 30) {
//     Serial.println("Status: DANGER - VIBRATING MAX");
//     analogWrite(vibePin, 255); 
//     delay(250);
//   }
  
//   else {
//     Serial.println("Status: APPROACHING - PULSING");
    
//     int pauseTime = map(distance, 30, 150, 50, 800);

//     analogWrite(vibePin, 200);  
//     delay(150);                 
//     analogWrite(vibePin, 0);   
//     delay(pauseTime);           
//   }
// }


#include <Arduino.h>
#include "Ultrasonic.h"


Ultrasonic ultrasonic(4); 
const int speakerPin = 6; 

void setup() {
  pinMode(speakerPin, OUTPUT);
  Serial.begin(9600);
  delay(2000);
  Serial.println("--- Audio Proximity Demo Initialized ---");
}

void loop() {
  long distance = ultrasonic.MeasureInCentimeters();
  
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");


  if (distance > 150 || distance <= 0) {
    Serial.println("Status: SAFE - SILENT");
    noTone(speakerPin); 
    delay(250); 
  }
  
  
  else if (distance < 30) {
    Serial.println("Status: DANGER - SOLID TONE");
    tone(speakerPin, 1000);
    delay(250); 
  }

  else {
    Serial.println("Status: APPROACHING - BEEPING");
    
    int pauseTime = map(distance, 30, 150, 50, 800);

    tone(speakerPin, 800);   
    delay(100);              
    noTone(speakerPin);      
    delay(pauseTime);        
  }
}