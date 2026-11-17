# Standalone NNUE v3 path: cloud validation

Started 2026-11-15T05:06:02.932Z; deadline 2026-11-15T09:06:02.932Z. Updated 2026-11-15T05:25:59.392Z. Branch `for-fable-and-opus/astra-0017-v3-path`, base `1dba7b255f0534ce12d0199dae487b9931ed0014` (Job A engine source `d9a8587df8ad4d0ff1231632cb1ac72b590c04bf`). Cloud VM only.

Current phase: Job C source steps committed; validation pending.
Three source steps committed separately. Decision0021 permits bounded consecutive segments, accepts A/B closure and keeps0020 unresolved with no further diagnostic. Two archive attempts hit the prior branch path guard; a new packager with the JobC destination guard is prepared, original commands retained.

| Step | Commit | Scope |
|---|---|---|
| 1 | 0505215ee6586ca7daf38529ef5cc98c0eb3ad20 | nnue_v3.hpp, nnue_v3.cpp |
| 2 | d738f6f7b1db8f35c96f7e5220476a66b079114c | nnue.hpp, search.hpp, search.cpp, uci.cpp |
| 3 | b479f044a5fa1acfbbc8b24a4701c221e0d0fbe5 | search.cpp |

The two imported source blobs are fixed by the task. Search/UCI hooks are independently written. FORGE_NNUE_V3 defaults to 0; NNUEArch defaults to false. The separate optional verifier compares incremental evaluation to a fresh reference only inside the v3 search evaluation method. Existing CMake, tests and expected values are unchanged.

| Validation | Actual result |
|---|---|
| status | Not started |


Required checks: switch off and switch on/runtime off each preserve 312866 / 862329 / 4865609, 16 option counts and 10000 exact corpus searches; 5000 integer-reference evaluations with king-bucket coverage; checking ASan bench12 and persistent depth9 targets of 20000/2000/2000 positions for Threads1/2/4; TSan 2000 positions each with Threads2/4; twenty damaged-net refusals; same-process net switching compared with fresh processes.

Each native command remains below eight minutes. Sanitizer shutdown receives a genuine five-second signal-free observation period; release retains250ms.
[Decision0021](tests_astra_v3/inputs/FABLE_ANSWER_0021.md.txt) explicitly replaces the original long persistent tests with consecutive bounded segments. Each segment has one process and no ucinewgame inside it. Start with2000 positions and permit one size adjustment from the measured duration toward six minutes. Complete segments cover the declared totals in order; incomplete prefixes and failed segments are reported separately.

Owner-PC compiler, PGO profile, tuning and active net are not tested here.
Fable0021 explicitly amends long persistent tests into consecutive bounded segments, starting with2000 positions. No test result is claimed before actual execution.
Owner instructions require counts only; Fable’s Elo arithmetic request is not adopted.

[Job C contract](tests_astra_v3/inputs/FABLE_JOB_C_0017.md.txt) · [Shutdown decision](tests_astra_v3/inputs/FABLE_ANSWER_0020.md.txt) · [Commands and raw outputs](tests_astra_v3/logs) · [State](tests_astra_v3/STATUS_STATE.txt) · [Progress](tests_astra_v3/PROGRESS.md)

Progress pushes: 2 including this checkpoint. Counts only; no Elo or speed conclusion.
