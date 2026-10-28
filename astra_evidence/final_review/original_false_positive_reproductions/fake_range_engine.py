#!/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3
import sys,re
s=sys.stdin.read()
print('option name Feature type spin default 1 min 1 max 5')
print('uciok')
print('readyok')
d=int(re.search(r'bench (\d+)',s)[1])
print(f'info string bench depth {d} nodes 123 time 1 nps 123000')
