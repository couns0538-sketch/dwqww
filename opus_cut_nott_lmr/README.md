# opus_cut_nott_lmr - CutNoTtLmr (deep-research card T04D-01), gate-ready, default OFF

## What it is
One more LMR term. At a cut node with no TT move, a late move is reduced `CutNoTtLmr` more plies. Runtime 0 is off.
- Site: right after the existing cut-node term `if (cut_node) r += 2;`, at trial_w6 `src/search.cpp:1383` (the spec's
  lock line :1141).
- The clamp below it, `std::clamp(new_depth - r, 1, new_depth)`, is unchanged, so the reduced depth stays in
  [1, new_depth].
- IIR stays. A cut node with no TT move at depth >= IirDepth 4, not in check, has already lost one ply there. The new term
  stacks a second ply on each of its late moves, and the spec intends this.
- In the singular verification search, `tt_move` is the excluded TT move (never none), so the term is dead there. It does
  not overlap SingularNonCut.

## Switches
- Compile macro `FORGE_CUT_NO_TT_LMR` (search.hpp, default 0). At 0 the source is the parent's token for token: the
  identity exe is the live lock trial_w6 4181A589 byte for byte.
- At 1 the source adds:
  - one `tune::` int `CutNoTtLmr = 0` and its extern;
  - one `parameters()` row `{"CutNoTtLmr", &CutNoTtLmr, 0, 2}`, so the gate exe advertises
    `option name CutNoTtLmr type spin default 0 min 0 max 2`;
  - the use site.
- No other option or switch is touched. The six trial_w6 switches stay as `opus_speed/patches/trial_w6.patch` sets them.
  The hunt flags (H1-H9, H5 MOVE_STORE32) stay off.

## Files
| file | what |
|---|---|
| `cut_nott_lmr_after_w6.patch` | the change vs the trial_w6 source (5 hunks, search.hpp + search.cpp) |
| `cut_nott_lmr_stack.patch` | lock source -> this tree (trial_w6.patch + the change) |
| `tools/port_controls.sh` | makes the identity copy (`cnl_id`: the six flipped, macro 0) and the gate copy (`cnl_gate`: + macro 1) |
| `IDEA_SOURCE.md` | the source of the idea (ideas only) |
| `BENCH.md` | identity, gate OFF and ON numbers |
| `STATUS.md` | done / in progress / next step / resume / unproven |
| `logs/` | build summaries, bitexact logs, ON pin check |

## Exes (on F:, not in git)
- Identity: `F:\ospd\cut_nott_lmr\build\cnl_id_lp_v1\src_copy\forge_lp_v1.exe`, sha256 = trial_w6 (see BENCH.md).
- Gate: `F:\ospd\cut_nott_lmr\pack\forge_cut_nott_lmr_gate_@GATE8@.exe`, sha256 `@GATESHA@`, pc1 = pc2.

## Gate line (for QA / Strength after Code Review; nothing is queued by this job)
```
cand: forge_cut_nott_lmr_gate_@GATE8@.exe   setoption name CutNoTtLmr value 1
base: trial_w6  sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0
```
- Spec crew line: SPRT [0,5] normalized Elo, UHO book, Threads 1, STC first, LTC only after an STC H1.
- Bounds, TC, book and cap are QA's decision. This job starts no gate or SPRT.

## Notes for Code Review
- 5 hunks, all behind `#if FORGE_CUT_NO_TT_LMR`. The use site is one added line, so macro 0 leaves the parent's
  statements unchanged.
- `tt_move` is the node's const (`tt_hit ? tte.move : Move::none()`, `:1129`). It is fixed before the move loop and is
  in scope at the LMR block.
- The term reads `cut_node`, the same flag the `+2` term uses. It adds nothing at PV or all-nodes.
- The PGO profile is trained with the option at 0, so the ON path is cold-optimised. ON nps was not measured.
- Every review so far is the author's own (NOT independent).

## Rebuild
1. Copy `F:\ospd\src\lock`; it must pass `sha256sum -c lock_SOURCES.sha256` from inside the folder.
2. `patch -p1 -F0 < opus_cut_nott_lmr/cut_nott_lmr_stack.patch` gives tree `cnl`.
3. `bash opus_cut_nott_lmr/tools/port_controls.sh <src folder> cnl FORGE_CUT_NO_TT_LMR`.
4. From Git Bash, run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
   'F:\ospd\wt\opus_speed\tools\build_variants.ps1' -SrcDir <folder>\cnl_gate -Tag <new tag> -Variant lp_v1 -Work <dir>
   -Twice`. Use `cnl_id` without `-Twice` for the identity exe.
