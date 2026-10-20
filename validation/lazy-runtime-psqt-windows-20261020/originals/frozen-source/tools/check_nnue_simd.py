#!/usr/bin/env python3
"""Check that an AVX2 build actually widens the NNUE output arithmetic."""
import argparse
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("object", help="nnue object file or unstripped executable")
args = parser.parse_args()
assembly = subprocess.check_output(["objdump", "-Cd", args.object], text=True)
match = re.search(r"^[0-9a-f]+ <forge::nnue::evaluate\([^\n]*>:\n(.*?)(?=\n[0-9a-f]+ <|\Z)",
                  assembly, re.M | re.S)
if not match:
    raise SystemExit("FAIL: NNUE evaluate symbol not found")
body = match.group(1)
for instruction in ("vminps", "vmaxps", "vmulps", "vaddps"):
    if not re.search(r"\b" + instruction + r"\b[^\n]*%ymm", body):
        raise SystemExit(f"FAIL: NNUE output has no 256-bit {instruction}")
if re.search(r"\bvfn?m(?:add|sub)", body):
    raise SystemExit("FAIL: fused arithmetic changes the rounding contract")
print("PASS: NNUE output uses 256-bit clamp/multiply/add without fused arithmetic")
