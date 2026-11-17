# STATUS — `setoption name Hash` resize audit

**State: COMPLETE.** Five verdicts measured, all evidence in `evidence/`, all
controls fired. Base commit `6b98f2170a3210e71beed04bbd2553972c253ed7`.

## Deliverables

| file | what |
|---|---|
| `FINDINGS.md` | the five verdicts, the RSS curve, the runner recommendation |
| `STATUS.md` | this file |
| `scripts/` | 17 scripts; each is rerunnable and prints its own controls |
| `evidence/` | every number, raw (`*.jsonl` per-position, `*.json` summaries) |

## Honesty pins — CONFIRMED

`scripts/pins.py`, `evidence/pins.json`:

```
net-on : 312866 862329 3024920 12389307 34048354    PASS (all 5)
net-off: 375354 907205 2448617 13573040 24506465    PASS (all 5)
perft5 : 4865609                                    PASS
```

Build: `-DCMAKE_CXX_COMPILER=/usr/bin/g++`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`,
CMake Release, `-march=x86-64-v4`. g++ 13.3.0. Re-checked at the end of the
20-cycle RSS run (`bench 11` = 312,866) so the binary did not drift mid-run.

## Verdicts

| # | question | verdict | strength |
|---|---|---|---|
| 1 | resize vs fresh process, 30 pos, both directions | **differs 30/30 both ways** — but the TABLE is emptied (0/30 warm on a probe whose both controls are validated) and the residue is **histories**. Proven sharp: in the window where Hash 16 and 64 are equivalent (0/24), a resize still differs **24/24**. | measured, replicated |
| 2 | resize mid-search | **`bestmove` arrives, and it is the searched one** — 30/30 equal to an explicit `stop`, 30/30 equal to the announced PV head, 0/30 "neither", 0 post-stop `info` lines | measured |
| 3 | RSS across 16→256→16 ×20 | **no leak** — one distinct RSS pair in 20 rounds (287,304 / 25,156 kB), HWM flat, pins intact at the end. **But the transient is one full table**: 7/7 at each of 16–256 MB, and it **doubles the memory requirement at Hash ≥128** (256 MB: 300 → **597 MB**, bisected to 1 MB, stable 3/3) | measured |
| 4 | resize before vs after `ucinewgame` | **no difference, 0/30 both orders**, with and without a warm start — `ucinewgame` masks it completely | measured |
| 5 | resize to the same value | **a table clear, identical to `Clear Hash` 30/30 in both sizes.** On an empty table it fires but is unobservable (12/12 identical, positive control 12/12) | measured, replicated |

## The two results that are new since the coordinator's table

1. **The decomposition.** A same-value resize is not "a wipe" — it is **cold
   table + warm histories**. Proven by the equivalence window: `fresh(64) vs
   fresh(16)` = 0/24, `[warm16 → resize 64] vs fresh(64)` = 24/24, and
   `[warm16 → resize 64 → ucinewgame] vs fresh(64)` = 0/24.
2. **The memory cliff moves.** At Hash 256 a same-value resize needs **597 MB**
   where a fresh process needs **300 MB** (1.99×) — with a third arm proving it is
   the resize and not the second search (no-resize control = 300 MB). This is
   the only finding that changes a *requirement* rather than a speed or an answer.

## Controls that fired (every null has its two proofs)

- `go wtime 0` table probe: warm arm 30/30, fresh arm 0/30 — the probe reads both.
- Equivalence window: E1 0/24 (replication 0/30) against E2 24/24 (29/30).
- Fresh-vs-fresh repeats: 0/30 at both sizes — comparisons are exact and stable.
- Empty-table null: cold arms 12/12 identical, **same re-send warm 12/12 differs**.
- ASan: nine blocks clean, **and** a canary binary proves the detector reports a
  real `AddressSanitizer` line. The first ASan probe passed for the wrong reason
  (an optimised-away overflow) and was replaced.
- Cliff: the fresh arm reproduces the audit's published 60 MB / 300 MB exactly.

## Contradiction check (the one a reader will look for)

`I2` reports **+157%** nodes and `J` reports **−7.8%** for the same-value resize.
Both are correct and both are in the document with their baselines named: I2 is
measured against the WARM arm (the wipe destroys working state), J against a FRESH
process (both cold; the resized arm keeps histories). See `FINDINGS.md` §Verdict 5.

## Not established (also carried into FINDINGS.md)

- Which history table carries the residue — needs a build that clears them one at a time.
- The 2× memory requirement is measured at 16/32/64/128/256 MB only; the delta is
  not a clean 2× below 128 MB and is reported as measured, not fitted.
- `Threads > 1` untested (every figure here is at the default of 1).
- The engine-side one-line fix (`if (mb == current && clusters_) return;`) is
  **recommended, not applied** — this is an audit.

## Reproduce

```bash
ENGINE=/path/to/forge
python3 scripts/pins.py $ENGINE evidence/pins.json
python3 scripts/exp_resize_state.py   --count 30  --out evidence/A.jsonl
python3 scripts/exp_table_probe.py    --count 30  --out evidence/B.jsonl
python3 scripts/exp_midsearch.py      --count 30  --out evidence/C.jsonl
python3 scripts/exp_rss.py            --rounds 20 --out evidence/D.json
python3 scripts/exp_small_window.py   --count 24  --nodes 50000 --out evidence/E.jsonl
python3 scripts/exp_samevalue.py      --out evidence/F.json
python3 scripts/exp_transient.py      --out evidence/H.json
python3 scripts/exp_runner_cost.py    --count 30  --out evidence/I.json
python3 scripts/exp_between_games.py  --count 30  --out evidence/J.json
python3 scripts/exp_cliff_bisect.py   --engine $ENGINE --out evidence/K2.json
python3 scripts/exp_empty_table.py    --count 12  --out evidence/L.json
python3 scripts/exp_asan.py           --engine <asan-build>/forge --out evidence/G.json
```
