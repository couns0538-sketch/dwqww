# REPORT — deepseek6, long 4b (kimi5's SoundSteps patch, on the chain its own header requires)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** the long-2 test for `SoundSteps.patch.txt` on a clean copy of 6b98f217.
**Answer:** it CANNOT be applied to a clean copy — its own header says it applies after `SoundRegret.patch.txt`, and I proved the clean-copy dry run fails and the chain dry run passes. On the chain SoundArms+SoundRegret+SoundSteps it is an exact identity at the defaults (200/200 O, 353/353 G, 200/200 O-none, all four honesty numbers), its one unique option `SoundStepMask` is inert whenever no arm's case is active (as its own comment requires) and IS wired when a case is active, and measuring all six single bits found that **bit 4 (step 5, capture futility) is dead inside a PV case** and **bit 3 (step 4, quiet SEE) is by far the largest**, while `mask=0` with the arm forced on is byte-identical to the plain base.
**How sure:** certain of every number and every row-by-row equality; the claims about which step is "dead" or "largest" are measurements of node sums, not explanations, and are labelled so.

## 2. The honesty numbers (on the chain, all options at their defaults)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe `/agent/repos/work/build-l4b/forge`, sha256 `b8e0d1668c9afe202a07ece8ad029914e0c44c029bb64fccf0f46c555a098dd2`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate` (`uci.txt`). Clean copy `/agent/repos/p6`
at 6b98f2170a3210e71beed04bbd2553972c253ed7.

## 3. Steps

### The application (this is a step of its own, because the answer is "clean copy: no")

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| dry run on a CLEAN 6b98f217 | done | `patch_apply.txt` (see section 4.1) | **FAILS** — "Hunk #1 FAILED at 354", the `search.hpp` hunk |
| dry run on SoundArms+SoundRegret | done | `patch_apply.txt` | **passes**, all 3 files |
| apply SoundArms -> SoundRegret -> SoundSteps, each `-p1 --fuzz=0` | done | `patch_apply.txt` | three clean applications, exit 0 each |
| build | done | `exe.sha256` | Release g++ 13.3.0, 0 errors, 0 warnings |
| honesty at the defaults | done | `honesty_*.txt` | all four met |

### The long-2 test, on the chain

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| identity O/S14 vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, sum 9,500,069 |
| identity G/S14 vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, sum 18,466,239 |
| identity O/none vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, sum 12,573,318 |
| inert with no case active: `SoundStepMask=0` | done | `O_S14_sm0.rows` | **9,500,069, 200 of 200 equal** (predicted) |
| inert with no case active: `SoundStepMask=21` | done | `O_S14_sm21.rows` | **9,500,069, 200 of 200 equal** (predicted) |
| wired with a case active: `SoundPvArm=1`, mask 63 | done | `O_S14_pv63.rows` | **9,966,105**, and **200 of 200 equal** to long 4a's `SoundPvArm=1` |
| wired with a case active: `SoundPvArm=1`, mask 0 | done | `O_S14_pv0.rows` | **9,500,069 — byte-identical to the plain base**, 200 of 200 equal |
| wired: each single bit, `SoundPvArm=1` | done | `O_S14_pv{1,2,4,8,16,32}.rows` | six different sums, all ≠ 9,966,105 — except 16, see 4.4 |
| `SoundPvArm=1`, mask 62 (all but bit 0) | done | `O_S14_pv62.rows` | **10,344,833** |
| out-of-range stop: `SoundStepMask=64` | done | `stopcheck_sm64.rows` | `invalid value`, stopped, exit 2 |
| word-value stop: `SoundStepMask=true` | done | `stopcheck_smword.rows` | `invalid value`, stopped, exit 2 |

## 4. Findings

### 4.1 The patch does not apply to a clean copy, and the reason is in its own header

Its first line is `# applies from the repository root, AFTER SoundRegret.patch.txt: patch -p1 <
SoundSteps.patch.txt`, and the third hunk needs the `SoundRegretCounts` struct that `SoundRegret.patch.txt`
adds to `include/forge/search.hpp`. Verified both ways:

```
cd /agent/repos/p6   (clean 6b98f217)
patch -p1 --fuzz=0 --dry-run < SoundSteps.patch.txt
  -> Hunk #1 FAILED at 354.  1 out of 1 hunk FAILED
(after SoundArms and SoundRegret)
patch -p1 --fuzz=0 --dry-run < SoundSteps.patch.txt
  -> checking file forge-combo29/src/uci.cpp / src/search.cpp / include/forge/search.hpp   exit 0
```
So "the same [test] for SoundSteps" cannot mean a clean copy. I ran the chain and I say so in every table.

### 4.2 The chain is an exact identity at the defaults

```
cd forge-combo29/tests_deepseek6_long4/SoundSteps
python3 cmprows.py O_S14_def.rows ../../../tests_deepseek6_long1/O_S14.rows   -> 200 of 200 equal
python3 cmprows.py G_S14_def.rows ../../../tests_deepseek6_long1/G_S14.rows   -> 353 of 353 equal
python3 cmprows.py O_none_def.rows ../../../tests_deepseek6_long1/O_none.rows -> 200 of 200 equal
```
This also says SoundRegret is inert at its defaults (`SoundRegretCount=false`, `SoundRegretProbe=false`),
which long 4a could not say because SoundRegret was not in that build.

### 4.3 The gate `sound_mate_case ? SoundStepMask : 0` behaves exactly as its comment says

With all three arms at 0 and `SoundMatePruning=false`, `sound_mate_case` is false, the gate is 0, and the
mask cannot matter:

```
SoundStepMask=0   -> 9500069, 200 of 200 equal to the default
SoundStepMask=21  -> 9500069, 200 of 200 equal to the default
```
That is a **positive** result about the patch's structure, not a skipped test: an option that leaked
outside its case would have shown here.

### 4.4 The mask IS wired, and all six single bits move the tree differently

With `SoundPvArm=1` so a case is active, over 200 positions of O under S14:

| mask | bits set | sum | delta vs base 9,500,069 |
|---|---|---|---|
| 0 | none (prune like an ordinary node) | **9,500,069** | **0 — byte-identical to the base, 200 of 200 rows** |
| 1 | s1 LMP | 9,476,627 | −23,442 |
| 2 | s2 futility | 9,477,552 | −22,517 |
| 4 | s3 history prune | 9,501,148 | +1,079 |
| 8 | s4 quiet SEE | 10,206,405 | +706,336 |
| 16 | s5 capture futility | **9,500,069** | **0 — byte-identical to the base, 200 of 200 rows** |
| 32 | s6 noisy SEE | 9,858,330 | +358,261 |
| 63 | all six (today's arm) | 9,966,105 | +466,036 |
| 62 | all but LMP | 10,344,833 | +844,764 |

Three results here that are worth more than the wiring proof:

1. **`mask=0` with the PV arm forced on is the plain base, row for row.** That is exactly what the design
   intends (skip no steps = behave like an ordinary node = the case has no effect) and it is a strong check:
   it says the arm's ONLY effect on the tree is the six steps the mask controls, with nothing else riding
   along on `sound_mate_case`.
2. **Bit 4 (step 5, capture futility) is dead in a PV case at depth 12 on O.** `mask=16` alone equals the
   base to the row. **Suspicion, not proven:** the capture-futility guard also requires `capture &&
   !in_check && !gives_check && lmr_depth <= CaptureFutilityDepth`, and at a PV node in these 200 positions
   that combination apparently never fires before the mask would have skipped it. A probe would need the
   counter `SoundRegretProbe` turned on, which I did not do.
3. **Bit 3 (step 4, the quiet SEE test) is the biggest single step by a factor of ~20** over the next
   largest (+706,336 vs +358,261), and the two "s1/s2" bits are NEGATIVE — skipping LMP or futility makes
   the tree slightly SMALLER, which is the opposite of the direction I predicted and of the intuition "skip
   more pruning = search more".

**My filed bands were missed.** I predicted both `mask=1` and `mask=62` would land strictly between
9,500,069 and 9,966,105. `mask=1` is 9,476,627 (below the floor) and `mask=62` is 10,344,833 (above the
top). I record both as missed, and in the same breath: the reason is the same lesson as long 3 — the six
steps do not add up, because turning a pruning step off changes which moves survive to be pruned later. The
"sum of the parts" is 58,020,131 against a whole of 9,966,105, i.e. not even the right order of magnitude
for anything additive.

### Suspicions, not proven

- Why skipping LMP or futility makes the tree SMALLER: a pruned move that is searched can raise `best_score`
   or change `improving`, which then affects later moves' reductions and the LMR depth of the whole node. I
  did not instrument this; the numbers are the finding.
- Whether bit 4 is dead at other depths or on G. I tested O only at depth 12 for the six single bits
  (6 runs, 30 s); G would be another 6 runs and I did not spend them.
- Whether the single-bit responses are stable across sets: one set, one depth.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its job-9 note reports the *other* end of this family — `NullStaticSlope 48`
  = 27.0 % of O best moves at +1.2 % tree, etc. — and says all eight options of `NodeLiterals.patch.txt`
  passed defaults-identity on 553 positions x 2 profiles. That patch is long 5 material; I have not opened it.
  Its notes do not claim anything about `SoundStepMask` beyond the design sentence in the patch header, which
  I verified independently.
- **glmflash5** (`NOTES_glmflash5.md`): its job-15 note puts `qseewide` (its own quiet-SEE experiment) at
  −15.4 pool; my bit 3 result says the quiet SEE step is the largest single lever inside a PV case on my
  tree (+706,336 nodes when skipped). Different questions (its is strength, mine is tree size), but they
  point at the same step as the one that matters. I do not claim its −15.4 from my data.
- **deepseek5** (`NOTES_deepseek5.md`): its job-30 lesson (read the state variable when the event happens)
  is precisely the trap bit 4's silence sets — a step that never fires cannot be seen by a counter read at
  the wrong moment. I did not use a counter here, so the silence is a tree fact, not a counter artefact.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- **SoundSteps was not applied to a clean copy, because it cannot be.** This is the one place I departed
  from long 4's literal wording, and section 4.1 is the proof that the departure was forced. Everything
  about `SoundStepMask` in this report is a statement about the 3-patch chain, not about SoundSteps alone.
- I did not run the six single bits on G, or at another depth.
- I did not turn on `SoundRegretProbe`/`SoundRegretCount`, so I have no counters and no explanation of bit 4's
  silence beyond the code reading.
- I did not measure strength; a node sum is not a verdict.
- I did not commit engine source; the three patches are committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether "the same test" for SoundSteps should have been refused outright with a request for a rebased
  patch. I chose to run the chain so there would be a result either way, and I flagged it in the first
  three lines.
- Bit 4's silence (4.4 item 2) is a fact for O/depth 12 and a guess everywhere else.
- The negative signs on bits 0 and 1. I have no mechanism for them.

## 8. A better way

The single-bit sweep is the cheap way to test any masked option: six runs, 30 s, and it produced three
findings (a dead bit, a dominant bit, and a `mask=0` identity) that no single moved value could have shown.
For long 8's "each option moved once", a mask-typed option should get the single-bit sweep, not one value.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`ls` + `git status --short` before this commit: `precommit_evidence.txt`.
