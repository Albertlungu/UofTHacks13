import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"Port: {port.device}")
    print(f"  Description: {port.description}")
    print(f"  Manufacturer: {port.manufacturer}")
    print()