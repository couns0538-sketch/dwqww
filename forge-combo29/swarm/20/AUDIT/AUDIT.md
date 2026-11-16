# AUDIT — seat 20's harnesses against 19-F12 (fabricated bestmove) and against silent-parse verdicts

Two broadcasts, two audits. Nothing here changes a number; it shows whether my numbers *could* have been wrong.

## A. 19-F12 — fabricated `bestmove` when `quit` / EOF arrives mid-search

Method: I classified every script of mine that drives the engine by whether it reads stdout to `bestmove` before
writing `quit`. Raw: `harness_audit.txt`. Replacement driver: `hardened.py`.

| class | scripts |
|---|---|
| VALID (wait for `bestmove`, then quit) | `job1/check_s01f5.py`, `job3/drive.py`, `job3/clockcut.py`, `job5/check_s02f2.py`, `job6/check_s12f1.py`, `job8/check_s02f1.sh` (no search), `job9/check_s06f1b.py`, `job10/check_s28f1.py`, `job11/check_s05f3.py`, `job12/check_mate_pv*.py`, `job13/bisect_s14.py`, `job13/pairwise_s14.py`, `job14/lmpbase_ladder.py`, `job15/withdraw_s21.py`, `job16/*.py`, `job2/myfuzz.py` |
| INVALID, already discarded before the broadcast | `job3/out/fallback.out.txt` (first run) and `job2/quitcut.sh` |
| deliberately measures 19-F12, claims nothing | `job2/quitcut.sh` — its "quit-immediately" column *is* the fabricated answer; kept as a demonstration, never a finding |

Re-verified on `hardened.py` after the broadcast: startpos `go depth 12` → **`e2e4`, cp 30, 56,720 nodes, 12 depth
lines** — matching seat 19's real number, not the fabricated `a2a3`. The same driver reproduces the S-F19 board's
`mate -7` at 15,465 nodes, 14-ply PV.

## B. silent-parse verdicts (seat 19's `clock_plan` NaN case)

Method: a FAKE engine that answers `uci`/`uciok`/`readyok` correctly and then prints **nothing at all** for every
`go` and every `eval` (`fake_engine.py`). Each of my parsing checkers was run against it. Raw: `parse_audit.txt`.

| checker | behaviour on a silent engine |
|---|---|
| `job9/check_s06f1b.py` | HUNG — refuses to invent an answer |
| `job11/check_s05f3.py` | HUNG |
| `job12/check_mate_pv_s14.py` | HUNG |
| `job13/bisect_s14.py` | HUNG |
| `job10/check_s28f1.py` | HUNG |
| `job14/lmpbase_ladder.py` | HUNG |
| `job6/check_s12f1.py` | HUNG (verified separately, 90 s) |

**None of them printed a CONFIRMS/EQUAL/consistent verdict on a silent engine**, so none has the silent-parse defect.
Two weaknesses remain, and I state them rather than hide them:
1. they HANG instead of failing loudly — a better design asserts the parsed line exists (my newer scripts do:
   `job14` and `job16` return `{"verdict": "no score"}` / raise, and `prove_mate_line.py` carries
   `assert alllegal and rb.is_checkmate()`);
2. a hang is only safe because a human/agent notices it; a CI run would just time out.

## C. What this audit does NOT cover
- It does not re-run the checks' measurements; it shows they cannot produce a verdict from nothing.
- `job2/myfuzz.py`'s legality classifier pairs bestmoves with `go` boards by COUNT, and it is guarded: if the
  counts differ it records `unpaired` instead of judging (added during that job after I saw 9 false illegals).
- My S-F21 was withdrawn for a *related but different* reason (a mate line that was not forced) — see
  `job15/WITHDRAWN_s21.md`. The pattern is the same: a value that nothing verified reached a finding.
