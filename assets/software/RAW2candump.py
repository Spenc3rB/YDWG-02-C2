#!/usr/bin/env python3
import argparse
import datetime as _dt
import re
import sys

_line_re = re.compile(
    r"""^
        (?P<ts>\d{2}:\d{2}:\d{2}\.\d{3})
        \s+[RT]\s+
        (?P<id>[0-9A-Fa-f]{8})
        \s+
        (?P<data>(?:[0-9A-Fa-f]{2}\s+){0,7}[0-9A-Fa-f]{2})
        \s*$
    """, re.VERBOSE,
)

def _to_epoch(day: _dt.date, hms_ms: str) -> float:
    t = _dt.datetime.strptime(hms_ms, "%H:%M:%S.%f")
    dt = _dt.datetime.combine(day, t.time())
    return dt.timestamp()

def convert(infile, outfile, iface, day):
    base_date = _dt.datetime.strptime(day, "%Y-%m-%d").date()
    for ln, line in enumerate(infile, 1):
        m = _line_re.match(line)
        if not m:
            outfile.write(f"# {line}")
            continue

        epoch = _to_epoch(base_date, m["ts"])
        can_id = m["id"].upper()
        data = m["data"].replace(" ", "").upper()
        outfile.write(f"({epoch:0.6f}) {iface} {can_id}#{data}\n")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="input log file (YD RAW log format)")
    ap.add_argument("-o", "--output", help="output file (candump).  Default: stdout")
    ap.add_argument("--iface", default="can0", help="candump interface name (default: can0)")
    ap.add_argument("--date", default=_dt.date.today().isoformat(),
                    help="calendar date (YYYY-MM-DD) assumed for the timestamps\n"
                         "when the log itself contains only clock‑time")

    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8", errors="ignore") as fin:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fout:
                convert(fin, fout, args.iface, args.date)
        else:
            convert(fin, sys.stdout, args.iface, args.date)

if __name__ == "__main__":
    main()
