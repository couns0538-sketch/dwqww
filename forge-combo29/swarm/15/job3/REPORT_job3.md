# REPORT job 3 — seat 15, area 5 (checkmated and stalemated roots)

**What was asked.** 10 checkmated and 10 stalemated root positions, each searched with
`go depth 5`, `go nodes 100` and `go movetime 50` (60 searches), recording the exact answer
lines, under ASan + UBSan.

**The answer.** All 60 searches answer `bestmove 0000`, exit 0, and produce **no sanitizer
line**. But every single one prints a full run of `info depth 1..N` lines with
`score cp 0` / `score mate 0` and `nodes 0` before that `bestmove`, and with a node- or
time-limited `go` it iterates all the way to depth 64 instead of stopping at once. That is
wasted work and it is a wrong score type (`mate 0` is not a legal UCI mate score).

**How sure.** High for the counts: one committed script over the committed transcripts, and the
sanitizer claim carries both proofs the brief demands (see below). The depth-64 walk is visible
in the pasted raw files and reproduces on the release build as well.

## Honesty numbers

Release build used for job 1 and job 2: `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
bench 11/13/16 and perft 5 all exact (`HONESTY.txt`).

ASan+UBSan build used here: see `evidence/asan/meta_asan.txt` for its own sha256 and `nm -C`
counts. Sanitizer proofs in `evidence/sanitizer_proof.txt`:

- proof 1: `nm -C <exe> | grep -c __asan_` = 35 and `__ubsan_` = 15 for the build that was run;
- proof 2: a scratch copy with **one planted fault** behind `go depth 64` (a signed overflow in
  `src/uci.cpp`), built the same way and run through **the same runner**, which counted its
  `runtime error: signed integer overflow` line. The runner therefore does see sanitizer lines,
  so "0 lines" on the real build means something.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 10 checkmated roots | done | `sets/mate10.fens`, `gen_terminal.log` | every FEN verified `is_checkmate()` by python-chess |
| 10 stalemated roots | done | `sets/stale10.fens`, `gen_terminal.log` | every FEN verified `is_stalemate()` by python-chess |
| ASan+UBSan build | done | `evidence/asan/meta_asan.txt` | 35 `__asan_`, 15 `__ubsan_` symbols |
| planted fault counted by same runner | done | `evidence/sanitizer_proof.txt`, `plant_diff.txt` | 1 of 1 runs reported; `uci.cpp:549` overflow line |
| 60 searches | done | `evidence/asan/asan.jsonl`, `evidence/asan/asan_*_*.txt` | 60 records |
| `bestmove` check | done | `analyze_terminal.txt` | 60 / 60 exactly `bestmove 0000`, 0 other values |
| sanitizer lines | done | `evidence/asan/asan.jsonl` | 0 runs of 60 |
| exit codes | done | `analyze_terminal.txt` | 0 non-zero of 60 |
| prediction P2 (no info line) | done — **refuted** | `analyze_terminal.txt` | 60 of 60 runs print info lines |
| wall time of movetime 50 | done | `analyze_terminal.txt` | min 60, median 64, max 91 ms; none over 500 |

## Prediction, as committed before measuring

| # | prediction | verdict |
|---|---|---|
| P1 | every answer exactly `bestmove 0000` | **HELD** (60/60) |
| P2 | no info line printed at all | **REFUTED** (60/60 print `info depth …` lines) |
| P3 | 0 sanitizer lines | **HELD** (0 of 60) |
| P4 | movetime 50 never over 500 ms | **HELD** (max 91 ms) |
| P5 | exit code 0 for all 60 | **HELD** |

## Findings

### 15-F5 — a terminal root is searched to depth 64 instead of answered at once (NEW)

```bash
cd forge-combo29/swarm/15/job3
grep -c "^info depth" evidence/asan/asan_000_nodes100.txt     # 64
grep -c "^info depth" evidence/asan/asan_000_depth5.txt       # 5
```

Raw line, from `evidence/asan/asan_000_depth5.txt` (FEN `7K/8/7q/8/8/8/bk4r1/8 w`, white mated):

```
info depth 5 seldepth 5 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv
bestmove 0000
```

Two separate defects in one behaviour:

1. **The score type is wrong.** At a checkmated root the score is printed as `score mate 0`.
   UCI reserves `mate 0` for nothing; a mate **score** of 0 with the side to move checkmated
   should not be emitted as a mate score at all. On a stalemated root the same position prints
   `score cp 0`, so the two terminal cases are reported inconsistently.
2. **The iteration is not terminated.** With `go nodes 100`, `go movetime 50` and `go depth 64`
   the engine emits 64 info lines with `nodes 0` and `time 0..4`, i.e. it walks the depth ladder
   to the clamp maximum although there is no move to search. With `go depth D` it emits exactly
   D lines, so the ladder is driven by the limit, not by anything about the position.

Reproduces on the release build as well, so it is not a sanitizer artefact:

```
depth 5      info_lines=5    last: info depth 5 seldepth 5 score cp 0 nodes 0 ... pv   bestmove 0000
nodes 100    info_lines=64   last: info depth 64 seldepth 64 score cp 0 nodes 0 ... pv  bestmove 0000
movetime 50  info_lines=64   last: info depth 64 seldepth 64 score cp 0 nodes 0 ... pv  bestmove 0000
```

**Impact.** Small in time (the whole walk is ~20-30 ms wall) but it is 64 spurious lines on every
terminal position, and any GUI or test harness that decides "the engine searched" by the presence
of an `info depth` line will mis-read a dead position as a searched one — which is exactly the trap
that cost 80 rows in my own job 2 analysis (`15-F4`).

## Suspicions, not proven

- The `nodes 0` with a rising `seldepth` in the same line suggests the seldepth counter is being
  incremented per iteration without any node being visited; I did not read the code to confirm.
- `score mate 0` may be the engine's internal "mated now" encoding leaking into the UCI writer
  without a special case. Not established.

## What I did NOT do

- Did not read the search or UCI source to find the cause (area 7's job).
- Did not test positions where a side is mated *in one* (i.e. non-terminal roots with mate 0) —
  only true terminal roots.
- Did not run TSan on this job; area 4 owns threads.
- Did not measure how the 64-line walk behaves at Threads > 1.

## What I am NOT sure about

- Whether a GUIs cares about the 64 lines in practice; I only assert the files show it.
- Whether `mate 0` is intended as "no mate" for some downstream consumer. I state only that it is
  not a legal UCI mate score and that it is inconsistent with the stalemate case printing cp 0.

## Times

`stamps.txt` — every line is a pasted `date -u`.

## Last command's output

```
$ ls
analyze_terminal.py
analyze_terminal.txt
evidence
gen_terminal.log
gen_terminal.py
plant
plant_diff.txt
prediction.txt
REPORT_job3.md
run_asan.log
sets
stamps.txt
terminalrun.py
```

`evidence/asan/` holds the 60 transcripts + `asan.jsonl` + `meta_asan.txt`;
`evidence/plant/` the planted-fault run; `plant/` the scratch source copy (never committed as engine source).
