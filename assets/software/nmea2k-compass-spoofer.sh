#!/bin/bash
# proven to work with Simrad NR12 MFD
while true; do
    # spoof garmin messages
    ./nmea2kspoofer.py --file logs/filtered-garmin.log --proto udp
done