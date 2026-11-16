# deepseek6 long 25 — depth-14 rows on O for V, CED 8, T1, T2

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long25/`
Model: DeepSeek V4.1 Flash 1017

## 1. What was asked, the answer, how sure

**Asked:** depth-14 rows on O for V, CED 8 alone, T1 and T2 (known: S14 at depth 14 on O = 21,812,100).

**Answer:** all five sums measured, every known answer exact. **S14 21,812,100 (pin, exact) · CED8 19,944,501 ·
V 19,759,587 · T1 22,329,867 · T2 27,469,140.** The interesting result is not the levels but the **change in
shape with depth**: CED 8's relative saving **grows** from depth 12 to 14 (0.9490 → 0.9144 of S14), while V's
stays essentially flat (0.9016 → 0.9059) and T1's grows a lot (1.0705 → 1.0237). I predicted the opposite for
CED 8 and was wrong; that is the finding (section 5, F2).

**Two predictions killed:** P2 and P3 (I thought both check configurations would come in *below* S14 by more than
depth 12 suggests — they came in at ~19.8–19.9 M, about 12 % above my band). Four held, one held by 0.0043.
Full scorecard in `prediction_scorecard.txt`, written from the measured numbers.

**How sure:** certain of the ten sums — every one comes from the same two binaries whose four depth-12 anchors
reproduce the standing known sums exactly (V 8,565,026 · CED8 9,015,167 · T1 10,170,054 · T2 11,915,365 ·
S14 9,500,069). The interpretation in F2 is measurement plus one mechanism sentence, marked as such.

## 2. Honesty numbers (raw output in `raw/`)

| build | bench 11 | bench 13 | bench 16 | perft 5 | sha256 |
|---|---|---|---|---|---|
| plain (6b98f217) | 312866 | 862329 | 3024920 | 4865609 | `7c4e1aee…33622` |
| + ChecksLmr (**bv**, for V/CED8) | 312866 | 862329 | 3024920 | 4865609 | `7203fd3d…38805` |
| + LmrFine (**bf**, for T1/T2) | 312866 | 862329 | 3024920 | 4865609 | `6cfebede…15cf4` |

Files: `raw/bv_bench11.txt`, `raw/bv_bench13.txt`, `raw/bv_bench16.txt`, `raw/bv_perft5.txt`, and the same four
for `bf`; `id name Chess Engine Forge 6.4.24 candidate` in `raw/bv_uci.txt` / `raw/bf_uci.txt`. Both patched
builds print all four pins exactly, so nothing in the patches disturbs the search at its defaults.

Patch provenance, shas verified against the names in the job files before use:
`p/ChecksLmr.patch.txt` = d33b27ca… (glmflash5 job 21 — the build my long 18 measured V on), `p/LmrFine.patch.txt`
= f7bf3f43… (kimi5 job 11). Both applied with `patch -p1 --fuzz=0`, dry run first (`p/` files are copies of the
inputs, committed so the shas can be re-checked).

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claim, then prediction, each its own commit | done | `CLAIM.txt` (68ec6c59b), `PREDICTION.md` (facc8c2cd) | prediction before the first build |
| three builds | done | `raw/*_bench*.txt`, `raw/*_perft5.txt` | all four pins exact on all three |
| harness check 1: LmrHistoryDivisor 5644 on O, d12 | done | `runs/hd5644b_d12.rows` | **9,512,627 EXACT** (job 6) |
| harness check 2: QsSeeMargin 100 on O, d12 | done | `runs/qsm100_d12.rows` | **9,768,507 EXACT** (kimi5 job 13) |
| S14 depth-14 pin | done | `runs/S14_d14.rows` | **21,812,100 EXACT** |
| CED 8 depth 14 | done | `runs/CED8_d14.rows` | 19,944,501 |
| V depth 14 | done | `runs/V_d14.rows` | 19,759,587 |
| T1 depth 14 | done | `runs/T1_d14.rows` | 22,329,867 |
| T2 depth 14 | done | `runs/T2_d14.rows` | 27,469,140 |
| depth-12 anchors on the SAME binaries | done | `runs/{S14,CED8,V,T1,T2}_d12.rows` | all five exact |
| ratio table | done | `ratio_table.py`, `ratio_out.txt` | section 4 |
| best-move churn | done | `bm_churn.txt` | section 5 F4 |
| a harness that first produced garbage, kept | done | `runs_bad_pipe/`, `rows.py` header | section 5 F1 |

`.meta` beside every rows file holds the exe path started, its sha256 at start and end, the `id name`, the FEN
set and count, the depth, and every setoption line in order. Every run in `runs/` reports `rows_written=200`.

## 4. The table

| config | d12 sum | d14 sum | d12/S14 | d14/S14 | change in ratio | d14/d12 growth |
|---|---|---|---|---|---|---|
| S14 | 9,500,069 | 21,812,100 | 1.0000 | 1.0000 | — | 2.2960 |
| CED 8 | 9,015,167 | 19,944,501 | 0.9490 | **0.9144** | **−0.0346** | 2.2123 |
| V | 8,565,026 | 19,759,587 | 0.9016 | 0.9059 | +0.0043 | 2.3070 |
| T1 (RoundF 512) | 10,170,054 | 22,329,867 | 1.0705 | 1.0237 | −0.0468 | 2.1956 |
| T2 (RoundF 0) | 11,915,365 | 27,469,140 | 1.2542 | 1.2594 | +0.0051 | 2.3054 |

Every number from `ratio_out.txt`; every d12 sum is a published known sum reproduced exactly.

## 5. Findings, each with the command that shows it again

**F1. My first harness silently produced zero-node rows, and I kept the evidence.**
`printf 'go depth 12\n' | forge` returns `bestmove` with **no search at all**: the engine aborts when stdin
closes, so the node count is never printed. My first shell harness did exactly that and wrote 200 rows of
`NONODES`. `sum_rows.py` refused to sum them — that refusal is the only reason I caught it before quoting a
number. The broken files are committed in `runs_bad_pipe/`; `rows.py`'s header documents the cause. Rerun:
`python3 sum_rows.py runs_bad_pipe/hd5644_d12.rows` → "refusing to sum".

**F2. The extension's saving grows with depth, not shrinks — my prediction was backwards.**
CED 8 at depth 12 is 0.9490 of S14; at depth 14 it is 0.9144 — the *opposite* direction from P4. Meanwhile V
(which removes both check discounts on top of the extension) is flat, 0.9016 → 0.9059. So at depth 12 the two
LMR-discount removals add 4.7 points of saving on top of CED 8; at depth 14 they add only 0.9. Rerun:
`python3 ratio_table.py`. Mechanism (suspicion, not proven): CheckExtensionDepth 8 extends into deeper check
lines, and those pay off more per node as the search gets longer, while removing the "give check / in check"
LMR discounts is a depth-12-sized effect that does not compound.

**F3. Fitting a depth-14 sum by scaling a depth-12 ratio is simply wrong, and my own table shows why.**
The growth factors differ by configuration: S14 2.2960, V 2.3070, T2 2.3054, but CED 8 only **2.2123** and T1
**2.1956**. The two configurations with a smaller growth factor are exactly the two whose ratio moved the most.
That is why P2 and P3 missed by ~12 % and P5 (which I gave a multiplicative band rather than a scaled one) held.
Rerun: `python3 ratio_table.py`, the second table.

**F4. Best-move agreement with S14 at depth 14 is high for all four; deeper search converges.**
`bm_churn.txt`: changed moves of 200 — CED8 **44**, V **51**, T1 **41**, T2 **44**. At depth 12 the same churn
was 133–143 (my long 18/21 rows). P7 said "≤130"; the measured values are three times better than that.

**F5. T1's whole advantage over S14 is a depth-12 phenomenon.**
T1 is 7.05 % *more* nodes than S14 at depth 12 and only 2.37 % more at depth 14 — T1's growth factor is the
lowest measured, 2.1956. If the fine-history term is a node-cost knob, its cost is largely amortized by depth 14.
That is a measurement, not yet a recommendation; a match would be needed to say what it buys.

## 6. Suspicions, not proven

- **S1.** The mechanism sentence in F2 (deeper check lines paying off more, discounts not compounding). The
  ratios are measured; the reason is inference.
- **S2.** Whether the CED 8 curve keeps turning: one step from 12 to 14 cannot distinguish "growing saving"
  from "a dip at 14". A depth-16 run of CED 8 and S14 would settle it, at roughly 5× the cost of these runs.
- **S3.** Whether the 44–51 changed best moves are quality changes or ties: with 200 positions and no match this
  item cannot tell a better move from a different equally-scored one.

## 7. What I read from my colleagues

Nothing new this item — the item took about 40 minutes and the colleague read is on the four-hour clock (last
full read before long 23, next due ~23:30Z). No advice from any note was used as an instruction; the harness,
the pins and the ratio design are mine. `p/LmrFine.patch.txt` and `p/ChecksLmr.patch.txt` are inputs, not
advice, and their shas were checked against the job file before use.

## 8. What I did NOT do

- **Did not run G at depth 14.** The item names O only.
- **Did not run any match.** These are node counts, not strength measurements; nothing here says CED 8 or V wins
  games.
- **Did not test depth 16** (see S2).
- **Did not reuse `runs_bad_pipe/` numbers** in any table — they are committed only as the evidence for F1.
- **No pull request**, no branch but mine, no engine source committed (patched trees live in `/tmp/ds6/long25`).

## 9. What I am NOT sure about

- The 12-to-14 comparison is one step. My own long 20 result (a non-monotone CED curve at depth 12: peak at 3,
  dip at 6, rise at 12) is a warning against reading a two-point trend as a law. F2 is what this measurement
  shows, not a curve.
- The churn numbers compare node counts *and* best moves only; equal-count rows do not exist here (0 identical
  rows in `bm_churn.txt`), so every configuration searches a genuinely different tree.

## 10. A better way

For any future item that compares a configuration across depths, **measure both depths on the same binary and
report the growth factor**, not a scaled ratio — F3 is exactly what happens when you don't. My prediction was
written before I had the growth factors; the report's table now makes them the first-class quantity.

Second: keep the broken run. `runs_bad_pipe/` is 2 MB of noise that proves a real trap (F1); deleting it would
have made the "the harness works" claim unfalsifiable.

## 11. Times and the folder

times: see `stamps.txt` (a `date -u` line before the first build, after each harness check, before the five
depth-14 runs, before the depth-12 anchors, and after the last run).
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

The last command before this commit was `git status --short` plus `ls` of the folder and of `runs/`; both are
pasted verbatim in `final_ls.txt`.
