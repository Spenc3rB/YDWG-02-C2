#!/usr/bin/env python3
import argparse
import socket
import serial
import sys
import textwrap

def calc_checksum(nmea_body):
    checksum = 0
    for char in nmea_body:
        checksum ^= ord(char)
    return f"{checksum:02X}"

def build_nmea_sentence(body):
    checksum = calc_checksum(body)
    return f"${body}*{checksum}\r\n"

def send_serial(port, sentence, baud=4800):
    with serial.Serial(port, baudrate=baud, timeout=1) as ser:
        ser.write(sentence.encode('ascii'))
        print(f"[SERIAL] Sent: {sentence.strip()}")

def send_udp(host, port, sentence):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(sentence.encode('ascii'), (host, port))
        print(f"[UDP] Sent to {host}:{port} -> {sentence.strip()}")

def send_tcp(host, port, sentence):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(sentence.encode('ascii'))
        print(f"[TCP] Sent to {host}:{port} -> {sentence.strip()}")

if __name__ == "__main__":
    if '--docs' in sys.argv:
        nmea_docs = {
            "GGA": {
                "description": "Global Positioning System Fix Data",
                "fields": [
                    "1. UTC Time (hhmmss)",
                    "2. Latitude (ddmm.mmmm)",
                    "3. N/S Indicator",
                    "4. Longitude (dddmm.mmmm)",
                    "5. E/W Indicator",
                    "6. Fix Quality (0=Invalid, 1=GPS fix, 2=DGPS fix)",
                    "7. Number of Satellites",
                    "8. Horizontal Dilution of Precision",
                    "9. Altitude",
                    "10. Altitude Units",
                    "11. Geoid Separation",
                    "12. Geoid Separation Units",
                    "13. Age of Differential GPS data",
                    "14. Differential Reference Station ID"
                ]
            },
            "RMC": {
                "description": "Recommended Minimum Navigation Info",
                "fields": [
                    "1. UTC Time (hhmmss)",
                    "2. Status (A=active, V=void)",
                    "3. Latitude (ddmm.mmmm)",
                    "4. N/S Indicator",
                    "5. Longitude (dddmm.mmmm)",
                    "6. E/W Indicator",
                    "7. Speed over ground (knots)",
                    "8. Course over ground (degrees)",
                    "9. Date (ddmmyy)",
                    "10. Magnetic variation",
                    "11. Magnetic variation direction (E/W)"
                ]
            },
            "HDT": {
                "description": "Heading True",
                "fields": [
                    "1. Heading in degrees",
                    "2. 'T' (indicates true north)"
                ]
            },
            "HDG": {
                "description": "Heading, Deviation, and Variation",
                "fields": [
                    "1. Heading (degrees)",
                    "2. Deviation",
                    "3. Deviation Direction (E/W)",
                    "4. Magnetic Variation",
                    "5. Variation Direction (E/W)"
                ]
            },
            "RSA": {
                "description": "Rudder Sensor Angle",
                "fields": [
                    "1. Starboard angle",
                    "2. Starboard status (A=valid)",
                    "3. Port angle",
                    "4. Port status (A=valid)"
                ]
            },
            "GSA": {
                "description": "GNSS DOP and Active Satellites",
                "fields": [
                    "1. Mode (M=manual, A=auto)",
                    "2. Fix type (1=none, 2=2D, 3=3D)",
                    "3–14. PRNs of satellites used",
                    "15. PDOP",
                    "16. HDOP",
                    "17. VDOP"
                ]
            },
            "GSV": {
                "description": "GNSS Satellites in View",
                "fields": [
                    "1. Total sentences",
                    "2. Sentence number",
                    "3. Satellites in view",
                    "4–7. Satellite PRN, Elevation, Azimuth, SNR (repeated)"
                ]
            }
        }

        for sentence, info in nmea_docs.items():
            print(f"\n{sentence} - {info['description']}")
            for field in info['fields']:
                print(f"  {field}")
        print("""\nExamples:\n\
./nmea0183spoofer.py --type serial --target /dev/ttyUSB0 --sentence "GPGGA,123456,3723.2475,N,12158.3416,W,1,08,0.9,545.4,M,46.9,M,,"

./nmea0183spoofer.py --type udp --target 192.168.1.100:10110 --sentence "GPGLL,4916.45,N,12311.12,W,225444,A"

./nmea0183spoofer.py --type tcp --target 192.168.4.1:1456 --sentence "YDHDG,231.2,0.0,E,4.9,W"
            """)
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Spoof an NMEA 0183 sentence. This program also comes with quick references of NMEA sentences if you run it with --docs.")
    parser.add_argument('--type', choices=['serial', 'udp', 'tcp'], required=True,
                        help="Output type: serial, udp, or tcp")
    parser.add_argument('--target', required=True,
                        help="Serial device (/dev/ttyUSB0) or IP:PORT")
    parser.add_argument('--sentence', required=True,
                        help="NMEA sentence body (without $ or *checksum)")
    parser.add_argument('--baud', type=int, default=4800,
                        help="Baud rate for serial (default: 4800)")

    args = parser.parse_args()
    full_sentence = build_nmea_sentence(args.sentence)

    if args.type == "serial":
        send_serial(args.target, full_sentence, baud=args.baud)
    else:
        if ':' not in args.target:
            raise ValueError("For TCP/UDP, target must be in format IP:PORT")
        ip, port = args.target.split(':')
        port = int(port)
        if args.type == "udp":
            send_udp(ip, port, full_sentence)
        elif args.type == "tcp":
            send_tcp(ip, port, full_sentence)
