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

- P3, identity bit-exact (`logs/bx_id.log`): **BIT-EXACT** L1-L3. Net on + off d11-d22 = pins, perft = pins,
  2,000 / 2,000 FENs.
- P4, gate OFF at the defaults, started 03:33:50 (`logs/bx_gate_off.log`): **BIT-EXACT** L1-L3 vs trial_w6.
- P5: README.md (gate lines, CR notes, rebuild), BENCH.md, IDEA_SOURCE.md, logs.
- **Pack milestone: READY FOR CODE REVIEW.**

## In progress
- Nothing for this pack. It waits for Code Review. Job 4 (NmpTtCaptureMin) goes on in its own branch.

## Exact next step
Code Review of this pack: the patch, BENCH.md, README.md. After CR, QA / Strength run the SPRT with the README gate
lines:
- cand = the gate exe with `TtCutNodeDepth 6` + `TtCutNodeForm 1`;
- base = trial_w6 4181A589;
- form 2 only after a form-1 H0 or a cap at <= 0.

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

## Leftover checks (owner /plan brief 2026-11-06 ~11:35 PC clock; plan `C:\Users\Administrator\.claude\plans\transient-strolling-bumblebee.md`)
- Owner-reported, not seen by me: QA's Code Review APPROVE, ASan, bench and WAC are done and QA has queued the SPRT.
  This work touches no SPRT, gate, lock or queue file, and the gate exe in `pack\` is run in place, never rebuilt.
- Jobs, in this order: 1 full 12k (fens_12k_v2, depth 13) at the defaults vs trial_w6, net on AND net off; 2 mate
  probes option OFF vs ON; 3 counter box tests (test-only counter build); 4 ON / OFF nps ABBA only if usage remains.
- Tool change: `opus_speed/tools/bitexact_check.ps1 -FenOptions 'Name=Value,...'` = extra UCI options for L3 on ref AND
  cand, with its own ref cache name (suffix `_UseNNUE-false`). Default empty = the old run and the old cache names.
  Smoke 11:50:49-11:51:50: cnl gate, 50 FENs net off: 50 / 50 identical; the net-off ref rows differ from the net-on
  cache rows (the option is live).
- Job 1 RUNNING since 2026-11-06 11:52:06 (PC clock): chain `D:\oleft2\chain1.sh` (private copy), progress
  `D:\oleft2\chain1.log`, outputs `D:\oleft2\<cnl|tcn|ntc>\fens12k_on|fens12k_off\` (bitexact.log + TSVs).
- NOT DONE: jobs 1 (running), 2, 3, 4.
- Resume (Git Bash): `tail D:/oleft2/chain1.log`; a step that did not end rc=0 is re-run with a NEW -Out:
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'D:/oleft2/tools/bitexact_check.ps1' -Cand <gate exe>
  -Out 'D:/oleft2/<p>/fens12k_off_r2' -SkipSan [-FenOptions 'UseNNUE=false']`.
