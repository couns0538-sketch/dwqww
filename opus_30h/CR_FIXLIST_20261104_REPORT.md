# Report-back: owner's fix lists of 2026-11-04 (list 1 items 9-13 here, 0-8 on the R14 branch; list 2 items 1-7)

Before-edit md5 check (certutil-equivalent md5sum of the PC file vs the list):
- main.rs: 5aa38dab, list 2a61a522 -> CHANGED since review (review fix G-001 in 8860bac6, 11:18); re-read before editing.
- o30_gpu_guard.py: 9b6855e9, list 060e0a6f -> CHANGED since review (G-003 / G-006 in 8860bac6); re-read before editing.
- gpu_ckpt_watch.sh: 4305ad3f = list (reviewed version). warmproof01.out: cc578ed4 = list (kept unchanged; new proofs added).
- pins_lockkb8_v2p4.txt 5c50ee2d, lockstep_200k_5g.out 7700dd38 before the labels (no md5 in the list).

| item | commit | changed files (md5 at that commit) | verify output line |
|---|---|---|---|
| 10 | 8b57f4a8 | a/forge_v2_bullet_o30/src/main.rs a3e5f156; a/logs/gpu/cr10_refusal01.out c485b032; a/logs/gpu/build_rocm_cr10.log ffeb6f9b; a/logs/gpu/WINDOW.md 1bf6f674 | 3 cases (no CLIP+DECAY / CLIP only / DECAY only): "refusing: O30_INIT_DIR (warm start) needs O30_CLIP and O30_DECAY set explicitly ..." "exit 2; out dir created: no"; with both set: warmproof03_rocm3 "COMPARE: byte-identical -> PASS". New build D:\o30\target_rocm3 (exe md5 d0395d88); the running job's exe untouched |
| 9 | 24d98b82 | a/o30_gpu_guard.py 78994100; a/o30_guard_dummy.py 6d7cec59; a/logs/gpu/cr9_guard_tests.out b4c2b1a2 | hard self-termination while suspended: "beats with the guard gone: 0 -> 0 over 5 s (equal = frozen)", "dummy status stopped", "resumed pid 12968 ... status before stopped, after running"; injected errors: "ABORT: 15 poll errors in a row ... Trainer LEFT SUSPENDED (fail closed) ...", guard exit 79, "beats after ABORT: 39 -> 39" |
| 11 | f9136f2f | a/logs/gpu/warmproof02_rocm2.out 5f940f12; warmproof03_rocm3.out ce48ca67; warmproof04_kb16.out 87cc6dfe; STATUS.md fb8ffe30 | each log: "AdamW weight clip +-7.99 decay 0", exe md5 + sha256, env, "COMPARE: byte-identical -> PASS" (02 = exe of runs 2-6 md5 04b6944a, 03 = item-10 build) |
| 12 | 16e84bc9 | a/gpu_ckpt_watch.sh ef8d3e07; a/logs/gpu/cr12_watch_tests.out 7ab9e7ed | fake log, no end line, cap 1 min: "GIVE UP: no end line ... after 1 min" "exit 3 after 64 s"; failing TSV step: "GIVE UP on ... after 2 failed tries (no .done written)" ".done present: 0" exit 5; control: ".done present: 1" exit 0 |
| 13 | 345cf411 | a/logs/bughunt/pins_lockkb8_v2p4.txt 27e36d6e; a/logs/bughunt/lockstep_200k_5g.out e0b15d57 | first line "LABEL ...: pin_check FAIL expected: identity net, benches 312866/862329/3024920 equal the lock, perft OK."; lockstep header names both exes (sha256) and the net (md5) |

Not done / needs the owner: item 13's last part - the 4-h GPU window quote in WINDOW.md cannot be verified from the
branch; it is copied verbatim from the session; please confirm it (and the second, 5-h quote added 13:27).
Item 9 caveat: the console handler (Ctrl+C / close) is in the code but was not exercised by a test (no console in the
agent's shell). The new guard was installed 13:39; run 7 (started 13:36) ran under the previous version; run 8
(started 13:50:22) is the first real trainer under the new guard (start line with pid + create time, no poll errors).
Item 11 wording: no exe built from exactly da62a1a8's main.rs (2a61a522) ever trained a run. The proofs ran on the exe
that trained runs 2-6 (D:\o30\target_rocm2, built 11:17:34 from 8860bac6's main.rs 5aa38dab = da62a1a8 plus the
G-001 assert line only; the clip/decay path is identical) and on the item-10 build.

## Items 0-8 (R14 finish, branch opus-astra-r14-finish)

Done by the R14-finish agent, verified by the main session at 14:3x PC clock: head
cdc487a8714361da1f4a53414821028a21e2ee47 = remote, CI run 41835764229 success, report D:\a14\FINAL_REPORT.md md5
1e99b1a1c6ddb1ec4905dec002814dcd (its section "Owner's fix list of 2026-11-04" has the per-item table: commits
87ef93ee + e3957e1f, new md5s, verify lines). Item 6's PROOF.json rerun was not done (about 2 GB of scratch against
the D: floor; the build is named in sep\TOOL_MD5_CHAIN.md). The branch moved on with fix list 2 (below); its final
head is 0e9f68e160c9a9a0b797331f2b0864c3e6f2cca5.

The overlap is still unresolved: 4,088 board+side-to-move keys stay shared after en-passant normalisation (4,118 train
rows, 4,090 holdout rows); npt data stays BLOCKED.

## Fix list 2 of 2026-11-04 (CR_O30_6033_R14FIN_CDC4), items 1-7

Before-edit md5 check (certutil): queue_runner.sh f5ae44c2e1f1632b1bd962a97bf4e9c0, probe_extra.sh a9f7585174e849da8b3bec605c4849c1, STATUS.md 7baf03653d1e12dca33d51b4a56d32fc and o30tuned_tuned184.patch eaa42c9fb3806a884c46a6f635548b93 = the reviewed versions; o30_gpu_guard.py fb4d6a38 CHANGED since the review's 78994100 (commit ee316963, review fixes W2-03 / W2-04) -> re-read before editing.
md5s are of the file in that commit (`git show <commit>:<path> | md5sum`). No promotion, no --confirm-owner-decision.

| item | commit | changed files (new md5) | verify output line |
|---|---|---|---|
| 1 | 73e4c828 | a/queue_runner.sh 36de6806d5cfd7be663f504709ee10b0; a/logs/fix2/item1_runner_test.out 2047d9115dfa626dfa9733c412b14649; a/logs/fix2/item1_stub.sh e199d3154c58615f0306dc07429d3e6a | stub exits 78 then 0: "rX_test refused at start (exit 78): not marked; retry in 3 s", "stub run rX_test call 2: plan.done now: []", "rX_test exit 0", "plan.done after the run: [rX_test ]", "calls: 2" |
| 2 | 8f473e8a + 0b245bbc | a/o30_gpu_guard.py 34a49a48926ddce4c5d6fc636d20ddcb; a/logs/fix2/item2_guard_race_test.out 57d0cee00bc59e562db4cf2e7c34e663; a/logs/fix2/item2_guard_regression.out 687910f5244f4f72a2ba0aeb43a00f8b | forced race on a dummy (never the live trainer): "console event 1: guard exits; trainer (pid 9416 ...): it was suspended by the guard and has just been resumed", "dummy pid 9416 cpu time 4.14 s -> 7.14 s over 3 s: RISING = running"; regression: "resumed pid 7376 ... status before stopped, after running", "beats after resume: 4" |
| 3 | 3bc5cd88 | a/logs/checks_gpu/scripts/probe_extra.sh 25dcb4158ae8c1123ed4ab49f3acedf3; a/logs/fix2/item3_probe_rc_test.out 1fad0021b8eb0a50b8cff67733dc0a1c | stub step exit 0 and 75: "probe_extra testnet tagX end ... rc=0", "probe_extra testnet tagX end ... rc=75" |
| 4 | 101379e6 | STATUS.md 3968c83ed429d71fa90357319decd2ec; skills/forge-o30-v2net/SKILL.md 470ca54092432a3bc3c8e6f2940730fc; a/logs/fix2/item4_verify.out 329ed9c106ce2ae1aa1fa1f1d98b1ebb | "Select-String 'beat every' -> 0 lines"; the layout-speed lines say "SINGLE RUNS" (later replaced by 3-4-run means: KB8 0.988, KB16 0.969, KB32 0.942) |
| 5 | 6085d7b2 | b/logs/itemB/build_o30tuned_tuned184.out 0fb5a98dfadea95cc875bc6f9c41c94a; b/logs/itemB/tuned184_pc1.out f33fca047d18e9ffe5d714eef498030c; b/logs/itemB/tuned184_pc2.out 9718aa2767b1192d1a81426953f38a1b | logs only, patch unchanged (eaa42c9f = reviewed): "PASS 3 true then false = the lock pins", "O30TUNED PASS exe .../forge_ltopgo_tuned184_pc1.exe (3b35f5cfa662f4f0...)" |
| 6 | 78d83508 (R14 branch) | D:\a14\tools\opus_prod_separation.py 7f0a3ae03e02a2b8ee551c3548aef782; D:\a14\TOOLS.md 89f181ae43a42bbe76422569f5d2d64b; D:\a14\sep\TOOL_MD5_CHAIN.md 038647fcf3ffe3763f3f31c6416ca444; evidence\test_logs\r14\opus-prodsep-relpath01\output.log 0875daed9ceff901fd078458ea9bcc30 + command.txt 23c39367611781287d3ccb04a3d1ee5c | "refusing to write PROD_SEPARATION.json: refusing: C:/a14x/prodsep_relpath_test/x.json not under D:/a14/", exit code 1, "traceback present: False", dummy md5 d11d325009336b0f249138a1abea9fdf unchanged, "RESULT PASS" (path C:\a14x instead of the list's C:\Users\Administrator\scratch: the job's own scratch, also another drive) |
| 7 | 78d83508 + 179430bd (R14 branch) | D:\a14\tests\test_r14_preflight.py dfdf6235e5d88aed5f99bbfd2464cd51 (Import-Module of the two modules before the mocks); suite log evidence\test_logs\r14\full-suite-r14cont03\output.log 0e607316e0b09f1b746bf56c6d894b30 (first line 78d83508c7291321330ab356f14d8e1a9f8602f5); R14_OPEN_ISSUES.md 97913e353b975b300ddb692c0a8ce376 | "8 failed, 328 passed, 67 subtests passed in 64.54s (0:01:04)"; test_floor_breach_after_hash_writes_no_receipt passed (not in the failed list), so no "does not prove the floor rule" label was needed. Failures: F-003 (1), F-005 (2), F-006 (1) as before + 4 launcher cases refused by the CPU-admission guard ("CPU admission refused", the suite's own CPU above 70 %) - environmental, they passed on CPUs 1 and 2 earlier |

Correction to item 1 (found in the end-of-job bug hunt, 19:2x): the retry of 73e4c828 could never start the run.
The guard opens <run>.guard.log before its checks and the bat's redirect creates <run>.out; the bat refuses a
run whose folder / .out / .guard.log exist (exit 4), so the retry landed in plan.failed (and queue_runner2.sh's
retries in plan2.skipped). The item-1 stub created none of these files. Fixed in 1ab804be: before a retry both
runners move the attempt's files aside as <file>.refused<N>; a/queue_runner.sh 841113255756ed419012eab8e5f46678,
a/queue_runner2.sh d86daaf474879b162a02823967cded0d; verify a/logs/bughunt/runner_retry_test.out
(defc3649981fa5f3fae993c5fc6a641d): old runner "stub call 2: ABORT: rX_test.out exists (the bat's check) -> exit 4",
"plan.failed: [rX_test rc 4 ...]"; new runners "stub call 2: trainer started and ended (exit 0)", "plan.done: [rX_test ]".
No refusal happened in the live window (plan2.refused and plan2.skipped empty), so no run was lost.

R14 branch after the list: report commits ed068336 + 0e9f68e1; head 0e9f68e160c9a9a0b797331f2b0864c3e6f2cca5 = remote,
CI run 41872225602 success, D:\a14\FINAL_REPORT.md md5 9a011f87f70ea8b7264b311fa6c040b8 (addendum "owner's fix list 2").
Not done: none of items 1-7. Still open from earlier: item 6 of the first list (PROOF.json rerun, disk floor) and the
owner's confirmation of both window quotes in D:\o30\WINDOW.md. The 4,088-key overlap is unchanged.
