# opus_tt_cut_node - TtCutNodeDepth (deep-research card T04D-02), gate-ready, default OFF

## What it is
One more term on the main-search TT cutoff (trial_w6 `src/search.cpp:1137-1142`, the spec's lock lines :921-926). At
depth <= `TtCutNodeDepth`, a cutoff also needs the stored direction to match the node type. Runtime 0 is off.
- Form 1 (`TtCutNodeForm` 1, the gate ON form): a cutoff at `tt_score >= beta` needs `cut_node`. Fail-low cutoffs are
  unchanged.
- Form 2 (`TtCutNodeForm` 2): `(tt_score >= beta) == cut_node`. It is built in, but this job does not gate it; QA uses it
  only after a form-1 H0 or a cap at <= 0.
- Non-PV nodes are null-window, so `tt_score >= beta` gives the direction for all three bounds.
- `depth` is the node's entry depth; IIR comes later.
- A refused cutoff searches the node normally (eval, NMP, move loop), and `tt_move` is still ordered first.
- qsearch's TT cutoff is not changed.
- The new term is appended last and starts with `TtCutNodeDepth == 0 ||`, so at 0 it is constant true and the form is
  never read.

## Switches
- Compile macro `FORGE_TT_CUT_NODE_DEPTH` (search.hpp, default 0). At 0 the original `if` is kept verbatim in `#else`, so
  the identity exe is the live lock trial_w6 4181A589 byte for byte.
- At 1 the source adds:
  - the `tune::` ints `TtCutNodeDepth = 0` and `TtCutNodeForm = 1`, with their externs;
  - the `parameters()` rows `{"TtCutNodeDepth", &TtCutNodeDepth, 0, 14}` and `{"TtCutNodeForm", &TtCutNodeForm, 1, 2}`;
  - the guarded copy of the cutoff `if`.
- No other option or switch is touched. The six trial_w6 switches stay as `opus_speed/patches/trial_w6.patch` sets them.
  The hunt flags stay off.

## Files
| file | what |
|---|---|
| `tt_cut_node_after_w6.patch` | the change vs the trial_w6 source (5 hunks, search.hpp + search.cpp) |
| `tt_cut_node_stack.patch` | lock source -> this tree (trial_w6.patch + the change) |
| `tools/port_controls.sh` | makes the identity copy (`tcn_id`: the six flipped, macro 0) and the gate copy (`tcn_gate`: + macro 1) |
| `IDEA_SOURCE.md` | the source of the idea (ideas only) |
| `BENCH.md` | identity, gate OFF and ON numbers |
| `STATUS.md` | done / in progress / next step / resume / unproven |
| `logs/` | build summaries, bitexact logs |

## Exes (on F:, not in git)
- Identity: `F:\ospd\tt_cut_node\build\tcn_id_lp_v1\src_copy\forge_lp_v1.exe`, sha256 = trial_w6 (see BENCH.md).
- Gate: `F:\ospd\tt_cut_node\pack\forge_tt_cut_node_gate_8151e220.exe`, sha256 `8151e220360126264da984432ca2d5ad077c39aade78170b020d38ec35666d6b`, pc1 = pc2.

## Gate line (for QA / Strength after Code Review; nothing is queued by this job)
```
cand: forge_tt_cut_node_gate_8151e220.exe   setoption name TtCutNodeDepth value 6
                                            setoption name TtCutNodeForm value 1
base: trial_w6  sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0
```
- Spec crew line: SPRT [0,5] normalized Elo, UHO book, Threads 1, STC first.
- Form 2 (`TtCutNodeForm value 2`) is run only after line 1 ends H0 or capped <= 0.
- Bounds, TC, book and cap are QA's decision. This job starts no gate or SPRT.

## Notes for Code Review
- 5 hunks, all behind `#if FORGE_TT_CUT_NODE_DEPTH`.
- The ON condition is the original condition `&& (TtCutNodeDepth == 0 || depth > TtCutNodeDepth || match)`.
  - Form 1: `match = (tt_score < beta || cut_node)`.
  - Form 2: `match = ((tt_score >= beta) == cut_node)`.
  - Any value other than 2 reads as form 1. The option range is 1-2.
- The term only refuses cutoffs; it never adds one. A refused node runs the normal search, which stores its own TT
  entry.
- The PGO profile is trained with the option at 0, so the ON path is cold-optimised. ON nps was not measured.
- Every review so far is the author's own (NOT independent).

## Rebuild
1. Copy `F:\ospd\src\lock`; it must pass `sha256sum -c lock_SOURCES.sha256` from inside the folder.
2. `patch -p1 -F0 < opus_tt_cut_node/tt_cut_node_stack.patch` gives tree `tcn`.
3. `bash opus_tt_cut_node/tools/port_controls.sh <src folder> tcn FORGE_TT_CUT_NODE_DEPTH`.
4. Build with `build_variants.ps1 -SrcDir <folder>\tcn_gate -Tag <new tag> -Variant lp_v1 -Work <dir> -Twice` from Git
   Bash. Use `tcn_id` without `-Twice` for the identity exe.
