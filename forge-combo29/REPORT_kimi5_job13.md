# REPORT — kimi5, job 13 (the tuner's 35 settings: where a step changes nothing)

Branch `for-fable-and-opus/kimi5-work` · folder `forge-combo29/tests_kimi5_job13/` · base 6b98f217 plain
(no patch) · engine `/tmp/j13/build/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
(same sha256 as deepseek6's plain build of 6b98f217, quoted in its job-1 report).

## The first three lines

(1) **Step 0 met**: bench 11 = 312,866; bench 13 = 862,329; `go perft 5` = 4,865,609; S14 on O =
9,500,069 with the first three 41,311 / 24,872 / 28,574 — every known number exact.
(2) **Proven dead (Part 2: both ends equal, outside differs): `QsSeeMargin` dead on [0, 99]**
(0 and 99: nodes 200/200 and best moves 200/200 equal to S14; 100 differs: sum 9,768,507, nodes
1/200 equal — the held-back known answers matched exactly). **`CaptureFutilityMultiplier` dead on
[0, 1000]** and **`CaptureFutilityDepth` dead on [0, 15]** — each the whole option range (0 and the
maximum: 200/200 and 200/200 equal); no value outside the range exists, so the outside check does
not apply (the claim cannot be "too narrow").
(3) **Claims that failed in Part 2: none.** All 32 "live" claims were confirmed by deepseek6's
job-1 O rows (every one of its 64 runs at value±c differs from S14 on at least one position; my own
re-count in `deepseek6_crosscheck.txt`).

## 1. What was asked, the answer, how sure

Asked: for each of the 35 settings our SPSA tuner moves by ±c, can that step provably NOT change the
search (guard, staircase, integer division, clamp, unreachable depth), proven from the source and by
trees. Answer: exactly three are dead at value±c — `QsSeeMargin` (SEE quanta of 100), and
`CaptureFutilityMultiplier` / `CaptureFutilityDepth` (their only read sits behind
`CaptureFutilityBase > 0`, and that base is 0). The other 32 are live. How sure: the dead claims are
proven by endpoint runs on 200 positions with the outside point firing exactly on the known answer;
the live claims are confirmed by deepseek6's 64 committed runs, re-counted by my own committed
command; every source line cited was opened and read.

## 2. Step 0 known numbers (raw files)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | 312866 | `step0_bench11.txt` |
| `bench 13` | 862329 | 862329 | `step0_bench13.txt` |
| `go perft 5` | 4865609 | 4865609 | `step0_perft5.txt` |
| S14 on O, sum (first three) | 9,500,069 (41,311 / 24,872 / 28,574) | 9,500,069 (41,311 / 24,872 / 28,574) | `rows/i2.json`, `rows/i2_full.txt` |

Fresh engine process per line; `ucinewgame` + `isready` before every `go`; Threads 1, Hash 16,
OwnBook false; `.meta` beside every rows file (`rows/*.json.meta`: exe, sha256, `id name`, every
option line); every `setoption` quoted in `rows/*_input.log` (the runner stops on `unknown option` /
`invalid value`; none occurred; an existing output file stops the run — none existed).

## 3. Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Step 0 pins | done | `step0_bench11.txt`, `step0_bench13.txt`, `step0_perft5.txt`, `rows/i2.json` | all four exact |
| Part 1 (source table, 35 rows) | done | this report §4; `prediction.txt` (same claims, committed first) | 3 dead, 32 live |
| Prediction, own commit before any Part 2 run | done | `prediction.txt`, commit `kimi5 job 13 prediction` | predicted exactly the 3 dead; count 3 — **met** |
| Part 2 dead claims: endpoints + outside | done | `rows/see0,see99,see100,cfm0,cfm1000,cfd0,cfd15.json` (+`_full.txt`, `_input.log`, `.meta`), `compare_i2.txt` | endpoints 200/200 and 200/200; outside (100) differs on 199/200, sum 9,768,507 = known |
| Part 2 live claims via deepseek6 | done | `deepseek6_crosscheck.py`, `deepseek6_crosscheck.txt` | my sum of its `runs/O_QsSeeMargin_34.rows` = 9,500,069 = its table; all 32 live settings differ on ≥1 of 200 positions in both of its runs |
| `.gitignore` before first `git add` | done | `.gitignore` (claim commit) | no binaries committed |

## 4. Part 1 — the table (file:line in 6b98f217, `src/search.cpp` unless said)

Quantization facts used below: **(Q1)** every SEE result is a multiple of 100 — `board.cpp:24`
`SeeValue{0,100,300,300,500,900,0}` (a swap sum of these); `see_ge(m, X)` is constant in X on
((k−1)·100, k·100]. **(Q2)** the LMR table stores `std::uint8_t` (222–225): the double
`base/100 + ln(d)·ln(m)/(div/100)` is truncated; a parameter moves a cell only across an integer.
Options arrive through `uci.cpp:294` → `tune::refresh()` (311) which rebuilds the table.
**(Q3)** evals, alpha, beta, history, move counts are arbitrary integers — a plain integer margin or
divisor flips some comparison somewhere; "live" rows below say only where the read is, with the step
mechanism. Values: S14 where S14 sets the setting, else the tune default (41–99, ranges 114–149).

| setting | value | c | reads (lines) | what it feeds / steps | claim |
|---|---|---|---|---|---|
| LmrQuietBase | 93 | 8 | 223 | quiet reduction table cell, uint8-truncated (Q2); ±0.08 shifts some of 3969 cells across an integer | **live** (deepseek6: 200/200 pos. differ both ways) |
| LmrQuietDivisor | 205 | 12 | 223 | divisor of the same cell (Q2) | **live** (200/200 differ) |
| LmrNoisyBase | 10→13 | 6 | 225 | noisy table cell (Q2); S14 value 13 | **live** (161/147 differ) |
| LmrNoisyDivisor | 333 | 20 | 225 | divisor of the noisy cell (Q2) | **live** (159/199 differ) |
| NullMoveBase | 5 | 1 | 1701 | `reduction = base + depth/div + min((eval−beta)/evaldiv, 3)` — plain integer | **live** (200/200) |
| NullMoveDepthDivisor | 3 | 1 | 1701 | integer `depth / div`; depth 4: 4/3=1 vs 4/2=2 vs 4/4=1 | **live** (200/200) |
| NullMoveEvalDivisor | 200 | 20 | 1702 | integer `(eval−beta)/div`, capped at 3 by `min` | **live** (69/56) |
| RfpDepth | 8 | 1 | 1689 | guard `depth <= RfpDepth` — depth 8 nodes in/out | **live** (121/60) |
| RfpMargin | 72 | 6 | 1689 | `margin*depth − improving*imp` vs arbitrary `eval−beta` | **live** (200/200) |
| RfpImproving | 40 | 6 | 1689 | same margin | **live** (200/200) |
| RazorBase | 150 | 20 | 1683 | `eval + base + mult*depth < alpha`, arbitrary eval/alpha | **live** (162/146) |
| RazorMultiplier | 350 | 25 | 1683 | same sum | **live** (181/156) |
| FutilityDepth | 7 | 1 | 1869, 1921 | guards `lmr_depth <= FutilityDepth` (and the tight variant) | **live** (67/36) |
| FutilityBase | 100 | 12 | 1873, 1922 | `static_eval + base + mult*d <= alpha`; 1922 halves by integer `/2` | **live** (199/199) |
| FutilityMultiplier | 110 | 10 | 1873, 1922 | same margin | **live** (199/199) |
| LmpBase | 8 | 1 | 239 (used 1866) | `move_count >= base + depth²` (or `/2` not improving) — integer | **live** (200/200) |
| HistoryPruneMultiplier | 2220 | 200 | 1880 | `history < −mult*depth`; history (int16, gravity 247–249) passes −2220·d | **live** (165/155) |
| SeeQuietMultiplier | 24 | 3 | 1885 | `see_ge(move, −m·lmr_depth²)` — Q1 staircase: effective `floor(m·d²/100)`; at d=2, 24→25 crosses (0.96→1.00) | **live** at c=3 (200/200) |
| SeeNoisyMultiplier | 150 | 12 | 1903 | `see_ge(move, −m·depth)` — Q1: `floor(m·d/100)`; at d=2, 138→150 crosses (276→300) | **live** at c=12 (199/187) |
| SingularDepth | 6 | 1 | 1929 | guard `depth >= SingularDepth` | **live** (200/200) |
| SingularMargin | 2 | 1 | 1931 | `singular_beta = tt_score − m·depth` | **live** (200/200) |
| IirDepth | 2 | 1 | 1784 | guard `depth >= IirDepth` → `−−depth` | **live** (200/200) |
| ProbcutDepth | 5 | 1 | 1747 | guard `depth >= ProbcutDepth` | **live** (200/200) |
| ProbcutMargin | 180 | 15 | 1746, 1753 | `probcut_beta = beta + m − 50·imp`; also the SEE threshold `probcut_beta − static_eval` (arbitrary offset, Q1 no help) | **live** (198/195) |
| QsFutilityMargin | 160 | 14 | 1483 (used 1496) | `futility_base = static_eval + m`; `futility_base + capture_value <= alpha`, arbitrary static_eval/alpha | **live** (200/200) |
| **QsSeeMargin** | 40 | 6 | 1500 | `see_ge(move, −QsSeeMargin)` — Q1: constant for the margin in [0, 99] | **dead on [0, 99]** (proven §5) |
| AspirationDelta | 18 | 2 | 2400 (used 2407–2408) | root window `score ± delta` from depth 4; fail-high/low events change | **live** (200/200) |
| HistoryBonusQuadratic | 24 | 3 | 243 | `bonus = min(max, q·d² + l·d − 32)` → history → ordering | **live** (200/200) |
| HistoryBonusLinear | 54 | 6 | 243 | same | **live** (200/200) |
| HistoryBonusMax | 2212 | 180 | 243 | the clamp; binds at d ≥ 9 under S14 (24·81+54·9−32 = 2398) | **live** (190/187) |
| LmrHistoryDivisor | 5643 | 500 | 2002 | `clamp(history / div, −2, 2)`; flips for \|history\| in [5144, 6143], reached | **live** (200/200) |
| LmrCutoffThreshold | 3 | 1 | 2001 | `cutoff_count > thr` flips at counts 3 and 4; also `> 0` guard | **live** (200/200) |
| MaterialCorrectionWeight | 100 | 10 | 1218–1219 (guard 1237) | `correction += entry·W/100`, integer; W=100 is the identity, ±10 is not | **live** (200/200) |
| **CaptureFutilityMultiplier** | 250 | 25 | 1898 | read only inside `if (CaptureFutilityBase > 0 && …)` (1893); base = 0 (default, not in S14) | **dead on [0, 1000]** (whole range; proven §5) |
| **CaptureFutilityDepth** | 6 | 1 | 1894 | same guard | **dead on [0, 15]** (whole range; proven §5) |

(The "differ" counts are deepseek6's job-1 O runs at value−c / value+c, re-counted by me from its
`runs/O_*.rows` against its `O_S14_base.rows`: `deepseek6_crosscheck.txt`.)

## 5. Part 2 — the trees (set O, `go depth 12`, S14 + one option)

All 8 runs started together and overlapped on the 4-core machine (11 s wall; fixed-depth
single-thread searches, node counts unaffected — noted per the job-14 rule). One committed compare
command: `cmp_j13.py` → `compare_i2.txt`.

| run | option | node sum | nodes equal to S14 | best moves equal |
|---|---|---|---|---|
| i2 (base) | S14 only | 9,500,069 | — | — |
| see0 | + QsSeeMargin 0 | 9,500,069 | **200 of 200** | **200 of 200** |
| see99 | + QsSeeMargin 99 | 9,500,069 | **200 of 200** | **200 of 200** |
| see100 (outside) | + QsSeeMargin 100 | 9,768,507 | 1 of 200 (differs — as required) | 173 of 200 |
| cfm0 | + CaptureFutilityMultiplier 0 | 9,500,069 | **200 of 200** | **200 of 200** |
| cfm1000 | + CaptureFutilityMultiplier 1000 | 9,500,069 | **200 of 200** | **200 of 200** |
| cfd0 | + CaptureFutilityDepth 0 | 9,500,069 | **200 of 200** | **200 of 200** |
| cfd15 | + CaptureFutilityDepth 15 | 9,500,069 | **200 of 200** | **200 of 200** |

Known answers matched exactly: 0/99 → 9,500,069; 100 → 9,768,507. For the CaptureFutility pair the
claimed interval is the whole option range, so no outside value exists; the "claim is too narrow"
check does not apply. (deepseek6's Part 3 independently ran both at +4c — still exact identities.)

## 6. Findings (file and line; command that shows it again)

- F1 — `QsSeeMargin` is dead on [0, 99]: `board.cpp:24` (SEE values are multiples of 100),
  `search.cpp:1500`. Show again: `python3 cmp_j13.py rows` (see0/see99 vs i2) and `rows/see100.json`
  for the outside point.
- F2 — `CaptureFutilityMultiplier`/`CaptureFutilityDepth` are dead while `CaptureFutilityBase = 0`:
  the only reads are inside `if (tune::CaptureFutilityBase > 0 && …)` at `search.cpp:1893`
  (depth read 1894, multiplier 1898); base default 0 at `search.cpp:89`, not set by S14 (s14.opt).
  Show again: `compare_i2.txt` (cfm0/cfm1000/cfd0/cfd15 all 200/200).
- F3 — the LMR parameters are staircase parameters, not smooth ones: `search.cpp:222–225` truncate
  to `uint8_t`; arrival is wired `uci.cpp:294` → `search.cpp:311`. A SPSA ±c on them moves the tree
  (deepseek6: every position), but the effect is cell-wise floors, so the tuner's "gradient" is
  plateaus plus jumps.
- F4 — `SeeQuietMultiplier`/`SeeNoisyMultiplier` are live at their c only because c carries the
  product across a multiple of 100 (1885: 24→25 at lmr_depth 2; 1903: 138→150 at depth 2). Both
  have wide dead plateaus elsewhere (e.g. SeeNoisyMultiplier is dead on (100, 200) at depth 1
  alone); a smaller c could be pure noise. Not proven for other c — listed under §8.
- F5 — option arrival: every `setoption` line is in `rows/*_input.log` (e.g. `setoption name
  QsSeeMargin value 99`), no refusal lines; the runner stops on refusal.

Suspected, not proven: none.

## 7. From my colleagues

Read: `NOTES_deepseek5.md` (stand5 self-play protocol; job 30's one-late stage label — read state at
the event), `NOTES_glmflash5.md` on `cursor/glmflash5-work-cb5c` (jobs 21–24: seed-inertness under
sequential openings; CED8 ≈ +6.7 pooled), `REPORT_deepseek6_job1.md` + its O rows. Applied: the
job's own rule — live claims judged by deepseek6's rows, not by 64 new runs of mine; I summed one of
its O rows files myself (9,500,069 = its table) before trusting any cell, and re-counted every
setting's differences (`deepseek6_crosscheck.txt`). Checked: my i2 base and its `O_S14_base.rows`
agree (same sum, same first three; same build sha256). glmflash5's seed warning does not touch this
job (no games played).

## 8. What I did NOT do

No value±c runs of my own for the 32 live settings (the job assigns them to deepseek6; its report
exists). No G-set runs (Part 2 is set O only). `bench 16` not run (not in this job's step 0). No
outside run for the CaptureFutility pair (interval = whole range). I did not enumerate which LMR
table cells flip per step (the live claim rests on the measured rows, F3 is mechanism only).

## 9. What I am NOT sure about

Nothing that changes a claim. Minor: whether every one of the 32 live settings would also differ on
G at ±c I take from deepseek6's report (it says the same 3 inert on G); I re-counted only O. The
exact plateau edges of F4 for depths/multipliers I did not need are computed from the formula, not
measured.

## 10. A better way

For the quantized settings (all SEE thresholds, the uint8 LMR table, the integer divisions), the
dead intervals can be enumerated statically in milliseconds: evaluate the effective integer
(`floor(m·d²/100)`, the table cell, `depth/div`) over the option range for every reachable depth and
emit the plateaus. The tree runs then only prove that the option arrives and that nothing else reads
the value — one endpoint pair per claim instead of a full sweep, and the tuner gets the complete
plateau map (F4's "which c is noise") rather than point answers. Check that it is better: the
enumeration must reproduce every interval proven here ([0, 99] for QsSeeMargin; both whole ranges)
and every live flip deepseek6 measured at ±c; any mismatch indicts the enumerator, not the trees.
For the CaptureFutility pair the static way is already the stronger proof: one grep for the guard
plus the `CaptureFutilityBase 0` input line outranks two 200-position runs.

## 11. UTC stamps

times: see stamps.txt

## 12. Model name

Kimi K3 (run name kimi5).

## 13. The last commands

`git status --short` and `ls` of the job folder, pasted below (run just before this commit):

```
=== git status --short ===
 M forge-combo29/tests_kimi5_job13/stamps.txt
?? forge-combo29/REPORT_kimi5_job13.md
?? forge-combo29/tests_kimi5_job13/cmp_j13.py
?? forge-combo29/tests_kimi5_job13/compare_i2.txt
?? forge-combo29/tests_kimi5_job13/deepseek6_crosscheck.py
?? forge-combo29/tests_kimi5_job13/deepseek6_crosscheck.txt
?? forge-combo29/tests_kimi5_job13/exe_sha256.txt
?? forge-combo29/tests_kimi5_job13/rows/
?? forge-combo29/tests_kimi5_job13/step0_bench11.txt
?? forge-combo29/tests_kimi5_job13/step0_bench13.txt
?? forge-combo29/tests_kimi5_job13/step0_perft5.txt
=== ls tests_kimi5_job13 ===
cfd0.opt
cfd15.opt
cfm0.opt
cfm1000.opt
cmp_j13.py
compare_i2.txt
deepseek6_crosscheck.py
deepseek6_crosscheck.txt
exe_sha256.txt
first200.fens
prediction.txt
rows
run_j13.py
s14_cfd0.opt
s14_cfd15.opt
s14_cfm0.opt
s14_cfm1000.opt
s14.opt
s14_see0.opt
s14_see100.opt
s14_see99.opt
see0.opt
see100.opt
see99.opt
stamps.txt
step0_bench11.txt
step0_bench13.txt
step0_perft5.txt
=== ls rows ===
cfd0_driver.log
cfd0_full.txt
cfd0_input.log
cfd0_input.log.meta
cfd0.json
cfd0.json.meta
cfd15_driver.log
cfd15_full.txt
cfd15_input.log
cfd15_input.log.meta
cfd15.json
cfd15.json.meta
cfm0_driver.log
cfm0_full.txt
cfm0_input.log
cfm0_input.log.meta
cfm0.json
cfm0.json.meta
cfm1000_driver.log
cfm1000_full.txt
cfm1000_input.log
cfm1000_input.log.meta
cfm1000.json
cfm1000.json.meta
i2_driver.log
i2_full.txt
i2_input.log
i2_input.log.meta
i2.json
i2.json.meta
see0_driver.log
see0_full.txt
see0_input.log
see0_input.log.meta
see0.json
see0.json.meta
see100_driver.log
see100_full.txt
see100_input.log
see100_input.log.meta
see100.json
see100.json.meta
see99_driver.log
see99_full.txt
see99_input.log
see99_input.log.meta
see99.json
see99.json.meta
```
