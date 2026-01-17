# Arduino Stepper Motor Controller

## Hardware Setup

### Components Required:
- Arduino Uno R4 Minima
- 28BYJ-48 Stepper Motor
- ULN2003 Driver Board
- USB Cable (for Arduino connection)
- 5V Power Supply for motor

### Wiring Connections:

**ULN2003 Driver to Arduino:**
- IN1 → Pin 8
- IN2 → Pin 9
- IN3 → Pin 10
- IN4 → Pin 11
- VCC → 5V
- GND → GND

**ULN2003 Driver to Stepper Motor:**
- Connect the 5-wire connector from motor to driver

**Power:**
- Connect 5V power supply to ULN2003 board (separate from Arduino if needed)
- Ensure common ground between Arduino and motor power supply

## Arduino Setup

### 1. Install Arduino IDE
Download from: https://www.arduino.cc/en/software

### 2. Install Board Support
- Open Arduino IDE
- Go to Tools → Board → Boards Manager
- Search for "Arduino UNO R4"
- Install "Arduino UNO R4 Boards" package

### 3. Upload Sketch
1. Open `stepper_controller.ino` in Arduino IDE
2. Select Board: Tools → Board → Arduino UNO R4 Boards → Arduino UNO R4 Minima
3. Select Port: Tools → Port → (your Arduino port)
4. Click Upload button

### 4. Verify Upload
Open Serial Monitor (Tools → Serial Monitor) and set baud rate to 115200. You should see:
```
READY
```

## Python Setup

Install required package:
```bash
pip install pyserial
```

## Testing

### Test Arduino Directly (Serial Monitor)

In Arduino IDE Serial Monitor, send these commands:

```
STEP:100      # Move forward 100 steps
STEP:-50      # Move backward 50 steps
CALIBRATE     # Return to center
STATUS        # Get current position
PING          # Test connection
RELEASE       # Turn off motor coils
```

### Test Python Connection

```python
from src.hardware.stepper_motors.stepper_controller import ArduinoStepperController

# Auto-detect Arduino
motor = ArduinoStepperController()

# Move motor
motor.step_forward(100)
motor.step_backward(50)
motor.calibrate()

# Check position
print(motor.get_position())

# Cleanup
motor.cleanup()
```

### Test Center Stage System

```bash
source venv/bin/activate
python tests/test_center_stage.py
```

## Serial Communication Protocol

### Commands (Python → Arduino):

| Command | Description | Example |
|---------|-------------|---------|
| `STEP:n` | Move n steps (+ = forward, - = backward) | `STEP:100` |
| `CALIBRATE` | Return to center position | `CALIBRATE` |
| `STATUS` | Request current position | `STATUS` |
| `RELEASE` | Turn off motor coils | `RELEASE` |
| `PING` | Connection test | `PING` |

### Responses (Arduino → Python):

| Response | Description | Example |
|----------|-------------|---------|
| `READY` | Arduino initialized | `READY` |
| `POS:n` | Current position | `POS:150` |
| `CALIBRATED` | Calibration complete | `CALIBRATED` |
| `RELEASED` | Motor released | `RELEASED` |
| `PONG` | Ping response | `PONG` |
| `ERROR:msg` | Error message | `ERROR:Unknown command` |

## Troubleshooting

**Arduino not detected:**
- Check USB cable connection
- Install CH340 drivers if using clone boards
- Check port permissions on Linux: `sudo usermod -a -G dialout $USER`

**Motor not moving:**
- Verify wiring connections
- Check 5V power supply to ULN2003
- Ensure sketch is uploaded correctly
- Test with Serial Monitor commands

**Erratic movement:**
- Check all wire connections
- Ensure adequate power supply (5V, 500mA+)
- Reduce step delay in Arduino code if too slow

**Serial communication errors:**
- Verify baud rate is 115200 in both Arduino and Python
- Close Arduino Serial Monitor before running Python
- Check correct port in Python code

## Port Detection

The Python code auto-detects Arduino on these ports:
- Linux: `/dev/ttyACM0`, `/dev/ttyUSB0`
- macOS: `/dev/cu.usbmodem*`, `/dev/cu.usbserial*`
- Windows: `COM3`, `COM4`, `COM5`, etc.

To specify port manually:
```python
motor = ArduinoStepperController(port='/dev/ttyACM0')
```
