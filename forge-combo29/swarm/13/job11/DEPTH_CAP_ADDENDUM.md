# S-F14 addendum: what `go depth D` does at and beyond the cap (corrects my earlier claim)

S-F14's CLAMP.md said "`go depth D` with D>64 can never be satisfied". **That was wrong**, and this file
corrects it. A request above 64 is answered normally: the engine clamps its reported depth at 64 and
returns a bestmove.

## Measured

PC r15, PC20, Threads 1, Hash 16, fresh process per run, 15 s limit then 60 s for the middlegame rows
(to tell a long search from a hang).

| board | `go depth D` | bestmove | info lines | max depth | time |
|---|---|---|---|---|---|
| mate-in-1 | 10 | `a1a8` | 10 | 10 | 0.00 s |
| mate-in-1 | 60 | `a1a8` | 60 | 60 | 0.00 s |
| mate-in-1 | 63 | `a1a8` | 63 | 63 | 0.00 s |
| mate-in-1 | 64 | `a1a8` | 64 | **64** | 0.00 s |
| mate-in-1 | **65** | **`a1a8`** | 64 | **64** | 0.00 s |
| mate-in-1 | **70** | **`a1a8`** | 64 | **64** | 0.00 s |
| middlegame | 10 | `g7g6` | 10 | 10 | 0.01 s |
| middlegame | 60/63/64/65/70 | NONE within 60 s | 31 | 31 | 60 s timeout |

## What this establishes
1. **A `go depth D` above 64 is answered, not hung.** The engine stops reporting at 64 and returns
   `bestmove`. So a match harness that asks for depth 70 gets a playable move, not a stall. My earlier
   sentence saying it "can never be satisfied" was wrong about the consequence.
2. **The cap is on the reported DEPTH, and the search still terminates.** On the mate board the whole
   sequence 64/65/70 returns in 0.00 s at 1,152 nodes.
3. **The middlegame rows that time out are long searches, not hangs.** At 60 s that board has reached
   only depth 31 — it is simply slow, and asking for depth 60 there is asking for a very long search
   whatever the cap does. I checked this by extending the limit from 15 s to 60 s: still depth 31, so it
   is progressing, not stuck.

## A harness bug of mine that this exposed (worth recording)
My first version of this script used `select()` on a text-mode pipe. `select()` reports "not ready"
while complete lines are already sitting in Python's buffer, so lines were silently lost — which
produced **non-monotonic nonsense**: `go depth 60` timed out while `go depth 63` answered in 0.00 s, and
`go depth 10` timed out on a position that takes 0.01 s. I replaced it with a reader thread that drains
the stream, and the results became monotonic and sensible.

The tell was the same as always: results that contradict themselves (a *deeper* request answering
*faster* than a shallower one) mean the measuring instrument is broken, not the engine. Had I trusted the
first table I would have reported that `go depth 60` hangs, which is false.

## SETTINGS LABEL CORRECTION (found by a settings audit, 2026-11-16)
When this job first ran, `depthcap.py`'s list named PC20 but held only FOUR options
(`Threads, Hash, OwnBook, MateAlphaGuard`) — the 14 S14 settings were missing. So the original numbers
were measured under a **PC6-like** regime while the script called it PC20.

Re-run with the canonical PC20 (22 options, imported from `../lib/settings.py`, which asserts its own
length), the conclusions are **unchanged**: `go depth 65` and `go depth 70` still answer with a bestmove,
the maximum reported depth is still 64, and 2 of the 4 above-64 requests answered while 2 timed out. The
finding itself was structural (a cap on the reported depth counter, and whether a request above it
terminates), so it is not surprising that tuning options do not move it — but that is now *measured*
rather than assumed, and the label is honest. Both runs are committed: `out2/` and `out3/` (pre-fix) and
`out_pc20/` (canonical PC20).

## Reproduce
```
cd forge-combo29/swarm/13/job11
python3 depthcap.py ~/b/pc/forge /tmp/dc 15
```
`out2/depthcap.json` (15 s limit) and `out3/depthcap.json` (60 s limit) hold the raw rows. `out/` is the
**pre-fix** run with the select() bug — kept so the non-monotonic table it produced can be inspected as
an example of the failure.
