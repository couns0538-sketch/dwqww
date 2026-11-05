#!/usr/bin/env python3
"""board.py - claim / release a slot on the crew's WORKER_BOARD.md (max 3 active workers) and log finished work.

usage: python -I -B board.py start S1|S2|S3 "<worker>" "<task>"
       python -I -B board.py done  S1|S2|S3 "<worker>" "<task>" "<result path>"
       python -I -B board.py check          (exit 1 if more than 3 slots are ACTIVE)
The board has exactly three slot lines (S1..S3), so it can never list more than 3 active workers. Updates hold a
byte lock on the board file itself (msvcrt.locking, retried for 30 s); nothing is ever deleted. Times are the PC clock.
"""
import msvcrt
import os
import re
import sys
import time

BOARD = 'D:/grok-pc-data/dwqww/WORKER_BOARD.md'


def now():
    return time.strftime('%H:%M')


def update(fn):
    with open(BOARD, 'r+b') as f:
        for _ in range(300):
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                time.sleep(0.1)
        else:
            sys.exit('board.py: board locked for 30 s, giving up (nothing written)')
        try:
            f.seek(0)
            text = f.read().decode('utf-8')
            new = fn(text)
            f.seek(0)
            f.write(new.encode('utf-8'))
            f.truncate()
            f.flush()
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def set_slot(text, slot, value):
    rx = re.compile(r'^' + slot + r' \|.*$', re.M)
    if not rx.search(text):
        sys.exit(f'board.py: slot {slot} not on the board')
    return rx.sub(f'{slot} | {value}', text, count=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    a = sys.argv[1:]
    if a and a[0] == 'check':
        text = open(BOARD, encoding='utf-8').read()
        n = len(re.findall(r'^S\d \| ACTIVE', text, re.M))
        print(f'{n} active slot(s) on the board')
        sys.exit(1 if n > 3 else 0)
    if len(a) < 4 or a[0] not in ('start', 'done') or a[1] not in ('S1', 'S2', 'S3'):
        sys.exit(__doc__)
    cmd, slot, worker, task = a[0], a[1], a[2], a[3]
    if cmd == 'start':
        update(lambda t: set_slot(t, slot, f'ACTIVE | {worker} | {task} | since {now()}'))
    else:
        result = a[4] if len(a) > 4 else '-'
        update(lambda t: set_slot(t, slot, 'idle').rstrip('\n') + f'\n{now()} | {worker} | {task} | {result}\n')
    print(open(BOARD, encoding='utf-8').read())


if __name__ == '__main__':
    main()
