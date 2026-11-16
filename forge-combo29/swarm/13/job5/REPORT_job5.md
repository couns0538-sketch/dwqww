# REPORT_job5 — `go softnodes N` on the PC build under PC20, Threads 1 (suggested area, FABLE file 6)

## What was asked
File 6's suggested area: on the PC build under PC20 at Threads 1, is `go softnodes N`
(1) deterministic run to run, (2) stopping at a finished depth, and (3) how far past N does it go.

## The answer
1. **Deterministic: yes, without exception.** 63 runs, each repeated twice in separate fresh
   processes with full PC20 applied: **63/63 identical** in depth, node count, score and bestmove.
   Cross-checked again between two separate script invocations (6 overlapping cases): identical.
2. **Stops at a finished depth: yes, 63/63.** Verified by re-searching each position with
   `go depth <the depth softnodes reached>` and requiring the same node count. That is a real test —
   if softnodes cut mid-depth the two counts would differ.
3. **Overshoot: large and not bounded in proportion.** The search finishes the depth it is in, so the
   overshoot is whatever the rest of that depth costs. Measured medians and worst cases over 12 real
   game positions:

| N | median overshoot | median % past N | worst overshoot | worst % past N |
|---|---|---|---|---|
| 2,000 | 568 | 28 % | 2,121 | 106 % |
| 20,000 | 5,875 | 29 % | 14,723 | 74 % |
| 250,000 | 55,047 | 22 % | **409,130** | **164 %** |

So at the PC's 250,000-node match budget the search can consume **over twice the budget** (659,130
nodes for a 250,000 request, position 7 of the real-game set, depth 17).

## How sure
High for (1) and (2): the Rule-1 control (`CONTROL_SOFTNODES.md`) shows the same comparison functions
catch a 1-node difference, a 1-depth difference, a score difference, a bestmove difference, and a
mid-depth stop, while correctly not flagging identical runs. The zeros are therefore measurements.
High for (3) as a measurement; see "not sure" for what it does *not* say about strength.

`info string softnodes nodes X` reported the same number as the last info line's `nodes` in every one
of the 63 runs, so the engine's own report of what it did is consistent with its output.

## Settings and build
PC r15 build, sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`, built with
`-DFORGE_MATE_ALPHA_GUARD=1`. **PC20** applied in full (Threads 1, Hash 16, the 14 S14 settings, then
CuckooRep true / HistRework 2 / TtPruneV2 true / CorrHistV2 true / MateAlphaGuard true /
OwnBook false), with `isready`/`readyok` after every `setoption` and every option name checked against
the exe's own `uci` list.

## Table of steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Harness: fresh PC20 process per search, read to bestmove, never close stdin mid-search | done | `softnodes.py` | 63 runs |
| Determinism: every case run twice in separate processes | done | `out/`, `out2/`, `out_real/` JSON | 63/63 identical |
| Cross-invocation determinism | done | comparison of `out/` and `out2/` | 6/6 shared cases identical |
| Finished-depth test via `go depth <reached>` | done | same JSON (`finished_depth_matches_go_depth`) | 63/63 true |
| Rule-1 control | done | `control_softnodes.py`, `CONTROL_SOFTNODES.md` | 5 plants all flagged, 2 identities not flagged |
| Real-game positions (first 12 of G) | done | `realgame12.fens`, `out_real/` | 36 runs |
| Hand-built positions incl. startpos | done | `pos3.fens`, `out/`, `out2/` | 27 runs |
| Strength consequence of the overshoot | not done | — | that is a match question, not a perft question |

## Findings
- S-F6: `go softnodes N` on the PC build under PC20 at Threads 1 is **fully deterministic**
  (63/63 identical across separate fresh processes, including depth, nodes, score and bestmove) and
  **always stops at a finished depth** (63/63, proven by re-searching with `go depth` to the same
  node count). Reproduce: `cd forge-combo29/swarm/13/job5 && python3 softnodes.py ~/b/pc/forge
  realgame12.fens /tmp/sn 2000,20000,250000`.
- S-F7: the softnodes budget is exceeded substantially and unboundedly in proportion: median 22–29 %
  past N, but worst observed **409,130 nodes past a 250,000 budget (164 %, 659,130 total)** on a real
  game position. So a match that budgets 250,000 nodes can spend more than twice that on one move.
  Reproduce with the same command; read `overshoot`/`overshoot_pct` in `/tmp/sn/softnodes.json`.

## Suspicions, not proven
- **That the overshoot costs strength.** A longer search at a fixed depth is normally *better*, so the
  overshoot is not obviously harmful — the cost is time, not quality. Whether the PC's 6 s + 0.06 s
  clock interacts badly with a 2x-node move is a clock question I have not measured. I am recording
  this as a suspicion, not a defect.
- The overshoot's size looks tied to how expensive the depth being finished is, which is why sparse
  endgame-ish positions (position 7) overshoot most. I have not proven that relation.

## What I did NOT do
- No clock measurements (`go wtime/btime` with the PC's 6 s + 0.06 s): that is another area's job and
  it needs the Threads-1 discipline plus more time than the run window.
- No strength matches.
- `go nodes` at the PC's three budgets was not re-measured here beyond what job 4 and the earlier
  work covered; softnodes was the question asked.

## What I am NOT sure about
- 63 runs over 15 distinct (position, N) cases is enough to establish determinism convincingly
  (a single mismatch would have shown) but it is not a proof for every position. Non-determinism at
  Threads 1 would have to come from state I am not varying; I kept PC20, Hash 16 and a fresh process.
- The real-game set is 12 positions from G, which are middlegame positions from engine games, not the
  owner's actual match games. The magnitudes may differ on his positions.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
CONTROL_SOFTNODES.md
control_softnodes.py
out
out2
out_real
out_real.log
pos3.fens
realgame12.fens
realstat.txt
REPORT_job5.md
softnodes.py
stamps.txt
```
