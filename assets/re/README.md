# ESP8285 Binary Format and Findings

### Header

https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/firmware-image-format.html

00000000  e9 03 03 2f 38 04 10 40  00 00 10 40 68 09 00 00  |.../8..@...@h...|
00000010  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|

0xE9: Magic byte
0x03: Segment count (3)
0x03: Flash mode (DOUT)
0x2f: Flash size / frequency (80MHz 4MB)
0x38: Entry address (0x40100438)

### Segments

#### Segment 1

00000000  e9 03 03 2f 38 04 10 40  00 00 10 40 68 09 00 00  |.../8..@...@h...|

Memory offset: 0x40100000
Segment size: 0x968 (2408 bytes)

#### Segment 2

00000970  60 86 06 b2 ff 00 00 00  00 80 fe 3f 08 03 00 00  |`..........?....|

Memory offset: 0x3FFE8000
Segment size: 0x308 (776 bytes)

#### Segment 3

00000c80  77 9d d7 46 b9 ff 00 00  10 83 fe 3f 78 02 00 00  |w..F.......?x...|

Memory offset: 0x3FFE8310
Segment size: 0x287 (647 bytes)

To find more about the metadata of this file: https://microcontrollerelectronics.com/decoding-an-esp8266-firmware-image/