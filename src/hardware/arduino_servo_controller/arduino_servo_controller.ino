/*
Arduino Uno R4 WiFi - Servo Motor Face Tracking Controller
Single servo on Pin 9 for pan (left/right tracking)
Receives pan angle via serial and controls servo

Wiring:
- Servo data pin → Pin 9 (PWM)
- Servo 5V → Arduino 5V
- Servo GND → Arduino GND
*/

#include <Servo.h>

// Pin definition
const int SERVO_PIN = 9;  // PWM pin for servo

// Servo object
Servo panServo;

// Current angle
int currentAngle = 90;

void setup() {
  // Initialize serial
  Serial.begin(115200);
  
  // Attach servo
  panServo.attach(SERVO_PIN);
  
  // Center servo
  panServo.write(90);
  currentAngle = 90;
  
  Serial.println("✓ Arduino Servo Controller Ready - Pin 9");
  delay(1000);
}

void loop() {
  // Check for incoming serial data
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      parseAndExecute(command);
    }
  }
}

void parseAndExecute(String command) {
  /*
  Expected format: "PAN:90"
  */
  
  int angle = -1;
  
  // Parse angle value
  int panIndex = command.indexOf("PAN:");
  if (panIndex != -1) {
    String angleStr = command.substring(panIndex + 4);
    angle = angleStr.toInt();
  }
  
  // Apply servo command
  if (angle >= 0 && angle <= 180) {
    panServo.write(angle);
    currentAngle = angle;
  }
  
  // Send acknowledgment
  Serial.print("OK:PAN:");
  Serial.println(currentAngle);
}