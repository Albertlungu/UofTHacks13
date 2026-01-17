# Center Stage - Arduino Wiring Guide

## Quick Start Wiring

### Components You Need:
1. **Arduino Uno R4 Minima** - The microcontroller
2. **28BYJ-48 Stepper Motor** - The motor (usually comes with ULN2003 driver)
3. **ULN2003 Driver Board** - Controls the motor
4. **USB Cable** - To connect Arduino to computer
5. **Jumper Wires** - 4 male-to-female wires
6. **5V Power Supply** (optional but recommended for better performance)

---

## Step-by-Step Wiring

### 1. ULN2003 Driver Board → Arduino Uno R4

Connect these 4 signal pins:

```
ULN2003 Board          Arduino Pin
─────────────          ───────────
IN1                →   Digital Pin 8
IN2                →   Digital Pin 9
IN3                →   Digital Pin 10
IN4                →   Digital Pin 11
```

### 2. Power Connections

**Option A: USB Power Only (for testing)**
```
ULN2003 Board          Arduino
─────────────          ────────
VCC (+)            →   5V Pin
GND (-)            →   GND Pin
```

**Option B: External Power (recommended)**
```
5V Power Supply    →   ULN2003 VCC (+)
Power Supply GND   →   ULN2003 GND (-)
                       AND
Power Supply GND   →   Arduino GND (common ground!)
```

### 3. Motor to Driver

Simply plug the 5-wire connector from the 28BYJ-48 motor into the ULN2003 board's motor socket. It only fits one way!

---

## Visual Pin Layout

```
Arduino Uno R4 Minima
┌─────────────────────┐
│  USB                │
│  ▼                  │
│                     │
│  D8  ───────────────┼── IN1 (ULN2003)
│  D9  ───────────────┼── IN2 (ULN2003)
│  D10 ───────────────┼── IN3 (ULN2003)
│  D11 ───────────────┼── IN4 (ULN2003)
│                     │
│  5V  ───────────────┼── VCC (ULN2003)
│  GND ───────────────┼── GND (ULN2003)
│                     │
└─────────────────────┘

ULN2003 Driver Board
┌──────────────────┐
│ IN1 IN2 IN3 IN4  │ ← Signal pins (to Arduino)
│                  │
│   [LEDs]         │ ← Status LEDs
│                  │
│  VCC  GND        │ ← Power input
│                  │
│ [Motor Socket]   │ ← 5-wire connector to motor
└──────────────────┘

28BYJ-48 Motor
     ╔═════╗
     ║     ║
     ║ ⚙   ║
     ║     ║
     ╚══╤══╝
        │ 5-wire cable
        └──→ Plugs into ULN2003
```

---

## Complete Connection Checklist

- [ ] IN1 from ULN2003 connected to Arduino Pin 8
- [ ] IN2 from ULN2003 connected to Arduino Pin 9
- [ ] IN3 from ULN2003 connected to Arduino Pin 10
- [ ] IN4 from ULN2003 connected to Arduino Pin 11
- [ ] VCC from ULN2003 connected to Arduino 5V (or external 5V supply)
- [ ] GND from ULN2003 connected to Arduino GND
- [ ] Motor 5-wire connector plugged into ULN2003 socket
- [ ] USB cable connected from Arduino to computer
- [ ] If using external power: Common ground between Arduino and power supply

---

## Upload Arduino Code

1. Open Arduino IDE
2. Open file: `src/hardware/stepper_motors/arduino/stepper_controller.ino`
3. Select Board: **Tools → Board → Arduino UNO R4 Boards → Arduino UNO R4 Minima**
4. Select Port: **Tools → Port → (your Arduino's port)**
5. Click **Upload** button (→ arrow icon)
6. Wait for "Done uploading"

---

## Test It Works

### Method 1: Serial Monitor Test
1. Open **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. You should see: `READY`
4. Type `STEP:100` and press Enter
5. Motor should rotate!

### Test Commands:
```
STEP:100       → Motor moves forward 100 steps
STEP:-100      → Motor moves backward 100 steps  
CALIBRATE      → Return to center position
STATUS         → Show current position
PING           → Test (should reply PONG)
```

### Method 2: Python Test
```bash
# Install Python package
pip install pyserial

# Run center stage test
python tests/test_center_stage.py
```

---

## Troubleshooting

**Motor not moving?**
- Check all 4 signal wire connections (IN1-IN4)
- Verify motor cable is fully inserted into ULN2003 socket
- Try external 5V power supply instead of USB power
- Check LEDs on ULN2003 board - should light up when motor moves

**Arduino not detected?**
- Check USB cable (use data cable, not charge-only)
- Install CH340 drivers if needed
- Try different USB port

**Motor moves erratically?**
- Use external 5V power supply (USB may not provide enough current)
- Check for loose wire connections
- Ensure common ground if using external power

**Serial Monitor shows nothing?**
- Verify baud rate is 115200
- Press Arduino reset button
- Re-upload the sketch

---

## Camera Mount Setup

To mount the camera:
1. Attach motor shaft to a simple pan mechanism
2. Mount webcam on the pan platform
3. Motor will rotate left/right to track faces
4. Typical range: ±90 degrees (about 512 steps each direction)

## Next Steps

Once wired and tested:
1. Keep Arduino USB connected
2. Run Python center stage system: `python src/camera/center_stage.py`
3. The camera will track faces and send commands to Arduino
4. Motor automatically pans to keep person centered!
