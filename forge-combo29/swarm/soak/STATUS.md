# STATUS — soak seat (single-process memory stability)

Branch `swarm/soak`, base `6b98f217`. Deliverables in `forge-combo29/swarm/soak/`.

## Sealed verdict

**Soak-clean. No leak in any of the six measurements. One prediction failed and it is reported
as a failure.**

| # | question | answer |
|---|---|---|
| 1 | RSS over 5,000 depth-12 searches, one process | **flat at 42.1 MB**, slope **0.000 MB / 1,000 searches**, +1.5 MB total (all in search 1) |
| 2 | RSS tracks `Hash` at 16/64/256/1024 | **exact to 0.1 %**; non-table memory constant at **10.1 MB** |
| 2b | the "~105 MB alternate table" | it is **105.9 ms**, a latency figure. The table is **the same size as the main table** and **is freed** |
| 3 | 5,000 × `ucinewgame` / `Clear Hash` | **0 kB RSS delta** for both; equal cost, both are a full table memset (86 ms at Hash 1024) |
| 4 | 1,000 MultiPV-4 at Hash 64 | peak **145.1 MB ± 0.2 MB** across all 1,000; settled by search 250; **+0 kB** after |
| 5 | `ulimit -v` just above working set | **REPLICATION** of prior work: no middle band, 0 of 18 survivors differ, cliff = Hash + 44 MB. The 59 MB boundary was re-tested at 1 MB resolution |
| 5b | does the cliff move with MultiPV? | **yes — 152 vs 108 at Hash 64, 598 vs 300 at Hash 256 — but my `2·Hash+44` prediction FAILED both ways** |
| 5c | is the alternate table really full-size? | **yes, on a slope**: peak RSS grows **1.000 MB per MB of Hash at MPV 1** and **2.001 at MPV 2** (predicted 1.0 / 2.0) |
| 5d | the resize transient | **old + new, exactly**: 16→256 peaks at **281.9 MB**, `256→256` at **521.9 MB**, excess +9.9 MB in every growth case |
| 6 | ASan+UBSan `detect_leaks=1` | **0 leaks, 0 UB**; detector proven (0 / 0 / 4 lines on clean / untriggered / triggered) |

## Honesty pins on the measured binary

312,866 / 862,329 / 3,024,920 / perft 5 4,865,609 — all four, on both the release and the
ASan build.

## The headline is the failure

I predicted the `ulimit -v` cliff at MultiPV 2 would be `2 × Hash + 44` MB. It is **152 MB**
where I said 168–176, and **598 MB** where I said 548–564 — one low, one high, which no single
linear model can produce. **The cliff was the wrong instrument**: it measures `peak resident +
the address space glibc had reserved at that instant`, and the reservation is 10.1 MB at
Hash 64 but 70.5 MB at Hash 256, decided by the cap being probed.

The sizing claim it was meant to test survives, measured instead as a **slope**: 1.000 / 2.001
/ 2.000 MB of peak RSS per MB of Hash at MultiPV 1 / 2 / 4, against 1.0 / 2.0 / 2.0 predicted.
**A slope asks how memory scales; a cliff asks where a threshold sits, and that threshold is
not the engine's.**

## Files

- `FINDINGS.md` — the curves, verdict, the failed prediction, and the limits.
- `PREDICTION.md` — committed before measurement 1; **9 of 9 held**.
- `PREDICTION2.md` — committed before the MultiPV measurements; **6 of 7 held, P7 killed**.
- `evidence/` — raw CSV/JSON/log per arm plus `meta/` (build hashes, `nm` sanitizer counts,
  LSan control).
- `scripts/` — driver, one harness per arm, `analyze.py` (every report number, asserted row
  counts, cwd-independent), `check_consistency.py` (**169 checks**, planted-fault tested).

## Corrections I made to my own instruments (all recorded in FINDINGS.md)

1. First `ulimit` sweep reported 13 of 15 caps "not identical" — the key included `nps`, a
   timing field. Re-keyed to `(bestmove, score, nodes)`: 0 of 18 differ.
2. First sanitizer proof used `printf |` — the EOF-fabrication trap, which returned
   `bestmove a2a3` with no `info depth` lines as though it were an answer.
3. First sanitizer proof waited for an in-band stdout line after an ASan abort: a wait that
   can only time out.
4. `check_consistency.py` had `if False else 43116`, comparing two literals — a check that
   could not fail. Found by its own selftest.
5. That checker then passed **four of five planted table-cell faults**, because it compared
   prose only. The two central tables are now real markdown tables and every cell is checked.
6. `soak2`'s 2 ms sampler under-reported the resize transient by an order of magnitude
   (23.7 MB vs 281.9 MB). **A polling sampler is the wrong instrument for a transient;
   `VmHWM` is.**
7. An MPV-4 answer check compared against a **MultiPV-2** reference and reported 6 of 6 rows
   differing — the harness comparing two different searches. Re-keyed per configuration:
   0 of 6 differ in all six cells.

## Next, if this continues

- `Threads 8` resident memory per worker (unmeasured; every arm is Threads 1).
- Confirm the §5b arena mechanism directly by sweeping `MALLOC_ARENA_MAX`.
- A run longer than 5 minutes of engine time, if "days of uptime" is to be claimed directly
  rather than inferred from a zero slope.
