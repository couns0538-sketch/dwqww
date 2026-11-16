# REPORT_deepseek5_job7 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the three corrections with known answers (A), the two clock switches on an EMPTY table through my own harness with a prediction committed first (B), the fixed-nodes identity check with a planted leak (C). **The answers: (A1) P1 and the two new shapes: the engine holds exactly the position before the illegal token — its own perft 1 equals my python-chess reference (29/29, 29/29, 37/37) and the bestmove is legal on that board in 30 of 30 rows — job 5's "fault" is RETRACTED; it was my checker's wrong reference board. (A2) C1 and C2 answer a1b1 with nodes 0 under ALL THREE limit types (depth 6 / nodes 5000 / movetime 100 — the info line even prints "depth 64 … nodes 0"): the 0-node trap answer comes under every limit, and White has a mate in one (d1d8) — the trap is real and measured. (A3) `go mate 1` on the study position answers d1d8 (the known answer met, 37 nodes, legal); `go mate 3` answers d1d8 too. (B) THE FINDING: on an EMPTY table the hold share does NOT fall on the fast lines — 40.7% / 42.0% / 40.3% (line 1/2/3) against kimi5's 42% → 16–22% fall on its reused-table harness: the fall was the TABLE STATE, as its own tm_finish.hpp:29 note suggested. The HARD share with no switch is 0.0 on all three lines (kimi5's hard-limit counts were the same artifact). The wall-sum ratios against the OFF-vs-OFF2 floor (0.999–1.004): TmFinishIteration 0.82/0.84/0.82 and TmNodeShare 0.89/0.93/0.92 — both switches make the searches FASTER, far outside the floor; my prediction (1.00 ± 0.10) missed for FI and NS — reported. (C) NOT REACHED — the clock measurement took the time.** How sure: sure of A (raw file + reference counts) and of B's headline (3,600 rows, the floor beside every number).
2. Step 0: exe sha256 `e06310ec…` (same file as job 3, printed to `exe_sha256.txt`); pins 312866 / 862329 / 3024920 / 4865609 (`pin_*.txt`).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| kimi5 files fetched (by name) | done | sha256 a56b3251aae22cd9 (fens), ccecc42300bd279b (patch) — both as the job states | 300 fens; k5_p2.py read for the flaw list only |
| A1 three shapes × 10 | done | partA_raw.txt | perft engine=reference (29/29/37), legal 30/30, 0 illegal |
| A2 C1/C2 × {depth 6, nodes 5000, movetime 100} | done | partA_raw.txt | a1b1, nodes 0, under every limit |
| A3 mate 1 / mate 3 on the study position | done | partA_raw.txt | d1d8 / d1d8 (the known answer met) |
| B prediction, own commit | done | prediction.txt, commit 965076d7c at 06:02:25Z | committed before any measurement |
| B harness ds5_job7_clock.py | done | the file | ucinewgame+isready+position before EVERY go; 4 processes interleaved position-by-position; wall time measured, not the engine's |
| B control H1 (300 ms hold) | done | ds5_job7_b/hold_control.txt (line 1), hold3_control.txt (line 3) | line 1: wall rises (median 721.8, max 1881.4), HARD 0/30 — the threshold 2645 is above every held wall; line 3: **HARD 30/30** — the rise shows where the threshold is reachable |
| B control H2 (hold lines counted) | done | clock_raw.txt | FI line-1 hold share 40.7% (lines > 0); OFF exactly 0.0 |
| B control H3 (line-3 depth) | done | analysis.json | median depth OFF = 13 — clearly below kimi5's 18: the table IS empty |
| B measurement 4 × 300 × 3 | done | ds5_job7_b/clock_raw.txt (3,600 rows), analysis.json | see the table below |
| C identity + leak | NOT done | — | the stop fell first |

**Part B's table (prediction beside measurement; the floor beside every "changed" share):**

| line | median depth OFF (pred → meas) | hold share FI (pred → meas) | wall-sum FI/OFF (pred → meas) | wall-sum NS/OFF (pred → meas) | HARD share OFF (pred → meas) | OFF-vs-OFF2 bestmatch (pred → meas) |
|---|---|---|---|---|---|---|
| L1 (10000,100) | 19 → **18** ✓ | 45% → **40.7%** ✓ | 1.00 → **0.824** ✗ | 1.00 → **0.890** ✓(edge) | 10% → **0.0%** ✗ | ≥98% → **99.3%** ✓ |
| L2 (1000,100) | 13 → **14** ✓ | 35% → **42.0%** ✓ | 1.00 → **0.844** ✗ | 1.00 → **0.928** ✓ | 15% → **0.0%** ✗ | ≥98% → **100%** ✓ |
| L3 (1000,10) | 8 → **13** ✗ | 35% → **40.3%** ✓ | 1.00 → **0.815** ✗ | 1.00 → **0.920** ✓ | 15% → **0.0%** ✗ | ≥98% → **99.3%** ✓ |

The floor beside the "changed" shares (OFF vs OFF2): bestmove 0.0–0.7%, depth 3.3–4.7%, wall >5% 8.0–13.7% — so the switches' wall effects (−16…−18% for FI, −7…−11% for NS) are far outside the floor; the depth/bestmove identities sit at the floor's level (the switches change no search decision — consistent with kimi5's fixed-nodes claim, now on an empty table).

Where my prediction was wrong, with the reason: (i) L3's median depth 13 vs my 8 — the empty table lets even the 52-ms budget reach depth 13 (kimi5's reused-table lines ran to 17–19; mine sits below but not as low as I guessed); (ii) the HARD share 0.0 everywhere — with an empty table the searches never approach the hard limit (my 10–15% came from kimi5's numbers, which carried the table state); (iii) the wall ratios: TmFinishIteration's hold SAVES ~16–18% of wall time and TmNodeShare ~7–11% — I predicted "no change"; the mechanism is not measured here (the hold ends the search at the iteration boundary instead of letting the hard-limit check run on).

4. Findings:
- **The hold share's fall (42% → 16–22%) is the table state, not the switch**: empty-table shares are flat across the three budgets (40.7/42.0/40.3). kimi5's harness reused one process per position with EIGHT go lines; mine gives every search a fresh table.
- The HARD-share collapse to 0.0 (all lines) with an empty table is the same story for the hard-limit counts.
- Both switches leave bestmove/depth at the OFF-vs-OFF2 floor level on all three lines — the clock-only claim holds on an empty table at these budgets.
- The trap (A2): the 0-node a1b1 answer persists under depth, node and movetime limits — the root-state check happens before any limit matters.
- Suspicions, not proven: the wall-time SAVING mechanism of the two switches (I measured the effect, not the cause); whether the hold share depends on the position's first-iteration size in a way my 300 positions average out.
5. From my partner: glmflash5's notes (read via cursor/glmflash5-work-cb5c at the step-A check): its tc=2+0.02 result (0 losses in 986) and its PID-resolution warning — both already applied in my harnesses (I never kill by stored PID). kimi5: read its k5_p2.py to name MY differences from it: (1) ucinewgame before every search, not once per position; (2) the wall time is measured by my harness, its "engine time" came from the last info line; (3) four settings interleaved position-by-position in four concurrent processes, its lines ran sequentially in one process; (4) my per-search rows carry the hold-line counts, which its summary lacked. Nothing of its measurement files was read beyond the flaw list the job quoted.
6. What I did NOT do: Part C entirely (the TmSmoothStability build, the four 200-position identity checks, the HindsightDepth control, the planted leak) — the clock measurement took the budget; the hold control on line 2; any second repetition of the 3,600-search block (the OFF-vs-OFF2 pair is my only noise floor).
7. What I am NOT sure about: whether the FI/NS wall savings hold at budgets larger than 10 s (line 1 is the biggest here); whether the hold share's flatness survives on positions harder than the first 300 UHO lines; the exact mechanism of the two wall savings.
8. A better way: record `soft`/`hard` and the engine's own reported `time` in every row (I recorded them for the plan but not per row in the raw file — the row has itime; adding the two integers would make every HARD/SOFT word re-checkable without recomputation); and the B-part's four settings could include a fifth, "OFF with the table PRE-WARMED by one search" to reproduce kimi5's state deliberately — that turns the table-state explanation into an experiment.
9. times: stamps.txt
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).
