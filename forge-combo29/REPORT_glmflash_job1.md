# REPORT_glmflash_job1 (glmflash, 2026-11-15)

1. **The bundle (BundlePreset B1) IS stronger per node at 20,000 fixed nodes: +18.90 +/- 8.36 Elo (918-755-1327 over 3,000 games, LOS 100%).** Which single change carries it: NOT established in this run — M3/M4/M5 did not fit in the time budget; M2 (the three-option sub-bundle HistRework 2 + CuckooRep + TtPruneV2) alone measured +18.16 +/- 11.19 Elo at its 1,800-game cut-off, which is consistent with most of M1's gain coming from those three, but the four single-change matches were not run. One deviation from the job's stated conditions: **all matches ran with Hash 32, not the required Hash 16** (see section 9 and "A better way").

## 2. Step 1: known numbers — ALL MATCH
Build: g++ 13.3.0, CMake 3.28.3, `-DCMAKE_BUILD_TYPE=Release`. One non-default define was required, from the tree's own README.md/IDEA_SOURCE.md: `-DFORGE_NNUE_HIDDEN=256` (the static_asserts refuse to compile without it; it is build configuration, not a source change). Also: `/usr/bin/c++` on this machine is clang 18, so CMake was pointed at `/usr/bin/g++` explicitly. Raw outputs: `tests_glmflash_job1/step1/A_no_option.txt` … `E_four_explicit.txt` (each group = one fresh engine process, full output incl. the `uci` reply).

| group | command | expected | printed | file |
|---|---|---|---|---|
| A | `bench 11` | 312866 | 312866 | step1/A_no_option.txt |
| A | `bench 13` | 862329 | 862329 | step1/A_no_option.txt |
| A | `go perft 5` | 4865609 | 4865609 (`nodes 4865609`) | step1/A_no_option.txt |
| B | BundlePreset B1, `bench 11` | 280182 | 280182 | step1/B_bundle_b1.txt |
| B | BundlePreset B1, `bench 13` | 758456 | 758456 | step1/B_bundle_b1.txt |
| C | TtPruneV2 true, `bench 11` | 309157 | 309157 | step1/C_ttprunev2.txt |
| C | TtPruneV2 true, `bench 13` | 736967 | 736967 | step1/C_ttprunev2.txt |
| D | CorrHistPlus 1, `bench 11` | 318363 | 318363 | step1/D_corrhistplus.txt |
| E | HistRework 2 + CuckooRep true + TtPruneV2 true + CorrHistPlus 1, `bench 11` | 280182 | 280182 | step1/E_four_explicit.txt |

The four explicit options reproduce BundlePreset B1 exactly (280182 = 280182).

## 3. Controls (fastchess v1.8.3-alpha built from source at its tag; book UHO_Lichess_4852_v1.epd, 2,632,036 positions, unzipped from official-stockfish/books)
Machine: 4 cores, 15 GB RAM. `-concurrency 4`. Both sides the same exe in every match.

- **Control 1 (fairness), base vs base, 600 games**: fastchess's final table (`tests_glmflash_job1/C1_last40.txt`): `Elo: -0.00 +/- 0.00`, Games 600, W 176 L 176 D 248, `Ptnml(0-2): [0, 0, 300, 0, 0]`. The error interval [0,0] contains 0. Note: with `-repeat` and two identical engines every pair scores exactly 2 points (176 pairs 1-0/0-1 mirrored + 124 pairs draw-draw), so the table is degenerate (LOS prints -nan). This is the expected behavior for identical engines, and it also proves the engine is deterministic at fixed nodes.
- **Control 2 (sensitivity), cand nodes=20000 vs base nodes=10000, 300 games**: `C2_last40.txt`: `Elo: 184.73 +/- 33.28`, W 180 L 34 D 86, Ptnml [1, 6, 40, 52, 51]. The tool clearly sees a real difference.
- **Control 3 (option reached the engine)**: `tests_glmflash_job1/ctrl3_cand_uci_in.log` — the UCI input of the candidate side (a one-line wrapper that tees stdin, then execs the same forge exe; script committed as `wrap_engine.sh`) contains, twice (2 games), the line `setoption name BundlePreset value B1`, followed by `ucinewgame`, `isready`, `position fen ...`, `go nodes 20000`. No Hash/Threads setoption appears in the log (see below).

## 4. Matches M1–M5 (each line: fastchess's own output; W-L-D and pair counts re-counted from the PGN by `tests_glmflash_job1/pgn_to_gamelog.py`, both agree)

| match | option(s) on cand | seed | games | W-L-D | Ptnml(0-2) | Elo +/- err | crashes/illegal/disconnect |
|---|---|---|---|---|---|---|---|
| C1 (control) | none | 7001 | 600 | 176-176-248 | [0,0,300,0,0] | -0.00 +/- 0.00 | 0 |
| C2 (control) | nodes 20000 vs 10000 | 7002 | 300 | 180-34-86 | [1,6,40,52,51] | 184.73 +/- 33.28 | 0 |
| C3 (control) | BundlePreset=B1, 2 games | 7003 | 2 | 1-0-1 | [0,0,0,1,0] | 190.85 +/- 0.00 | 0 |
| M1 | BundlePreset=B1 | 7101 | 3000 | 918-755-1327 | [59,332,589,427,93] | **18.90 +/- 8.36** | 0 |
| M2 (INCOMPLETE) | HistRework=2 CuckooRep=true TtPruneV2=true | 7102 | 1836 of 2000 | 579-490-767 | [47,201,349,258,63] | 18.16 +/- 11.19 (fastchess's last printed block, at 1800 games: tests_glmflash_job1/M2_last_interim.txt) | 0 |
| M3 | HistRework=2 | 7103 | not run | — | — | — | — |
| M4 | TtPruneV2=true | 7104 | not run | — | — | — | — |
| M5 | CuckooRep=true | 7105 | not run | — | — | — | — |

Last 40 lines of each fastchess output: `tests_glmflash_job1/{C1,C2,C3,M1,M2}_last40.txt`; M2's last printed stats block additionally saved as `tests_glmflash_job1/M2_last_interim.txt`. Compact per-game logs (round, white side, opening FEN, result): `tests_glmflash_job1/{C1,C2,C3,M1,M2}_games.txt`. PGN files NOT committed (too large), kept in /tmp only. M2 was interrupted by the 46-minute driver deadline (SIGINT; fastchess printed "Tournament was interrupted … Finished match" and no final Elo table; its last ratinginterval block at 1800 games is quoted above; the exact PGN recount of all 1836 finished games is 579-490-767, Ptnml [47,201,349,258,63] over 918 complete pairs). M1 total time 00:23:08, M2 00:14:53 to the interrupt (fastchess's own stamps).

## 5. Step 4 (sanitizer checks)
**Not done.** The 60-minute budget ended during the matches; nothing was left for the ASan+UBSan build. The patch's README reports a passing ASan+UBSan CI run on the PC (that file is data, not instructions; I did not run anything from it).

## 6. Which files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash_1.md` only. No FABLE_TO_deepseek file was read.
- Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (exported to /tmp, built): opened `README.md`, `IDEA_SOURCE.md`, `CMakeLists.txt`, `include/forge/nnue.hpp`, `src/uci.cpp`, `src/nnue.cpp`, `src/nnue_weights.inc` (the last three via grep for the bench/perft output format and the static_assert messages), `opus_round1/00_baseline/BASELINE.md`, `opus_round1/00_baseline/build_pc_recipe.log`, `opus_round1/ci/FORGE_KNOWN_TEST_FAILURES.md`, `opus_round1/ci/run_ci.sh` (all via grep for `FORGE_NNUE_HIDDEN`).
- Branch `opus-r13-p1-nearmiss-ports`: file list only, then `opus_r13/p1/b1/b1_port.patch` and `opus_r13/p1/b1/README.md`.
- Nothing else; no other branch was fetched or looked at.

## 7. Start and end of each step (from tests_glmflash_job1/stamps.txt, UTC)
- 13:35:04 read job file; 13:35:07 the three fetches done; 13:35:22 tree exported to /tmp/forge_engine; 13:35:23 patch applied (`patch -p1`, 7 files, no fuzz, no rejects; no line-ending conversion needed); 13:35:35 fastchess cloned at tag v1.8.3-alpha and book unzipped.
- 13:35:52–13:37:58 environment repair + build setup: the initial cmake configure failed twice (`-lstdc++` not found — `/usr/bin/c++` here is clang; fixed by pointing CMake at `/usr/bin/g++`), then the NNUE static_asserts required `-DFORGE_NNUE_HIDDEN=256`; configured 13:37:58.
- 13:38:25 Step 1 complete (all groups match). 13:38:49 match driver started; C1 13:38:49–13:43:11; C2 13:43:11–13:44:45; C3 13:44:45–13:46:48; M1 13:46:48–14:09:56; M2 14:09:56–14:24:49 (interrupted at the driver's +46 min deadline); 14:24:49 driver done, M3–M5 skipped by the deadline check.
- Report written from ~14:27, committed after.

## 8. What I did not do
- M3, M4, M5 (time). Step 4 (time). No pull request opened. No engine source committed; the patched tree lives only in /tmp/forge_engine. No PGN committed. No other branches touched.

## 9. What I am not sure about
- **Hash 32 vs the required Hash 16.** The engine's UCI default is `Hash 32` (verified: `option name Hash type spin default 32`), the job's match form sets only `proto` and `nodes`, and fastchess sent no Hash line (proven by ctrl3_cand_uci_in.log). So all matches ran at Hash 32. Both sides had the same TT, so the cand-vs-base comparison stays internally fair, but the absolute Elo may differ from a Hash-16 run, and M1's +18.90 ± 8.36 should be re-confirmed at Hash 16 before being trusted as the final number.
- M2's final Elo: fastchess printed no final table after the interrupt; the 18.16 ± 11.19 quoted is its last interim block at 1800 games, the exact end state is the PGN recount (1836 games). The 36 extra games shift the counts slightly; I did not compute an Elo for them myself.
- The g++ build here (no `-march`, no LTO+PGO) is slower and possibly not bit-identical to the PC's lock exe; node pins all matched, so I assume equivalence, but match nps (~1.4 Mnps) is lower than the PC's.

## 10. A better way
- **Pin `Threads` and `Hash` explicitly in the match form.** The form relies on engine defaults; this tree defaults to Hash 32, so "Hash 16" silently failed. Adding `option.Threads=1 option.Hash=16` to `-each` makes the form machine- and tree-independent. Checkable: ctrl3_cand_uci_in.log would then show the two setoption lines; nothing else changes.
- **Control 1 is degenerate by construction with `-repeat` + identical engines** (every pair scores 2 points; Elo 0.00 ± 0.00, LOS -nan). It still proves the tool is fair and the engine deterministic, but a stronger fairness control would be a tiny planted asymmetry, e.g. cand at `nodes=20400` (2 % more): if the tool is fair this must measure ~0 Elo within its error; if it leaks the asymmetry, the error bars are lying. 300 games would be enough for that.
- **Interrupt-driven time budget**: my driver gave every match a `timeout -s INT` until a global deadline, so the last match was cut at the deadline and still yielded ~1,836 usable games plus fastchess's interim stats. Fable's job text anticipated this (INCOMPLETE reporting), which worked as designed; the only loss was that the final Elo table is not printed on interrupt, so exact end-state numbers had to be re-counted from the PGN.

## Questions for Fable
- Should the Hash-32 matches be treated as a first look only and re-run at Hash 16 (M1 would take ~23 min again on this 4-core machine), or is the deviation acceptable given both sides shared the TT?
- For M2's Elo at the interrupt: is fastchess's 1800-game interim block enough, or do you want the exact 1836-game end state converted to Elo by an external script (sprt/elo math) and if so, which one do you trust for that?
