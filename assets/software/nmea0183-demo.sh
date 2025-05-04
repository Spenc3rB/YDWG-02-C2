#!/bin/bash

TARGET="192.168.4.1:1456"
PROTO="tcp"
SPOOFER="./nmea0183spoofer.py"

declare -a SENTENCES=(
    # GPS Positioning
    "GPGLL,4807.038,N,01131.000,E,123519,A"
    "GPGGA,123456,3723.2475,N,12158.3416,W,1,08,1.0,545.4,M,46.9,M,,"
    "GPGNS,3723.2475,N,12158.3416,W,AA,1,08,1.0,545.4,46.9,,"
    "GPRMC,123519,A,4807.038,N,01131.000,E,0.00,69.0,230394,,,A"
    "GPVTG,134.4,T,,M,10.5,N,19.4,K,A"
    "GPZDA,201530.00,04,07,2023,,"

    # Heading
    "GPHDG,123.4,0.0,E,3.1,W"
    "GPHDT,123.4,T"
    "GPHDM,123.4,M"
    "GPROT,+2.5,A"

    # Wind & Environmental
    "WIMWD,045.0,T,023.0,M,5.5,N,10.2,M"
    "WIMWV,045.0,R,10.2,N,A"
    "WIMDA,29.92,I,1.013,B,25.0,C,22.0,C,80.0,P,5.5,N,045.0,T"
    "WIMTW,22.5,C"
    "YDXDR,A,22.5,C,TempAir,A,1013,B,Baro"

    # Depth & Speed
    "SDDBT,100.0,f,30.5,M,16.5,F"
    "SDDBS,30.5,M"
    "SDDPT,30.5,0.4"
    "VWVHW,,T,,M,5.5,N,10.2,K"
    "VWVBW,5.5,5.5,0.0,0.0"
    "VWVLW,12345.6,100.2"

    # Navigation
    "GPAPB,A,A,0.10,R,N,V,V,005.5,T,003.5,M,DEST,001"
    "GPRMB,A,0.66,L,DEST,START,4807.038,N,01131.000,E,000.5,360.0,000.5,A"
    "GPBOD,045.0,T,023.0,M,DEST,START"
    "GPBWR,123519,4807.038,N,01131.000,E,045.0,T,10.5,N,DEST"
    "GPRTE,1,1,c,RouteName,001,002,003"
    "GPWPL,4807.038,N,01131.000,E,WAYPOINT"

    # Rudder
    "GPRSA,15.0,A,-15.0,A"

    # AIS
    "AIVDM,1,1,,A,13aG;o0000QK;88MD5MTDwwP0000,0"

    # Engine / Status
    "YDRPM,0,1,1000.0"
    "YDDSC,123456789,1,12,34,56,0,1,2,3"
    "YDDSE,123456789,1,0,,TEST DATA"
)

for sentence in "${SENTENCES[@]}"; do
    echo "Sending: $sentence"
    $SPOOFER --target "$TARGET" --sentence "${sentence}" --type "$PROTO"
    sleep 0.03
    # send a GPGLL sentence every 0.03 seconds to delimit the messages, since we know that works
    $SPOOFER --target "$TARGET" --sentence "GPGLL,4807.038,N,01131.000,E,123519,A" --type "$PROTO"
    sleep 0.03
done
