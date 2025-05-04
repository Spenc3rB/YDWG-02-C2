#!/usr/bin/env python3
import sys
import re

def parse_trc_line(line):
    line = line.strip()
    if not line or line.startswith(';'):
        return None

    pattern = re.compile(r"^\s*\d+\s+([0-9.]+)\s+DT\s+([0-9A-F]{8})\s+Rx\s+(\d)\s+(.+)$")
    match = pattern.match(line)
    if not match:
        return None

    timestamp = float(match.group(1)) / 1000.0
    can_id = match.group(2).upper()
    data_len = int(match.group(3))
    data_bytes = match.group(4).strip().split()

    if len(data_bytes) != data_len:
        return None 

    data = ''.join([b.upper() for b in data_bytes])
    return f"({timestamp:.6f}) can0 {can_id}#{data}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pcantrc2candump <file.trc>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        for line in f:
            parsed = parse_trc_line(line)
            if parsed:
                print(parsed)
