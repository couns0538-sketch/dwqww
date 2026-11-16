# REPORT — deepseek6, the depth-14 identity repeat, and long 7 at depth 12

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** the long list's step after long 8 — "long 5 again for any new kimi5 patch; otherwise long 2 to 4 again at `go depth 14` on O (the identity must hold at every depth), then long 7 at depth 12."
**Answer:** long 5 has nothing new (only `NodeLiterals` exists for N ≥ 9, already done in long 5a), so I ran the depth-14 repeat: the plain build's depth-14 sum on O/S14 is **21,812,100**, it is bit-identical across two processes, and **all five patch sets from long 2–4 reproduce it 200 of 200 rows at depth 14**. Then long 7 at depth 12: **0 sanitizer lines** on O (200) and G (353), and the sanitizer build's depth-12 sums are **exactly** the published 9,500,069 and 18,466,239, row for row.
**How sure:** certain — every number is a raw rows file with a `.meta`, and the depth-14 baseline was measured twice before any patched build touched it.

## 2. The honesty numbers

No new release build was made for this step (all six exes are the ones long 1–4 already built and already passed
the pins with); no sanitizer build is asked to pass the pins (see long 7's reasoning). Exe identities:

| exe | sha256 (first 16) | used for |
|---|---|---|
| `/agent/repos/work/build-base/forge` | `e06310eca3368556` | the depth-14 baseline, and the depth-12 comparison |
| `/agent/repos/work/build-l2/forge` | `919a4f4ecda2ea75` | LmrGiveCheck at depth 14 |
| `/agent/repos/work/build-l3a/forge` | `0fb846a67ff2e975` | LmrCutNode at depth 14 |
| `/agent/repos/work/build-l3b/forge` | `926f48eba93f5583` | LmrTtPv at depth 14 |
| `/agent/repos/work/build-l4a/forge` | `ed29427b10efba49` | SoundArms at depth 14 |
| `/agent/repos/work/build-l4b/forge` | `b8e0d1668c9afe20` | SoundSteps chain at depth 14 |
| `/agent/repos/work/build-l7san/forge` | `9e3de2e5a1b12c1d` | ASan+UBSan, depth 12 |

The base build's four pins were met in long 1 (`tests_deepseek6_long1/honesty_*.txt`) and that exe's sha256 has
not changed (`e06310eca3368556…`).

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| long 5 again: any new kimi5 patch with N ≥ 9? | done | (this report, and `git ls-tree` over kimi5's branch) | **none** — only `tests_kimi5_job9/NodeLiterals.patch.txt`, done in long 5a |
| depth-14 baseline, plain build, O/S14, run 1 | done | `O_S14_d14_base_r1.rows` | sum **21,812,100** |
| depth-14 baseline, run 2 (a separate process) | done | `O_S14_d14_base_r2.rows` | **200 of 200 equal**, sum 21,812,100 |
| LmrGiveCheck defaults at depth 14 | done | `O_S14_d14_LmrGiveCheck.rows` | **200 of 200 equal** |
| LmrCutNode defaults at depth 14 | done | `O_S14_d14_LmrCutNode.rows` | **200 of 200 equal** |
| LmrTtPv defaults at depth 14 | done | `O_S14_d14_LmrTtPv.rows` | **200 of 200 equal** |
| SoundArms defaults at depth 14 | done | `O_S14_d14_SoundArms.rows` | **200 of 200 equal** |
| SoundSteps chain defaults at depth 14 | done | `O_S14_d14_SoundSteps.rows` | **200 of 200 equal** |
| long 7 at depth 12: sanitizer build, O under S14 | done | `O_S14_d12_san.rows` | **0 sanitizer lines**, 200 positions, sum 9,500,069 |
| long 7 at depth 12: sanitizer build, G under S14 | done | `G_S14_d12_san.rows` | **0 sanitizer lines**, 353 positions, sum 18,466,239 |
| a bonus check I did not plan: sanitizer vs release at depth 12, row by row | done | `cmpcols.py` output in 4.3 | **200 of 200** and **353 of 353 equal** |

## 4. Findings

### 4.1 The depth-14 identity holds for every patch that passed long 2–4

```
cd forge-combo29/tests_deepseek6_depth14
for n in LmrGiveCheck LmrCutNode LmrTtPv SoundArms SoundSteps; do
  python3 cmprows.py O_S14_d14_$n.rows O_S14_d14_base_r1.rows
done
200 of 200 equal     (each of the five)
```
All five sums are 21,812,100, the same as the plain build's. So the claim "the default is an exact identity"
is now established at depth 12 (long 2–4), depth 14 (here), and depth 10 in a sanitizer build (long 8) — three
depths and two build types.

### 4.2 The depth-14 baseline is itself reproducible, which is what makes 4.1 mean anything

```
python3 cmprows.py O_S14_d14_base_r1.rows O_S14_d14_base_r2.rows
200 of 200 equal
```
Two separate processes, same 200 rows, same 21,812,100. Had the baseline wobbled, "200 of 200 equal" for a
patched build would have been a much weaker statement.

Cost, for later jobs: **12 s per 200-position depth-14 run on O** (measured: 11.99 s and 12.36 s for the two
baseline runs; the five patched runs took 60.6 s total, about 12 s each). Depth 14 on O is cheap on this VM.

### 4.3 The sanitizer build at depth 12 is bit-identical to the release build, and reports nothing

```
python3 sancount.py O_S14_d12_san.rows   ->  sanlines 0 (positions 200),  sum 9500069
python3 sancount.py G_S14_d12_san.rows   ->  sanlines 0 (positions 353),  sum 18466239
python3 cmpcols.py O_S14_d12_san.rows ../tests_deepseek6_long1/O_S14.rows  -> 200 of 200 equal
python3 cmpcols.py G_S14_d12_san.rows ../tests_deepseek6_long1/G_S14.rows  -> 353 of 353 equal
```
This is worth more than the "0 sanitizer lines" alone: it says the sanitizer instrumentation changed **not one
node** of the search on 553 positions. If ASan/UBSan had perturbed any arithmetic (or if the base engine had
UB that the release build silently exploited), these rows could not have matched the release build's rows to
the node.

**A caution I have to state:** this equality is evidence that the sanitizer build behaves like the release
build, NOT evidence that the sanitizer sees everything. It only means no observable UB was triggered on these
positions.

The sums here are the FIRST time the published depth-12 known answers have been reproduced by a build that is
not the plain release build. Long 1's 9,500,069 and 18,466,239 are now confirmed by a second, very differently
compiled binary.

### Suspicions, not proven

- Whether the depth-14 identity would still hold on G. This step's wording says "on O", so I ran O only; G at
  depth 14 is cheap enough (about 20 s) that I could run it in a later pass.
- Whether depth-16 or depth-20 identities hold. The pattern (three depths, two build types, always exact) makes
  me expect yes, but "expect" is not "measured".

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its job-9 note says `NullEvalRedMax` caps are invisible at depth 12 and may need
  depth > 12 — which is a direct reason to be careful with any depth-14 conclusion about the NodeLiterals
  options. I did not test NodeLiterals at depth 14 (it is not in long 2–4), so that caution does not touch 4.1,
  but it is the reason I am not extending 4.1's "identity holds" claim to that patch set here.
- **glmflash5** (`NOTES_glmflash5.md`): nothing on depth.
- **deepseek5** (`NOTES_deepseek5.md`): nothing on depth.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- I did not run the depth-14 identity on G (the step says "on O").
- I did not run depth 14 for `NodeLiterals` or my own `IirNoRoot`; the step names long 2 to 4, and long 5's
  patch was not asked for at depth 14. `IirNoRoot` is mine and not in any of those ranges.
- I did not run long 7 at depth 12 for the PATCHED builds (long 8 did depth 10 for those; this step says "then
  long 7 at depth 12", which I read as the plain base at depth 12).
- I did not test whether LeakSanitizer is enabled (the same missing positive control as long 7; I said in long 7
  I would add a deliberate-leak control if a job allowed, and this step's wording did not).
- I did not commit engine source; no source was changed for this step at all.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether "long 7 at depth 12" meant the plain base (my reading, because long 8 already did the patches at depth
  10) or every patch again at depth 12 (which would be another 25 minutes). I took the cheaper reading and I say
  so plainly so the reading can be corrected.
- The leak-check question, unchanged from long 7.

## 8. A better way

The depth-14 baseline should have been measured as part of long 1, not discovered here. A single new number
(21,812,100) defined the reference for five identity checks, and if the plain build had been wrong at depth 14
every one of the five "200 of 200 equal" results would have been equal to the WRONG number. Recording baselines
at several depths up front turns every later identity check into a comparison against a known answer instead of
against another build. I will add depth 10/12/14/16 baselines for both sets to my notes for the next such job.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`precommit_evidence.txt`; the 7 depth-14 rows files; the 2 depth-12 sanitizer rows files (raw logs dropped, same
policy as long 8 — `sancount.py` output is in the run logs, and every path/option is in the `.meta`).
