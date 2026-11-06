# NmpTtCaptureMin (T04E-02) - STATUS

Owner Couns. Brief = the leftover /plan of 2026-11-06 (jobs 1-4; this is job 4). Plan file
`C:\Users\Administrator\.claude\plans\compiled-wobbling-hamming.md`.
- Branch `opus-nmp-tt-capture-20261105`, cut from 277a8f90 (the final tip of `opus-speed-20261105`). It is isolated:
  not stacked on any other port.
- Worktree `F:\ospd\wt` (sparse; `/opus_nmp_tt_capture/` added).
- Builds and outputs only under `F:\ospd\nmp_tt_capture\`. Message files go in `F:\ospd\tmp\`. Nothing is written to D:.
- Parent exe = the live lock trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0.
- Names (exact SPEC):
  - compile macro `FORGE_NMP_TT_CAPTURE_MIN`, default 0;
  - UCI spins (gate build only) `NmpTtCaptureMin` 0-5, default 0 (ON 4) and `NmpTtCaptureSee` 0-900, default 0
    (variant B, start 300, not gated here).
- `opus_speed/tools/commit_push.sh` = the file at 68fe3646 (job 2's tip).

## Done
- P0: branch from 277a8f90, commit_push.sh restored from 68fe3646, sparse pattern added.
- P1, source and patch:
  - Parents as in job 2. Tree `ntc` = trial_w6 + 5 hunks:
    - search.hpp: the macro default block and two externs;
    - search.cpp: two ints, two `parameters()` rows, and the NMP `if` (trial_w6 `:1181-1184`) duplicated under `#if`,
      with `&& !nmp_tt_capture_block()` appended last and the original kept verbatim in `#else`;
    - the lambda just above it:
      - both options <= 0 returns false;
      - then `tt_capture && board.is_pseudo_legal(tt_move)`;
      - only after that, the victim type test or `see_ge`.
  - `nmp_tt_capture_after_w6.patch` has md5 af81472d and `nmp_tt_capture_stack.patch` has md5 06d47aa6, both with
    timestamps stripped.
  - Apply proofs (`patch -p1 -F0`): no offset, fuzz or reject; `diff -r` = `ntc`.
  - `tools/port_controls.sh` (same file as job 2): `ntc_id` / `ntc_gate`. No CR bytes.
- P3, identity build: **IDENTITY PASS**. `F:\ospd\nmp_tt_capture\build\ntc_id_lp_v1\src_copy\forge_lp_v1.exe` has
  sha256 4181a589...6fb0 = trial_w6, `cmp` byte-identical, quick pins OK.
- P4, gate build: **REPRO pc1 = pc2**, sha256 1c6e105ee74ff31b1343307b320dc88b48cef6faa2879bdf97f9be43c3feaa87.
  - Quick pins OK at the defaults.
  - Handoff copy: `F:\ospd\nmp_tt_capture\pack\forge_nmp_tt_capture_gate_1c6e105e.exe`.
- P4, gate ON, MCP `pin_check -Full NmpTtCaptureMin=4;NmpTtCaptureSee=0`, 03:39:47-03:40:22: **LIVE**, perft = pins.
  - Both spins are advertised as specified.
  - d11 329842, d13 936622 (!= 862329), d16 3034926, d20 **12816428**, d22 34919651.

- P3, identity bit-exact (`logs/bx_id.log`): **BIT-EXACT** L1-L3. Net on + off d11-d22 = pins, perft = pins,
  2,000 / 2,000 FENs.
- P4, gate OFF at the defaults, started 03:39:50 (`logs/bx_gate_off.log`): **BIT-EXACT** L1-L3 vs trial_w6.
- P5: README.md (gate line, CR notes, rebuild), BENCH.md, IDEA_SOURCE.md, logs.
- **Pack milestone: READY FOR CODE REVIEW.**

## In progress
- Nothing. The pack waits for Code Review. All four jobs of the brief are done.

## Exact next step
Code Review of this pack: the patch (above all the `is_pseudo_legal`-before-victim order), BENCH.md and README.md. After
CR, QA / Strength run the SPRT:
- cand = the gate exe with `setoption name NmpTtCaptureMin value 4`;
- base = trial_w6 4181A589;
- variant B only after A's H0 / cap <= 0.

## Resume commands
- `git -C /f/ospd/wt switch opus-nmp-tt-capture-20261105 && git -C /f/ospd/wt log --oneline -3`
- Push: message file under `F:\ospd\tmp\`, then `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <message file>`.
- Rebuild: lock copy + `patch -p1 -F0 < opus_nmp_tt_capture/nmp_tt_capture_stack.patch` gives `ntc`, then
  `bash opus_nmp_tt_capture/tools/port_controls.sh <dir> ntc FORGE_NMP_TT_CAPTURE_MIN`. Build `build_variants.ps1
  -SrcDir <dir>\ntc_id|ntc_gate -Tag <new> -Variant lp_v1 -Work F:\ospd\nmp_tt_capture\build [-Twice]` from Git Bash.

## Unproven claims (and what is not done)
- Any Elo effect of NmpTtCaptureMin=4 in Forge: no Forge game result exists. The card estimates +1 to +3; the sources'
  numbers are their own.
- ON nps: not measured; the PGO profile is trained with the options at 0 (ON path cold-optimised).
- Not done (not in this brief):
  - the variant B ON bench;
  - the counter box tests (blocked share by victim type, null tries / cutoffs per 1M nodes);
  - mate probe, L4 sanitizers, full 12k gate OFF, Threads > 1 smokes.
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
