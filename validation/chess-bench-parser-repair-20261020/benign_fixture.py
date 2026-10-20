#!/usr/bin/env python3
"""Benign parser-test process; contains no chess engine or search implementation."""
import os
from pathlib import Path
import sys
import time

assert sys.stdin.read() == 'bench 11\nquit\n'
mode = os.environ['BENCH_FIXTURE_MODE']
data = (Path(__file__).parent / 'captures/hosted.stdout.bin').read_bytes()
if mode == 'malformed':
    data = data.removeprefix(b'info string ')
sys.stdout.buffer.write(data)
sys.stdout.buffer.flush()
if mode == 'stderr':
    sys.stderr.write('benign fixture diagnostic\n')
if mode == 'timeout':
    time.sleep(30)
sys.exit(7 if mode == 'nonzero' else 0)
