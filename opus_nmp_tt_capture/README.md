# opus_nmp_tt_capture - NmpTtCaptureMin (deep-research card T04E-02), gate-ready, default OFF

## What it is
No null move when the TT move is a real capture of a valuable piece. The term is appended last to the NMP condition
(trial_w6 `src/search.cpp:1181-1184`, the spec's lock lines :965-968), so it is evaluated only where NMP would otherwise
run. Runtime 0 is off.
- `NmpTtCaptureMin` N > 0 (form A, the gate ON form, N = 4 = rook or queen) blocks NMP when the victim's piece type is
  >= N.
- `NmpTtCaptureSee` S > 0 (variant B, not gated by this job) blocks NMP when `see_ge(tt_move, S)` holds.
- When both are > 0, either one blocks.
- `tt_move` is not validated before NMP in the lock (a colliding TT entry can carry another position's move). So the block
  first runs the lock's own `board.is_pseudo_legal(tt_move)`, the MovePicker's test. It reads the victim
  (`captured_piece`) or calls `see_ge` only after that test passes.
- `plausible` = `tt_capture && is_pseudo_legal(tt_move)` is computed only after a `> 0` test, and at most once per node.
- En-passant victims are pawns (type 1), below every start value.
- A blocked node goes on to ProbCut and the move loop, with the TT move first.

## Switches
- Compile macro `FORGE_NMP_TT_CAPTURE_MIN` (search.hpp, default 0). At 0 the original `if` is kept verbatim in `#else`, so
  the identity exe is the live lock trial_w6 4181A589 byte for byte.
- At 1 the source adds:
  - the `tune::` ints `NmpTtCaptureMin = 0` and `NmpTtCaptureSee = 0`, with their externs;
  - the `parameters()` rows `{"NmpTtCaptureMin", &NmpTtCaptureMin, 0, 5}` and `{"NmpTtCaptureSee", &NmpTtCaptureSee, 0, 900}`;
  - a local lambda `nmp_tt_capture_block` and the guarded copy of the NMP `if`.
- No other option or switch is touched. NmpCutOnly, HistoryLmp, TtMoveHistLmr, FracLmr, HindsightDepth and SingularNonCut
  are not in this tree. The six trial_w6 switches stay as `opus_speed/patches/trial_w6.patch` sets them.

## Files
| file | what |
|---|---|
| `nmp_tt_capture_after_w6.patch` | the change vs the trial_w6 source (5 hunks, search.hpp + search.cpp) |
| `nmp_tt_capture_stack.patch` | lock source -> this tree (trial_w6.patch + the change) |
| `tools/port_controls.sh` | makes the identity copy (`ntc_id`: the six flipped, macro 0) and the gate copy (`ntc_gate`: + macro 1) |
| `IDEA_SOURCE.md` | the sources of the idea (ideas only; no licence at the Reckless merge commit) |
| `BENCH.md` | identity, gate OFF and ON numbers |
| `STATUS.md` | done / in progress / next step / resume / unproven |
| `logs/` | build summaries, bitexact logs |

## Exes (on F:, not in git)
- Identity: `F:\ospd\nmp_tt_capture\build\ntc_id_lp_v1\src_copy\forge_lp_v1.exe`, sha256 = trial_w6 (see BENCH.md).
- Gate: `F:\ospd\nmp_tt_capture\pack\forge_nmp_tt_capture_gate_1c6e105e.exe`, sha256 `1c6e105ee74ff31b1343307b320dc88b48cef6faa2879bdf97f9be43c3feaa87`, pc1 = pc2.

## Gate line (for QA / Strength after Code Review; nothing is queued by this job)
```
cand: forge_nmp_tt_capture_gate_1c6e105e.exe   setoption name NmpTtCaptureMin value 4
base: trial_w6  sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0
```
- Spec crew line: SPRT [0,5] normalized Elo, UHO book, Threads 1, STC first.
- Variant B (`setoption name NmpTtCaptureSee value 300`, with NmpTtCaptureMin at 0) is run only after A ends H0 or capped
  <= 0.
- Bounds, TC, book and cap are QA's decision. This job starts no gate or SPRT.

## Notes for Code Review
- 5 hunks, all behind `#if FORGE_NMP_TT_CAPTURE_MIN`.
- The lambda captures by reference and is called only as the last `&&` term.
- At runtime 0 / 0, the lambda's first line returns false, so the term is constant true and reads nothing.
- Blocking only removes null searches. It adds no new zugzwang exposure.
- `null_tries_` counts only the NMP searches that still run.
- The PGO profile is trained with the options at 0, so the ON path is cold-optimised. ON nps was not measured.
- Every review so far is the author's own (NOT independent).

## Rebuild
1. Copy `F:\ospd\src\lock`; it must pass `sha256sum -c lock_SOURCES.sha256` from inside the folder.
2. `patch -p1 -F0 < opus_nmp_tt_capture/nmp_tt_capture_stack.patch` gives tree `ntc`.
3. `bash opus_nmp_tt_capture/tools/port_controls.sh <src folder> ntc FORGE_NMP_TT_CAPTURE_MIN`.
4. Build with `build_variants.ps1 ... -Twice` from Git Bash, as in the other packs.
