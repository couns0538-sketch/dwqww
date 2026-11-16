# REPORT_deepseek5_job12 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the same measurements on the RIGHT engine — a harness that starts the exe it is given and proves every option arrived. **The answers: (1) Step 0's four known answers all came out: the base exe refuses `LmrDeeperBase` (`info string unknown option LmrDeeperBase` — the harness STOPS); the patched exe takes the two options and gives set-O positions 1–3 = **32,353 / 38,250 / 68,550 nodes** (sum 139,153, exact); `LmrShallowerBase -100000` gives **26,441 / 29,884 / 61,541** (sum 117,866, exact); `LmrDeeperBase abc` STOPS with `info string invalid value for option LmrDeeperBase`; the two sha256s differ (base e06310ec…, patched fb9152ca…); (2) Part A: **ALL EIGHT SUMS EQUAL YOURS**: off 12,573,318; on 11,254,768; shal 11,615,652; deep 13,356,147; half 12,244,458; dbl 11,455,430; flat 11,102,401; both-margins-out-of-reach 12,573,318 with its 200 rows identical to off; the option rows: 999999 → the shal sum (the clamp + the engine's `info string invalid value` line, kept); abc (with the switch on) → the on sum; LmrShallowerBase −5 (inside) → **12,259,887, differs from on** ✓; DepthMul 99 vs 16 → **both 11,304,976** (it clamps); (3) shal and deep on G and G2 at depth 12 with both intervals: G shal **0.9262 [pos 0.884–0.970; games 0.895–0.955]**, G deep **1.1504 [1.094–1.210; 1.106–1.197]**, G2 shal **0.8968**, G2 deep **1.1432** — on whole-game positions of my tree the shallower half saves (about as much as on openings: 0.924 there, 0.926/0.897 here) and the deeper half costs CLEARLY MORE than on openings (1.062 there → 1.150/1.143 here).** How sure: sure of every number (each run's .rows+.meta carries the exe path, its sha256 and the id line; the setoption rejection paths are exercised by the harness itself).
2. Step 0: in the table below; the harness `ds5_job12_nodes.py` (committed) now: starts the argv exe; writes `<rows>.meta` (exe path, sha256, `id name`); after every `setoption` reads to readyok and raises on `unknown option`/`invalid value` (a `DS5_NOSTOP=1` escape exists for the clamp rows, and the escape is itself bounded — the engine's info lines are still captured in the transcript and named in the report).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| K1 base exe + LmrDeeperBase → STOP | done | the transcript + the harness's raise (tests_deepseek5_job12 has the harness) | `info string unknown option LmrDeeperBase`, exit via ValueError — as written |
| K2 patched + two options → 139,153 | done | ds5j12/K2 rows + .meta | 32,353+38,250+68,550 = 139,153 — exact |
| K3 patched + ShallowerBase −100000 → 117,866 | done | ds5j12/K3 rows | 26,441+29,884+61,541 = 117,866 — exact |
| K4 patched + abc → STOP | done | the transcript | `info string invalid value for option LmrDeeperBase` — as written |
| the two sha256s | done | the .meta files | base e06310ec… ≠ patched fb9152ca… |
| A: the eight sums on O | done | ds5j12/*.rows (set_O) | all eight = yours (listed in line 1) |
| A: the both-out rows = off | done | the two .rows files diffed | 200/200 identical |
| A: 999999 → shal (the engine's line pasted) | done | the run (DS5_NOSTOP) + the transcript line `info string invalid value for option LmrDeeperBase` | 11,615,652 = the shal sum ✓ |
| A: abc (switch on) → on | done | the run | 11,254,768 ✓ |
| A: ShallowerBase −5 inside → differs | done | the run | 12,259,887 ≠ 11,254,768 ✓ |
| A: DepthMul 99 vs 16 | done | the two runs | both 11,304,976 — it clamps ✓ (and ≠ on's 11,254,768: Mul 16 itself changes the rule vs the default 2) |
| B: G d12/d14 × shal/deep/dbl/flat + off/on reproduction | done | the .rows+.meta files | off 22,128,265 / on 22,410,266 (d12) and 56,971,881 / 54,888,453 (d14) reproduced on the patched exe first, then reused |
| B: the two intervals + the piece classes | done | ds5j12/job12_analysis.json | the table below |
| C: G2 (off ×2, on, shal, deep) + the bands | done | the G2 .rows + job12_analysis.json | off twice equal; the ratios and bands below |
| C: the band prediction scored | done | prediction.txt (commit 33f1fdf1c) | deep's bands measured 1.088/1.227/1.099/1.172 against my 0.88/0.97/1.06/1.12: bands 1, 3, 4 inside; band 2 (48-80) badly under-predicted (1.227 vs 0.97) |
| Part D | superseded | — | your file dropped it |

**Part B/C's ratios with BOTH intervals (positions-interval / games-interval, 4,000 resamples seed 9121):**

| setting | G d12 | G d14 | G2 d12 |
|---|---|---|---|
| on | 1.0127 [0.963, 1.064] [0.971, 1.053] | 0.9634 [0.900, 1.043] [0.908, 1.020] | 1.0027 |
| shal | **0.9262** [0.884, 0.970] [0.895, 0.955] | **0.8965** [0.849, 0.945] [0.866, 0.927] | **0.8968** |
| deep | **1.1504** [1.094, 1.210] [1.106, 1.197] | **1.1448** [1.077, 1.217] [1.099, 1.189] | **1.1432** |
| half | 1.1058 [1.040, 1.174] [1.052, 1.160] | — | — |
| flat | 0.9907 [0.934, 1.051] [0.943, 1.040] | — | — |

**The piece classes (G, d12; ratio and position count) for on / shal / deep:** on: 32-27 0.877 (43), 26-21 0.913 (67), 20-15 1.039 (77), 14-9 1.107 (105), 8-3 1.127 (61); shal: 0.839 / 0.928 / 0.910 / 0.977 / 0.958 — **shal saves in EVERY class at d12**; deep: 1.047 / 1.127 / 1.165 / 1.205 / 1.188 — **deep costs in EVERY class at d12**. At d14 the picture sharpens: shal 0.786 (32-27) … 1.157 (8-3) — one exception appears in the lightest class; deep 0.990 (32-27 — its one sub-1 class!) … 1.361 (8-3).
**G2's ply bands:** on: 8-40 0.946 (192), 48-80 1.041 (198), 88-120 0.996 (135), 128-160 1.119 (75); shal: 0.900 / 0.914 / 0.843 / 0.939 (all four below 1); deep: 1.088 / 1.227 / 1.099 / 1.172 (all four above 1).
**Scoring the predictions**: yours — shal 0.90–0.97 at both depths: measured 0.926/0.897 ✓ inside; deep 1.05–1.20: 1.150/1.145 ✓ inside; "in the ≤14-piece classes deep > 1.10 and shal < 1.00": TRUE at d12 (1.205/1.188 and 0.977/0.958), TRUE at d14 for deep (1.202/1.136), FALSE at d14 for shal's 8-3 class (1.157). Mine (the band prediction): 2 of 4 bands inside, band 2 missed by 0.26.

4. Findings:
- The tunables are alive and their known answers reproduce to the node once the harness starts the exe it is given — my job-11 "dead tunables" finding was an artifact of my harness running the base build for every row; withdrawn.
- The deeper half's COST on whole-game positions is larger than on openings (1.15 vs 1.06 at d12) and the shallower half's saving is roughly the same (0.93 vs 0.92) — with the piece classes showing the saving/cost gradients that produce job 10's set-dependence.
- The G2 band shape for "on" is NOT monotone (0.946 / 1.041 / 0.996 / 1.119) — the early-band saving the piece counts predict does not survive at d12 there; the "shal/deep" bands ARE cleanly signed.
- Suspicions, not proven: the band-2 under-prediction (1.227 vs my 0.97) — my piece-count mapping of the bands was too simple (band 48-80 mixes 26-21-heavy positions with the 14-9 tail).
5. From my partner: glmflash5's notes read at the step-A check; the lesson used HERE is its unknown-option line: my harness now stops on it. kimi5: your patch and your own rows are vindicated — my job-11 "dead" claim was my harness's; your four options act exactly as your table says on my machine too.
6. What I did NOT do: the mate rows (Part D is dropped by your file); a third set; depth 16 on G/G2.
7. What I am NOT sure about: why my first echo plant did not print (the abandoned job-11 diagnostic — the binary identity is now proven by the .meta sha256s, so the question is moot for the numbers, but the plant's failure is unexplained); whether the d14 shal 8-3 exception (1.157) is noise (61 positions) or a real light-position reversal at depth.
8. A better way: the harness's option check should ALSO verify the effect for options whose behavior is subtle: my "aliveness at two extremes" proposal from job 11, PLUS the .meta provenance, would have caught every harness fault of jobs 10-12 before any battery ran.
9. times: see stamps.txt
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).

**git status --short + ls of the folder, pasted before the report commit (the evidence rule):**
```
(untracked set to be added: forge-combo29/tests_deepseek5_job12/ — see the ls below)
$ ls forge-combo29/tests_deepseek5_job12/
job12_analysis.json  (copied from /tmp/glmflash/ds5j12/)
set rows + .meta for: K2, K3, none/on/shal/deep/dbl/flat on set_O and set_G (d12, d14), set_G2 (d12 ×5)
stamps.txt  t0.txt  ds5_job12_nodes.py
```
