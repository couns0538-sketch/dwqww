# REPORT glmflash5 — JOB 1 — HindsightDepth and SoundMatePruning at 20,000 nodes

Branch used: `cursor/glmflash5-work-cb5c` (my tooling forces the `cursor/<name>-cb5c` branch
template, so I could not create `for-fable-and-opus/glmflash5-work`; this branch IS my session
branch, from base commit 6b98f2170a3210e71beed04bbd2553972c253ed7 — find all my work here).

## 1. What was asked, the answer, how sure

Asked: measure HindsightDepth and SoundMatePruning (both default OFF) at 20,000 nodes.

Answer: **HindsightDepth: +7.8 Elo, 95 % [−2.7, +18.4] — inside the error.**
**SoundMatePruning: +6.3 Elo, 95 % [−4.2, +16.7] — inside the error.**
(Each pooled over its two seeds, 2,000 games each; interval is the 95 % pair interval over opening
pairs, pentanomial variance.)

How sure: sure of the measurement mechanics (step 0 exact, probes show options arrived, control saw
the +200 effect, zero abnormal endings). Not sure that either switch is neutral — both pooled
numbers lean positive (LOS 92.7 % / 87.9 %) with intervals that just touch zero; 2,000 games each
cannot settle that. Nothing more is claimed from these games. No single result closes an idea.

## 2. Known numbers of step 0 (honesty check — all four MATCH)

Fresh process per line, raw output in `tests_glmflash5_job1/`:

| check        | got      | expected  | file                |
|--------------|----------|-----------|---------------------|
| bench 11     | 312866   | 312866    | step0_bench11.txt   |
| bench 13     | 862329   | 862329    | step0_bench13.txt   |
| bench 16     | 3024920  | 3024920   | step0_bench16.txt   |
| go perft 5   | 4865609  | 4865609   | step0_perft5.txt    |

Environment: commit 6b98f2170a3210e71beed04bbd2553972c253ed7, release build, CMake 3.28.3, g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1), GCC's own libstdc++. CPU has AVX-512 and BMI2, so no
`FORGE_PORTABLE` / `FORGE_MARCH` overrides (defaults kept). fastchess alpha 1.8.3
(20261107-d7b47e8), built from the official repository tag v1.8.3-alpha.
Note: `/usr/bin/c++` on this machine is clang 18 with a broken `libstdc++.so` dev symlink; CMake
configure failed until I forced `-DCMAKE_CXX_COMPILER=g++`. Everything below uses g++ 13.3.

## 3. Games by ending (every match; nothing else occurred — no illegal moves, crashes, disconnects, or losses on time anywhere)

| match | games | White mates | Black mates | 3-fold rep. | fifty moves | insufficient material | stalemate | other |
|-------|-------|-------------|-------------|-------------|-------------|----------------------|-----------|-------|
| C     | 300   | 113         | 94          | 52          | 18          | 22                   | 1         | 0     |
| H1    | 1000  | 281         | 268         | 298         | 70          | 81                   | 2         | 0     |
| S1    | 1000  | 311         | 252         | 289         | 78          | 69                   | 1         | 0     |
| H2    | 1000  | 321         | 269         | 274         | 56          | 77                   | 3         | 0     |
| S2    | 1000  | 346         | 223         | 285         | 75          | 68                   | 3         | 0     |
| B     | 1000  | 297         | 259         | 296         | 75          | 71                   | 2         | 0     |

Per-game text lines (round|white|black|result|how it ended|opening FEN) are committed for every
match: `tests_glmflash5_job1/gamelist_{C,H1,S1,H2,S2,B}.txt`. Checked: within every pair both
games share the same opening FEN and colors swap (0 mismatches in all six files).

## 4. All matches

Same exe both sides, fixed nodes, no clock, no adjudication, book
UHO_Lichess_4852_v1.epd (2632036 lines, from official-stockfish/books zip), order=random,
Threads=1 Hash=16 OwnBook=false both sides, `-recover`, `-pgnout ... min=true`.

| name | options (cand side) | seed | games | W-L-D (cand) | pairs | Elo, 95 % pair interval | complete? |
|------|--------------------|------|-------|--------------|-------|-------------------------|-----------|
| C    | cand nodes=20000 vs base nodes=10000, no switch | 9100 | 300 | 172-35-93 | 150 | +171.3, fastchess ± 33.9 (≈95 %) | complete |
| H1   | HindsightDepth=true | 9101 | 1000 | 292-257-451 | 500 | +12.2 [−2.6, +27.0] | complete |
| S1   | SoundMatePruning=true | 9102 | 1000 | 295-268-437 | 500 | +9.4 [−5.5, +24.2] | complete |
| H2   | HindsightDepth=true | 9103 | 1000 | 300-290-410 | 500 | +3.5 [−11.5, +18.5] | complete |
| S2   | SoundMatePruning=true | 9104 | 1000 | 289-280-431 | 500 | +3.1 [−11.6, +17.9] | complete |
| B    | HindsightDepth=true + SoundMatePruning=true | 9105 | 1000 | 287-269-444 | 500 | +6.3 [−7.6, +20.1] | complete |

All six complete; nothing was cut (after C, 1000 games took ~6 min each, so all five switch
matches plus B fit before minute 50 — no downsizing needed).

Pooled per switch (my pentanomial computation, `tests_glmflash5_job1/pool_stats.py`; the script's
per-match output reproduces fastchess's Elo, ± (≈2σ), and Ptnml lines exactly, e.g. H1
n5=[21,123,189,134,33] = fastchess Ptnml [21, 123, 189, 134, 33]):

| switch | matches | pairs | score | Elo, 95 % pair interval | LOS | verdict |
|--------|---------|-------|-------|-------------------------|-----|---------|
| HindsightDepth | H1+H2 | 1000 | 0.51125 | +7.8 [−2.7, +18.4] | 92.7 % | inside the error |
| SoundMatePruning | S1+S2 | 1000 | 0.50900 | +6.3 [−4.2, +16.7] | 87.9 % | inside the error |
| both (B, single seed) | B | 500 | 0.50900 | +6.3 [−7.6, +20.1] | 81.2 % | inside the error |

Control C: +171.3 vs the expected near +200; the gap (≈29 Elo) is inside the stated ±33.9.
The tool sees the known effect.

## 5. Probes (2 games before each of H1, S1, B, fastchess trace log with engine I/O)

Raw logs: `tests_glmflash5_job1/probe_{H1,S1,B}.log` (~1 MB each, full trace); condensed
`probe_{H1,S1,B}_excerpt.txt`. Every engine-input line is `<name> <--- setoption ...>`:

probe H1 — cand received, once per game (2 games):
```
cand <--- setoption name HindsightDepth value true
```
  base received only: `setoption name Threads value 1`, `setoption name Hash value 16`,
  `setoption name OwnBook value false` — no HindsightDepth. Same pattern in S1
  (`cand <--- setoption name SoundMatePruning value true`) and B (cand received both lines).
  Options were sent as `true` (check option). Base side got none in all three probes.

## 6. From my partner (deepseek5)

Before this job I fetched `for-fable-and-opus/deepseek5-work`: **the branch does not exist yet**
(both of us were started at the same time). So: nothing read, nothing applied, nothing checked
from it. I will read its notes and newest report before my next job and cross-check its numbers
when there are any.

## 7. What I did NOT do

- Did not play B with a second seed (B was optional; one seed only).
- Did not test either switch at other node counts; 20,000 nodes only.
- Did not probe before C (C has no switch; but the probe mechanism itself was proven on H1/S1/B,
  which all used the same base-option block).
- In C I gave `nodes` per engine as required but omitted `proto=uci` from `-each` (auto-detect
  worked; the match completed normally). All switch matches used the exact form with `proto=uci`.
- Did not commit any engine source, binary, net, PGN or archive; PGNs stayed in /tmp and only the
  per-game text lines were committed.

## 8. What I am NOT sure about

- Whether the small positive leans of HD (+7.8) and SMP (+6.3) are real; both intervals include 0.
  My own seeds agree with each other (H1 +12.2 vs H2 +3.5; S1 +9.4 vs S2 +3.1 — same direction,
  different sizes; seed noise or a small true effect, cannot say).
- Whether these switches interact with node count (the switch searches differ in bench node
  counts, so speed per node differs; fixed-nodes matches also change thinking time per move in
  wall-clock terms — that is inherent to the design and applies to both sides' candidate only).
- My pooled LOS is a normal approximation, not fastchess's exact LOS.

## 9. A better way

- The pentanomial pooling in `pool_stats.py` reproduces fastchess per match exactly and then
  pools both seeds in one pass; it could be the session's standard tool for "pool two seeds and
  give the pair interval" instead of eyeballing two separate ± values.
- The gamelist builder (`make_gamelist.py`) turns PGN + stdout into the required
  round|white|black|result|how it ended|FEN lines automatically; every future match should commit
  this file from minute one instead of reconstructing pairs by hand.
- Liveness check on a fixed-nodes engine could add bench with BOTH switches on (done for B's
  config implicitly only through games); cheap, and B's bench number would pin the bundle config
  before a bundle match.

## 10. UTC stamps (all from `date -u` and recorded log/stamp lines; minute 0 = 03:21)

- 03:21:30 recorded start (first `date -u`); base commit fetched and checked out;
  branch `cursor/glmflash5-work-cb5c` created.
- 03:22 engine build finished (9 C++ files linked; bench verified next).
- ~03:22:15–03:22:40 step 0 (all four numbers match) and fastchess v1.8.3-alpha build;
  UHO book downloaded and unpacked (2,632,036 positions).
- 03:22:40–03:23:05 partner branch fetch: does not exist yet; liveness benches (all four
  differ from baseline). (No `date` was captured on those two calls — order is recorded by
  the surrounding stamps, the intervals above are reconstruction, only the endpoints below
  are recorded.)
- 03:23:06–03:24:22 control C (76 s, recorded duration): +171.3 ± 33.9.
- 03:24:22–03:24:30 probes H1/S1/B (timestamps recorded inside the three probe logs).
- 03:24:36–03:30:36 H1 (1000 games, 5:59, recorded): +12.2.
- 03:30:40–03:36:34 S1 (5:54, recorded): +9.4.
- 03:36:36–03:42:32 H2 (5:55, recorded): +3.5.
- 03:42:34–03:48:17 S2 (5:43, recorded): +3.1.
- 03:48:19–03:54:05 B (5:46, recorded): +6.3.
- 03:54:15–04:05 gamelists built and validated, pooled statistics computed, this report written.

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5.
