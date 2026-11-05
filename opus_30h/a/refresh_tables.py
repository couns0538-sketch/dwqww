#!/usr/bin/env python3
"""refresh_tables.py - Opus 30-h job: replace the two generated tables in FINAL_REPORT.md (the window runs table and the
sanity table, each from its header row to the first blank line) with the current output of w2_tables.py. Prints what
it replaced; refuses when a header is not found exactly once. Own code."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent / 'FINAL_REPORT.md'
RUNS_HEAD = '| run | layout | superbatches / lr | final checkpoint | S31 vs lock (z) | jobA vs lock (z) | rule |'
SAN_HEAD = '| net | games (W / L / D, points) | Elo +/- (SANITY ONLY) | planned |'


def block(text, head):
    if text.count(head) != 1:
        sys.exit(f'header found {text.count(head)} times: {head[:40]}')
    i = text.index(head)
    j = text.find('\n\n', i)
    j = len(text) if j < 0 else j
    return i, j


def main():
    out = subprocess.run([sys.executable, '-I', '-B', str(HERE / 'w2_tables.py')], capture_output=True, check=True)
    new = out.stdout.decode('utf-8').replace('\r\n', '\n')
    runs_new, san_new = new.strip('\n').split('\n\n')
    t = REPORT.read_bytes().decode('utf-8')
    for head, repl in ((RUNS_HEAD, runs_new), (SAN_HEAD, san_new)):
        i, j = block(t, head)
        old_rows, new_rows = t[i:j].count('\n') + 1, repl.count('\n') + 1
        t = t[:i] + repl + t[j:]
        print(f'replaced {head[:30]}...: {old_rows} -> {new_rows} lines')
    REPORT.write_bytes(t.encode('utf-8'))


if __name__ == '__main__':
    main()
