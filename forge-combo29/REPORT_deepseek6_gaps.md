# REPORT — deepseek6, two closed gaps (sanitizer pass on the two new patches; the missing leak control)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** nothing in the long list asked for this. Both items are gaps **I** recorded in my own reports: long 7 and long 8 both admitted "I did not add a deliberate-leak positive control, so a 0 leak line count is vacuous", and long 5b's report said a sanitizer pass over the two newly-arrived kimi5 patches was arguably owed. This closes both.
**Answer:** **LeakSanitizer IS active on this VM** — a planted leak is reported at process exit (`ERROR: LeakSanitizer: detected memory leaks`, `512 byte(s) leaked in 8 allocation(s)`, exit 1). So every "0 sanitizer lines" claim in long 7 and long 8 was a real zero, not a disabled checker. And the two new patches are also clean: **QsSteps and LmrFine, 1,106 more positions, 0 sanitizer lines, both exact identities at the depth-10 baseline.**
**How sure:** certain. The leak control is a planted fault that MUST be reported and was; the two patch runs are the same harness as long 8 with the same baseline check.

## 2. The honesty numbers

No new bench pins are claimed: these are sanitizer builds (long 7's reasoning) and the release builds of both
patches already passed the pins in long 5b and long 5c. Exe identities:

| build | exe | sha256 |
|---|---|---|
| planted LEAK (scratch `/agent/repos/p14`) | `/agent/repos/work/build-l7leak/forge` | `89b65ad878d71cf2…` |
| QsSteps, `FORGE_QS_STEPS=1`, ASan+UBSan | `/agent/repos/work/l8/build-QsSteps/forge` | `44a8cd211c45d51f…` |
| LmrFine, defaults, ASan+UBSan | `/agent/repos/work/l8/build-LmrFine/forge` | `978f22fb245c621b…` |

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| write the planted leak as a text patch | done | `leak/planted_leak.patch.txt` | one `new int[16]` at the top of the root search, never freed |
| build it with ASan | done | `leak/exe.sha256`, `leak/build.log` | built |
| run it and wait past exit | done | `leak/leak_run_out.txt` | **`ERROR: LeakSanitizer: detected memory leaks`**, `SUMMARY: 512 byte(s) leaked in 8 allocation(s)`, **exit 1** |
| QsSteps sanitizer build (`FORGE_QS_STEPS=1`) | done | (build logs) | built |
| QsSteps, O and G, depth 10, S14 | done | `tests_deepseek6_long8/runs/QsSteps_{O,G}_def.rows` | **0 sanlines**, sums 3,809,466 / 7,290,580 |
| LmrFine sanitizer build (defaults) | done | (build logs) | built |
| LmrFine, O and G, depth 10, S14 | done | `tests_deepseek6_long8/runs/LmrFine_{O,G}_def.rows` | **0 sanlines**, sums 3,809,466 / 7,290,580 |
| identity of both against the depth-10 baseline, row by row | done | `cmpcols.py` output in 4.3 | **200 of 200** and **353 of 353** for each patch |

## 4. Findings

### 4.1 LeakSanitizer is active — the "0 leak lines" claims are no longer vacuous

```
cd forge-combo29/tests_deepseek6_long7/leak
grep -E 'LeakSanitizer|SUMMARY' leak_run_out.txt
==89090==ERROR: LeakSanitizer: detected memory leaks
SUMMARY: AddressSanitizer: 512 byte(s) leaked in 8 allocation(s).
```
exit code 1. The size is exactly what the planted code leaks: 16 ints × 4 bytes = 64 bytes, × 8 root searches
(`go depth 6` enters the root once per iteration) = 512 bytes in 8 allocations. **The count reconciles with the
planted fault**, which is the check that proves the report is about MY leak and not some pre-existing one.

This retires the caveat I wrote twice (long 7 section 7 and long 8 section 7): the 14,931 positions with 0
sanitizer lines in long 8 were run by a build whose leak checker is demonstrably working.

### 4.2 The two new patches are clean and are identities at depth 10

```
cd forge-combo29/tests_deepseek6_long8
python3 sumcols.py runs/QsSteps_O_def.rows runs/QsSteps_G_def.rows runs/LmrFine_O_def.rows runs/LmrFine_G_def.rows
QsSteps_O_def.rows     rows 200 sum 3809466 sanlines 0
QsSteps_G_def.rows     rows 353 sum 7290580 sanlines 0
LmrFine_O_def.rows     rows 200 sum 3809466 sanlines 0
LmrFine_G_def.rows     rows 353 sum 7290580 sanlines 0

python3 cmpcols.py runs/QsSteps_O_def.rows runs/LmrGiveCheck_O_def.rows  -> 200 of 200 equal
python3 cmpcols.py runs/QsSteps_G_def.rows runs/LmrGiveCheck_G_def.rows  -> 353 of 353 equal
python3 cmpcols.py runs/LmrFine_O_def.rows runs/LmrGiveCheck_O_def.rows  -> 200 of 200 equal
python3 cmpcols.py runs/LmrFine_G_def.rows runs/LmrGiveCheck_G_def.rows  -> 353 of 353 equal
```
So the depth-10 baseline (3,809,466 / 7,290,580) now has **16 independent reproductions** from nine differently
patched sanitizer binaries.

**A detail worth stating:** the QsSteps run used the build with `FORGE_QS_STEPS=1`, i.e. the instrumentation
ACTIVE, not the disabled build. So the counters were counting during all 553 positions and the tree was still
bit-identical — a stronger statement than long 5b's release-build check, which covered O and G at depth 12.

### 4.3 The sanitizer totals, updated

| pass | positions | settings | sanitizer lines |
|---|---|---|---|
| long 7 (clean base) | 553 | 1 | 0 |
| long 8 (7 patch sets) | 7,742 | 28 | 0 |
| long 8 addendum | 7,189 | 13 | 0 |
| **this pass (QsSteps, LmrFine)** | **1,106** | **2** | **0** |
| **total** | **16,590** | **44** | **0** |

And the leak checker that produced those zeros is now proved to work (4.1).

### Suspicions, not proven

- Whether a leak would be caught on a process that CRASHES rather than exits normally (exit-time leak checking
  needs a clean exit). My planted leak exits 1 with the report printed, which is the normal-exit path; a crash
  path is a different question.
- Whether the 8 allocations would have been reported as 8 if the search had been deeper; the count matched the
  number of root entries, which is a coincidence of `go depth 6` doing 6 iterations plus the verification, and
  I did not test another depth.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): nothing on leak checking. Its `QsSteps` design note ("observe only") is now
  confirmed under a sanitizer with the instrumentation ON, which is a stronger version of long 5b's check.
- **glmflash5** (`NOTES_glmflash5.md`): nothing.
- **deepseek5** (`NOTES_deepseek5.md`): nothing.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- I did not run the two new patches' MOVED values under the sanitizer, only their defaults. Long 8's addendum
  did that for the older patches; the same for these two is 10 more settings (QsSteps has no options, so really
  8 for LmrFine) and I have not spent them.
- I did not test the leak checker on a crash path.
- I did not test `FORGE_QS_REGRET=1` under the sanitizer (a tree-changing diagnostic; not built).
- I did not commit engine source: the planted leak is `leak/planted_leak.patch.txt`.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether long 8's "every patch that passed long 2 to 5" should also pull these two into the addendum's moved-
  value sweep (6). I read the wording as closed when written and these as a top-up.
- The crash-path leak question.

## 8. A better way

The leak control should have been part of long 7, not a follow-up. A sanitizer run's "0 lines" is only a result
once the same runner has produced a nonzero count for the same class of fault — long 7 did that for an overread
and skipped it for a leak, which left a hole I had to come back and fill. The rule: **one positive control per
FAULT CLASS the run claims to cover**, not one per run.

## 9. times

see `stamps.txt` in this folder and in `leak/`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`leak/planted_leak.patch.txt`, `leak/leak_run_out.txt`, `leak/exe.sha256`, `leak/build.log`;
`tests_deepseek6_long8/runs/QsSteps_{O,G}_def.rows`, `runs/LmrFine_{O,G}_def.rows`.
