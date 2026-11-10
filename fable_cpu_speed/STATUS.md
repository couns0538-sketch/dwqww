# STATUS: job fable4cpu (Fable job 4, CPU only)

Last update: 2026-11-10 16:29 Vienna (T+0.65 h). Read this first after any interruption, then check the real state against it.

## Fixed facts

- T0 = 2026-11-10 15:50:08 Vienna (approval). Monotonic timer: `out\T0.json` (QPC ticks 1504117574091, frequency 10,000,000).
- Clock: the PC is set to Pacific time and its UTC clock runs 25,159 s ahead of github.com's Date header (measured at the clone, 14:50:43 GMT). The PC's local clock therefore shows Vienna minus 2 h 00 m 41 s. All times here are Vienna = PC UTC - 25,159 s + 1 h. `preflight_001.txt` was written before this was known; its "Vienna(PC clock)" label is 6 h 59 m ahead of true Vienna.
- Job folder `D:\forge_jobs_20261110\fable4cpu`: `repo` (clone), `out` (builds, copies, raw data), `tmp` (TEMP/TMP).
- Clone: `https://github.com/couns0538-sketch/dwqww`, branch `lock/combo29-20261110`, depth 1, no tags, no filter; `extensions.partialclone` unset; HEAD `16833ecc03b425586f91f4c8834dea8807bf4c22`. Work branch `fable52-cpu-20261110`. History before that commit is not local (reported limit, no further fetch).
- Lock exe copy `out\base\combo29_lock.exe`: MD5 `c0051c99695f48bf93272d96fe7548c3`, SHA256 `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e` (original and copy verified).
- My lock-recipe build `out\build\c29ctl\m2use\forge_m2use.exe`: MD5 `eaf05dca39eb20a794b873dc54849d45`, SHA256 `2542e9445b7776da8cd9a768ea10ad1325a4ddb8d47a36595f758c13d1997ebe`; code and data bytes equal the lock exe's (only the debug record and one header byte differ).
- CPUs: mask 0x707F only (0-6, 12-14). They are logical CPUs of an 8-core Ryzen 7 9850X3D. All my processes run at BelowNormal priority.

## Rulings in force (approved plan)

- R1 network: one clone (done) and normal pushes of this branch; nothing else.
- R2 the lock exe has no static-eval command, so "12,000-position static-eval parity against the lock" is reported BLOCKED (unobservable on the release exe); a source-level harness comparison is delivered as separate evidence under its own name. The release row comparison was planned only for a candidate at or above +2 %; none reached it.
- R3 profile by my own instruction-pointer sampler plus `llvm-symbolizer`.
- R4 candidates are build flags that default to 0.
- R5 a patch is applied in the clone's working tree only for the moment needed to copy the patched source out, then reverted and hash-checked.
- R6 tool shells pin themselves in their first statement; children inherit.
- R7 a CPU counts as free when it averages under 10 % (max under 20 %) over three 10 s samples.
- Added by Couns at 15:52: no subagents under any circumstances; a 30-minute bug hunt at the end if useful.

## Items

| Item | State | Evidence (under `evidence/logs/`) |
|---|---|---|
| C0 preflight | done 15:50: no chess process active; CPUs 1,3,4,5,6,12,13,14 free; CPUs 0 and 2 carried outside load (avg 22 % and 12 %) from processes whose CPU use cannot be read | `preflight_001.txt`, `../../UTILIZATION.log` |
| C1 build and freeze | DONE: inputs frozen, lock rebuilt, 13 of 13 pins equal; rebuild is code-and-data identical to the lock exe | `freeze.log`, `build_c29ctl.log`, `pins_c29ctl.log`, `bytecmp_lock_vs_c29ctl_r2.log` |
| C2 dup check | DONE as far as local sources go; branch history UNVERIFIED (not fetchable) | `../../DUPCHECK.md` |
| C3 profile | DONE: top category hand-crafted evaluation 20.9 % | `profile_bench22_neton_quiet.log`, `profile_bench22_neton.log`, `profile_call_counts.log`, `../../PROFILE.md` |
| C4 speed lane | running: candidate 1 `NNUE_WPREFETCH` stopped at -4.42 % (slower); candidate 2 `NNUE_FUSE_EVAL` identity steps all equal, timing running | `patch_*_apply.log`, `pins_wpf_*.log`, `pins_fuse_*.log`, `bytecmp_c29ctl_vs_*_off*.log`, `cmp_harness_*.log`, `timing_*.log` |
| C5 ASan | PASS: full bench 10 of 10, node counts equal the pins, no report | `san_fixtures_r2.log`, `san_build_asan_r2.log`, `san_bench_asan_r2.log` |
| C5 UBSan | PASS: full bench 10 of 10, node counts equal the pins, no report | `san_fixtures.log`, `san_build_ubsan.log`, `san_bench_ubsan.log` |
| C5 TSan | BLOCKED: the compiler refuses `-fsanitize=thread` for this target (both installed compilers) | `san_fixtures_r2.log` |
| C5 determinism | PASS: 13,000 of 13,000 row comparisons equal | `cmp_det_*.log` |
| C5 table stress | PASS: 480 of 480 row comparisons equal; ASan run 240 searches, no report | `cmp_tt_lock_*.log`, `ttstress_asan_on_1.rows.tsv` |
| Extra, not TSan | multi-thread fixed-node searches, Threads 2-9: 600 of 600 complete, legal best moves, no report | `mt_asan_r2.log`, `mt_ubsan.log`, `mt_release_lock.log` |
| C6, C7 | NOT RUN so far | |

## Things that went wrong and how they were handled

- `freeze.ps1` first failed on its last step (`$R` and a loop variable `$r` are the same name in PowerShell); fixed before a verdict was written. The same trap hit `cand_ladder.ps1` (`$T` / `$t`) after the pins of candidate 2; the remaining two steps were run by hand and the script was fixed.
- The first ASan engine link failed (duplicate `typeinfo for std::thread::_State` with the static libstdc++): `san_build_asan.log` records it. The link line got `-Wl,--allow-multiple-definition`, the fixtures were re-run with that same line (`san_fixtures_r2.log`), and the build was repeated as `san_asan2`.
- `bytecmp.py` first called the debug directory plus its record "code or data" because it judged a merged range as a whole and did not know the `.buildid` section. `bytecmp_lock_vs_c29ctl.log` and `bytecmp_c29ctl_vs_wpf_off.log` (verdict DIFFERENT) are from that version and are superseded by the `_r2` logs.
- The harness-set script expected the planted fault to show with the net off as well. It cannot: the fault is in network code. `cmp_harness_mutant_capture_column_vs_ctl_netoff.log` therefore says PASS, which is correct; the net-on comparison catches the fault in 9,619 of 12,000 rows.

## Running now

`abba.py` timing of candidate 2 on CPU 12 (parent on CPU 4), about 3 minutes. Utilization logger on CPU 1 (one line every 15 minutes until about 19:35).

## Next

1. Read `timing_fuse_1.log`; below +2.0 % the candidate is stopped.
2. Bug hunt on the lock source (30 minutes), findings with a reproduction, no fixes.
3. `README.md`, `DONE_head.md`, then `tools\make_manifest.py write` and `verify`, commit, push.

Command pattern for any step:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\forge_jobs_20261110\fable4cpu\repo\fable_cpu_speed\tools\pin.ps1 -Mask 0x10 -Exe C:\Python315\python.exe -ArgLine "-I -B <tools>\<script>.py ..."
```

## Disk

D: 31.8 GiB free at 16:28 (start 32.18). Stop line for builds and large writes: 31 GiB. Each timing run costs 54 MiB (a fresh exe copy per arm, kept); each lock-recipe build 17 MiB.

## Notes for the owner (suggestions, nothing changed)

- The weight table happens to start on a 64-byte line because of how the allocator places one large block (`probe_w1_alignment.log`). Nothing guarantees it; an explicitly aligned allocation would make it a property of the code.
- Foreign processes seen on CPU 15 (two `python`, mask 0x8000, CPU 15 at 100 %) and a `powershell` with mask 0xFF87 that overlaps my CPUs 0-2 lightly. Not touched.
