#!/usr/bin/env python3
"""Usage: python3 uci_option_case.py BASELINE CANDIDATE; candidate macro=1."""
import re
import subprocess
import sys
commands = 'setoption name usennue value false\nbench 11\nsetoption name USENNUE value true\nbench 11\nquit\n'
def nodes(exe):
    result = subprocess.run([exe], input=commands, text=True, capture_output=True, check=True, timeout=30)
    return [int(n) for n in re.findall(r'bench depth 11 nodes (\d+)', result.stdout)]
old, new = nodes(sys.argv[1]), nodes(sys.argv[2])
assert old == [312866, 312866], old
assert new == [375354, 312866], new
print('PASS baseline ignores noncanonical option names; candidate accepts both cases')
