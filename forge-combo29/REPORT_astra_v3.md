# Standalone NNUE v3 path: cloud validation

Started 2026-11-15T05:06:02.932Z; deadline 2026-11-15T09:06:02.932Z. Updated 2026-11-15T05:14:23.617Z. Branch `for-fable-and-opus/astra-0017-v3-path`, base `1dba7b255f0534ce12d0199dae487b9931ed0014` (Job A engine source `d9a8587df8ad4d0ff1231632cb1ac72b590c04bf`). Cloud VM only.

Current phase: Job C step 2 hooks committed; checking switch pending.
Implementation and validation are in progress; pending work is not a pass.

| Step | Commit | Scope |
|---|---|---|
| 1 | 0505215ee6586ca7daf38529ef5cc98c0eb3ad20 | nnue_v3.hpp, nnue_v3.cpp |
| 2 | d738f6f7b1db8f35c96f7e5220476a66b079114c | nnue.hpp, search.hpp, search.cpp, uci.cpp |

The two imported source blobs are fixed by the task. Search/UCI hooks are independently written. FORGE_NNUE_V3 defaults to 0; NNUEArch defaults to false. The separate optional verifier compares incremental evaluation to a fresh reference only inside the v3 search evaluation method. Existing CMake, tests and expected values are unchanged.

| Validation | Actual result |
|---|---|
| status | Not started |


Required checks: switch off and switch on/runtime off each preserve 312866 / 862329 / 4865609, 16 option counts and 10000 exact corpus searches; 5000 integer-reference evaluations with king-bucket coverage; checking ASan bench12 and persistent depth9 targets of 20000/2000/2000 positions for Threads1/2/4; TSan 2000 positions each with Threads2/4; twenty damaged-net refusals; same-process net switching compared with fresh processes.

Each native command remains below eight minutes. Sanitizer shutdown receives a genuine five-second signal-free observation period; release retains250ms. A bounded persistent attempt that does not reach its target is reported as an incomplete prefix, never replaced by fresh-process aggregation.

The owner-PC compiler, PGO profile, tuning and active net are not tested here.
The single-process target versus eight-minute limit question is pending in coordination0021. Other work proceeds within the existing scope.

[Job C contract](tests_astra_v3/inputs/FABLE_JOB_C_0017.md.txt) · [Shutdown decision](tests_astra_v3/inputs/FABLE_ANSWER_0020.md.txt) · [Commands and raw outputs](tests_astra_v3/logs) · [State](tests_astra_v3/STATUS_STATE.txt) · [Progress](tests_astra_v3/PROGRESS.md)

Progress pushes: 1 including this checkpoint. Counts only; no Elo or speed conclusion.
