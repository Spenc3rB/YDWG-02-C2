#!/usr/bin/env python3
import argparse
import socket
import re

def parse_can_messages(log_data):
    pattern = r'([0-9A-Fa-f]{8})#([0-9A-Fa-f]+)'
    messages = []
    for match in re.finditer(pattern, log_data):
        msg_id = match.group(1)
        data = match.group(2)
        # Pad to 8 bytes if needed
        bytes_list = [data[i:i+2] for i in range(0, len(data), 2)]
        while len(bytes_list) < 8:
            bytes_list.append('00')
        messages.append(f"{msg_id} {' '.join(bytes_list)}")
    return messages

def send_messages(messages, ip, port, protocol):
    if protocol == "tcp":
        with socket.create_connection((ip, port)) as sock:
            for msg in messages:
                sock.sendall((msg + '\r\n').encode())
                print(f"Sent TCP: {msg}")
    else:  # udp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for msg in messages:
            sock.sendto((msg + '\r\n').encode(), (ip, port))
            print(f"Sent UDP: {msg}")

def print_docs():
    docs = """
YDWG-02 CAN Log Sender
----------------------

This tool parses CAN logs and sends them over TCP or UDP to a YDWG-02 device.

Usage Examples:
1. Send from string directly:
   ./nmea2kspoofer.py "(1746126375.113601) can0 09F80103#FFFFFF7FFFFFFF7F"

2. Send from a log file:
   ./nmea2kspoofer.py /path/to/log.txt --file

3. Use UDP instead of TCP:
   ./nmea2kspoofer.pylog.txt --file --proto udp

Common NMEA 2000 PGNs:
- PGN 127488: Engine Parameters, Rapid Update
  Fields: Engine Speed, Boost Pressure, Tilt-Trim Position

- PGN 127489: Engine Parameters, Dynamic
  Fields: Oil Pressure, Oil Temperature, Coolant Temperature, Alternator Voltage

- PGN 127250: Vessel Heading
  Fields: Heading, Deviation, Variation

- PGN 128259: Speed
  Fields: Speed Water Referenced

- PGN 128267: Water Depth
  Fields: Depth Below Transducer

- PGN 129025: Position, Rapid Update
  Fields: Latitude, Longitude

- PGN 130306: Wind Data
  Fields: Wind Speed, Wind Angle

For a comprehensive list of PGNs and their fields, refer to the NMEA 2000 standard documentation.
"""
    print(docs)

def main():
    parser = argparse.ArgumentParser(description="Replay or spoof CAN logs to YDWG-02 in RAW format.")
    parser.add_argument("log", nargs='?', help="String of log formatted messages OR path to a log file.")
    parser.add_argument("--ip", default="192.168.4.1", help="Target IP address (default: 192.168.4.1)")
    parser.add_argument("--port", type=int, default=1456, help="Target port (default: 1456)")
    parser.add_argument("--proto", choices=["tcp", "udp"], default="tcp", help="Protocol (default: tcp)")
    parser.add_argument("--file", action="store_true", help="Treat log as a file path, not raw string")
    parser.add_argument("--docs", action="store_true", help="Display usage examples and common NMEA 2000 PGNs")

    args = parser.parse_args()

    if args.docs:
        print_docs()
        return

    if not args.log:
        parser.print_help()
        return

    if args.file:
        with open(args.log, "r") as f:
            raw_data = f.read()
    else:
        raw_data = args.log

    messages = parse_can_messages(raw_data)
    if not messages:
        print("No valid CAN messages found.")
        return

    send_messages(messages, args.ip, args.port, args.proto)

if __name__ == "__main__":
    main()
