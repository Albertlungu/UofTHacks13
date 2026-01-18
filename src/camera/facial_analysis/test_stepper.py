import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import servo tracker
stepper_tracker = None
try:
    from hardware.servo_tracker import StepperTracker
except ImportError:
    StepperTracker = None

print("=== Stepper Motor Direct Test ===\n")

# Initialize
tracker = StepperTracker(port='COM12')  # Change to your port

if not tracker.connect():
    print("Failed to connect!")
    exit()

tracker.start_tracking()

print("\nSending test commands:")
print("1. Center (90°)")
tracker._send_servo_command(90)
time.sleep(2)

print("2. Left (45°)")
tracker._send_servo_command(45)
time.sleep(2)

print("3. Right (135°)")
tracker._send_servo_command(135)
time.sleep(2)

print("4. Center (90°)")
tracker._send_servo_command(90)
time.sleep(2)

print("\n✓ Test complete")
tracker.disconnect()