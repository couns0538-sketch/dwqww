# SingularNonCut (T04-01) - STATUS

Owner Couns. Brief = the /plan args of 2026-11-06 (one item: SingularNonCut). Plan file
`C:\Users\Administrator\<cfg>\plans\quiet-rolling-summit.md` (approved 01:27 PC clock).
- Branch `opus-singular-noncut-20261105`, cut from 277a8f90 (final tip of `opus-speed-20261105`, local = remote).
- Worktree `F:\ospd\wt`. Builds and outputs only under `D:\opus_singular_noncut\` (src, build, out, pack, msg).
- Parent exe = the live lock trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0
  (`forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`). The hunt's H1-H9 were screening only; none is in the lock.
- Names: compile macro `FORGE_SINGULAR_NONCUT` (default 0); UCI spin `SingularNonCut` 0-1, default 0 (gate build only).
  No other option or switch is touched.
- CPU window (owner message 01:27 PC clock): CPUs 0-6 + GPU for one hour, 01:27 -> 02:27. Afterwards CPUs 0-3 only.
  This job has no GPU work and uses no GPU. Own work runs at Idle; builds and checks pin themselves to CPUs 0-1.
- Push only with `opus_speed/tools/commit_push.sh`, branch-aware since this job: on this branch it stages
  `opus_singular_noncut opus_speed skills` and pushes this branch; on `opus-speed-20261105` it behaves as before.

## Done
- S1 01:27-01:30: branch created; `commit_push.sh` branch-aware; `IDEA_SOURCE.md` (Caissa 1b7a871, MIT notice
  verbatim); this file. The first push 948e0334 carried only the script: the sparse checkout (`/opus_speed/`,
  `/skills/`) skipped the new folder and the old script committed the rest anyway. Fixed in 12db033c:
  `/opus_singular_noncut/` added to the sparse patterns, and `commit_push.sh` now exits 1 when `git add` fails or
  leaves files unstaged.
- S2 01:30-01:32, source + patch:
  - D: copies: the lock copy passes `sha256sum -c lock_SOURCES.sha256` (20 / 20); both copies = the F: trees by
    content; `diff -ruN lock trial_w6` = `opus_speed/patches/trial_w6.patch` (timestamps stripped, md5 9b9ea01b).
  - The five edits in `D:\opus_singular_noncut\src\snc` (search.hpp + search.cpp only):
    `singular_noncut_after_w6.patch` (md5 442bb4fb) and `singular_noncut_stack.patch` (vs the lock, md5 f22eccfd).
  - Apply proofs: fresh lock copy + trial_w6.patch + after_w6.patch, and lock + stack.patch, both with
    `patch -p1 -F0`: no offset, fuzz or reject; `diff -r` = `snc` for both.
  - Preprocessor check (`logs/pp_neutrality.txt`): `g++ -E -P` with the kit flags + the six trial_w6 values, blank
    lines stripped. Macro 0: all 8 units = trial_w6's token stream. Macro 1: search.cpp differs only by the extern,
    the int, the table row and the call (`verify_cut`); uci.cpp only by the extern from search.hpp.
  - `tools/snc_controls.sh` (01:32): `snc_id` = the six flipped (macro stays 0); `snc_gate` = the six + macro 1.
    Every flip hit exactly one `#define X 0` line; no CR bytes (`logs/snc_controls.out.txt`).

- S3 identity build 01:32:53-01:33:52: **IDENTITY PASS**. `D:\opus_singular_noncut\build\snc_id_lp_v1\src_copy\forge_lp_v1.exe`
  sha256 4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0 = the live lock trial_w6
  (`forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`), `cmp` byte-identical; quick pins bench 11/13/16 net on
  312866 / 862329 / 3024920 OK. So the parent still builds trial_w6's exact exe, and macro 0 adds nothing.

- S3 gate build 01:32:53-01:34:46: **REPRO pc1 = pc2** sha256 5f6be7c55ba318790c26690b0a96edec678aab786334247a8e7a630c5610d117;
  quick pins OK at the default 0; vfmadd 0. Handoff copy `D:\opus_singular_noncut\pack\forge_singular_noncut_gate_5f6be7c5.exe`.
- S4 identity bit-exact 01:34:07-01:37:41: **BIT-EXACT** L1-L3. Net on + off d11-d22 = pins, perft 5 startpos +
  kiwipete = pins, 2,000 / 2,000 FENs identical (`logs/bx_id.log`).
- S4 gate exe `uci`: `SingularNonCut type spin default 0 min 0 max 1` advertised (MCP uci_options).
- S4 ON, MCP pin_check `-Full SingularNonCut=1`, 01:38:30-01:39:07: **LIVE**, perft = pins.
  - net on: d11 368386, d13 863236, d16 3254758, d20 **10207303**, d22 28667881;
  - net off: d13 873459, d20 12554284;
  - pc2 repeat d20 = 10207303.
- `BENCH.md` + `README.md` written (gate line, rebuild, CR notes).

## In progress
- S4 gate OFF, full 12k (started 01:35): `bitexact_check.ps1 -Cand <gate pc1 exe> -Out
  D:\opus_singular_noncut\out\bx_gate_off_12k -SkipSan`. L1 + L2 PASS; L3 on 12,000 FENs is running.
- S6 smoke A in the CPU window (started 01:37:48), `tools/smoke_run.ps1 -Out D:\opus_singular_noncut\out\smoke_a
  -Mask 0x70 -Concurrency 3 -Rounds 50 -Srand 20261106 -MaxMinutes 30`:
  - CPUs 4-6 at Idle, checked on all 7 processes;
  - 100 games, gate exe ON vs trial_w6, tc 10+0.1 timemargin 1000, Hash 16, Threads 1, 8moves_v3 random;
  - ~37 s per game per slot.

## Exact next step
1. When the 12k ends: copy `bitexact.log` to `logs/bx_gate_off_12k.log` and put the L3 line in BENCH.md.
2. When smoke A ends (expected ~01:58): smoke B with the same settings and `-Srand 20261107 -Out ...\smoke_b`, on 0x70
   only if it can end before 02:27 (`-MaxMinutes 25`, the script refuses otherwise). Otherwise run it on `-Mask 0x4`
   (CPU 2) with concurrency 1.
3. Then stop for Code Review.

## Resume commands
- `git -C /f/ospd/wt switch opus-singular-noncut-20261105 && git -C /f/ospd/wt log --oneline -3`
- Push: write a message file under `D:\opus_singular_noncut\msg\`, then
  `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <message file>`.
- Rebuild the trees from git: copy `F:\ospd\src\lock` (check `lock_SOURCES.sha256`) to `D:\...\src\snc`, then
  `patch -p1 -F0 < opus_singular_noncut/singular_noncut_stack.patch`, then `bash opus_singular_noncut/tools/snc_controls.sh`.
- Builds (from Git Bash, never the PowerShell tool): `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  'F:\ospd\wt\opus_speed\tools\build_variants.ps1' -SrcDir 'D:\opus_singular_noncut\src\snc_id' -Tag <new tag>
  -Variant lp_v1 -Work 'D:\opus_singular_noncut\build'` (gate: `snc_gate`, add `-Twice`); a new tag per run.

## Unproven claims
- Any Elo effect of SingularNonCut=1 in Forge (card estimate 0 to +3 at STC; Caissa's +4.20 is Caissa's own result).
- Nothing is built or measured yet.
