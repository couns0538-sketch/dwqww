# R3-1 Integration stack (opus-r3-stack) — IN PROGRESS

Branch `opus-r3-stack` = `d4f4312` + one merge commit per feature branch (see `git log --first-parent`). Machine
exclusive: no (gates, self-play and NNUE training ran throughout; my builds and checks at nice 19). No Elo claims.

## Acceptance

| line | result | evidence |
|---|---|---|
| all passed O/C/opus-sol features merged | O1, O1-LTT, O2, O3, O4, O5, O6, O7, O8, C1, C2, C3, C4, C5, C6; opus-sol S04fix, S08fix, S11, S12, S13, S14, S29, S32, S37, S41, A1, S-A2, S-A4, S-IT (S32/S37/S04fix ported on `opus-r3-port-b`, S-A2/S-A4 on `opus-r3-port-c`, both merged); then the R3 jobs: R3-5 tests (`2afd036`), R3-2 tools (`7e0660a`), R3-6 SmpHelpersPastDepth (`1f354cc`), R3-4 tunables + SPSA tool (`064af73`) | `git log --first-parent opus-r3-stack` |
| each behind its own option, default OFF | runtime options (UCI) and build switches, list below and in `OPTIONS.md`; every default is off; the 20 R3-4 spins default to the AL1 s198 values | `src/uci.cpp`, `CMakeLists.txt` |
| conflicts resolved cleanly | every merge commit message states how; unified search instances, NNUE v2 rules, O2 switch (below) | merge commits |
| all OFF = bench 312866/862329/3024920/12389307/34048354, perft5 4865609 | ALL OK after every merge (d11/13/16 + perft + kiwipete) and full (d20/d22) at the switch checkpoints; every switch-off exe byte-identical to the previous stack exe except the PE timestamp | `logs/identity_after_each_merge.log`, `logs/build_after_each_merge.log` |
| each option ON reproduces its branch | all recorded ON pins match: CorrMargins, CorrExt, CuckooRep, HistRework 1/2/3, NNUE smoke nets of C5 (ob8, kb4+ob8), O6 threats, O7 pawn pairs, O4 pure; options without recorded pins match their branch exe: CorrHistPlus 1/2/4/7, NetScale 90/110, Syzygy (3-4-5 tables), LocklessTT@T1; NnueInt16 (switch FORGE_NNUE_INT16) reproduces S-A2's ON pins d11 330610 d13 858175 d16 2760596 d20 9564588; node-exact switches stay at the lock pins ON (MaterialKeyTable, FORGE_SPEEDSTACK to d22, TtChildPrefetch, NnueLazyAcc to d20, FORGE_PROF to d22, FORGE_NNUE_O2, FORGE_NOZERO_MOVE_BUFFERS) | `logs/nnue_branch_pins_summary.txt`, `logs/branch_crosscheck_9588a109.log`, merge commit messages |
| CMake + CTest | all targets build; full CTest: only the 4 known `forge_tests` lines fail (known-failure check PASS): `9588a10` default (37 tests) and FORGE_PROF + FORGE_NNUE_LAZY_ACC (40); `d5023654` (port merges) default (45); `5792074` (HardDeadline fix) default (45, incl. the extended hard_deadline_regression); every switch at once (O2, NOZERO, TT prefetch, SPEEDSTACK, LAZY_ACC, PROF, INT16, DATAGEN, ATTACKS_INIT_ONCE) builds with 0 warnings, FMA 0 and passes uci_check --full | `logs/ctest_stack_*.log*` |
| GitHub CI (release, ASan+UBSan, TSan) | see OPUS_R3_REPORT.md (run table) | `gh run list --branch opus-r3-stack` |
| 500 fast self-games per option ON alone and all ON: no crash, no illegal move, no double bestmove | running on `opus-r3-selfplay` (checker + runs) | pending |

## Options in the stack (all default OFF)
- Runtime (UCI): SmpExactNodes, SmpBestThread, LocklessTT (O1/O1-LTT); SyzygyPath (+ SyzygyProbeDepth,
  Syzygy50MoveRule) (C1); CorrHistPlus (C2); HardDeadline (C3); NNUEFile + NNUEKingBuckets (C4), NNUEOutputBuckets
  (C5), PureNnue (O4), NNUEThreats (O6), NNUEPawnPairs (O7); CorrMargins (O5); CorrExt (O8); CuckooRep (C6);
  MaterialKeyTable (S11); NetScale (S41, default 100 = off); HistRework (A1); IntendedThreefold (S-IT);
  TtChildPrefetch (S13, needs its build switch); NnueLazyAcc (S12, needs its build switch); Profile (S08fix, needs
  FORGE_PROF); SmpHelpersPastDepth (R3-6); 20 search-constant spins for SPSA (R3-4, defaults = AL1 s198 values).
- Build switches: FORGE_NNUE_O2 (O2, new in R3), FORGE_NOZERO_MOVE_BUFFERS (S14), FORGE_S13_TT_CHILD_PREFETCH (S13),
  FORGE_SPEEDSTACK (S29), FORGE_NNUE_LAZY_ACC (S12), FORGE_PROF (S08fix), FORGE_NNUE_INT16 (S-A2; + UCI NnueInt16; a
  build switch in the stack because the always-compiled option cost 0.4-0.5% NPS with the option off),
  FORGE_DATAGEN (S32, `forge datagen`), FORGE_ATTACKS_INIT_ONCE (S04fix), FORGE_NNUE_WEIGHTS + FORGE_NNUE_HIDDEN (S-A4
  H512); S37 adds the forge_nnue_microbench tool target.

## How the conflicts were resolved (details in each merge commit)
- **Search instances.** O5 (CorrMargins), O8 (CorrExt) and C6 (CuckooRep) each compiled their own copy of
  alphabeta.inc with a different macro scheme. The stack has one scheme (FORGE_SEARCH_FN / _CALL,
  FORGE_QSEARCH_CALL, FORGE_LMP_THRESHOLD, FORGE_SEARCH_CORR_MARGINS, FORGE_SEARCH_CORR_EXT) and one instance per
  combination of the three options (8 alpha-beta + 2 quiescence; cuckoo.inc defines a repetition-bound wrapper per
  CuckooRep instance). The root picks the instance once per iteration. A single option runs its branch's code.
- **NNUE v2 options.** C5 (output buckets) and O6/O7 (threats, pawn pairs) and O4 (PureNnue) were all built on C4
  and each changed the net selection and the fail-loud rules. The stack has one rule set covering all five
  options; each branch's test phrases are kept; the tools (replica writer, trainer copy, v2_parity) accept the
  flags together.
- **O2.** O2 (bit-identical kernels) had no option; in the stack it is the build switch FORGE_NNUE_O2 (default
  off), generated with `diff -D` and fixed by hand in the preprocessor header. Off: preprocessed nnue.cpp
  token-identical to the pre-O2 file and exe byte-identical; on: token-identical to O2's file, exe byte-identical.
- **A1 + C2.** HistRework's joint correction is also applied in CorrHistPlus's cold twins, so both options combine.
- **opus-sol ports.** The opus-sol branches were written against the single-file search.cpp; their hunks were
  placed into the O3 module files (`tools/port_search_hunks.py` for verbatim context, the rest by hand). Fields
  moved with O3's header split (search_types.hpp, thread_data.hpp, history.hpp).

## Findings
- **HardDeadline (C3) defect, fixed in the stack.** The R3-1 self-play checker (`opus-r3-selfplay`) found search
  output after the watchdog's bestmove: when the watchdog answers a starved go, the stopped search could still
  print an `info depth` line (33 in ~140 all-ON games; in 27 of 33 its PV started with another move than the
  bestmove sent). Exactly one bestmove per go held throughout. Fix `5792074`: `SharedSearchState::output_closed`,
  set by the watchdog under the output mutex right before its bestmove, checked by every search-side output,
  cleared at each go; only the watchdog sets it, so HardDeadline 0 is unchanged. `tools/hard_deadline_regression.py`
  now fails on any info line between a watchdog bestmove and the next readyok: red on the unfixed engine, green on
  the fixed one (200 searches at T1/T2); the agent's repro: 2/200 late lines before, 0/200 after
  (`logs/hard_deadline_late_output_fix.log`).
- NnueLazyAcc (S12) acts on the compiled-in network only: with a v2 net loaded it is set but unused (as on S12).
- CI run 40564150654 failed: two opus-sol tests (S-IT, A1) used the pre-O3 member names; my per-merge checks used
  the PC build of the engine only. Fixed in `2432670` (`opus-r3-cifix`, green 40565363595); since then every push
  is preceded by a full local CMake build and the full CTest list.
- S41 NetScale scales the compiled-in network only (as on its branch); v2 nets are not scaled.
- IntendedThreefold leaves bench unchanged (no claimable history in the bench positions); its behaviour is covered
  by forge_intended_threefold_tests and uci_regression.

## Left / UNVERIFIED
- Final CTest and CI on the final head.
- Self-play evidence (500 games per option and all ON) on the final head.
