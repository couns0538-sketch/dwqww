# STATUS: job fable4cpu (Fable job 4, CPU only)

Last update: 2026-11-10 15:59 Vienna (T+0.15 h). Read this first after any interruption, then check the real state against it.

## Fixed facts

- T0 = 2026-11-10 15:50:08 Vienna (approval). Monotonic timer: `out\T0.json` (QPC ticks 1504117574091, frequency 10,000,000).
- Clock: the PC is set to Pacific time and its UTC clock runs 25,159 s ahead of github.com's Date header (measured at the clone, 14:50:43 GMT). The PC's local clock therefore shows Vienna minus 2 h 00 m 41 s. All times here are Vienna = PC UTC - 25,159 s + 1 h. `preflight_001.txt` was written before this was known and its "Vienna(PC clock)" label is 6 h 59 m ahead of true Vienna.
- Job folder `D:\forge_jobs_20261110\fable4cpu`: `repo` (clone), `out` (builds, copies, raw data), `tmp` (TEMP/TMP).
- Clone: `https://github.com/couns0538-sketch/dwqww`, branch `lock/combo29-20261110`, depth 1, no tags, no filter; `extensions.partialclone` unset; HEAD `16833ecc03b425586f91f4c8834dea8807bf4c22`. Work branch `fable52-cpu-20261110`. History before that commit is not local (reported limit, no further fetch).
- Lock exe copy `out\base\combo29_lock.exe`: MD5 `c0051c99695f48bf93272d96fe7548c3`, SHA256 `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e` (original and copy verified).
- My lock-recipe build `out\build\c29ctl\m2use\forge_m2use.exe`: MD5 `eaf05dca39eb20a794b873dc54849d45`, SHA256 `2542e9445b7776da8cd9a768ea10ad1325a4ddb8d47a36595f758c13d1997ebe`.
- CPUs: mask 0x707F only (0-6, 12-14). They are logical CPUs of an 8-core Ryzen 7 9850X3D. All my processes run at BelowNormal priority.

## Rulings in force (approved plan)

- R1 network: one clone (done) and normal pushes of this branch; nothing else.
- R2 the lock exe has no static-eval command, so "12,000-position static-eval parity against the lock" is reported BLOCKED (unobservable on the release exe); a source-level harness comparison and a release row comparison are delivered as separate evidence under their own names.
- R3 profile by my own instruction-pointer sampler plus `llvm-symbolizer`.
- R4 candidates are build flags that default to 0.
- R5 a patch is applied in the clone's working tree only for the moment needed to copy the patched source out, then reverted and hash-checked.
- R6 tool shells pin themselves in their first statement; children inherit.
- R7 a CPU counts as free when it averages under 10 % (max under 20 %) over three 10 s samples.
- Added by Couns at 15:52: no subagents under any circumstances; a 30-minute bug hunt at the end if useful.

## Items

| Item | State | Evidence |
|---|---|---|
| C0 preflight | done at 15:50: no chess process active; my CPUs 1,3,4,5,6,12,13,14 free; CPUs 0 and 2 carried outside load (avg 22 % and 12 %) from processes whose CPU use cannot be read; heavy work started on the free subset | `evidence/logs/preflight_001.txt`, `UTILIZATION.log` |
| C1 build and freeze | DONE: inputs frozen (every check OK), lock rebuilt, 13 of 13 pins equal | `evidence/logs/freeze.log`, `build_c29ctl.log`, `pins_c29ctl.log` |
| C2 dup check | not started | |
| C3 profile | not started | |
| C4 speed lane | not started | |
| C5 audit | not started | |
| C6, C7 | NOT RUN so far | |

## Running now

Nothing heavy. Next: checker self-tests, byte comparison with the lock exe, DUPCHECK.md, then the profile on CPU 12.

## Next command

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\forge_jobs_20261110\fable4cpu\repo\fable_cpu_speed\tools\pin.ps1 -Mask 0x707A -Exe C:\Python315\python.exe -ArgLine "-I -B <tools>\<script>.py ..."
```

## Notes for the owner (suggestions, nothing changed)

- PowerShell names are case-insensitive: my first `freeze.ps1` used `$R` and a loop variable `$r` and failed on its last step; fixed before any verdict was written.
