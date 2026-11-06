# CutNoTtLmr (T04D-01) - STATUS

Owner Couns. Brief = the leftover /plan of 2026-11-06 (jobs 1-4; this is job 2). Plan file
`C:\Users\Administrator\.claude\plans\compiled-wobbling-hamming.md` (approved before 03:14 PC clock).
- Branch `opus-cut-nott-lmr-20261105`, cut from 277a8f90 (the final tip of `opus-speed-20261105`, the same parent
  SingularNonCut used). It is not stacked on SingularNonCut.
- Worktree `F:\ospd\wt` (sparse checkout; `/opus_cut_nott_lmr/` added).
- Builds and outputs only under `F:\ospd\cut_nott_lmr\` (src, build, out, pack). Message files go in `F:\ospd\tmp\`.
  Nothing is written to D:.
- Parent exe = the live lock trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0.
- Names (exact SPEC):
  - compile macro `FORGE_CUT_NO_TT_LMR`, default 0;
  - UCI spin `CutNoTtLmr` 0-2, default 0, gate build only;
  - gate ON value 1.
- Push only with `opus_speed/tools/commit_push.sh`. On this branch it is the SingularNonCut branch's branch-aware,
  fail-closed version, with the three port branches added (each with its pack folder and its literal push line; the
  pack's .ps1 files get the parse check).

## Done
- P0, branch and tooling: branch from 277a8f90, `commit_push.sh` as above, sparse pattern added.
- P1, source and patch:
  - Parents:
    - `F:\ospd\src\lock` passes `sha256sum -c lock_SOURCES.sha256` (20 / 20).
    - `diff -ruN lock trial_w6`, timestamps stripped, has md5 9b9ea01b = `opus_speed/patches/trial_w6.patch`.
    - The copies in `F:\ospd\cut_nott_lmr\src\{lock,trial_w6}` equal the F: trees.
  - Tree `cnl` = trial_w6 + 5 hunks:
    - search.hpp: the macro default block and the extern;
    - search.cpp: the int, the `parameters()` row, and the use site right after `if (cut_node) r += 2;` (trial_w6
      `:1383`): `if (tune::CutNoTtLmr > 0 && cut_node && tt_move.is_none()) r += tune::CutNoTtLmr;`.
  - `cut_nott_lmr_after_w6.patch` has md5 66432f98 and `cut_nott_lmr_stack.patch` (vs the lock) has md5 bf5ce9ea, both
    with the `---` / `+++` timestamps stripped.
  - Apply proofs with `patch -p1 -F0`: lock + trial_w6.patch + after_w6.patch, and lock + stack.patch. No offset, fuzz or
    reject; `diff -r` = `cnl` for both.
  - `tools/port_controls.sh` is snc_controls.sh with the folder, tree and macro as arguments:
    - `cnl_id` = the six flipped, with the macro still 0;
    - `cnl_gate` = the six flipped + macro 1;
    - every flip hit exactly one `#define X 0` line, and there are no CR bytes.
- P3, identity build (started 03:26:16): **IDENTITY PASS**.
  - `F:\ospd\cut_nott_lmr\build\cnl_id_lp_v1\src_copy\forge_lp_v1.exe` has sha256
    4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0 = trial_w6
    (`forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`). `cmp` says byte-identical.
  - Quick pins 312866 / 862329 / 3024920 OK.
  - So the parent 277a8f90 still builds trial_w6's exact exe, and macro 0 adds nothing. There is no new UCI option,
    because the bytes are the same.
- P4, gate build: **REPRO pc1 = pc2**, sha256 dcdec9a7d71aec370cba9516ed75183f2ee433f71f6024ebdfa4e23c8a56a0c4.
  - Quick pins OK at the default 0.
  - Handoff copy: `F:\ospd\cut_nott_lmr\pack\forge_cut_nott_lmr_gate_dcdec9a7.exe`.
- P3, identity bit-exact (`logs/bx_id.log`): **BIT-EXACT** L1-L3.
  - Net on + off d11-d22 = pins.
  - perft 5 startpos + kiwipete = pins.
  - 2,000 / 2,000 FENs identical at depth 13.
- P4, gate OFF (runtime default 0), started 03:29:14 (`logs/bx_gate_off.log`): **BIT-EXACT** L1-L3 vs trial_w6 on the
  same set. So the gate exe at its default searches trial_w6's nodes.
- P4, gate ON, MCP `pin_check -Full CutNoTtLmr=1`, 03:29:18-03:29:54: **LIVE**, perft = pins.
  - Advertised: `CutNoTtLmr type spin default 0 min 0 max 2`.
  - Net on: d11 318696, d13 780755 (!= 862329), d16 2738962, d20 **16243524**, d22 26960018. Table in BENCH.md.
- P5: README.md (gate line, CR notes, rebuild), BENCH.md, IDEA_SOURCE.md, logs.
- **Pack milestone: READY FOR CODE REVIEW.**

## In progress
- Nothing for this pack. It waits for Code Review. Job 3 (TtCutNodeDepth) goes on in its own branch.

## Exact next step
Code Review of this pack: the patch, BENCH.md, README.md, `tools/port_controls.sh`, and the extended
`opus_speed/tools/commit_push.sh`. After CR, QA / Strength run the SPRT with the gate line in README.md:
- cand = the gate exe with `setoption name CutNoTtLmr value 1`;
- base = trial_w6 4181A589.
- The owner decides TC / book / bounds / Threads for that SPRT.

## Resume commands
- `git -C /f/ospd/wt switch opus-cut-nott-lmr-20261105 && git -C /f/ospd/wt log --oneline -3`
- Push: write a message file under `F:\ospd\tmp\`, then `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <message file>`.
- Rebuild the trees:
  1. Copy `F:\ospd\src\lock` (check `lock_SOURCES.sha256` from inside it) to `<dir>\lock`, and make `<dir>\cnl` the same way.
  2. In `cnl`, run `patch -p1 -F0 < opus_cut_nott_lmr/cut_nott_lmr_stack.patch`.
  3. `bash opus_cut_nott_lmr/tools/port_controls.sh <dir> cnl FORGE_CUT_NO_TT_LMR`.
- Builds (from Git Bash, never the PowerShell tool): `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  'F:\ospd\wt\opus_speed\tools\build_variants.ps1' -SrcDir 'F:\ospd\cut_nott_lmr\src\cnl_id' -Tag <new tag> -Variant
  lp_v1 -Work 'F:\ospd\cut_nott_lmr\build'`. For the gate, use `cnl_gate` and add `-Twice`. Use a new tag per run.

## Unproven claims (and what is not done)
- Any Elo effect of CutNoTtLmr=1 in Forge: no Forge game result exists. The card estimates 0 to +3 at STC; the source's
  numbers are the source's own.
- ON nps: not measured. The PGO profile is trained with the option at 0, so the ON path is cold-optimised.
- Not done (not in this brief): the counter-build box tests of the spec, the mate probe, L4 sanitizers, the full 12k gate
  OFF run, and Threads > 1 smokes.
- Code Review of this pack has not happened. Every review so far is my own (NOT independent).

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

### Leftover jobs 2 + 3 DONE (2026-11-06 11:54-12:01 PC clock)
- **Job 2, mate probe** of the gate exe dcdec9a7, OFF (defaults) vs ON `CutNoTtLmr=1`:
  - Crew set `tools/mate_probe.epd` (md5 df9a6967, 22 FENs) at nodes 3M: mates OFF 19, ON 19.
    - Fen 1 LOST: OFF mate 15, ON cp 581.
    - Fen 8 LONGER: 14 -> 15.
    - Fen 12 GAINED: cp 544 -> mate 16.
  - Re-run of fens 1, 8 and 12 at 30M nodes: OFF / ON mate 11 / 11, 12 / 12 and 14 / 13. So **no mate is lost or longer**
    at 30M: the 3M flags were horizon effects.
  - S1-S5 at depth 12: OFF = ON and the right classes: mate 1 d1d8; 0000 cp 0; mate 1 e6c8; cp 0; mate 1 a1a8.
- **Job 3, counter box test** (test-only counter build, never the gate exe):
  - Patch `cut_nott_lmr_counters_test.patch`. o3 exe sha256 5ab51a3d..., pins 312866 / 862329 / 3024920.
  - bench 16 OFF 3024920 and ON 2738962 are the gate's nodes, so the counters do not change the search.
  - The rule fires only ON, and at every cut node without a TT move: `applied` = `lmr_cut_nott` = 117,422 at bench 16
    (0 OFF).
  - F1-F5 d16, ON / OFF nodes: 1.692 / 1.136 / 0.600 / 0.716 / 1.057, total 1.103. Every bestmove is legal and the same
    as OFF on all 10 FENs; S1-S5 are identical.
  - Per 1M nodes (F1-F5), OFF -> ON, at cut nodes without a TT move:
    - LMR searches 41.3k -> 41.1k;
    - share clamped at reduced depth 1: 88.8 % -> 94.1 %;
    - re-search rate 8.05 % -> 8.36 %;
    - boosts 3.72k -> 3.87k.
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
