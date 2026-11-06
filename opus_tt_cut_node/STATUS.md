# TtCutNodeDepth (T04D-02) - STATUS

Owner Couns. Brief = the leftover /plan of 2026-11-06 (jobs 1-4; this is job 3). Plan file
`C:\Users\Administrator\.claude\plans\compiled-wobbling-hamming.md`.
- Branch `opus-tt-cut-node-20261105`, cut from 277a8f90 (the final tip of `opus-speed-20261105`). It is isolated: not
  stacked on CutNoTtLmr or SingularNonCut. The ranking note "stack on D-01" is the later gate order.
- Worktree `F:\ospd\wt` (sparse; `/opus_tt_cut_node/` added).
- Builds and outputs only under `F:\ospd\tt_cut_node\`. Message files go in `F:\ospd\tmp\`. Nothing is written to D:.
- Parent exe = the live lock trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0.
- Names (exact SPEC):
  - compile macro `FORGE_TT_CUT_NODE_DEPTH`, default 0;
  - UCI spins (gate build only) `TtCutNodeDepth` 0-14, default 0 (ON 6) and `TtCutNodeForm` 1-2, default 1 (ON 1; read
    only when TtCutNodeDepth > 0).
- `opus_speed/tools/commit_push.sh` = the file at 68fe3646 (job 2's tip): branch-aware, with this branch's pack folder
  and its literal push line.

## Done
- P0: branch from 277a8f90, commit_push.sh restored from 68fe3646, sparse pattern added.
- P1, source and patch:
  - Parents as in job 2: lock `sha256sum -c` 20 / 20, `diff lock trial_w6` md5 9b9ea01b; copies in
    `F:\ospd\tt_cut_node\src\{lock,trial_w6}`.
  - Tree `tcn` = trial_w6 + 5 hunks:
    - search.hpp: the macro default block and two externs;
    - search.cpp: two ints, two `parameters()` rows, and the main-search TT cutoff `if` (trial_w6 `:1137-1142`)
      duplicated under `#if`, with the new term appended last and the original kept verbatim in `#else`.
  - `tt_cut_node_after_w6.patch` has md5 add52bdf and `tt_cut_node_stack.patch` has md5 44e7b151, both with timestamps
    stripped.
  - Apply proofs with `patch -p1 -F0` (lock + trial_w6 + after_w6, and lock + stack): no offset, fuzz or reject; `diff -r`
    = `tcn`.
  - `tools/port_controls.sh` (same file as job 2): `tcn_id` = the six flipped, macro 0; `tcn_gate` = the six + macro 1.
    No CR bytes.
- P3, identity build: **IDENTITY PASS**. `F:\ospd\tt_cut_node\build\tcn_id_lp_v1\src_copy\forge_lp_v1.exe` has sha256
  4181a589...6fb0 = trial_w6, `cmp` byte-identical, quick pins OK.
- P4, gate build: **REPRO pc1 = pc2**, sha256 8151e220360126264da984432ca2d5ad077c39aade78170b020d38ec35666d6b.
  - Quick pins OK at the defaults.
  - Handoff copy: `F:\ospd\tt_cut_node\pack\forge_tt_cut_node_gate_8151e220.exe`.
- P4, gate ON, MCP `pin_check -Full TtCutNodeDepth=6;TtCutNodeForm=1`, 03:33:47-03:34:32: **LIVE**, perft = pins.
  - Both spins are advertised as specified.
  - d11 354466, d13 759020 (!= 862329), d16 3049356, d20 **10771342**, d22 25468915.

## In progress
- `bitexact_check -Quick -SkipSan` of the identity exe and of the gate exe at its defaults (OFF) ->
  `F:\ospd\tt_cut_node\out\bx_id`, `bx_gate_off`.

## Exact next step
1. Record both bit-exact verdicts in BENCH.md and here.
2. Mark the pack READY FOR CODE REVIEW and push.
3. Then Code Review. QA / Strength run the SPRT with the README gate lines; form 2 only after a form-1 H0 / cap <= 0.

## Resume commands
- `git -C /f/ospd/wt switch opus-tt-cut-node-20261105 && git -C /f/ospd/wt log --oneline -3`
- Push: message file under `F:\ospd\tmp\`, then `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <message file>`.
- Rebuild: lock copy + `patch -p1 -F0 < opus_tt_cut_node/tt_cut_node_stack.patch` gives `tcn`, then
  `bash opus_tt_cut_node/tools/port_controls.sh <dir> tcn FORGE_TT_CUT_NODE_DEPTH`. Build `build_variants.ps1 -SrcDir
  <dir>\tcn_id|tcn_gate -Tag <new> -Variant lp_v1 -Work F:\ospd\tt_cut_node\build [-Twice]` from Git Bash.

## Unproven claims (and what is not done)
- Any Elo effect of TtCutNodeDepth=6 form 1 in Forge: no Forge game result exists. The card estimates 0 to +3 at STC.
- ON nps: not measured; the PGO profile is trained with the options at their defaults (ON path cold-optimised).
- Not done (not in this brief): form 2 ON bench, counter box tests, mate probe, L4 sanitizers, full 12k gate OFF,
  Threads > 1 smokes.
- Code Review has not happened. Every review so far is my own (NOT independent).
