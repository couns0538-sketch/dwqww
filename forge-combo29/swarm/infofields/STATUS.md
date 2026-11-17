# STATUS — swarm/infofields (every `info` line field, one at a time)

**State: complete.** All nine fields and the `info string` variants are measured on the wire at
base `6b98f217`, four gate pins verified (312,866 / 862,329 / 3,024,920 / 4,865,609), and the
result is written up in `FINDINGS.md`.

## Verdicts

| field | verdict |
|---|---|
| `depth` | **NON-CONFORMANT** — bail (`depth 64`, 0 nodes) and abort revision (`depth 22` with the depth-21 score, proven on the wire) |
| `seldepth` | **NON-CONFORMANT on the bail**; ordering invariant **unfalsifiable** by construction (`max(seldepth_, depth)`) |
| `multipv` | **CONFORMANT** on searching paths; absent on book, degrades to `multipv 1` on a drawn root |
| `score` | **CONFORMANT** — side-to-move relative both ways, `mate ±N` and `mate 0` correct |
| `nodes` | **PARTLY NON-CONFORMANT** — exact vs the bench pin at Threads 1; falls across depth boundaries on 26% of transitions at MultiPV ≥ 2; two totals under `softnodes` |
| `nps` | **CONFORMANT arithmetic** (28/28 exact); `0` is a sentinel at `time 0` |
| `hashfull` | **NON-CONFORMANT** — counts only the current generation, so a 23× warm table reads `hashfull 10`; reports the alternate worker's table under MultiPV |
| `time` | **NON-CONFORMANT on ponder** — counts from `go`, budget counts from `ponderhit`; proven by `time 375` while the budget clock is pinned at 0 |
| `pv` | **CONFORMANT** on searching paths — final `pv[0] == bestmove` 17/17, zero illegal pv moves |
| `info string` | two variants collide: `softnodes nodes N` duplicates a field name, `searchmoves` emits no depth line |

## Deliverables

- `FINDINGS.md` — the conformance table, then the evidence per field
- `scripts/` — driver (`uci.py`), fixtures, 18 probe scripts, `controls.py` (planted-fault gates)
- `evidence/` — 21 JSON files, each stamped with build, base commit, threads, hash and pins

## Withdrawn / corrected during the work

1. **A first `nodes`-vs-bench comparison (343,222) was withdrawn.** It ran all eight bench FENs in
   one process with a reused table, while `bench` builds a fresh `Searcher(16)` per position. With a
   fresh process per FEN the sum is exactly 312,866. The 343,222 reading is kept as the *control*
   that proves the setup matters.
2. **A first abort-depth design was discarded.** It reset `Hash` between runs and compared ladders
   to a cold reference; the `Hash` reset clears the table but leaves histories warm, so the A/A
   control failed. The claim in `FINDINGS.md` uses no cross-run comparison — it compares one run's
   depth-21 score against that same run's depth-22 line.
3. **A first ponder-`time` design was discarded.** Varying the ponder wait with the budget fixed
   cannot attribute the surplus, because the final `time` is stamped at the last completed
   iteration, not at the stop. Replaced by the during-ponder snapshot, which needs no racy
   arithmetic.
4. **One illegal fixture was caught and replaced** (`6k1/6Q1/6K1/… w` — the engine refused it and
   searched the previous position). Re-validated in python-chess and for a wire refusal.
5. **A `pv` claim was restated.** "Every line's `pv[0] == bestmove`" is false and is *not* a
   violation; iterative deepening changes the best move. Only the final line is contractual.

## Not done

- `seldepth` truth beyond ordering — no wire-observable discriminator exists.
- `TmNodeShare` / `TmFinishIteration` `info string` lines — flags default to false; forcing them
  would perturb the pins.
- `hashfull` at Hash 2048 with multi-threaded fill.
- `nodes` at Threads > 1 against an independent count (none exists on the wire).

## Reproduction

```
cmake ../forge-combo29 -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
      -DCMAKE_BUILD_TYPE=Release
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j4
FORGE_BIN=./forge python3 scripts/controls.py      # planted-fault gates first
FORGE_BIN=./forge python3 scripts/probe.py          # all ten baseline probes
```

Verify the four pins before recording anything. `bench N` must go in on stdin.
