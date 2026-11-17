# ADDENDUM — harness integrity corrections to REPORT_job1 / REPORT_job3 / REPORT_job4

Written after two notices from the coordinator: seat 19's 19-F12 (a piped `quit` during a
search yields a fabricated `bestmove`) and seat 19's measurement-integrity warning (a check
must assert the line it parses was found). This file says exactly what was re-run, what
changed, and what did not.

## 1. Which of my harnesses were exposed to 19-F12

| harness | form it used | exposed? | why |
|---|---|---|---|
| `job1/run_fen.py` | `go depth 2`, read to `bestmove`, then `ucinewgame` | **no** | never closed stdin mid-search; one process per 500 FENs, `quit` never sent after a `go` |
| `job1/known.py`, `known8902.py`, `f1_8902.py`, `job3/fullmove0.py` | `go perft N` then `quit` | **no** | `go perft` is synchronous: it prints `nodes N` before returning, and `perft` is not the search loop |
| `job1/control.py`, `sticky.py`, `sticky_gui.py` | `go depth N` + `quit` in one pipe | **YES** | exactly the pipelined form 19-F12 invalidates |
| `job1/sanproof.py`, `fake_engines.py` | via `run_fen.py` | **no** | same reason as `run_fen.py` |
| `job2/check_30f6.py` | `go perft 1` + `quit` | **no** | synchronous perft |
| `job3/extreme.py` | `go depth 4` + `quit` in one pipe | **YES** | pipelined |
| `job3/accept_all.py` | `position` + `isready` only | **no** | no search at all |
| `job4/long_moves.py` | `go perft 1/2` + `quit` | **no** | synchronous perft |

## 2. What was re-run and what changed

All re-runs use the new driver `job6/safe_engine.py`, which (a) reads stdout to `bestmove`
(or to `nodes` for perft) before the next command, (b) raises rather than sending a command
while a search is outstanding, and (c) never closes stdin mid-search.

| measurement | old harness | re-run result | changed? |
|---|---|---|---|
| 20,000 mutated FENs (REPORT_job1 counts) | already safe | `job6/out6/asan6_summary.txt`: refused 18,775 / accepted 1,225 / py-valid 1,186 / py-invalid 39 / crash 0 / hang 0 / san 0 / illegal 0 | **no** — per-FEN verdicts identical on all 20,000 (`diff` empty). One difference: the old run recorded `illegal_best 1`, which was my classifier not accepting `bestmove 0000` in a checkmated position; the corrected classifier counts it legal (mate with no moves), so it is 0. The old report already said that move was not a fault. |
| 21-F2 GUI trace | pipelined | `job6/out/summary.md` (f2_safe): refused → both answers `g8e7`; accepted control → `d2d4` | **the specific move changed** (was `a7a6`); the CLAIM is unchanged and now has a control: with the FEN refused, the 2nd answer is a move of the old game (Black's move, legal only there); with the FEN accepted, it is a move of the new game. |
| 21-F9 halfmove ≥ 100 | pipelined | `job6/out/summary.md` (reverify): `go depth 8` → `a2a3`, `score cp 0 nodes 0` | **no** — the 0-node answer is real, not fabricated (it appears under the safe driver too). |
| 21-F8 fullmove 0, 21-C2 prefixes | perft-based, already safe | `job6/out/summary.md` (reverify_all): refused + stale 20 vs control 15; prefixes 20/400, 26/726, 22/100 | **no** |

## 3. Measurement-integrity audit of 21-C1

`job6/audit_c1.py` re-derives 21-C1 with a parser that **raises** when the `nodes N` line it
parses is absent, and with two plants:

| plant | what it proves | outcome |
|---|---|---|
| PLANT-empty (answer with no `nodes` line at all) | an empty result cannot pass as a measurement | correctly rejected: "NO `nodes N` line ... the check measured nothing" |
| PLANT-wrong (real 30 compared against an impossible 1030) | an unequal comparison cannot report success | correctly reported as a mismatch |

21-C1 still stands: `ucinewgame` before the position → 30; position then `ucinewgame` → 20;
second control position → 28; startpos → 20. Verdict: CONFIRMS 30-F6, with the parser proved
non-vacuous.

## 4. Corrections to my own records

- `REPORT_job3.md`'s 21-F9 row is **unchanged** (re-verified).
- `REPORT_job3.md`'s 21-F8 row is **unchanged** (re-verified).
- `REPORT_job1.md`'s counts are **unchanged**; its "0 genuinely illegal bestmoves" line now
  rests on a corrected classifier and a safe-driver re-run.
- `REPORT_job4.md`'s prefix table is **unchanged** (re-verified).
- The `a7a6` figures quoted in `FINDINGS.md` for 21-F2 came from a pipelined harness and are
  replaced by `g8e7` / `d2d4` from the controlled safe-driver run.
