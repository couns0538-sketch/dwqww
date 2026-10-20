#!/usr/bin/env python3
"""Benign parser-test process; contains no chess engine or search implementation."""
import os
from pathlib import Path
import sys
import time

mode = os.environ['BENCH_FIXTURE_MODE']
assert sys.stdin.read() == ('uci\nquit\n' if mode.startswith('uci-') else 'bench 11\nquit\n')
data = (Path(__file__).parent / 'captures/hosted.stdout.bin').read_bytes()
if mode.startswith('uci-'):
    data = (Path(__file__).parent / 'captures/native17-uci-prefix.stdout.bin').read_bytes()
    if mode == 'uci-noack':
        data = data.replace(b'uciok\n', b'')
    elif mode == 'uci-option-prefix':
        data = data.replace(b'option name Ponder', b'garbage option name Ponder')
    elif mode == 'uci-duplicateack':
        data += b'uciok\n'
if mode == 'malformed':
    data = data.removeprefix(b'info string ')
sys.stdout.buffer.write(data)
sys.stdout.buffer.flush()
if mode == 'stderr':
    sys.stderr.write('benign fixture diagnostic\n')
if mode == 'timeout':
    time.sleep(30)
sys.exit(7 if mode == 'nonzero' else 0)
