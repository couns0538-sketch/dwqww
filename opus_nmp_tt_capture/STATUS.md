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

### Leftover jobs 2 + 3 DONE (2026-11-06 11:56-12:02 PC clock)
- **Job 2, mate probe** of the gate exe 1c6e105e, OFF (defaults) vs ON `NmpTtCaptureMin=4`:
  - Crew set `tools/mate_probe.epd` (md5 df9a6967, 22 FENs) at nodes 3M: mates OFF 19, ON 19. All 22 are identical
    (score and bestmove), with no flag, so no 30M re-run was needed.
  - S1-S5 at depth 12: OFF = ON, right classes. **No mate lost or longer.**
- **Job 3, counter box test** (test-only counter build, never the gate exe):
  - Patch `nmp_tt_capture_counters_test.patch`. o3 exe sha256 bbac0e55..., pins OK.
  - bench 16 OFF 3024920 and ON 3034926 are the gate's nodes.
  - Only rook and queen victims are blocked. At bench 16 ON, blocked 1,582 = v4 617 + v5 965, which is every real TT
    capture of a rook or queen at an NMP-eligible node; v1-v3 are 0.
  - Null tries fall (the card's check): per 1M nodes (F1-F5) 31.9k -> 27.8k, cutoffs 21.9k -> 19.2k. At bench 16,
    null_tries = eligible - blocked (60,693 = 62,275 - 1,582).
  - F1-F5 d16, ON / OFF nodes: 0.871 / 0.914 / 0.761 / 1.004 / 1.176, total 0.930. Every bestmove is legal and the same
    as OFF on all 10 FENs. F3: OFF cp 120 b4f4, ON cp 187 b4f4 (same class and move). S1-S5 are identical.
  - FLAGS none.
- Notes for jobs 2 / 3:
  - The `rc=` fields in `D:\oleft2\chain*.log` are `date`'s exit status (a bug in my chain scripts), not the tools'. The
    verdicts come from each tool's own SUMMARY.txt / bitexact.log.
  - box_run.py ran on the read-only venv python (python-chess for legality).
  - The first cnl box start failed closed on a ctypes placement bug, fixed before any box ran. Every box run here is
    Idle with CPU mask 0xC, read back; the 30M mate runs were Idle on 0xC too.
  - Logs: `logs/mate/` (SUMMARY + TSV per run, the two FEN sets) and `logs/box/` (SUMMARY, rows, bench logs, build out).
    Tools: `tools/mate_probe.ps1`, `tools/mk_counters.py`, `tools/box_run.py`.
- NOT DONE: job 1 (chain still running; the results follow in this file), job 4 (ON / OFF nps). Not done inside job 3:
  the spec's "agreement"-type shares, which need node-exit tracking.
- Resume, job 2: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/mate_probe.ps1 -Exe <gate exe> -OnOptions
  '<ON line>' -Epd tools/mate_probe.epd -Out <new dir> [-Go 'nodes 30000000'] -Mask 0xC [-Index 'i,j']`.
- Resume, job 3:
  1. Copy `<x>_gate`.
  2. Run `python -I -B tools/mk_counters.py <cnl|tcn|ntc> <copy>`.
  3. Run `build_variants.ps1 -SrcDir <copy> -Tag <new> -Variant o3 -Define FORGE_SPEC_COUNTERS=1 -Work <dir>`.
  4. Run `python -I -B tools/box_run.py --port <p> --exe <o3 exe> --on '<ON line>' --out <new dir> --mask 0xC`.

### Leftover job 4 DONE: nps ON vs OFF (2026-11-06 12:07-12:16 PC clock; logs/abba/)
- Tool: `opus_speed/tools/abba.ps1 -OptionB 'NmpTtCaptureMin=4'`, the same gate exe on both arms, ON on arm B only, `-AllowNodeDiff`.
- Protocol: bench d16, **10 rounds**, ABBA / BAAB alternating, fresh copies, CPU 2 BelowNormal. The brief said 4 pairs, but abba.ps1 refuses fewer than 10 rounds (QA protocol), so 10 were run.
- Result (B = ON, A = OFF):
  - wall (engine nps): B/A median 0.9923 (-0.77%), 95% t-interval [0.9842, 1.0243], sd/round 2.79%, bootstrap median CI [0.9837, 1.0276]
  - cpu (nodes / process CPU time of the bench window): B/A median 0.9971 (-0.29%), 95% t-interval [0.9904, 1.0194], sd/round 2.02%, bootstrap median CI [0.9851, 1.0286]
- **The PC was not quiet.** load.txt: CPU 2 68-84 % busy, its sibling CPU 3 31-90 % busy (not mine: the trainer and others), total 58-69 %. Chain 1 (12k) ran on CPUs 0-1 at the same time.
- The ON tree differs from OFF (bench 16 nodes A 3024920 B 3034926), so this is nps per node of a different tree. It is not a cost of the code itself, and time to depth is not measured here. The PGO profile is trained with the option at 0.
- NOT DONE now: job 1 only (chain running, results follow).

### Leftover job 1: full 12k at the defaults vs trial_w6, net on and net off (written 2026-11-06 12:55:56 PC clock)
- Ref = trial_w6 4181A589, the default lock exe in forge_push\bin (read-only, as in every earlier run). Cand = the gate
  exe, run in place (sha256 in each log).
- L3 = fens_12k_v2.txt (md5 e7dbf2c8) at go depth 13, OwnBook=false, ucinewgame per FEN, two engines on CPUs 0 / 1 Idle.
  L1 (bench d11-d22 net on + off) and L2 (perft 5) ran in both runs too.
- Net on uses the cached ref. Net off adds `-FenOptions UseNNUE=false`; that ref was computed once in this chain
  (`F:\ospd\ref\4181a589\fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-false.tsv`, about 320 KB on F:).
- **net on**: `VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs)`, 12000 / 12000 identical.
  - Node totals over the 12,000 FENs: ref 1534521761, cand 1534521761.
  - md5: `logs/fens12k/bitexact_neton.log` a283b04d62d77e913a5d89af3b437ce2, cand TSV 4db620da5fa9051a4e2a08bceb69f027, ref TSV 4db620da5fa9051a4e2a08bceb69f027.
  - The TSVs stay in `D:\oleft2\ntc\fens12k_on\` and in the F: ref cache.
- **net off**: `VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs)`, 12000 / 12000 identical.
  - Node totals over the 12,000 FENs: ref 1578228148, cand 1578228148.
  - md5: `logs/fens12k/bitexact_netoff.log` 91d634dcc6b59969967ecb86e29db678, cand TSV bd7275929565a563786e79438bdb3f79, ref TSV bd7275929565a563786e79438bdb3f79.
  - The TSVs stay in `D:\oleft2\ntc\fens12k_off\` and in the F: ref cache.
- Job 1 verdict: **BIT-EXACT net on AND net off on all 12,000 FENs.**
- NOT DONE (this brief): none.
- Outside this brief: L4 sanitizers, Threads > 1 smokes, and the spec's agreement-type box shares.
