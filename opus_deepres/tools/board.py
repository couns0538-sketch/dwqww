#!/usr/bin/env python3
"""board.py - claim / release a slot on the crew's WORKER_BOARD.md (max 3 active workers) and log finished work.

usage: python -I -B board.py start S1|S2|S3 "<worker>" "<task>"
       python -I -B board.py done  S1|S2|S3 "<worker>" "<task>" "<result path>"
       python -I -B board.py check          (exit 1 if more than 3 slots are ACTIVE)
The board has exactly three slot lines (S1..S3), so it can never list more than 3 active workers. `start` takes the
named slot when it is idle, otherwise the first idle one (it prints which); when all three are ACTIVE it waits up to
10 minutes and then exits 3 (do not start work). `done` releases the slot that holds this worker + task (whatever its
number) and appends the done line. Updates hold a byte lock on the board file itself (msvcrt.locking, retried for
30 s); nothing is ever deleted. Times are the PC clock.
"""
import msvcrt
import re
import sys
import time

BOARD = 'D:/grok-pc-data/dwqww/WORKER_BOARD.md'
SLOTS = ('S1', 'S2', 'S3')


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
            new, info = fn(text)
            if new != text:
                f.seek(0)
                f.write(new.encode('utf-8'))
                f.truncate()
                f.flush()
            return info
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def slot_line(text, slot):
    m = re.search(r'^' + slot + r' \|(.*)$', text, re.M)
    if not m:
        sys.exit(f'board.py: slot {slot} not on the board')
    return m.group(1).strip()


def set_slot(text, slot, value):
    rx = re.compile(r'^' + slot + r' \|.*$', re.M)
    return rx.sub(f'{slot} | {value}', text, count=1)


def claim(slot, worker, task):
    def fn(text):
        order = [slot] + [s for s in SLOTS if s != slot]
        for s in order:
            if slot_line(text, s).startswith('idle'):
                return set_slot(text, s, f'ACTIVE | {worker} | {task} | since {now()}'), s
        return text, None
    return update(fn)


def release(slot, worker, task, result):
    def fn(text):
        held = None
        for s in SLOTS:
            line = slot_line(text, s)
            if line.startswith('ACTIVE') and f'| {worker} | {task} |' in f'{line} |':
                held = s
                break
        if held:
            text = set_slot(text, held, 'idle')
        return text.rstrip('\n') + f'\n{now()} | {worker} | {task} | {result}\n', held
    return update(fn)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    a = sys.argv[1:]
    if a and a[0] == 'check':
        text = open(BOARD, encoding='utf-8').read()
        n = len(re.findall(r'^S\d \| ACTIVE', text, re.M))
        print(f'{n} active slot(s) on the board')
        sys.exit(1 if n > 3 else 0)
    if len(a) < 4 or a[0] not in ('start', 'done') or a[1] not in SLOTS:
        sys.exit(__doc__)
    cmd, slot, worker, task = a[0], a[1], a[2], a[3]
    if cmd == 'start':
        got = None
        for i in range(31):
            got = claim(slot, worker, task)
            if got:
                break
            if i == 0:
                print('board.py: all 3 slots ACTIVE - waiting up to 10 minutes for a free slot')
            time.sleep(20)
        if not got:
            print('board.py: BOARD FULL for 10 minutes - do not start; hand back saying the board was full')
            sys.exit(3)
        if got != slot:
            print(f'board.py: {slot} was busy, took {got} (use any slot number in your done command)')
    else:
        result = a[4] if len(a) > 4 else '-'
        held = release(slot, worker, task, result)
        if not held:
            print('board.py: no ACTIVE slot held this worker + task; done line appended, no slot changed')
    print(open(BOARD, encoding='utf-8').read())


if __name__ == '__main__':
    main()
