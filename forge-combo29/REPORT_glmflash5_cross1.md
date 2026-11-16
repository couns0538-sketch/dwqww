# REPORT glmflash5 — CROSS 1 — deepseek5's job-30 HistExempt tree numbers, made again on my build

Branch `cursor/glmflash5-work-cb5c`. Build B8 = the PLAIN base tree 6b98f217 +
deepseek5's `tests_deepseek5_job30/HistExempt.patch.txt` (68 lines) applied with `-p1` FROM
INSIDE the `forge-combo29` folder of a COPY (the patch's own header says "repository root", but
its paths (`ds5_base_src/include/...` → `include/...` with -p1) resolve against the
forge-combo29 folder; with the repo-root layout `git apply` fails on all three files — one
more patch-apply-directory datum for kimi5's collection). B8 sha256
4525316efd7a337afe4edd76e9e43792e9f5493a23fa3709e0bb5ee443897e7a; HistPruneExempt in its uci
list (count 1). times: see stamps.txt.

## 1. What was asked (by the loop, not a job file), the answer, how sure

Cross-check of deepseek5's job-30 Part B over the SAME positions (kimi5's first200.fens, 200
openings, `go depth 12`, Threads 1, Hash 16, S14 on both runs): its mode-0 sum 9,500,069 and
mode-1 (Killer1 exempt) sum 9,459,684, plus its "changed best moves (O) 132".

Answer: **mode-0 = 9,500,069 — EXACT. mode-1 = 9,459,684 — EXACT (to the node, on my build, my
script). Its two tree sums are confirmed. Its "changed best moves 132" does NOT reproduce as
best moves: I count 6 changed best moves and 132 changed NODE COUNTS — the number 132 belongs
to the node column, so its table's column is very likely mislabeled** (its rows are right; the
name above the column is what failed — the same fault class its own job-18/29/30 notes keep
finding, this time in its own table).

How sure: the two sums are deterministic searches over the same 200 positions — exact match is
exact. The bestmove/node split is my measurement with the fixed capture (the bestmove line is
now taken from the engine's actual `bestmove` line, not from the last info line — my first
attempt made exactly that mistake and I reran it; the void attempt is noted in stamps).

## 2. The rows (`cross1_rows.txt`, one row per search: mode|position|nodes|bestmove)

| run | first-3 nodes | sum over 200 | deepseek5's number |
|-----|---------------|--------------|---------------------|
| mode0 (S14) | 41311, 24872, 28574 | 9,500,069 | 9,500,069 ✓ |
| mode1 (S14 + HistPruneExempt 1) | 41311, 24877, 38752 | 9,459,684 | 9,459,684 ✓ |

| comparison | my count | its table says |
|------------|----------|----------------|
| changed best moves (mode1 vs mode0) | **6** (positions 12, 81, 116, 132, 169, 193) | "132" |
| changed node counts | **132** | — |

Refusal lines: 0 in both runs. First differing positions (bestmove): 12, 81, 116, 132, 169, 193.

## 3. What this buys the session

- deepseek5's mode-1 tree claim (ratio 0.9957, interval straddling 1) now has TWO builds behind
  it (its machine and mine agree to the node).
- The "changed best moves" column of its job-30 table should be re-labeled (or re-measured with
  a bestmove-capturing script) before anyone uses it — 132 real changed best moves would have
  been a much stronger signal than the true 6.
- The patch applies with `-p1` from `forge-combo29/`, not from the repository root — its header
  should say so (third patch with an apply-directory surprise in this session).

## 4. What I did NOT do

- Modes 2/3/4 (both killers / + countermove / TT move) — not rerun (one cross-check number was
  the assignment; mode 1 was the headline).
- The G position set (its 353 game positions) — not on my branch; only O.
- Its bootstrap intervals — not recomputed (the sums are exact; the interval arithmetic is its
  own).

## 5. What I am NOT sure about

- Whether its "132" came from a node-count column (my 132 matches exactly — strong evidence) or
  from a different bestmove definition on its side (e.g. counting a move "changed" when the PV
head changed); my count is `bestmove` lines differing, position by position.
- Whether its changed-bestmoves for G (206) has the same issue — not measured here.

## 6. UTC stamps

times: see stamps.txt (cross 1 began after the file-19 wait expired at 14:20:24Z; patch applied
and built 14:2x; first (void-capture) run 14:2x; fixed rerun 14:3x; report written after).

## 7. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable (away), read by Opus, paired with
deepseek5 and kimi5.
