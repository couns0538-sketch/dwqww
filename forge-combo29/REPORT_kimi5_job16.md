# REPORT_kimi5_job16 — MalusE: the quiet-malus scaled by quiets tried (E1), a continuation malus on a failed re-search (E2)

(1) **Step 0 met; I2 met; W1 == I2 everywhere; both controls differ.** Patched build, no option:
bench 11 = 312,866 · bench 13 = 862,329 · bench 16 = 3,024,920 · `go perft 5` = 4,865,609 (raw:
`step0_bench11.txt`, `step0_bench13.txt`, `step0_bench16.txt`, `step0_perft5.txt`); the `uci` list holds
`QuietMalusBase` (spin default 64 min 0 max 128), `QuietMalusPerMove` (default 0 min -8 max 8),
`ResearchMalus` (default 0 min 0 max 1) (`step0_uci.txt`). W1 (S14 + the three options sent explicitly
at their defaults) equals my job-12 I2 rows on **every position, node count and best move, on O and G**
(O 9,500,069; G 18,466,239; `cmp` output below). Control 1 (QuietMalusPerMove 4): all 200 O positions
differ, 53 best moves changed. Control 2 (ResearchMalus 1): all 200 O positions differ, 58 changed.

(2) **Counters (Step 2), the two known answers first.** Summed over all 553 searches of each run pair
(200 O + 353 G; one MALC line per search; the committed summing command is
`python3 analyze_j16.py malc rows/cnt_s14_{O,G}_d12_full.txt`, it prints `MALC lines summed: 553`):
- *Known answer 1, in the form my answer (c) forces:* `researched_fail + (bonus_given − bonus_without_research)
  + noisy_pass == researched` — **exact on both runs**: S14: 81,809 + (326,417 − 169,626) + 12,221 =
  250,821 = researched ✓; S14+ResearchMalus 1: 81,499 + (323,166 − 167,017) + 12,482 = 250,130 = researched ✓.
  Fable's shorter form `researched_fail + bonus_given == researched` presumes answer (c) is "no"; here the
  raw sum overshoots researched by exactly `bonus_without_research` (169,626, to the unit), which is the
  internal-consistency proof for the counters.
- *Known answer 2:* `bonus_without_research == 0` only if (c) is "no". My (c) is **yes** (below), and the
  counter is nonzero as predicted: **169,626 (S14) / 167,017 (RM1) — 52 % of all bonus events fire WITHOUT
  a re-search** (reduced_depth == new_depth, i.e. r ≤ 0 after the clamp).
- The counting build equals the plain patched build on every position (S14: 9,500,069 O / 18,466,239 G;
  ResearchMalus 1: 9,480,482 O / 18,412,338 G — position-for-position equal to the plain `t_r1` rows,
  nodes and best moves): the counting patch is observe-only.
- Heads: fail share of researched **0.3262 (S14)** / 0.3258 (RM1) (prediction 0.30, survives).
  `update_quiet_stats` calls: 2,217,281; n-bins: n=0 1,730,525 (78.1 %) · 1: 273,713 · 2: 103,087 ·
  3: 46,289 · 4-7: 49,210 · 8-15: 11,327 · 16+: 3,130 → **n ≥ 4 share 0.0287** (prediction 0.15: KILLED).
  Depth splits (d1-8 / d9+): reduced_pass 427,616/8,075 · researched 244,815/6,006 · fail 79,471/2,338 ·
  bonus 320,840/5,577 · bwr 167,576/2,050 · noisy_pass 12,080/141. Full dumps: `malc_s14.txt`, `malc_r1.txt`.

(3) **Step 3 trees** (plain patched build, S14, depth 12, ratio to I2; bootstrap over positions,
2,000 resamples, seed 2601, `analyze_j16.py boot`; raw: `boot_trees.txt`):

| tree | O sum | O ratio [95 %] | bm chg | G sum | G ratio [95 %] | bm chg |
|---|---|---|---|---|---|---|
| T_m4  (PerMove 4)   | 9,002,902  | **0.9477** [0.9010, 0.9957] | 53/200 | 17,717,178 | **0.9594** [0.9161, 1.0029] | 76/353 |
| T_mn4 (PerMove -4)  | 10,409,352 | **1.0957** [1.0333, 1.1579] | 50/200 | 20,092,803 | **1.0881** [1.0337, 1.1426] | 91/353 |
| T_b32 (Base 32)     | 11,019,482 | **1.1599** [1.0985, 1.2281] | 53/200 | 20,726,599 | **1.1224** [1.0594, 1.1873] | 81/353 |
| T_r1  (ResMalus 1)  | 9,480,482  | **0.9979** [0.9462, 1.0499] | 58/200 | 18,412,338 | **0.9971** [0.9512, 1.0461] | 87/353 |
| T_m4r (m4 + r1)     | 9,088,475  | **0.9567** [0.9090, 1.0090] | 49/200 | 17,347,875 | **0.9394** [0.8953, 0.9839] | 89/353 |

Trees only, no strength claim. Weakening the quiet malus grows the tree (half it uniformly: +16 % O,
+12 % G, one-sided; let it decay with n: +9-10 %, one-sided); growing it with n shrinks the tree
(-5 % O; G straddles 1). E2 alone is neutral within error; E2 on top of m4 is one-sided below 1 on G.

## Answers (a) to (e) — all line numbers verified by opening `src/search.cpp` at 6b98f217

**(a) Can the cutoff move be inside `quiets`? No.** The cutoff does `++ss->cutoff_count; break;`
(search.cpp:2052-2055) and leaves the move loop BEFORE the append
`if (quiet && quiet_count < ...) quiets_tried[quiet_count++] = move;` at **2065**. The cutoff move is
never appended; every entry already in the array is a different move (each move is visited once), so
`move` is never inside `quiets`, the `if (quiet == move) continue;` at 1390 never fires, and
n == quiet_count always. `update_quiet_stats` has exactly one call site (2077).
Show again: `sed -n '2044,2066p;2075,2079p' src/search.cpp`.

**(b) Largest n and the sign of bonus.** `std::array<Move, 128> quiets_tried` (1789) → n ≤ 128; the
formula caps at `std::min(n, 16)`, so the factor `QuietMalusBase + QuietMalusPerMove * min(n,16)` spans
[64 − 8·16, 64 + 8·16] = [−64, 192], clamped by `std::max(0, …)` → malus ∈ [0, 3·bonus].
`history_bonus(d) = min(HistoryBonusMax, Quadratic·d² + Linear·d − 32)` (242-244); the move loop runs
only at depth ≥ 1 (`if (depth <= 0) return qsearch(...)` at 1556), and the call passes `depth` or
`depth + 1` (2077), so under S14 (24/54/2212) bonus ≥ history_bonus(1) = 46 > 0: **never zero or
negative under S14**. (With other tune values both coefficients can be 0 and bonus can go negative —
not under S14.)

**(c) Can the 2027-2030 bonus fire without a re-search? YES.** `full_depth_needed = score > alpha &&
reduced_depth < new_depth` (2014). When the reduction clamps to nothing — `reduced_depth = clamp(
new_depth − r, 1, new_depth)` (2011) with r ≤ 0 (tt_pv −1 at 1995, gives_check −1 at 1999, in_check −1
at 2000, history up to −2 at 2002, or a small table reduction) — `full_depth_needed` is false, the
re-search at 2023 is skipped, and the bonus still fires if that single (full-depth) null-window search
beat alpha. Measured: 52 % of the bonuses (169,626 of 326,417 over O+G) are exactly these
(`bonus_without_research`). Fable's reading ("no") holds only on the `reduced_depth < new_depth` path.

**(d) Same-node readers after E2's write: yes, two.** E2 writes inside the move loop; the node keeps
searching later moves. (i) each later move's LMR `history` is read fresh at **1829** → `quiet_history`
(1324-1328) reads the (ss−1) and (ss−2) continuation entries at **1335-1336**. (ii) the picker's
`QuietScorer` captures only the cont1/cont2 **pointers** at construction (789-790) and reads the table
entries at each `score()` call (798 → 266-267); scoring is on demand as the selection advances
("select those on demand and sort the remainder once if the search gets that far", 811-813), so a
quiet scored after E2's update sees the new values. Already-scored quiets are not re-scored. E1 is
different: it runs at node end (2077), after the loop — nothing at the same node reads after it.

**(e) Which E1/E2 continuation writes are read under S14.** `ContHist4PlyRead` is false (93). Reads of
continuation history under S14: cont1 (ss−1) and cont2 (ss−2) at 1335-1336 (`quiet_history`, feeding
LMR 2002 and history pruning) and through the picker scorer (789-790 → 266-267). The 4-ply entry is
read only behind the switch (791-792, 1337-1339), so **every 4-ply write E1 and E2 make (1367-1368, at
half bonus) is dead under S14** — consistent with Carbon's REPORT_t22 Finding A. The 1-ply and 2-ply
writes are read by later searches — and for E2 also by later moves of the same node, see (d). E1's
main-history and threat-quiet writes (1391-1392 region) are outside the question's scope but read normally.

## The patch, its sha256, how to apply, dry-runs

- `tests_kimi5_job16/MalusE.patch.txt`, sha256 **fe4e0de7bdc15668e90c7c156566b156466196c2ac4fca7c6d2aa583d479d7a2a**...
  (full value in `exe_sha256.txt`), a unified diff against plain 6b98f217 made with `diff -u`.
  Apply: `patch -p1 -F0 < MalusE.patch.txt` from the directory above `forge-combo29` (zero fuzz).
- `tests_kimi5_job16/MalusECount.patch.txt` (on top of MalusE; counters live only with
  `-DFORGE_MALUS_COUNT=1`; default 0 = the MalusE build bit-for-bit in behavior).
- Dry-runs (`patch --dry-run -p1 -F0`, raw in `dry12.txt dry14.txt dry15.txt dryplain.txt`):
  **plain 6b98f217 OK; on top of job-12 FailHighBlend OK; on top of the job-14 chain OK; on top of the
  job-15 chain OK.** NOTE: job-14's RfpGuards.patch.txt and job-15's AlphaQs.patch.txt are NOT diffs
  against plain 6b98f217 — their context carries job-12's FailHighBlend lines, so they apply only on
  6b98f217+FailHighBlend (on the pristine tree RfpGuards fails 3/3 hunks, AlphaQs fails its table hunk).
  The chains tested: 6b98f217+FailHighBlend+RfpGuards and 6b98f217+FailHighBlend+AlphaQs.
- Builds: g++ 13.3.0, `-DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release`, machine has AVX-512+BMI2
  (no FORGE_PORTABLE). WARNING: this VM's default `c++` is Clang 18 and fails to link `-lstdc++`;
  cmake must be pointed at g++ explicitly or the configure dies in `project()`. Exe sha256:
  plain 259c1844…, counting f5f1e020… (`exe_sha256.txt`; the count binary differs and its
  `MALC` lines prove the flag is in).

## The job-3 wiring-control paragraph (asked for in file 16)

"Cannot be told" in full. What the committed files pin: the position set (`tests_kimi5_job3/wire8.fens`,
8 positions), the two patches (`counters.patch.txt` then `tunable_AspReopenMargin.patch.txt`), the option
state (`AspCappedReopen` on, `AspReopenMargin` 0/13/100), and the three sums 279,937 / 407,550 / 469,476
(REPORT_kimi5_job3.md lines 38 and 132-136). What is NOT committed: the depth, the rest of the option
list, the exe sha256, and any input log — no `*_input.log` in `tests_kimi5_job3/` mentions wire8
(verified: `grep -l wire8 tests_kimi5_job3/*_input.log` is empty), and no committed json there has
wire8 as its fens or 8 positions at all (an earlier NOTES line claiming the .meta files pin the run is
wrong — the control's raw output was never committed). deepseek6's non-reproduction
(270,415 / 249,794 / 320,651 at depth 12 under S14) is therefore consistent with an unrecorded depth
and/or option set in my job-3 run; the run was not repeated, as instructed. Lesson carried to NOTES:
a control run without its input log committed is not a control.

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| claim + prediction commits | done | `prediction.txt` (commits 1794884614 / 1794884955) | prediction BEFORE Step 1 |
| patch + dry-runs | done | `MalusE.patch.txt`, `dry*.txt` | 4/4 apply, zero fuzz |
| Step 0 | done | `step0_*.txt` | all four numbers + 3 options met |
| Step 1 W1 identity | done | `rows/w1_{O,G}_d12.json` (+`.meta`, `_input.log`) vs job-12 `i2_s14_{O,G}_d12.json` | EQUAL on all 553 positions, nodes and best moves |
| Step 1 controls | done | `rows/t_m4_O_d12.json`, `rows/t_r1_O_d12.json` | both DIFFER from I2 (200/200 positions) |
| Step 2 counters | done | `rows/cnt_*_full.txt`, `malc_s14.txt`, `malc_r1.txt` | identities exact to the unit; sums == plain |
| Step 3 trees | done | `rows/t_*_d12.json`, `boot_trees.txt` | the table above |
| answers (a)-(e) | done | this file, lines verified against `src/search.cpp`@6b98f217 | above |

Runs: all 16 depth-12 runs overlapped (one concurrent launch; `.meta` beside every rows file carries
exe path, sha256, id name, every option line; every input is in `rows/*_input.log`; the runner stopped
on any existing output file and on `unknown option`/`invalid value` — none occurred).

## From my colleagues

- deepseek5 (branch for-fable-and-opus/deepseek5-work; notes through "after job 30" and
  REPORT_deepseek5_job30.md read): applied its lesson "read a state variable at the moment the event
  happens" — every E2 counter is incremented directly at the re-search call / bonus line, not derived
  later; that is why the counter identity closes to the unit. Its CounterMove-vs-Killer2 regret rates
  noted; not used here.
- glmflash5: the branch named in my instructions (`for-fable-and-opus/glmflash5-work`) does NOT exist;
  its notes live on `cursor/glmflash5-work-cb5c` (read through "after queue 5";
  `for-fable-and-opus/glmflash-work` exists but holds only old t-reports and no notes file). Its two
  source questions for me (the fastchess process-reuse TT-pollution path; whether the composed-bundle
  `LmrGiveCheckF=0` behaves like the integer branch's `LmrGiveCheck=0`) were not checkable inside this
  job's budget — carried to NOTES for a later run.
- deepseek6's two job-16 finds (recounted in file 16) addressed: the wiring-control paragraph above;
  its S14-depth-12 inertness result for AspReopenMargin noted (no action needed here).

## What I did NOT do

No matches, no Elo, no strength claim (the job is trees and counters only). The job-3 wiring control was
not rerun (instructed). The 4-ply continuation reads were verified by code inspection only, not by a
planted ContHist4PlyRead run. Job 17 not started (job 16 is this run's one job).

## What I am NOT sure about

- Whether the 52 % `bonus_without_research` share is an S14 artifact (LmrHistoryDivisor 5643 lets the
  ±2 history clamp zero the reduction often at shallow depth) or universal; it is one setting, measured.
- Whether E2's dead 4-ply writes under S14 matter for a future ContHist4PlyRead test (they would then
  be read at half weight — E2's signature would change).
- The n≥4 share (2.9 %) means E1's PerMove term is driven by the n=1..3 population (19.4 % of calls);
  the bins 4-7/8-15/16+ are thin (2.2 % / 0.5 % / 0.14 %) — tree effects of PerMove are mostly an
  n≤3 effect at depth 12.

## A better way

1. The job's own data answers a question it did not ask: 52 % of the LMR "reduced-search beats alpha"
   bonuses involve NO reduction (r ≤ 0 → full-depth null-window). If the bonus exists to reward a move
   that beat a genuine reduction, gate it on `reduced_depth < new_depth` — the `bonus_without_research`
   counter is the exact before/after measuring tool, and W1-style identity plus a T-r1-style tree run
   check it in one job.
2. Counting `n` with a loop is provably redundant: answer (a) shows n == quiet_count always, so the
   malus formula could read `quiet_count` directly (one less pass over up to 128 moves per cutoff).
   Checkable: the W1 identity must still hold position-for-position, and the counters' e1_n bins must
   reproduce exactly.
3. Counter depth splits at exact depths (1..16) instead of two bins cost the same one line per search
   and show where re-searches concentrate; the two-bin split hides that 96-97 % of everything happens
   at depth ≤ 8 at d12.

## times: see stamps.txt

## Final commands (last before the commit)

`git status --short` and `ls` of the job folder — pasted at the bottom of this report after the run.

## Model name

Kimi K3 (this runtime).

```
$ git status --short
 M forge-combo29/NOTES_kimi5.md
?? forge-combo29/REPORT_kimi5_job16.md
?? forge-combo29/tests_kimi5_job16/MalusE.patch.txt
?? forge-combo29/tests_kimi5_job16/MalusECount.patch.txt
?? forge-combo29/tests_kimi5_job16/analyze_j16.py
?? forge-combo29/tests_kimi5_job16/boot_trees.txt
?? forge-combo29/tests_kimi5_job16/dry12.txt
?? forge-combo29/tests_kimi5_job16/dry14.txt
?? forge-combo29/tests_kimi5_job16/dry15.txt
?? forge-combo29/tests_kimi5_job16/dryplain.txt
?? forge-combo29/tests_kimi5_job16/exe_sha256.txt
?? forge-combo29/tests_kimi5_job16/first200.fens
?? forge-combo29/tests_kimi5_job16/malc_r1.txt
?? forge-combo29/tests_kimi5_job16/malc_s14.txt
?? forge-combo29/tests_kimi5_job16/rows/
?? forge-combo29/tests_kimi5_job16/run_j16.py
?? forge-combo29/tests_kimi5_job16/s14.opt
?? forge-combo29/tests_kimi5_job16/set_G.epd
?? forge-combo29/tests_kimi5_job16/stamps.txt
?? forge-combo29/tests_kimi5_job16/step0_bench11.txt
?? forge-combo29/tests_kimi5_job16/step0_bench13.txt
?? forge-combo29/tests_kimi5_job16/step0_bench16.txt
?? forge-combo29/tests_kimi5_job16/step0_perft5.txt
?? forge-combo29/tests_kimi5_job16/step0_uci.txt
?? forge-combo29/tests_kimi5_job16/t_b32.opt
?? forge-combo29/tests_kimi5_job16/t_m4.opt
?? forge-combo29/tests_kimi5_job16/t_m4r.opt
?? forge-combo29/tests_kimi5_job16/t_mn4.opt
?? forge-combo29/tests_kimi5_job16/t_r1.opt
?? forge-combo29/tests_kimi5_job16/w1.opt

$ ls forge-combo29/tests_kimi5_job16 forge-combo29/tests_kimi5_job16/rows
forge-combo29/tests_kimi5_job16:
analyze_j16.py
boot_trees.txt
dry12.txt
dry14.txt
dry15.txt
dryplain.txt
exe_sha256.txt
first200.fens
malc_r1.txt
malc_s14.txt
MalusECount.patch.txt
MalusE.patch.txt
prediction.txt
rows
run_j16.py
s14.opt
set_G.epd
stamps.txt
step0_bench11.txt
step0_bench13.txt
step0_bench16.txt
step0_perft5.txt
step0_uci.txt
t_b32.opt
t_m4.opt
t_m4r.opt
t_mn4.opt
t_r1.opt
w1.opt

forge-combo29/tests_kimi5_job16/rows:
cnt_r1_G_d12_full.txt
cnt_r1_G_d12_input.log
cnt_r1_G_d12_input.log.meta
cnt_r1_G_d12.json
cnt_r1_G_d12.json.meta
cnt_r1_G_d12.stdout
cnt_r1_O_d12_full.txt
cnt_r1_O_d12_input.log
cnt_r1_O_d12_input.log.meta
cnt_r1_O_d12.json
cnt_r1_O_d12.json.meta
cnt_r1_O_d12.stdout
cnt_s14_G_d12_full.txt
cnt_s14_G_d12_input.log
cnt_s14_G_d12_input.log.meta
cnt_s14_G_d12.json
cnt_s14_G_d12.json.meta
cnt_s14_G_d12.stdout
cnt_s14_O_d12_full.txt
cnt_s14_O_d12_input.log
cnt_s14_O_d12_input.log.meta
cnt_s14_O_d12.json
cnt_s14_O_d12.json.meta
cnt_s14_O_d12.stdout
t_b32_G_d12_full.txt
t_b32_G_d12_input.log
t_b32_G_d12_input.log.meta
t_b32_G_d12.json
t_b32_G_d12.json.meta
t_b32_G_d12.stdout
t_b32_O_d12_full.txt
t_b32_O_d12_input.log
t_b32_O_d12_input.log.meta
t_b32_O_d12.json
t_b32_O_d12.json.meta
t_b32_O_d12.stdout
t_m4_G_d12_full.txt
t_m4_G_d12_input.log
t_m4_G_d12_input.log.meta
t_m4_G_d12.json
t_m4_G_d12.json.meta
t_m4_G_d12.stdout
t_m4_O_d12_full.txt
t_m4_O_d12_input.log
t_m4_O_d12_input.log.meta
t_m4_O_d12.json
t_m4_O_d12.json.meta
t_m4_O_d12.stdout
t_m4r_G_d12_full.txt
t_m4r_G_d12_input.log
t_m4r_G_d12_input.log.meta
t_m4r_G_d12.json
t_m4r_G_d12.json.meta
t_m4r_G_d12.stdout
t_m4r_O_d12_full.txt
t_m4r_O_d12_input.log
t_m4r_O_d12_input.log.meta
t_m4r_O_d12.json
t_m4r_O_d12.json.meta
t_m4r_O_d12.stdout
t_mn4_G_d12_full.txt
t_mn4_G_d12_input.log
t_mn4_G_d12_input.log.meta
t_mn4_G_d12.json
t_mn4_G_d12.json.meta
t_mn4_G_d12.stdout
t_mn4_O_d12_full.txt
t_mn4_O_d12_input.log
t_mn4_O_d12_input.log.meta
t_mn4_O_d12.json
t_mn4_O_d12.json.meta
t_mn4_O_d12.stdout
t_r1_G_d12_full.txt
t_r1_G_d12_input.log
t_r1_G_d12_input.log.meta
t_r1_G_d12.json
t_r1_G_d12.json.meta
t_r1_G_d12.stdout
t_r1_O_d12_full.txt
t_r1_O_d12_input.log
t_r1_O_d12_input.log.meta
t_r1_O_d12.json
t_r1_O_d12.json.meta
t_r1_O_d12.stdout
w1_G_d12_full.txt
w1_G_d12_input.log
w1_G_d12_input.log.meta
w1_G_d12.json
w1_G_d12.json.meta
w1_G_d12.stdout
w1_O_d12_full.txt
w1_O_d12_input.log
w1_O_d12_input.log.meta
w1_O_d12.json
w1_O_d12.json.meta
w1_O_d12.stdout
```
