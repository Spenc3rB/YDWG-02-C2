# NOTES

Logs have been collected and can be further filtered during my discovery of SAs using the Simrad Chartplotter, and are considered the first address chosen by the devices so far (at least with the Simrad and/or Autopilot connected first):
- SA: 0x00 = NAC_1 virtual rudder feedback
- SA: 0x07 = NAC_1 rudder feedback 
- SA: 0x01 = NAC_1 Autopilot
- SA: 0x05 = Simrad N12 MFD
- SA: 0x04 = Simrad N12 Navigator
- SA: 0x06 = Simrad N12 Pilot Computer
- SA: 0x03 = Simrad N12 iGPS
- SA: 0x43 = YDGW02 
- SA: 0x02 = Garmin Compass

It is recommended to get CANboat's analyzer tool to get more insights into the log details. For example:
```
cat candump-autopilot.log | candump2analyzer | analyzer
```

An example of the output of the analyzer tool is shown in the [canboat-output-0183.txt](./canboat-output-0183.txt) file.

This directory contains the following files:
```
.
├── autopilot
│   ├── candump-autopilot.log -- autopilot log as it is connected to the NMEA 2000 network
│   ├── candump-nac1-SWUP-addr-claim.log -- Software Update Address Claim log
│   └── SWUP-parsed-addr-claim.log -- parsed log of the SWUP address claim
├── canboat-output-0183.txt -- output of the analyzer tool from results of the nmea0183-demo.sh script
├── candump-sample-gnss.log -- sample GNSS log found online
├── garmin-compass
│   ├── candump-garmin.log -- garmin compass log as it is connected to the NMEA 2000 network
│   └── filtered-garmin.log -- filtered log of the garmin compass
├── pcan-2000.trc -- pcan log of the NMEA 2000 network
├── README.md -- this file
├── test-nmea0183spoofer-default.sh-results.txt -- results of the test-nmea0183spoofer-default.sh script
├── ydwg
│   ├── candump-ydwg02.log -- YDWG-02 log as it is connected to the NMEA 2000 network
│   ├── pcan-0183.log -- pcan log of NMEA 2K from 0183 messages
│   └── pcan-0183.trc -- pcan log of NMEA 2K from 0183 messages
└── YDWG-02 NMEA 2000 Raw Sample.log -- YDWG-02 NMEA 2000 raw sample log
```