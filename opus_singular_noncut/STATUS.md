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

- S4 gate OFF, full 12k, 01:35:16-01:45:55: **BIT-EXACT** L1-L3 on all 12,000 FENs (`logs/bx_gate_off_12k.log`). So
  the gate exe at its default searches trial_w6's nodes. Nothing was written on F: (the reference cache files keep
  their hunt times).
- **Pack milestone: READY FOR CODE REVIEW** (patch, IDEA_SOURCE, BENCH, README, STATUS, logs).

- S6 smoke A (optional; a crash / time-loss / illegal-move check, NOT a verdict), 01:37:48-01:53:40, in the owner's
  CPU window: **CLEAN**.
  - Command: `tools/smoke_run.ps1 -Out D:\opus_singular_noncut\out\smoke_a -Mask 0x70 -Concurrency 3 -Rounds 50
    -Srand 20261106 -MaxMinutes 30`.
  - CPUs 4-6 at Idle, checked on all 7 processes. Gate exe ON vs trial_w6, tc 10+0.1 timemargin 1000, Hash 16,
    Threads 1, 8moves_v3 random.
  - 100 / 100 games, 0 time losses (either engine), 0 disconnect / illegal / crash / stall / error lines.
  - A ran with the first script version. Its regex lacked `warning|responsive`; the A output re-grepped with the
    stricter pattern afterwards: 0 lines.
  - Information only: W 7 / D 84 / L 9, Ptnml [0, 8, 36, 6, 0]. 100 games say nothing about strength.
  - Logs: `logs/smoke_a_SUMMARY.txt`, `logs/smoke_a_fastchess.out.txt`. PGN and engine log stay in
    `D:\opus_singular_noncut\out\smoke_a`.

- S6 smoke B, 01:53:57-02:10:00: **CLEAN**.
  - Same settings as A with `-Srand 20261107 -Out D:\opus_singular_noncut\out\smoke_b -MaxMinutes 19`, on CPUs 4-6
    (gate: A's 15:52 + 3 min ended before the 02:27 window end). Stricter regex.
  - 100 / 100 games, 0 time losses, 0 disconnect / illegal / crash / stall / error / warning / responsive lines.
  - Information only: W 9 / D 83 / L 8, Ptnml [0, 7, 35, 8, 0].
  - Logs: `logs/smoke_b_SUMMARY.txt`, `logs/smoke_b_fastchess.out.txt`.
- **Smoke total: 200 games, gate exe ON vs trial_w6, 0 time losses, 0 crash / illegal / disconnect lines**
  (W 16 / D 167 / L 17, Ptnml [0, 15, 71, 14, 0]; not a verdict).
- CPU window compliance:
  - Every smoke process ran on 0x70 (CPUs 4-6) at Idle, and the last one ended 02:10:00. No GPU use at any time.
  - Sweep at 02:10:28 of [name withheld].exe 1700 + all descendants: 4 of 17 processes had 0xFFFF. They were the two MCP
    servers (forge-uci, forge-o30, python venv launchers + their conhost), started 2026-11-05 09:32:10 at the app
    restart, before the session was re-pinned. Normal priority, 0.0 s CPU; their engines ran on 0x3 Idle as the
    servers set them. My plan's "children inherit 0x3" did not hold for these four.
  - Re-pinned by handle (name / parent / start time checked first) to 0x3 Idle. Re-sweep 02:11:06: 0 of 17 own
    processes with affinity bits above 0xF.

  - Check 02:23:38: no smoke process (fastchess / gate exe / trial_w6 exe) of mine left.
  - **After the window end, sweep 02:27:35: 14 own processes ([name withheld].exe 1700 + descendants), 0 with affinity bits
    above 0xF.** Back to CPUs 0-3 only.
- Skill `forge-speed-lock-path` (user scope + repo mirror `skills/forge-speed-lock-path/SKILL.md`, kept identical):
  the restart pitfall now says to pin the MCP servers too.

- Owner message after DONE (keep working on the remaining jobs, push every 10 min); the crew items, from 02:32:
  - L4 sanitizers on `snc_gate`: **PASS** (MSVC ASan 2587341 = reference, UBSan-trap 3024920 = pin, 0 reports).
    The ON path on the same exes is clean too (UBSan ON 3254758 = gate ON d16, ASan ON 2505351, exit 0, 0 lines).
  - Box test with the counter build (`singular_noncut_counters_test.patch`, test only, `FORGE_SPEC_COUNTERS`):
    nodes = the gate exe's in all 4 runs. Live share 88-92 % of tries at cut nodes; ON has more nodes per
    verification (d20 22.2 vs 18.7); +1 / +2 share per try about the same, +2 slightly lower. Table in BENCH.md.

  - Mate probe OFF / ON, 02:37-02:38 (`tools/mate_probe.ps1`, crew set opus_r13 mate_probe.epd, 22 FENs):
    - at 3M nodes, mate found OFF 19, ON 19, both mate-in-1 found by both sides;
    - two deep KRK horizon flips (one each way); at 30M nodes both are mates on both sides;
    - no mate lost by ON. Details in BENCH.md.
  - All spec crew items are now done: counter box test, mate probe, L4. Not run: warm-table identity (not needed
    for a search candidate).

## In progress
- Nothing. The job waits for Code Review.

## Exact next step
Code Review of this pack: the patch, BENCH.md, README.md, and the branch-aware commit_push.sh. After CR, QA /
Strength run the SPRT with the gate line in README.md (cand = the gate exe with `setoption name SingularNonCut value 1`,
base = trial_w6 4181A589). Owner decisions for that SPRT: TC / book / bounds / Threads.

## Resume commands
- `git -C /f/ospd/wt switch opus-singular-noncut-20261105 && git -C /f/ospd/wt log --oneline -3`
- Push: write a message file under `D:\opus_singular_noncut\msg\`, then
  `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <message file>`.
- Rebuild the trees from git: copy `F:\ospd\src\lock` (check `lock_SOURCES.sha256`) to `D:\...\src\snc`, then
  `patch -p1 -F0 < opus_singular_noncut/singular_noncut_stack.patch`, then `bash opus_singular_noncut/tools/snc_controls.sh`.
- Builds (from Git Bash, never the PowerShell tool): `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  'F:\ospd\wt\opus_speed\tools\build_variants.ps1' -SrcDir 'D:\opus_singular_noncut\src\snc_id' -Tag <new tag>
  -Variant lp_v1 -Work 'D:\opus_singular_noncut\build'` (gate: `snc_gate`, add `-Twice`); a new tag per run.

## Unproven claims (and what is not done)
- Any Elo effect of SingularNonCut=1 in Forge: no Forge game result exists. The card estimates 0 to +3 at STC;
  Caissa's +4.20 is Caissa's own result. Fewer ON nodes at bench d20 / d22 (0.82 / 0.84 of OFF) are no strength
  evidence.
- ON nps: not measured. The PGO profile is trained with the option at 0, so the ON path is cold-optimised.
- Threads > 1 with ON: only what the smoke shows (it plays Threads 1).
- Done after the first DONE (02:32-02:38): the counter-build box test, the mate probe OFF / ON, L4 sanitizers (OFF +
  ON path).
- Not done: a warm-table identity run. bitexact L1-L3 are cold-table, Threads 1, which is enough for "runtime 0 =
  trial_w6" at a cold start; in-game tables are covered only by the smoke.
- The box-test counters are plain globals (valid at Threads 1 only). They live in a test-only patch, never in the
  gate exe.
- Code Review of this pack has not happened. Every review so far is my own (NOT independent).
