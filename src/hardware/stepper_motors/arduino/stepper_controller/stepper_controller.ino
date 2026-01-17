/*
 * Center Stage SERVO Controller
 * Arduino Uno R4 Minima
 *
 * Controls a servo motor
 * Receives commands via Serial from Python
 *
 * Protocol (same as stepper version):
 *  - STEP:<n>      (relative move; + = right, - = left)
 *  - CALIBRATE     (go to center position)
 *  - RELEASE       (detach servo)
 *  - STATUS        (print current position)
 *  - PING          (PONG)
 */

#include <Servo.h>

// Servo pin
const int SERVO_PIN = 9;

// Servo limits (adjust for your mechanism)
const int SERVO_MIN = 0;
const int SERVO_MAX = 180;

// "Center" position for CALIBRATE
const int SERVO_CENTER = 90;

// How many degrees to move per "STEP" unit
// If your Python sends small step counts (like 10, -10), set this to 1.
// If it used stepper-step counts (like 200, -200), set this smaller like 0.1 (see note below).
const float DEGREES_PER_STEP_UNIT = 1.0;

// Movement smoothing
const int MOVE_DELAY_MS = 10;   // delay between incremental degree updates
const int MOVE_INCREMENT_DEG = 1; // 1 degree increments

Servo servo;
bool servoAttached = false;

// We'll keep currentPosition like before, but now it's servo angle in degrees
int currentPosition = SERVO_CENTER;

void setup() {
  Serial.begin(115200);

  attachServoIfNeeded();
  servo.write(currentPosition);

  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
}

void processCommand(const String &command) {
  if (command.startsWith("STEP:")) {
    // Format: STEP:10 (positive = right, negative = left)
    long units = command.substring(5).toInt();

    // Convert units to degrees (relative)
    float deltaDegF = units * DEGREES_PER_STEP_UNIT;

    // Round to nearest int degree (servo works in degrees)
    int deltaDeg = (deltaDegF >= 0) ? (int)(deltaDegF + 0.5f) : (int)(deltaDegF - 0.5f);

    int target = clampAngle(currentPosition + deltaDeg);
    moveServoSmooth(target);

    Serial.print("POS:");
    Serial.println(currentPosition);

  } else if (command == "CALIBRATE") {
    moveServoSmooth(SERVO_CENTER);
    Serial.println("CALIBRATED");

  } else if (command == "RELEASE") {
    releaseServo();
    Serial.println("RELEASED");

  } else if (command == "STATUS") {
    Serial.print("POS:");
    Serial.println(currentPosition);

  } else if (command == "PING") {
    Serial.println("PONG");

  } else {
    Serial.println("ERROR:Unknown command");
  }
}

void attachServoIfNeeded() {
  if (!servoAttached) {
    servo.attach(SERVO_PIN);
    servoAttached = true;
  }
}

void releaseServo() {
  if (servoAttached) {
    servo.detach();     // stop holding position
    servoAttached = false;
  }
}

// Smooth move from currentPosition to target
void moveServoSmooth(int target) {
  attachServoIfNeeded();

  if (target == currentPosition) return;

  int step = (target > currentPosition) ? MOVE_INCREMENT_DEG : -MOVE_INCREMENT_DEG;

  while (currentPosition != target) {
    currentPosition += step;

    // Avoid overshoot
    if ((step > 0 && currentPosition > target) || (step < 0 && currentPosition < target)) {
      currentPosition = target;
    }

    servo.write(currentPosition);
    delay(MOVE_DELAY_MS);
  }
}

int clampAngle(int angle) {
  if (angle < SERVO_MIN) return SERVO_MIN;
  if (angle > SERVO_MAX) return SERVO_MAX;
  return angle;
}