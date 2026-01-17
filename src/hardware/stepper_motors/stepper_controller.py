import serial
import serial.tools.list_ports
import time
import threading

class ArduinoServoController:
    """
    Controls a servo via Arduino Uno R4 Minima over serial connection.
    Uses the same command protocol as your stepper version:
      STEP:<n>, CALIBRATE, RELEASE, STATUS, PING
    Where STEP:<n> is a relative move (in "step units").
    Recommended: set Arduino DEGREES_PER_STEP_UNIT = 1.0 so 1 unit = 1 degree.
    """

    def __init__(self, port=None, baudrate=115200, timeout=2):
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.current_position = 90   # servo angle in degrees (0..180), start at center
        self.connected = False
        self.simulation_mode = False
        self.lock = threading.Lock()

        if port is None:
            port = self._find_arduino()

        if port:
            self.connect(port)
        else:
            print("Warning: Arduino not found. Running in simulation mode.")
            self.simulation_mode = True

    def _find_arduino(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if 'Arduino' in p.description or 'CH340' in p.description or 'USB' in p.description:
                print(f"Found potential Arduino on {p.device}: {p.description}")
                return p.device

        common_ports = ['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 'COM4']
        for port in common_ports:
            try:
                test_serial = serial.Serial(port, self.baudrate, timeout=1)
                test_serial.close()
                return port
            except Exception:
                continue
        return None

    def connect(self, port):
        try:
            self.serial = serial.Serial(port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Arduino reset

            start_time = time.time()
            while time.time() - start_time < 5:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode(errors="ignore").strip()
                    if line == "READY":
                        self.connected = True
                        self.simulation_mode = False
                        print(f"Arduino connected on {port}")

                        self._send_command("PING")
                        response = self._read_response()
                        if response == "PONG":
                            print("Arduino communication verified")

                        # Sync current position from Arduino
                        self.get_position()
                        return True

            print("Warning: Arduino found but not responding. Check upload.")
            self.serial.close()
            self.serial = None
            self.simulation_mode = True

        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            self.simulation_mode = True

        return False

    def _send_command(self, command: str):
        if self.serial and self.connected:
            with self.lock:
                self.serial.write(f"{command}\n".encode())
                self.serial.flush()

    def _read_response(self, timeout=1):
        if not self.serial or not self.connected:
            return None
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                return self.serial.readline().decode(errors="ignore").strip()
        return None

    # ---- Servo actions ----

    def move_relative(self, delta_degrees: int):
        """
        Relative move in degrees (recommended if Arduino DEGREES_PER_STEP_UNIT = 1.0).
        Positive = right, negative = left (same convention as your stepper code).
        """
        if not self.connected or self.simulation_mode:
            self.current_position = max(0, min(180, self.current_position + delta_degrees))
            print(f"[SIM] Servo moved {delta_degrees}°. Angle: {self.current_position}")
            return

        self._send_command(f"STEP:{delta_degrees}")

        response = self._read_response()
        if response and response.startswith("POS:"):
            self.current_position = int(response.split(":")[1])

    def move_to_angle(self, angle_degrees: int):
        """
        Absolute move to angle (0..180).
        This maps to a relative STEP command to keep protocol unchanged.
        """
        angle_degrees = max(0, min(180, int(angle_degrees)))
        delta = angle_degrees - self.current_position
        self.move_relative(delta)

    # Keep old method names for backward compatibility
    def step_forward(self, steps=1):
        # For servo: treat "steps" as degrees
        self.move_relative(+int(steps))

    def step_backward(self, steps=1):
        self.move_relative(-int(steps))

    def calibrate(self):
        """Return to center (Arduino sets to SERVO_CENTER, typically 90)."""
        if not self.connected or self.simulation_mode:
            print(f"[SIM] Calibrating from angle {self.current_position} to 90")
            self.current_position = 90
            return

        self._send_command("CALIBRATE")
        response = self._read_response()
        if response == "CALIBRATED":
            # Arduino servo code sets center; sync from STATUS to be sure
            self.get_position()
            print("Servo calibrated to center")

    def release(self):
        """Detach servo (stop holding)."""
        if self.connected and not self.simulation_mode:
            self._send_command("RELEASE")
            self._read_response()

    def get_position(self):
        """Get current servo angle in degrees."""
        if self.connected and not self.simulation_mode:
            self._send_command("STATUS")
            response = self._read_response()
            if response and response.startswith("POS:"):
                self.current_position = int(response.split(":")[1])
        return self.current_position

    def cleanup(self):
        self.release()
        if self.serial and self.connected:
            self.serial.close()
        print("Arduino controller cleaned up")


# Backward compatible alias (if your code expects StepperMotor)
StepperMotor = ArduinoServoController

if __name__ == "__main__":
    m = ArduinoServoController()
    print("Angle:", m.get_position())

    m.move_to_angle(0)
    time.sleep(1)
    m.move_to_angle(90)
    time.sleep(1)
    m.move_to_angle(180)
    time.sleep(1)

    m.move_relative(-30)
    time.sleep(1)

    m.calibrate()
    m.cleanup()