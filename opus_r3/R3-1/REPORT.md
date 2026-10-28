# R3-1 Integration stack (opus-r3-stack) — IN PROGRESS

Branch `opus-r3-stack` = `d4f4312` + one merge commit per feature branch (see `git log --first-parent`). Machine
exclusive: no (gates, self-play and NNUE training ran throughout; my builds and checks at nice 19). No Elo claims.

## Acceptance

| line | result | evidence |
|---|---|---|
| all passed O/C/opus-sol features merged | O1, O1-LTT, O2, O3, O4, O5, O6, O7, O8, C1, C2, C3, C4, C5, C6; opus-sol S04fix*, S08fix, S11, S12, S13, S14, S29, S32*, S37*, S41, A1, S-A2*, S-A4*, S-IT (* = being ported on `opus-r3-port-b` / `opus-r3-port-c`) | `git log --first-parent opus-r3-stack` |
| each behind its own option, default OFF | runtime options (UCI) and build switches, list below; every default is off | `src/uci.cpp`, `CMakeLists.txt` |
| conflicts resolved cleanly | every merge commit message states how; unified search instances, NNUE v2 rules, O2 switch (below) | merge commits |
| all OFF = bench 312866/862329/3024920/12389307/34048354, perft5 4865609 | ALL OK after every merge (d11/13/16 + perft + kiwipete) and full (d20/d22) at the switch checkpoints; every switch-off exe byte-identical to the previous stack exe except the PE timestamp | `logs/identity_after_each_merge.log`, `logs/build_after_each_merge.log` |
| each option ON reproduces its branch | all recorded ON pins match: CorrMargins, CorrExt, CuckooRep, HistRework 1/2/3, NNUE smoke nets of C5 (ob8, kb4+ob8), O6 threats, O7 pawn pairs, O4 pure; options without recorded pins match their branch exe: CorrHistPlus 1/2/4/7, NetScale 90/110, Syzygy (3-4-5 tables), LocklessTT@T1; node-exact switches stay at the lock pins ON (MaterialKeyTable, FORGE_SPEEDSTACK to d22, TtChildPrefetch, NnueLazyAcc to d20, FORGE_PROF to d22, FORGE_NNUE_O2, FORGE_NOZERO_MOVE_BUFFERS) | `logs/nnue_branch_pins_summary.txt`, `logs/branch_crosscheck_9588a109.log`, merge commit messages |
| CMake + CTest | all targets build; full CTest: only the 4 known `forge_tests` lines fail (known-failure check PASS) in the default and the FORGE_PROF + FORGE_NNUE_LAZY_ACC configurations | `logs/ctest_stack_9588a109*.log*` |
| GitHub CI (release, ASan+UBSan, TSan) | see OPUS_R3_REPORT.md (run table) | `gh run list --branch opus-r3-stack` |
| 500 fast self-games per option ON alone and all ON: no crash, no illegal move, no double bestmove | running on `opus-r3-selfplay` (checker + runs) | pending |

## Options in the stack (all default OFF)
- Runtime (UCI): SmpExactNodes, SmpBestThread, LocklessTT (O1/O1-LTT); SyzygyPath (+ SyzygyProbeDepth,
  Syzygy50MoveRule) (C1); CorrHistPlus (C2); HardDeadline (C3); NNUEFile + NNUEKingBuckets (C4), NNUEOutputBuckets
  (C5), PureNnue (O4), NNUEThreats (O6), NNUEPawnPairs (O7); CorrMargins (O5); CorrExt (O8); CuckooRep (C6);
  MaterialKeyTable (S11); NetScale (S41, default 100 = off); HistRework (A1); IntendedThreefold (S-IT);
  TtChildPrefetch (S13, needs its build switch); NnueLazyAcc (S12, needs its build switch); Profile (S08fix, needs
  FORGE_PROF).
- Build switches: FORGE_NNUE_O2 (O2, new in R3), FORGE_NOZERO_MOVE_BUFFERS (S14), FORGE_S13_TT_CHILD_PREFETCH (S13),
  FORGE_SPEEDSTACK (S29), FORGE_NNUE_LAZY_ACC (S12), FORGE_PROF (S08fix).

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
- CI run 40564150654 failed: two opus-sol tests (S-IT, A1) used the pre-O3 member names; my per-merge checks used
  the PC build of the engine only. Fixed in `2432670` (`opus-r3-cifix`, green 40565363595); since then every push
  is preceded by a full local CMake build and the full CTest list.
- S41 NetScale scales the compiled-in network only (as on its branch); v2 nets are not scaled.
- IntendedThreefold leaves bench unchanged (no claimable history in the bench positions); its behaviour is covered
  by forge_intended_threefold_tests and uci_regression.

## Left / UNVERIFIED
- Ports S32/S37/S04fix and S-A2/S-A4 (agents), then final identity, CTest and CI on the final head.
- Self-play evidence (500 games per option and all ON) on the final head.
