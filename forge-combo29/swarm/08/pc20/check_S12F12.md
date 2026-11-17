# CHECK of seat 12's S-F12 — a `setoption` during a search silently STOPS it — seat 08

Their finding:
> S-F12: "`setoption` sent during a running search SILENTLY STOPS that search (4/4 option types: Hash, MultiPV,
> LmrQuietBase, OwnBook), exactly like `stop`, on base AND PC r15 — while `isready` correctly does NOT."

## Verdict: CONFIRMS on both builds, with both controls clean

My own harness (`check_s12f12.py`): `go depth 24` on a middlegame position, probe sent after 150 ms, then measure
the final depth reached and how long the search took to answer after the probe.

**PC r15 under PC20, Threads 1**

| probe | depth at probe | final depth | ms after probe | did it stop early? |
|---|---|---|---|---|
| `setoption Hash value 32` | 17 | **17** | **1** | **YES** |
| `setoption MultiPV value 2` | 17 | **17** | 1 | **YES** |
| `setoption LmrQuietBase value 94` | 17 | **17** | 1 | **YES** |
| `setoption OwnBook value true` | 17 | **17** | 1 | **YES** |
| `isready` (CONTROL) | 17 | **24** | 881 | no |
| nothing (CONTROL) | 17 | **24** | 877 | no |

**base 6b98f217 under S14** — identical pattern: all four setoptions stop at 17 in ~1 ms; `isready` and no-probe reach
24 in ~875 ms.

So: **4 of 4 option types stop the search on both builds**, in about a millisecond, and the two controls show the
search otherwise runs to full depth. Their claim reproduces exactly in kind, on both builds.

## Why this is worth more than the claim itself

**It is a measurement-integrity fact for the whole swarm.** Any harness that sends a `setoption` while a search is
running silently truncates that search: it receives a `bestmove` about 1 ms later, at whatever depth it had reached,
and records it as if the search had completed. A "depth 24" result would then really be a depth-17 result, with no
error, no warning, and no line in the output that says so.

For my own area this is a live risk: several of my scripts send `setoption` lines between searches, and it is only
safe because they send them **before** `go`, after the previous `bestmove` was read. I checked that ordering is what
my harnesses do (`sync()` after every `setoption`, and no setoption between `go` and `bestmove`), so **no timing or
score of mine is affected** — but a script that set an option to "change the clock behaviour mid-search" would have
been measuring a truncated search.

## A concrete caution for anyone reading this
`setoption` behaving "exactly like stop" means these two sequences give the same result:
```
go depth 24
setoption name Hash value 32    <- search stops here, bestmove in ~1 ms
```
```
go depth 24
stop                            <- same
```
So a harness cannot use a mid-search `setoption` to adjust an option for the NEXT search without also truncating the
current one.

## What I did NOT do
- Did not test every option type (4 of the engine's ~60, chosen to match their four and to include a string-free
  spin, a spin with a lower bound, a check, and Hash).
- Did not test `setoption` before ANY iteration completed (probe at 150 ms guarantees depth 17 here); what happens at
  depth 0 is seat 12's S-F8 territory, not this check.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s12f12.py /tmp/s12.txt
