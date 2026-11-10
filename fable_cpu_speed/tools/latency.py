# latency.py - bug hunt: how long does the engine take to answer a clocked search, measured from outside?
# For `go wtime T btime T` the whole remaining clock is T ms: an answer later than T would lose on time under a
# strict clock. For `go movetime M` the budget is M ms. Every case is repeated; the slowest answer counts.
# Wall time is taken in this process around "send go" .. "bestmove seen", so it includes pipe latency.
#   python -I -B latency.py --exe X --log L [--mask 0x1000] [--threads 1] [--repeats 5]
import argparse
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

POS = [('start', 'position startpos'), ('kiwipete', 'position fen ' + U.KIWIPETE),
       ('endgame', 'position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1'),
       ('middlegame', 'position fen r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--mask', default='0x1000')
    ap.add_argument('--threads', type=int, default=1)
    ap.add_argument('--repeats', type=int, default=5)
    a = ap.parse_args()
    U.require_lane()
    mask = U.parse_mask(a.mask)
    specs = [('wtime %d btime %d' % (t, t), t) for t in (1, 2, 5, 10, 15, 20, 30, 50, 100, 500)]
    specs += [('movetime %d' % m, m) for m in (1, 5, 10, 20, 50, 100)]
    specs += [('wtime 1000 btime 1000 movestogo 1', 1000), ('wtime 100 btime 100 winc 1000 binc 1000', 100),
              ('wtime 60 btime 60 winc 50 binc 50', 60)]
    planned = len(specs) * len(POS) * a.repeats
    L = U.header('BUG HUNT: answer time of clocked searches', [os.path.abspath(__file__), U.__file__], [a.exe], [
        'settings: Threads %d, Hash default, Move Overhead default (10 ms), net on, ucinewgame before every search; engine mask 0x%X; this process mask 0x%X' % (a.threads, mask, U.self_affinity()),
        'planned %d searches (%d limits x %d positions x %d repeats)' % (planned, len(specs), len(POS), a.repeats)])
    eng = U.Engine(a.exe, mask)
    L.append('child mask read back 0x%X' % eng.child_mask)
    eng.uci()
    eng.setoption('Threads', a.threads)
    eng.isready()
    done = late = 0
    L.append('%-42s %8s %8s %8s %8s  %s' % ('limit', 'budget', 'min ms', 'median', 'max ms', 'verdict'))
    try:
        for spec, budget in specs:
            times, worst = [], ''
            for name, pos in POS:
                for _ in range(a.repeats):
                    eng.send('ucinewgame')
                    eng.isready()
                    eng.send(pos)
                    t0 = time.perf_counter()
                    d, s, n, b = eng.go(spec, 30)
                    dt = (time.perf_counter() - t0) * 1000.0
                    times.append(dt)
                    done += 1
                    if dt >= max(times):
                        worst = '%s, depth %d, nodes %d, %s' % (name, d, n, b)
            over = max(times) > budget
            late += 1 if over else 0
            L.append('%-42s %8d %8.2f %8.2f %8.2f  %s' % ('go ' + spec, budget, min(times), statistics.median(times), max(times),
                                                        ('LATER THAN THE BUDGET (slowest: %s)' % worst) if over else 'inside the budget'))
        code = eng.quit()
    except Exception as e:  # noqa
        L.append('ERROR ' + str(e))
        eng.kill()
        code = None
    L.append('planned %d completed %d; limits with an answer later than their budget: %d of %d; exit code %s' % (planned, done, late, len(specs), code))
    L.append('VERDICT LATENCY %s; end %s' % ('DONE' if (done == planned and code == 0) else 'INCOMPLETE', U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L[-(len(specs) + 3):]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
