# fake_engine.py - a stand-in "engine" for checker self-tests. It answers the quick pin set with the right numbers
# and then exits with code 0 (mode ok) or 3 (mode exit3), so a checker that ignores exit codes is exposed.
import sys

mode = sys.argv[1] if len(sys.argv) > 1 else 'ok'
net = True
for line in sys.stdin:
    t = line.split()
    if not t:
        continue
    if t[0] == 'uci':
        print('id name fake')
        print('uciok')
    elif t[0] == 'isready':
        print('readyok')
    elif t[0] == 'setoption' and 'UseNNUE' in t:
        net = (t[-1] == 'true')
    elif t[0] == 'bench':
        d = int(t[1])
        n = {(True, 11): 312866, (False, 11): 375354}.get((net, d), 1)
        print('info string bench depth %d nodes %d time 1 nps 1' % (d, n))
    elif t[0] == 'go' and len(t) > 1 and t[1] == 'perft':
        print('nodes 4865609')
    elif t[0] == 'quit':
        break
    sys.stdout.flush()
sys.exit(3 if mode == 'exit3' else 0)
