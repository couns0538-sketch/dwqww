#!/usr/bin/env python3
"""fake_asan_engine.py : a fake engine that prints a REAL-LOOKING AddressSanitizer report.

Purpose: prove the job-3 runner can SEE a sanitizer line. It is not an engine and proves nothing about
the real engine; it only calibrates the runner (the brief's second proof, and Opus's Rule 1).
"""
import sys

for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name Planted Fault Engine")
        print("id author swarm-25")
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd.startswith("go"):
        print("=================================================================", flush=True)
        print("==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000010", flush=True)
        print("READ of size 8 at 0x602000000010 thread T0", flush=True)
        print("    #0 0x5555 in forge::Worker::search(Board&, SearchStack*, int, int, int, bool)", flush=True)
        print("SUMMARY: AddressSanitizer: heap-buffer-overflow in forge::Worker::search", flush=True)
        print("bestmove 0000", flush=True)
    elif cmd == "quit":
        break
