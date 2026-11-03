#!/usr/bin/env python3
"""stub_engine.py - tiny fake UCI engine for the smoke2m.py self-test (behaviour from the file name of a copy).

Mode = the first word of argv[1] if given, else taken from the script name (stub_<mode>.py):
  illegal  answers every search with an illegal move (a1a8 when only e2e4 / d2d4 are listed)
  crash    exits with code 3 at its first `go wtime`
  hang     never answers a timed search
  stderr   plays a legal move but writes a line to stderr
  legal    plays a legal move (positive control for the stub path)
Every position gets the same legal list (e2e4, d2d4); the stub does not track the board.
"""
import os
import sys

mode = sys.argv[1] if len(sys.argv) > 1 else os.path.basename(sys.argv[0]).split('_', 1)[-1].rsplit('.', 1)[0]
for raw in sys.stdin:
    line = raw.strip()
    if line == 'uci':
        print('id name stub ' + mode)
        print('option name Threads type spin default 1 min 1 max 8')
        print('uciok', flush=True)
    elif line == 'isready':
        print('readyok', flush=True)
    elif line == 'quit':
        break
    elif line == 'go perft 1':
        print('e2e4: 1')
        print('d2d4: 1')
        print('nodes 2', flush=True)
    elif line.startswith('go wtime'):
        if mode == 'crash':
            sys.exit(3)
        if mode == 'hang':
            continue
        if mode == 'stderr':
            print('stub: something went wrong', file=sys.stderr, flush=True)
        print('info depth 1 score cp 0')
        print('bestmove ' + ('a1a8' if mode == 'illegal' else 'e2e4'), flush=True)
    elif line == 'stop' and mode == 'hang':
        continue
