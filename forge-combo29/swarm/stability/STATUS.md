# STATUS — stability seat

**State: complete.** Five questions asked, five answered with numbers. One defect found in
my own instrument and fixed (recorded in FINDINGS).

## The question, answered

A fixed-depth score **is** usable as a training label at `Threads 1` — 1 distinct value
across 30 fresh processes on each of 4 positions, and 0 of 200 corpus positions disagreeing
on score, depth or bestmove in a fresh-process pair. It is **not** usable at `Threads 4`
(191 of 200 positions disagree, 189 on score alone). It is **not** usable from a reused
process without `ucinewgame` (197 of 200 wrong against fresh, with 433 cp worst-case).

## Gate

All four honesty pins matched before recording (`evidence/pins.txt`):
312,866 / 862,329 / 3,024,920 / perft 5 4,865,609.

## Conditions on every row

Base `6b98f217`, g++ 13.3.0 (`/usr/bin/g++`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`),
`-DFORGE_MARCH=x86-64-v4`, Release, 4-core Xeon.
`go depth 12` (one row at 16), `Hash 32` (one corpus arm at `Hash 1`), `MultiPV 1`,
`OwnBook false`, fresh process per run unless the row says "batch".
Engine `id name Chess Engine Forge 6.4.24 candidate`, binary sha256 `e06310ec…`.

## Measurements

| id | what | script | evidence |
|---|---|---|---|
| M1 | 30 fresh processes, 1 position, T1 depth 12 (+depth 16) | `meas_repeat.py` | `m1_t1_*.json` |
| M2 | 30 fresh processes, 4 positions, T4 depth 12 | `meas_repeat.py` | `m2_t4_*.json` |
| M3 | 200 corpus positions × 2, fresh, T1 / T4 / T1-Hash1 | `corpus_twice.py` | `m3_corpus_T1.json`, `m3b_corpus_T4.json`, `m3c_corpus_T1_hash1.json` |
| M4 | ABA order test, batch | `order_batch.py` | `m4_order.json` |
| M4b | order test ± `ucinewgame` | `order_reset.py` | `m4b_order_reset.json` |
| M5 | reset arms vs fresh reference | `batch_resets.py` | `m5_resets.json` |
| M6 | book RNG, `go depth` book reachability | `book_rng.py` | `book_rng.json` |
| M7 | drawn root + mate score, 30 fresh each, T1 and T4 | inline in FINDINGS | `m7_bail_mate.json` |
| — | 9 fault proofs | `fault_proof.py` | `fault_proof.txt`, `fault_proof.json` |
| — | 4 honesty pins | `pins_probe.py` | `pins.txt` |

Regenerate every table in FINDINGS with `python3 scripts/tables.py`.

## Controls, and what each one protects

- **A vs A2** (same batch order, fresh process) — 0 of 200. Without it, A vs B cannot be
  distinguished from noise.
- **No-reset arm inside `order_reset.py`** — 194 of 200. Proves that script can detect a
  leak, so its `ucinewgame` zero is a real zero.
- **F3** (T4 must show variation) — proves the distinct-score instrument is not blind, so
  the T1 single value is a measurement.
- **F9** (bail detector silent on a searching position) — the negative half that stops a
  `True`-hardwired detector from passing F8.
- **`rederive.py`** — recomputes every headline count from the per-run rows instead of the
  summary counters written in the same pass. All match, so no figure agrees with itself.
- **Clock control in M6** (20 of 20 book) — proves the `0 of 20` on `go depth` is a real
  zero, not a dead check.
- **`Book Variety 0` arm** — proves the book variation is the RNG, so `OwnBook false` is
  the right pin.

## Known limits (full list in FINDINGS)

One machine. No endgames below 12 pieces. No `go nodes`. No depth > 16. No order test at
T4. The corpus is self-play, and it contains 0 drawn roots, so bail frequency in a real
corpus is unknown — only that stability checks cannot reveal one.

## Nothing shipped to the engine

No source change, no patch, no binary. Only files under `forge-combo29/swarm/stability/`.
