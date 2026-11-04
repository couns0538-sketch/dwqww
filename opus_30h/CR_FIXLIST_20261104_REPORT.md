# Report-back: owner's fix list 2026-11-04, items 9-13 (30-h branch opus-30h-20261103)

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

Done by the R14-finish agent, verified by the main session at 14:3x PC clock: head cdc487a8714361da1f4a53414821028a21e2ee47

= remote, CI run 41835764229 success, report D:\a14\FINAL_REPORT.md md5 1e99b1a1c6ddb1ec4905dec002814dcd (its section

"Owner's fix list of 2026-11-04" has the per-item table: commits 87ef93ee + e3957e1f, new md5s, verify lines). Item 6's

PROOF.json rerun was not done (about 2 GB of scratch against the D: floor; the build is named in sep\TOOL_MD5_CHAIN.md).



The overlap is still unresolved: 4,088 board+side-to-move keys stay shared after en-passant normalisation (4,118 train

rows, 4,090 holdout rows); npt data stays BLOCKED.
