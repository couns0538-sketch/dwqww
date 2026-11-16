# REPORT — deepseek6, long 8 ADDENDUM (every option moved once, not one per patch set)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** my long-8 report said plainly that I had moved only one option per patch set when long 8's wording is "each option moved once". This addendum finishes that: 13 more settings (the remaining options of `SoundArms`, the `SoundSteps` chain and `NodeLiterals`), each under the sanitizer.
**Answer:** **7,189 more positions, 0 sanitizer lines, 0 nonzero exits.** With the original 28 settings that is **14,931 positions over 41 settings, 0 sanitizer lines**. The one surprising number is `SoundRegretProbe=true`, which inflates the tree by 939 % on O and 588 % on G — a real search cost, explained by the code, and still zero sanitizer lines.
**How sure:** certain of the zeros and the sums; the Probe explanation is a code reading I quote, labelled as such.

## 2. The honesty numbers

No new build was made: the same seven sanitizer exes as long 8 (`builds/*/exe.sha256`), used here for the
additional options. No pins are claimed for a sanitizer build (same reasoning as long 7). The identity available
and used: every setting's DEFAULTS run is the same one long 8 already recorded, and `long8addtable.py` compares
against it.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| `SoundInCheckArm=1`, O and G | done | `runs/SoundArms_{O,G}_ic1.rows` | −0.07 % / −1.36 %, **0 san** |
| `SoundMateAlphaArm=1`, O and G | done | `runs/SoundArms_{O,G}_ma1.rows` | **0.00 % on O**, +0.40 % on G, **0 san** |
| `SoundPvArm=1;SoundStepMask=8`, O and G | done | `runs/SoundSteps_{O,G}_mask8.rows` | +6.31 % / +1.85 %, **0 san** |
| `SoundPvArm=1;SoundStepMask=1`, O and G | done | `runs/SoundSteps_{O,G}_mask1.rows` | −2.50 % / −3.30 %, **0 san** |
| `SoundRegretCount=true`, O and G | done | `runs/SoundSteps_{O,G}_rc.rows` | **0.00 % both**, **0 san** |
| `SoundRegretProbe=true`, O and G | done | `runs/SoundSteps_{O,G}_rp.rows` | **+939.38 % / +587.72 %**, **0 san** |
| `NullStaticSlope=48` | done | `runs/NodeLiterals_{O,G}_nss48.rows` | −4.43 % / −12.21 %, **0 san** |
| `NullEvalRedMax=0` | done | `runs/NodeLiterals_{O,G}_nerm0.rows` | +0.06 % / −0.17 %, **0 san** |
| `NullVerifyDepth=1` | done | `runs/NodeLiterals_{O,G}_nvd1.rows` | +0.73 % / +0.27 %, **0 san** |
| `ProbcutImproving=0` | done | `runs/NodeLiterals_{O,G}_pci0.rows` | +0.21 % / −2.68 %, **0 san** |
| `ProbcutReduction=6` | done | `runs/NodeLiterals_{O,G}_pcr6.rows` | +0.73 % / −3.42 %, **0 san** |
| `ProbcutTtSlack=1` | done | `runs/NodeLiterals_{O,G}_pts1.rows` | +0.50 % / −1.88 %, **0 san** |
| `ProbcutStoreReduction=1` | done | `runs/NodeLiterals_{O,G}_psr1.rows` | +0.44 % / −0.43 %, **0 san** |

## 4. Findings

### 4.1 The full table, from one committed command

```
cd forge-combo29/tests_deepseek6_long8
python3 long8addtable.py
| set | moved value | O def | O mov | dO% | G def | G mov | dG% | san |
... 13 rows ...
settings 13, positions 7189, total sanitizer lines 0
moved values that did NOT change the tree: [('SoundArms', 'SoundMateAlphaArm=1', 'O'),
                                           ('SoundSteps', 'SoundRegretCount=true', 'O'),
                                           ('SoundSteps', 'SoundRegretCount=true', 'G')]
```
Every `def` column is the long-8 defaults sum (3,809,466 / 7,290,580), so all 26 runs here are consistent with
the earlier 28 — same builds, same sets, same depth.

### 4.2 `SoundRegretProbe=true` costs 9× the tree, and it is a DIAGNOSTIC mode, not a playing option

```
python3 long8addtable.py   ->  SoundSteps | `SoundRegretProbe=true` | 3809466 | 39594812 | +939.38% | 7290580 | 50139047 | +587.72%
```
Row-by-row, not one row is unchanged: **200 of 200 rows bigger on O, ratios between 2.1x and 38.4x**. That is
too uniform to be a bug, and the code says what it is — `src/search.cpp:1840`, inside
`sound_regret_drop`, `if (!tune::SoundRegretProbe) return;` guards a block that "mirrors the depth the move
loop would have given the move" and runs a verification search for every move the pruning steps dropped. So
turning the probe on converts every pruning decision into an extra search at every node. It is a measurement
instrument, and a node count taken with it on is not comparable with one taken with it off.

**This is a warning worth passing on:** any future job that reads a node sum with `SoundRegretProbe=true` and
compares it to a normal sum would report a 9x regression that is not a regression.

### 4.3 `SoundRegretCount=true` changes nothing — and that is BY DESIGN, and it is now measured

```
SoundSteps | `SoundRegretCount=true` | 3809466 | 3809466 | +0.00% | 7290580 | 7290580 | +0.00%
```
The patch's own comment says so: `src/search.cpp:1816`, "counting alone never searches, so a count-only build
keeps the unpatched node counts (rule R1)". My prediction said this one would "change the tree … if they do not
I will say the option is unmeasured-by-node-counts rather than unwired". It did not change the tree, so by my
own rule: **`SoundRegretCount` is not shown to be wired by this test**; it is a counter toggle whose effect is
invisible to node counts and would need the counter values read back (which the patch exposes as a trace, not
as UCI output I can capture here).

### 4.4 `SoundMateAlphaArm=1` is silent on O and live on G — the same result as long 4a, at another depth

```
SoundArms | `SoundMateAlphaArm=1` | 3809466 | 3809466 | +0.00% | 7290580 | 7319791 | +0.40%
```
Third independent confirmation (long 4a at depth 12 release, long 4b's chain, now depth 10 sanitizer) that this
arm's case does not arise in O at these depths but does in G. A job that tests this arm on O only will read it
as unwired; it is not.

### 4.5 The two `SoundStepMask` bits behave at depth 10 as they did at depth 12

```
mask=8 (bit 3, quiet SEE)  +6.31 % O, +1.85 % G     (long 4b at depth 12: +706,336 nodes ≈ +7.4 % O)
mask=1 (bit 0, LMP)        -2.50 % O, -3.30 % G     (long 4b at depth 12: -23,442 nodes ≈ -0.25 % O)
```
Bit 3 is the biggest single step again, and bit 0 is negative again — the *sign* of bit 0's effect is stable
across depths, which `LmrCutNode`'s sign was not. That distinguishes "step function" (long 3) from "a genuine
negative effect" (bit 0 here).

### Suspicions, not proven

- Why `NullStaticSlope=48` is NEGATIVE here (−4.43 % / −12.21 %) when it was POSITIVE in long 5a at depth 12
  release (+1.18 %). A sign flip on a slope that changes the null-move guard is plausible (a bigger slope makes
  the guard harder, cutting more null moves, which can go either way), but I have not separated depth from
  build type.
- Whether `SoundRegretCount`'s trace is readable anywhere; I did not look for an output path.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its design comment inside `SoundRegret.patch.txt` ("counting alone never
  searches … keeps the unpatched node counts (rule R1)") is exactly what 4.3 measured. Its note is right and my
  node-count test simply cannot see that option.
- **glmflash5** (`NOTES_glmflash5.md`): nothing on the Sound* family beyond the arms it already tested.
- **deepseek5** (`NOTES_deepseek5.md`): nothing here.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- I did not add a deliberate-leak sanitizer positive control (still the one gap from long 7; this addendum's
  budget went to the option sweep instead).
- I did not run `IirNoRoot` at a value that changes the tree under the sanitizer: its only option is inert
  without `searchmoves`, and the sanitizer runner does not send `searchmoves`. Long 6 measured that case at
  depth 12 in the release build; the sanitizer version of the `searchmoves` case is not done.
- I did not read any counter back, so `SoundRegretCount`'s wiring is untested by me.
- I did not commit the raw logs (regenerated by `long8add.sh`, deleted after counting; the counts are in the
  committed `.rows`).
- I did not commit engine source, and I did not open a pull request.

## 7. What I am NOT sure about

- The `NullStaticSlope` sign flip (see Suspicions).
- Whether "each option moved once" also means each option of MY OWN `IirNoRoot` in a configuration where it
  bites under a sanitizer; I judged long 8 to be about the patches that passed long 2–5 and long 6's own case
  was already measured.

## 8. A better way

The `SoundRegretProbe` result is the reason a "moved once" sweep must be paired with "and the option is a
DIAGNOSTIC or a PLAYING option". Three of my 13 moved values were instruments (`SoundRegretProbe`,
`SoundRegretCount`, and arguably `SoundStepMask` with a case forced on), and mixing them into one table invites
someone to read a 9× number as a search regression. A sweep should carry a column "is this a playing setting or
a measurement setting", taken from the patch's own comments. I will add that column whenever a job gives me a
patch with diagnostic toggles.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`long8addtable.py` (the one command), `long8add_table.txt` (its output), `runs/` now 54 rows files (544 KB),
`long8add.sh` (the driver), `precommit_addendum.txt`.
