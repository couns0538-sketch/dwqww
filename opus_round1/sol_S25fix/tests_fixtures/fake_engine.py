"""Synthetic UCI engine for the S25 v2 tests (no chess). usage: fake_engine.py MODE

MODE: al1 | lprime | crlf | tail | extra_option | expose | expose_check | missing_option | sleep
"""
import sys
import time

AL1 = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
LPRIME = {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774}
OPTIONS = ['option name Hash type spin default 32 min 1 max 2048',
           'option name Threads type spin default 1 min 1 max 256',
           'option name Move Overhead type spin default 10 min 0 max 1000',
           'option name Ponder type check default false',
           'option name OwnBook type check default true',
           'option name Book File type string default <empty>',
           'option name Book Depth type spin default 30 min 0 max 100',
           'option name Book Variety type spin default 30 min 0 max 100',
           'option name UseNNUE type check default true',
           'option name Clear Hash type button']


def main():
    mode = sys.argv[1]
    nl = '\r\n' if mode == 'crlf' else '\n'
    out = sys.stdout.buffer
    for raw in sys.stdin.buffer:
        cmd = raw.decode().strip()
        if cmd.startswith('bench'):
            depth = int(cmd.split()[1])
            if mode == 'sleep':
                time.sleep(20)
            nodes = (LPRIME if mode == 'lprime' else AL1)[depth]
            out.write(('info string bench depth %d nodes %d time 5 nps 100%s' % (depth, nodes, nl)).encode())
            if mode == 'tail':
                out.write(('info string stats 0%s' % nl).encode())
        elif cmd == 'uci':
            opts = list(OPTIONS)
            if mode == 'missing_option':
                opts = opts[:-1]
            if mode == 'extra_option':
                opts.append('option name NnueExactInt32 type check default false')
            if mode in ('expose', 'expose_check'):
                opts += ['option name LmrBase type spin default 77 min 0 max 200',
                         'option name RfpMargin type spin default 80 min 0 max 400']
            if mode == 'expose_check':
                opts.append('option name TuneFlag type check default false')
            out.write(('id name Fake%sid author Test%s' % (nl, nl) + ''.join(o + nl for o in opts) + 'uciok' + nl).encode())
        elif cmd == 'quit':
            break
        out.flush()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
