#!/usr/bin/env python
#
# esp8266_parse_bin.py Version 1.1 1/22/2018
# (C)opyright 2018 Email: earl@microcontrollerelectronics.com
# Parses (decodes) ESP8266 single or combined binary image files
#
#
# Partial document on the ESP8266 Image Format
# https://github.com/espressif/esptool/wiki/Firmware-Image-Format
#
#    0        1   2         3   4-7   8
# 0xE9 segments SPI mem/speed entry  ...
# 0xEA segments SPI mem/speed entry  ...
#
#  --SEGMENTS--
#
#     0-3   4-7   8-n
#  Offset  size   data

import os, sys, string, struct

fsize    = 0
chk      = 0
htype    = ''
filename = sys.argv[1]
f        = open(filename, "rb")
afsize   = os.stat(filename).st_size
baddr    = ""
bsize    = 0
useg     = ""
uaddr    = ""
usize    = 0

def blank_header():
  global baddr,bsize
  print("%-8s %-12s %-12s %-12s %-12s %-12s") % ("","","Size/Hex","Size/Bytes","File/Offset","File/Offset")
  print("%-8s %-12s %-12s %-12s %-12s %-12s") % ("Blank(s)","0xff",'0x'+hex(bsize)[2:].zfill(8),bsize,'0x'+hex(baddr)[2:].zfill(8),baddr)
  baddr = ""
  bsize = 0

def unknown_header():
  global uaddr,usize,useg 
  print("%-8s %-12s %-12s %-12s %-12s %-12s") % ("","","Size/Hex","Size/Bytes","File/Offset","File/Offset")
  print("%-8s %-12s %-12s %-12s %-12s %-12s") % ("Unknown","",'0x'+hex(usize)[2:].zfill(8),usize,'0x'+hex(uaddr)[2:].zfill(8),uaddr)
  for b in bytearray(useg): print(hex(b)),
  print
  uaddr = ""
  useg  = ""
  usize = 0

print("Parsing: %s Size: %s/%s") % (filename,hex(afsize),afsize)

while(1):
  t = f.read(8)
  if not t: break
  l = len(t)
  sh = ord(t[0])
  if (sh != 0xff):
    if (baddr != ""): blank_header()
  if ((sh == 0xea) or (sh == 0xe9) or (sh == 0xff)):
    if (uaddr != ""): unknown_header()
  if l < 8:
    print("Extra Data [no-header] of Length: %s -> ") % (len(t)),
    for b in bytearray(t): print(hex(b)),
    print
    fsize += l
    break
  h = struct.Struct("<BBBBI").unpack(t)
  if (h[0] == 0xea): 
    segments = 1
    htype    = 0xea
  else:
    if (h[0] == 0xe9):
      segments = int(h[1])
      htype    = 0xe9
      chk      = 0 
    else:
      if (h[0] == 0xff):
        if (baddr == ""): baddr = fsize
        bsize += l
        fsize += l
        continue
      else:
        if (uaddr == ""): uaddr = fsize
        useg  += t
        usize += l
        fsize += l
        continue

  fsize += l
  print "Header: ",hex(h[0]),int(h[1]),hex(h[2]),hex(h[3]),hex(h[4])
  print("%-8s %-12s %-12s %-12s %-12s %-12s") % ("Segment","Offset","Size/Hex","Size/Bytes","File/Offset","File/Offset")
  for x in range(0,segments):
    data = f.read(8)
    if not data: break
    s = struct.Struct("<II").unpack(data)
    offset  = s[0]
    size    = s[1]
    print("%-8s %-12s %-12s %-12s %-12s %-12s") % (x+1,'0x'+hex(offset)[2:].zfill(8),'0x'+hex(size)[2:].zfill(8),size,'0x'+hex(fsize)[2:].zfill(8),fsize),
    if (htype != 0xea):
      if (offset > 0x40200000): print(" <-- Offset > 0x40200000 "),
      if (offset < 0x3ffe0000): print(" <-- Offset < 0x3ffe0000 "),
      if (size > 65536):        print(" <-- Size > 65536 "),
    print
    l = int(s[1])
    fsize += 8 + l
    data = f.read(l)
    for b in bytearray(data): chk ^= int(b)

  if (htype == 0xea): continue
  pad  = 16 - (fsize % 16)
  print("Padding: %s bytes -> ") % (pad),
  data = f.read(pad)
  for b in bytearray(data): print(hex(b)),
  print
  chk = chk ^ 0xEF
  print("Calculated Checksum: %s") % (hex(chk)),
  if (ord(data[-1]) == chk): print " [matches]",
  print
  fsize += pad
  continue

if (uaddr != ""): unknown_header()
if (baddr != ""): blank_header()

print("File Size: %s  Calculated: %s") % (afsize,fsize),
if (afsize == fsize): print(" [matches]"),
print