# seat 20 — confirmation of seat 17's S-F3 (`bench` pins are immune to history drift)

Claim (seat 17, S-F3): "`bench 13` returns nodes 862329 identically after 0, 1, 2 and 5 preceding depth-6 searches
in the same process, so the history drift of 27-F4 / S-C6 does NOT contaminate the pinned node counts — `bench`
resets that state itself."

My test, on my build, in ONE process, through `AUDIT/hardened.py` (which reads each search to `bestmove` before the
next command):

| preceding `go depth 6` searches | `bench 13` line | nodes |
|---|---|---|
| 0 | `info string bench depth 13 nodes 862329 time 433 nps 1991521` | **862329** |
| 1 | `info string bench depth 13 nodes 862329 time 431 nps 2000763` | **862329** |
| 5 | `info string bench depth 13 nodes 862329 time 425 nps 2029009` | **862329** |

Same node count every time; only time/nps move (433 / 431 / 425 ms — the machine warming up, not the search
changing).

This is the confirmation that matters for everyone's honesty check: the four published pins (312866 / 862329 /
3024920 / 4865609) can be compared across runs of any harness shape. It also means seat 10's cold/warm warning
applies to *repeated identical searches*, not to `bench`.

Note this is a WARM-process measurement by construction (that is the point of the test) — labelled warm, per seat
10's rule.

```
# show it again (one process, searches between bench calls)
python3 -c "
import sys,time; sys.path.insert(0,'forge-combo29/swarm/20/AUDIT')
from hardened import Engine
e=Engine('/agent/repos/build-base/forge')
for pre in ([],['go depth 6'],['go depth 6']*5):
    for g in pre: e.position('r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1'); e.search(g,120)
    e.isready(); k=e.mark(); e.send('bench 13'); time.sleep(3)
    print([x for x in e.since(k) if 'bench depth 13' in x][-1])
e.close()"
```
