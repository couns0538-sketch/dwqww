# OPUS R3 report (job pack R3, Forge AL1 s198) — IN PROGRESS

Branch `opus-r3-stack` (base `d4f4312`). Machine exclusive: no (gates, self-play and NNUE training ran
throughout; my work at nice 19). No Elo claims: no gate was run.

## Status

| job | state | where |
|---|---|---|
| R3-1 integration stack | all O/C branches and every opus-sol engine feature merged (S32/S37/S04fix via `opus-r3-port-b`, S-A2/S-A4 via `opus-r3-port-c`); HardDeadline defect found by the self-play checker fixed; 500-game self-play runs on the final head in progress (`opus-r3-selfplay`) | `opus-r3-stack`, `opus_r3/R3-1/` |
| R3-2 interaction matrix | IN PROGRESS (agent) | `opus-r3-matrix` |
| R3-3 gate proposals | IN PROGRESS (agent) | `opus-r3-gates`, `F:\opus_scratch\r3\GATE_PROPOSALS.md` |
| R3-4 SPSA tool | IN PROGRESS (agent) | `opus-r3-spsa` |
| R3-5 regression test suite | IN PROGRESS (agent) | `opus-r3-tests` |
| R3-6 Lazy SMP scaling | IN PROGRESS (agent) | `opus-r3-smp` |

## CI (GitHub `opus-ci`: release, ASan+UBSan, TSan)
| run | head | result |
|---|---|---|
| 40561969912 | `c82ccbd` (all O/C merges) | success (release 3m34s, TSan 19m13s, ASan 4m27s) |
| 40564150654 | `467a59b` (+ S14, S13, S11, S29, S41, A1, S-IT) | **failure**: two tests (S-IT, A1) still used the pre-O3 member names; caught only by the CMake build, which I had not run locally |
| 40565363595 | `2432670` (`opus-r3-cifix`: the fix on top of `467a59b`) | success (11m38s) |
| 40566615160 | `7b431d4` (+ S12, the fix, a CMake endif fix) | success (20m13s) |
| 40568162589 | `2047348` (+ S08fix, evidence) | success (19m29s) |
| 40568260400 | `opus-r3-port-b` `a06b00d` (S32, S37, S04fix on `2432670`) | success |
| 40570018288 | `opus-r3-port-c` (S-A2 behind FORGE_NNUE_INT16, S-A4 on `2432670`) | release + ASan success, TSan running |
Since the failure every push is preceded by a full local CMake build of all targets and the full CTest list (only
the 4 known `forge_tests` lines may fail; `check_known_failures.py` PASS), and every run is followed to green.

## R3-1 so far (logs: `opus_r3/R3-1/logs/`, scratch `F:\opus_scratch\r3\logs`)
- Base: `d4f4312` fast-forwarded to `opus-O3` (`c7eb247`: the no-op module split every O/C branch is built on,
  plus the CI baseline `0d99f02`). Then one merge commit per branch: O1-LTT (contains O1), C1, C2, C3, O7 (contains
  C4 and O6), C5, O4, O5, O8, C6, O2, the evidence-only heads of O1 and O6, then the opus-sol features S14, S13,
  S11, S29, S41, A1, S-IT, S12, S08fix (ported from the single-file search.cpp onto the module layout:
  `opus_r3/R3-1/tools/port_search_hunks.py` places each hunk whose exact context exists in one module file, the
  rest by hand; every merge commit message lists what went where).
- After every merge: PC-recipe build (0 warnings, FMA 0) and bench d11/13/16 + perft5 + kiwipete = lock: ALL OK;
  for every build switch the switch-off exe is byte-identical to the previous stack exe (PE timestamp aside).
- Each feature's ON behaviour was checked against its branch where the branch recorded numbers:
  CorrMargins d11 343365 d13 858019 d16 2522546 d20 12894582; CorrExt 312961 / 838790 / 2891507 / 12313394;
  CuckooRep 324211 / 790682 / 3148570; HistRework=1 373261 / 1043893 / 3399770, =2 320427 / 881902 / 3041041;
  node-exact features stay at the lock pins when ON (MaterialKeyTable, FORGE_SPEEDSTACK to d22, TtChildPrefetch,
  NnueLazyAcc to d20, FORGE_PROF to d22, FORGE_NNUE_O2, FORGE_NOZERO_MOVE_BUFFERS).
- Semantic merges: (1) one selection / fail-loud rule for the five NNUE v2 options (C4, C5, O4, O6, O7; each
  branch's test phrases kept); (2) one search instance per combination of CorrMargins x CorrExt x CuckooRep (8
  alpha-beta + 2 quiescence instances; a single option runs its branch's code); (3) O2 behind the new build switch
  `FORGE_NNUE_O2` (off: token-identical preprocessed nnue.cpp and byte-identical exe vs. the pre-O2 stack);
  (4) A1's joint correction also in C2's cold CorrHistPlus path, so the two combine.

## Left
- R3-1: merge port-b / port-c, final identity + CMake/CTest + CI, self-play evidence on the final head.
- R3-2 .. R3-6: agents running; results to be merged and summarised here.
