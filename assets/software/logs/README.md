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
- SA: 0x02 = Garmin GPS

It is recommended to get CANboat's analyzer tool to get more insights into the log details. For example:
```
cat candump-autopilot.log | candump2analyzer| analyzer
```