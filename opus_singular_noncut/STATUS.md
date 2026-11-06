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
- S1 01:27-01:29: branch created; `commit_push.sh` branch-aware; `IDEA_SOURCE.md` (Caissa 1b7a871, MIT notice
  verbatim); this file.

## In progress
- S2: source tree on D: (lock copy check, trial_w6 copy check, five edits), patches, apply proofs, preprocessor
  neutrality check.

## Exact next step
Copy `F:\ospd\src\lock` and `F:\ospd\src\trial_w6` to `D:\opus_singular_noncut\src\`. Check the lock copy with
`sha256sum -c F:/ospd/src/lock_SOURCES.sha256`. Check that `diff -ruN lock trial_w6 | md5sum` = 5786e9b8 (=
`opus_speed/patches/trial_w6.patch`). Copy trial_w6 to `snc` and make the five edits from the plan.

## Resume commands
- `git -C /f/ospd/wt switch opus-singular-noncut-20261105 && git -C /f/ospd/wt log --oneline -3`
- Push: write a message file under `D:\opus_singular_noncut\msg\`, then
  `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <message file>`.

## Unproven claims
- Any Elo effect of SingularNonCut=1 in Forge (card estimate 0 to +3 at STC; Caissa's +4.20 is Caissa's own result).
- Nothing is built or measured yet.
