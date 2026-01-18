/*
Arduino Uno R4 Minima - Stepper Motor Face Tracking Controller
SEED Studio Gear Stepper Motor Driver Pack
4-wire stepper control for pan (left/right tracking)

Wiring:
- IN1 → Pin 8
- IN2 → Pin 9
- IN3 → Pin 10
- IN4 → Pin 11
- VCC → Arduino 5V
- GND → Arduino GND
- VM → External 5-12V supply
*/

#include <Stepper.h>

// Stepper motor specs (28BYJ-48)
const int STEPS_PER_REV = 2048;  // Steps per revolution (with half-step)

// Pin definitions (IN1, IN2, IN3, IN4)
const int IN1 = 8;
const int IN2 = 9;
const int IN3 = 10;
const int IN4 = 11;

// Create stepper object (note pin order for ULN2003 driver)
Stepper stepper(STEPS_PER_REV, IN1, IN3, IN2, IN4);

// Position tracking
int currentAngle = 90;        // Current angle (0-180 range)
long currentSteps = 0;        // Current step position
const float STEPS_PER_DEGREE = STEPS_PER_REV / 360.0;  // ~5.69 steps per degree

void setup() {
  // Initialize serial
  Serial.begin(115200);
  
  // Set stepper speed (RPM)
  stepper.setSpeed(10);  // 10 RPM - adjust for smoothness vs speed
  
  // Center position
  currentAngle = 90;
  currentSteps = 0;
  
  Serial.println("✓ Arduino Stepper Controller Ready - Pins 8-11");
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
  
  int targetAngle = -1;
  
  // Parse angle value
  int panIndex = command.indexOf("PAN:");
  if (panIndex != -1) {
    String angleStr = command.substring(panIndex + 4);
    targetAngle = angleStr.toInt();
  }
  
  // Validate and move stepper
  if (targetAngle >= 0 && targetAngle <= 180) {
    moveToAngle(targetAngle);
  }
  
  // Send acknowledgment
  Serial.print("OK:PAN:");
  Serial.println(currentAngle);
}

void moveToAngle(int targetAngle) {
  // Calculate step difference
  int angleDelta = targetAngle - currentAngle;
  long stepsToMove = (long)(angleDelta * STEPS_PER_DEGREE);
  
  // Move stepper
  if (stepsToMove != 0) {
    stepper.step(stepsToMove);
    
    // Update position
    currentAngle = targetAngle;
    currentSteps += stepsToMove;
  }
}