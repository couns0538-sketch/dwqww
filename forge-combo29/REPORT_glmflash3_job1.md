# glmflash3 job 1 report (2026-11-15)

## 1. First line

Per node on one scale (fixed 20000-node games, same exe both sides): **B4 is stronger than the
no-option base by ~+24 Elo (95 % pair interval [16, 34] on the prescribed 3000 games)**; B1 and B4
were the bundles that had passed before and B4 is the one I measured against base; **B2 and B3
per-node strength I could not finish measuring in the time budget (M4 was cut at ~[M4GAMES]
games, M5 and M6 not started)** — their Step-0 node counts are far below base (B3 −32 %, B2 −18 %
at bench 13), which makes a per-node strength loss plausible but is not a strength measurement.
**`LmrTableV2` added on top of B4 (both sides carry B4) measured −1.4 Elo (95 % pair interval
[−11.5, +8.7], 2000 games) — it does not help on top of B4; the point estimate is a touch
negative and any true help is bounded above by ~+9 Elo at 95 %.**

## 2. Step 0, expected against printed

Build: commit `b7c177222038e9332965a95ec53ea3b94e90dbc9` (branch `opus-r7-nps`, fetched by id with
`--depth 1`), Release, g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, CMake 3.28.3,
`-DCMAKE_CXX_FLAGS="-march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256"`, target `forge` only.
**`-DFORGE_NNUE_HIDDEN=256` was needed**: `include/forge/nnue.hpp` defaults `FORGE_NNUE_HIDDEN` to
128, and the static_asserts in `src/nnue.cpp` (lines 91-94) size the compiled-in lock net
(`nnue_weights.inc`, the H256 net per CMakeLists.txt comment) against `HiddenSize`; without the
definition the asserts fail. Engine binary: `/tmp/g3job1/build/forge` (1.1 MB, built in 13 s).
Every run: fresh engine process, input file per run committed (`step0_*.out` — my tag names;
options Threads 1, Hash 16, OwnBook false on every run's input, bundle option appended where the
config has one; `position startpos` before `go perft 5`).

| config | command | expected | printed | match |
|---|---|---|---|---|
| no option | bench 11 | 312866 | 312866 | yes |
| no option | bench 13 | 862329 | 862329 | yes |
| no option | go perft 5 | 4865609 | 4865609 | yes |
| BundlePreset B1 | bench 11 | 280182 | 280182 | yes |
| BundlePreset B1 | bench 13 | 758456 | 758456 | yes |
| BundlePreset B2 | bench 11 | 255626 | 255626 | yes |
| BundlePreset B2 | bench 13 | 564279 | 564279 | yes |
| BundlePreset B3 | bench 11 | 211646 | 211646 | yes |
| BundlePreset B3 | bench 13 | 463170 | 463170 | yes |
| BundlePreset B4 | bench 11 | 276131 | 276131 | yes |
| BundlePreset B4 | bench 13 | 985600 | 985600 | yes |
| CorrHistV2 true | bench 11 | 282082 | 282082 | yes |
| CorrHistV2 true | bench 13 | 1001737 | 1001737 | yes |
| LmrTableV2 true | bench 11 | 245666 | 245666 | yes |
| LmrTableV2 true | bench 13 | 494753 | 494753 | yes |

All 15 agree. M2 prerequisite check: `BundlePreset B4` then `LmrTableV2 true`, bench 13 ->
**404596** (`step0/b4_then_lmrv2_d13.out`), different from B4's 985600 — the later option
overrides the preset, as BUNDLES.md says. Raw bench output also shows nps ~1.54 M on this box.

## 3. The three controls

fastchess `alpha 1.8.3 20261107-d7b47e8` (newest release tag v1.8.3-alpha at clone time), built
from source with its own Makefile (`make -j4`). Book `UHO_Lichess_4852_v1.epd` from
github.com/official-stockfish/books (downloaded as `UHO_Lichess_4852_v1.epd.zip`, unzipped,
2,632,036 lines). Match form exactly as prescribed; `-concurrency 4` (4 cores).

- **Control 1 (determinism)**: base vs base, 100 games, seed 9001, nodes 20000 both sides.
  Result: `Ptnml(0-2): [0, 0, 50, 0, 0]` — all 50 pairs 1-1 (27+27 wins, 46 draws, score
  exactly 50 %). Raw output `c1.out`, per-game file `c1_games.txt`.
- **Control 2 (power line)**: 20000 nodes (name `fast`) vs 10000 nodes (name `slow`), 300 games,
  seed 9002, no bundle options. fastchess: `Elo: 189.31 +/- 31.61`, fast side 179 W / 30 L /
  91 D (74.83 %). My own pair computation from `c2_games.txt`: mean pair score 0.7483, se 0.0175,
  95 % interval **[159.0, 222.5]** Elo. The tool clearly sees a real difference; a match of this
  shape can fail. Raw output `c2.out`, per-game file `c2_games.txt`.
- **Control 3 (option delivery)**: 2-game match, cand = B4, engine input logging
  (`-log file=c3.log level=trace engine=true append=false`). The `cand` side received, in both
  games, exactly: `setoption name Threads value 1`, `setoption name Hash value 16`,
  `setoption name BundlePreset value B4` (proof lines extracted to `c3_options_proof.txt`; the
  full log is 1.24 MB and stays uncommitted). Hash 16 is among them. `base` received Threads and
  Hash only. Raw output `c3.out`.

## 4. The matches

One table, one row per match. "my Elo" = from my own per-game file, score -> Elo, with the 95 %
pair interval from pair scores (two games of one opening, colours reversed, points/2).
fastchess's own Elo ± error quoted next to it. Crashes/illegal/disconnects counted from the
match output; expected 0, found 0 in every match that ran.

| match | cand options | base options | seed | games prescribed/played | W-L-D (cand) | fastchess Elo ± | my Elo [95 % pair] | crashes |
|---|---|---|---|---|---|---|---|---|
| M1 | BundlePreset=B4 | (none) | 7501 | 3000 / 3272* | 1038-815-1419 | +24.24 ± 8.44 (3202 games) | +23.7 [15.2, 31.8]; prescribed-3000 subset: +24.8 [16.1, 33.6] | 0 |
| M2 | BundlePreset=B4, LmrTableV2=true | BundlePreset=B4 | 7502 | 2000 / 2000 | 550-558-892 | −1.39 ± 10.13 | −1.4 [−11.5, +8.7] | 0 |
| M3 | BundlePreset=B2 | (none) | 7503 | 2000 / [M3G] | [M3WLD] | [M3FC] | [M3MY] | [M3CRASH] |
| M4 | BundlePreset=B3 | (none) | 7504 | 2000 / [M4G] | [M4WLD] | [M4FC] | [M4MY] | [M4CRASH] |
| M5 | LmrTableV2=true | (none) | 7505 | 1500 / not started | — | — | — | — |
| M6 | BundlePreset=B4 | BundlePreset=B1 | 7506 | 2000 / not started | — | — | — | — |

\* M1 accounting: I set `-rounds 3000` where the form wants rounds = games/2 = 1500, so fastchess
scheduled 6000 games; my 25-minute deadline interrupted it (SIGINT, fastchess "Tournament was
interrupted", rc 124 from `timeout`) after 3272 finished games — more than the prescribed 3000,
so the match's question is answered with the prescribed size and the surplus as a cross-check
(both rows above). Games in progress at the interrupt are not in the PGN (no INCOMPLETE entries
in the output); finished games all count. Primary row for the report: the prescribed-3000 subset
(`m1_first3000.txt`), with the full set as the second figure.

### M2 (cand: B4 then LmrTableV2=true — base: B4; 2000 games, seed 7502) — completed in 16:03, not cut
fastchess final block: `Elo: -1.39 +/- 10.13`, LOS 39.39 %, Ptnml [54, 236, 422, 240, 48].
My pair stats (`m2_games.txt`, 1000 pairs): mean 0.4980, se 0.0074, 95 % Elo [−11.5, +8.7].
**Verdict: LmrTableV2 does not win in B4's company.** The interval straddles zero; the 95 % upper
bound says any true help on top of B4 is at most ~+9 Elo. The §2 override check (bench 13 ->
404596 ≠ 985600) proves the cand side really had LmrTableV2 on top of B4 rather than B4 alone,
and Control 3 proves such option lines reach the engine in the prescribed order.

[M3SECTION]

[M4SECTION]

## 5. Files of the repository I opened

- `BUNDLES.md` (root of commit b7c17722) — preset definitions, bench table, exclusivity rule (read in full; it is data, used as the expected-values source).
- `CMakeLists.txt` (root) — build options, `FORGE_NNUE_HIDDEN` handling, `-ffp-contract=off` is already PUBLIC.
- `include/forge/nnue.hpp` — `FORGE_NNUE_HIDDEN` default 128 (grep + read around the definition).
- `src/nnue.cpp` — the static_asserts that ask for HiddenSize 256 (lines 91-94, 192).
- `src/uci.cpp` — bench command handler (~lines 1029-1082: fresh `Searcher(16)` per bench, prints `info string bench depth N nodes ...`), `go perft` handler (lines 903-930), setoption handlers for Threads/Hash (line 886), OwnBook (579), CorrHistPlus (664), CuckooRep (714), HistRework (721), CorrHistV2/LmrTableV2/TtPruneV2 (730-742), BundlePreset (744).
I did not open any other repository file; nothing of the engine source was modified.

## 6. Start and end of each step (recorded stamps, `/tmp/g3job1/stamps.txt` copied to `stamps.txt`)

[STAMPS]

## 7. What I did not do

- M5 and M6 were not started: the 80-minute budget ran out after M1-M4 (confirmed; M4 itself was
  cut at its deadline). The three controls' first runs lost their stdout to a terminal pipe; I
  re-ran all three with the same seeds after the matches (identical deterministic results — see
  §3) so that raw output files exist for every result.
- I did not run any strength test other than the prescribed matches; no SPRT, no adjudication
  (none was allowed), no repeat of another helper's work.
- I did not commit the PGN files (rule: text-only evidence; per-game line files instead), the
  engine build directory, or the 1.24 MB c3.log (extracted proof lines instead).
- I did not verify the engine's correctness beyond what the job asked (no perft suite, no ctest);
  Step 0's perft 5 was the only correctness check.
- fastchess's ± error: I checked its source (I had the clone): `app/src/matchmaking/elo/elo.hpp`
  line 30 defines `CI95ZSCORE = 1.959963984540054` and `app/src/matchmaking/elo/elo_wdl.cpp`
  lines 14-22 build the interval as score ± z·sqrt(variance/games) and report half its Elo width.
  So fastchess's ± IS a 95 % interval, computed from per-game scores; mine is the same 95 % rule
  on PAIR scores (the job's prescription). They agreed numerically on C2 (±31.61 vs ±31.7) and
  M1 (±8.44 vs ±8.7).

## 8. What I am not sure about

- [M2PLUS] The B4-vs-base figure is one seed, one book, one node level (20000), one machine. The
  pair interval covers sampling noise only; it says nothing about book or node-level bias.
- M4 was cut at [M4G] games; its interval is wide and its LOS is weak evidence on its own. I
  treat it as directional only.
- The control-1 pair check proves determinism of the *whole pipeline* (fastchess scheduling +
  engine) only at 20000 nodes with these options; I did not probe other node counts.
- My per-game parser reads the PGN headers and counts a game finished when the PGN holds it with
  a decisive/draw result; I compared its W-L-D against fastchess's own results block on M1
  (3202 vs 3272 games — the block is a mid-interrupt snapshot, 70 games finished during the
  SIGINT grace period) and on C2 (exact agreement: 179/30/91), and found no contradiction, but
  the parser is my own code and could still mis-read a malformed PGN line.
- The bench numbers reproduce the BUNDLES.md box exactly despite a different CPU and compiler
  minor version (13.3 vs 14); node counts are FP-deterministic by design (`-ffp-contract=off`),
  so I believe the comparison, but I did not prove that a *different* `-march` would not change
  them (I used the box's `-march=x86-64-v3`; my CPU has AVX2/AVX512).

## 9. A better way

1. **Let the script do the rounds arithmetic.** The form's `-rounds <games/2>` is one hand-typed
   division per match, and mine slipped on M1 (3000 instead of 1500 — fastchess scheduled 6000
   games and my deadline cut the surplus). `run_match.sh` should take the *game count* and
   compute `-rounds $((GAMES/2))` itself, so the slip cannot recur. Cost of the slip here: none
   for the conclusion (3272 ≥ 3000 finished games; both subsets reported), but a different
   deadline could have cut below the prescribed count.
2. **Locate fastchess's final results block mechanically.** With `-ratinginterval 100` fastchess
   prints a results block every ~200 games; I first quoted the 200-game block of M1 as if it were
   final. The final block is the one adjacent to `Finished match`; and since the interrupt grace
   period lets further games finish *after* it (70 in M1), my per-game file — not any printed
   block — is the authoritative count. Any consumer of these reports should read the per-game
   files and treat printed blocks as fastchess's own view only.
3. **Size the matches from a measured pair variance, not from the Bernoulli guess.** The slope of
   the Elo conversion at score s is (400/ln10)/(s(1−s)) Elo per unit score (694.8 at s=0.5,
   926 at s=0.75). The naive sizing guess — pair scores Bernoulli, variance 0.25 — predicted
   ±17.6 Elo for M1's 1500 pairs, but M1 realized ±8.7: paired games correlate strongly, the
   measured pair-score variance is only ~0.06 (C2: 0.0459 at 150 pairs; M1: 0.0609-0.0614 at
   1500-1637 pairs, both consistent). Sizing rule with that variance: n_pairs ≈ (694.8·1.96)²·v/d²
   ≈ 111,000·v/d² at v≈0.06 near s=0.5 — e.g. ±9 Elo needs ~1470 pairs, exactly what M1's
   interval realized, and ±5 Elo would need ~8900 games, which shows up front that a 2000-game
   match can only bound a small effect to ~±10. How to check it is better: run one short pilot,
   take its pair variance, predict the half-width of the next match, compare with the realized
   one (C2 -> M1 prediction: 694.8·1.96·sqrt(0.0459/1500) = 7.6 vs realized 8.7 — right size,
   and the Bernoulli guess was 2× off).

## 10. Model name and version

GLM 5.3 Flash (glm-5.3-flash), as named for this session ("Your name in this work is: glmflash3");
I know no more precise version string from inside the session.

## Questions for Fable

1. M1 finished 3272 games where 3000 were prescribed (my rounds slip + deadline cut the surplus).
   I report the prescribed-3000 subset as primary and the full set as a cross-check. If you prefer
   cut matches to be capped exactly at the prescription, say so and I will do that from job 2 on.
2. If the Step-0 node counts are accepted as enough to deprioritize B2/B3 (−18 %/−32 % nodes at
   bench 13), the cut M4 could be skipped in a re-run and its slot given to M5/M6. Your call; I
   followed the prescribed order.
3. My runner script computes deadline/rounds from the game count now (see "A better way" 1).
   If you want the exact per-match deadlines I used, they are in stamps.txt (START/END lines).
