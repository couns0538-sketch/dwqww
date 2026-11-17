# STATUS — soak seat (single-process memory stability)

Branch `swarm/soak`, base `6b98f217`. Deliverables in `forge-combo29/swarm/soak/`.

## Sealed verdict

**Soak-clean. No leak in any of the six measurements.**

| # | question | answer |
|---|---|---|
| 1 | RSS over 5,000 depth-12 searches, one process | **flat at 42.1 MB**, slope **0.000 MB / 1,000 searches**, +1.5 MB total (all in search 1) |
| 2 | RSS tracks `Hash` at 16/64/256/1024 | **exact to 0.1 %**; non-table memory constant at **10.1 MB** |
| 2b | the "~105 MB alternate table" | it is **105.9 ms**, a latency figure. The table is **256 MB** at Hash 256 and **is freed** (+3.6 MB after `bestmove`) |
| 3 | 5,000 × `ucinewgame` / `Clear Hash` | **0 kB RSS delta** for both; equal cost (both are a full table memset) |
| 4 | 1,000 MultiPV-4 at Hash 64 | peak **145.1 MB ± 0.2 MB** across all 1,000; settled value reached by search 250; **+0 kB** after |
| 5 | `ulimit -v` just above working set | **no middle band**: 0 of 18 surviving caps changed any answer, 5 caps died with SIGABRT/bad_alloc. Cliff = **Hash + 44 MB** |
| 6 | ASan+UBSan `detect_leaks=1` | **0 leaks, 0 UB**; detector proven (0 / 0 / 4 lines on clean / untriggered / triggered) |

## Honesty pins on the measured binary

312,866 / 862,329 / 3,024,920 / perft 5 4,865,609 — all four reproduced, on both the release
and the ASan build.

## Files

- `FINDINGS.md` — the full curve, verdict and limits.
- `PREDICTION.md` — committed before the first measurement; **all nine predictions HELD**.
- `evidence/` — raw CSV/JSON/log per arm, plus `meta/` (build hashes, `nm` sanitizer counts,
  LSan control).
- `scripts/` — the driver, one harness per arm, `analyze.py` (every report number, asserted
  row counts, cwd-independent), `check_consistency.py` (73 checks, selftest proven).

## Predictions killed

None. P3 was scoped to RSS only, which was correct: the two clear paths are equal in both
RSS and time, and both are dominated by a full-table memset.

## Corrections I made to my own instruments (recorded in FINDINGS.md)

1. First `ulimit` sweep reported 13 of 15 caps "not identical" — the answer key included
   `nps`, a timing field. Re-keyed to `(bestmove, score, nodes)`: 0 of 18 differ.
2. First sanitizer proof drove the engine through `printf |` — the EOF-fabrication trap,
   which reported `bestmove a2a3` and no `info depth` lines as a real answer.
3. First sanitizer proof waited for an in-band stdout line after an ASan abort, i.e. a wait
   that can only time out.
4. `check_consistency.py` had a `if False else 43116` comparison of two literals — a check
   that could not fail. Found by its own selftest, which is the only reason it was found.
5. Three typed figures in the first FINDINGS draft were wrong or estimated (engine-op count,
   MPV-4 memset traffic, `ucinewgame` cost at Hash 1024). The last is now **measured: 86 ms**.

## Next, if this continues

- `Threads 8` resident memory per worker (unmeasured; every arm is Threads 1).
- A run longer than 5 minutes of engine time, if "days of uptime" is to be claimed directly
  rather than inferred from a zero slope.
- Optional one-line patch to `TranspositionTable::resize` to early-return when the new size
  equals the current one, removing the 2× transient. Owner decision, not a leak.
