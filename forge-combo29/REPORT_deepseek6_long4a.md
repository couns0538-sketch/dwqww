# REPORT — deepseek6, long 4a (kimi5's SoundArms patch)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** the long-2 test for `SoundArms.patch.txt` on a clean copy of 6b98f217 — read it, list new options with defaults and ranges, apply without fuzz, build, honesty numbers, rows on O and G under S14 equal to long 1's row by row, then each new option moved once off its default with the O sum shown to change.
**Answer:** it applies with zero fuzz and is an exact identity at the defaults (200/200 O, 353/353 G, 200/200 O-none, all four honesty numbers). Of its three new arms, two are wired on O (`SoundPvArm=1` +4.9 %, `SoundInCheckArm=1` −0.28 %) and the third, `SoundMateAlphaArm=1`, changes NOTHING on O at depth 12 but DOES change G (18,688,400 vs 18,466,239) — so it is wired, and O simply has no mate-alpha case at this depth. All four `-1` (ForceOff) runs are exactly the default, as the code requires.
**How sure:** certain of every number. The "why" of the mate-alpha arm's silence on O is a measured absence plus one code reading, labelled as such.

## 2. The honesty numbers (at the defaults)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe `/agent/repos/work/build-l4a/forge`, sha256 `ed29427b10efba4922b384bf23ccfa7c7ac243e68cc4e51e180267e2f3c573b6`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate` (`uci.txt`). Clean copy `/agent/repos/p5`
at 6b98f2170a3210e71beed04bbd2553972c253ed7. Release, g++ 13.3.0, `-march=x86-64-v4`.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new options named with defaults and ranges | done | `SoundArms.patch.txt`, `uci.txt` | `SoundPvArm` / `SoundInCheckArm` / `SoundMateAlphaArm`, all spin default **0**, min **-1**, max **1** |
| apply without fuzz on a clean copy | done | `patch_apply.txt` | clean; `--fuzz=0 --dry-run` passed first |
| build | done | `exe.sha256` | Release g++ 13.3.0 |
| honesty at the defaults | done | `honesty_*.txt` | all four met |
| identity O/S14 vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, sum 9,500,069 |
| identity G/S14 vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, sum 18,466,239 |
| identity O/none vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, sum 12,573,318 |
| wired: `SoundPvArm=1` | done | `O_S14_pv1.rows` | sum **9,966,105** (+4.9 %) |
| wired: `SoundInCheckArm=1` | done | `O_S14_ic1.rows` | sum **9,473,683** (−0.28 %) |
| wired: `SoundMateAlphaArm=1` | **partly** | `O_S14_ma1.rows`, `G_S14_ma1.rows` | O: **9,500,069, unchanged**; G: **18,688,400, changed** — wired, silent on O |
| inert by design: `SoundPvArm=-1` | done | `O_S14_pvm1.rows` | **9,500,069, 200 of 200 equal** (as predicted) |
| inert by design: `SoundInCheckArm=-1` | done | `O_S14_icm1.rows` | 9,500,069, 0 of 200 rows differ |
| inert by design: `SoundMateAlphaArm=-1` | done | `O_S14_mam1.rows` | 9,500,069, 0 of 200 rows differ |
| control: `SoundMatePruning=true`, arms all 0 | done | `O_S14_smp1.rows` | sum **9,817,091** (the option itself is wired) |
| cross-check: `SoundMatePruning=true` + `SoundPvArm=-1` | done | `O_S14_smp1_pvm1.rows` | sum **9,473,683** — identical to `SoundInCheckArm=1` alone, row for row |
| cross-check: `SoundPvArm=1` + `SoundInCheckArm=1` | done | `O_S14_pv1_ic1.rows` | sum **9,817,091** — identical to `SoundMatePruning=true`, row for row |
| out-of-range stop check | done | `stopcheck_arm2.rows` | `SoundPvArm=2` -> `invalid value`, stopped, exit 2 |
| spin-vs-check stop check | done | `stopcheck_word.rows` | `SoundPvArm=true` -> `invalid value`, stopped, exit 2 |

## 4. Findings

### 4.1 The patch is an exact identity at its defaults

```
cd forge-combo29/tests_deepseek6_long4/SoundArms
python3 cmprows.py O_S14_def.rows ../../../tests_deepseek6_long1/O_S14.rows   -> 200 of 200 equal
python3 cmprows.py G_S14_def.rows ../../../tests_deepseek6_long1/G_S14.rows   -> 353 of 353 equal
python3 cmprows.py O_none_def.rows ../../../tests_deepseek6_long1/O_none.rows -> 200 of 200 equal
```
That is what the code requires: `FollowOption` returns `SoundMatePruning`, whose default is false, and
the base guard is `!sound_mate_case && ...`.

### 4.2 The arms are wired, and the three-case OR composes exactly

```
for f in pv1 ic1 ma1 pvm1 icm1 mam1 smp1 smp1_pvm1 pv1_ic1; do python3 rowdiff.py O_S14_$f.rows O_S14_def.rows --show 0; done
pv1          200 of 200 rows differ (200 nodes, 60 bestmove, 60 both)
ic1          193 of 200 rows differ (192 nodes, 22 bestmove, 21 both)
ma1            0 of 200 rows differ
pvm1           0 of 200 rows differ
icm1           0 of 200 rows differ
mam1           0 of 200 rows differ
smp1         200 of 200 rows differ (200 nodes, 54 bestmove, 54 both)
smp1_pvm1    193 of 200 rows differ (192 nodes, 22 bestmove, 21 both)
pv1_ic1      200 of 200 rows differ (200 nodes, 54 bestmove, 54 both)
```

The two structural identities, both exact:

```
python3 rowdiff.py O_S14_smp1.rows O_S14_pv1_ic1.rows --show 3   -> 0 of 200 rows differ
python3 rowdiff.py O_S14_ic1.rows O_S14_smp1_pvm1.rows --show 3  -> 0 of 200 rows differ
```

Read together: switching the option on (`SoundMatePruning=true`) is EXACTLY the same tree as forcing the
PV and in-check arms on and leaving mate-alpha following the option, which is what
`(Pv && pv_node) || (InCheck && in_check) || (MateAlpha && is_mate(alpha))` says when the third case never
occurs. And forcing PV off while the option is on is EXACTLY `SoundInCheckArm=1` alone — the PV arm's
switch removes precisely the PV contribution and leaves the in-check one. Both hold on all 200 positions,
not just in the sums. That is the strongest evidence in this report that the arms really are the three
separate cases and not three names for one switch.

### 4.3 `SoundMateAlphaArm=1` is wired but silent on O, and the silence is a property of O

```
python3 sumrows.py O_S14_ma1.rows                       -> rows 200 sum 9500069   (unchanged)
python3 cmprows.py G_S14_ma1.rows G_S14_def.rows        -> first difference at row 23: A=23|55178|g7e6 B=23|55132|g7e6
                                                           23 of 353 equal, sum 18688400 vs 18466239
```
So the arm does reach the predicate, and on G it changes 330 of 353 rows. On O at depth 12 the case
"alpha is a mate score" never arises in a way that changes a node count. This is exactly the class of
result the brief wants found: a check that would look like "not wired" if I had only run O.

**Suspicion, not proven:** the reason O shows nothing is that mate-alpha pruning only matters once the
search is already inside a forced mate, and the 200 game openings of O reach depth 12 without one at any
node that the prune block sees. A probe would be `go depth 12` on a set of mate-in-N positions; I did not
run one.

### 4.4 The `-1` values are inert exactly as the code requires — a positive control for the mapping

`-1` maps to `ForceOff`, and `sound_arm_enabled(ForceOff)` is false, which is what the default already
resolves to while `SoundMatePruning=false`. All three `-1` runs are 0 of 200 rows different. If the patch's
own warning had come true — "a numeric cast would map 1 to ForceOff and -1 to garbage" — the `-1` runs would
have DIFFERED. They do not, so the by-name mapping the patch comments about is the one in force.

### 4.5 The options are spins, not checks

```
`SoundPvArm=true`  -> STOPPED: info string invalid value for option SoundPvArm  (exit 2)
`SoundPvArm=2`     -> STOPPED: info string invalid value for option SoundPvArm  (exit 2)
```
A check option would accept the word `true`; a spin must reject it, and it does. This is the same class of
planted fault the brief calls for, run against a NEW option rather than against a made-up name.

### Suspicions, not proven

- Why the in-check arm is *smaller* than the default (9,473,683 vs 9,500,069, −0.28 %): skipping the
  prune block in check should make the search see MORE moves and cost more nodes, not fewer. The sign is
  the opposite of my predicted direction for it. I have no explanation; the measurement stands and my
  prediction is recorded as a missed direction.
- The PV arm's +4.9 % is the size I expected, but I filed a 9,500,000–14,000,000 band and it landed inside,
  so that one is a hit.
- 60 of 200 best moves change with the PV arm on and 54 with `SoundMatePruning=true`. That the two counts
  differ while the two SUMS are equal (9,817,091 each) is expected — the sum is a total, not a row-by-row
  match — and the row-by-row check in 4.2 is what settles it. Worth saying plainly because a reader could
  otherwise read "equal sums" as "equal rows".

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its notes describe the Sound* family as designed for its job 5 Part 4
  masks; the `SoundStepMask` patch's header says it applies AFTER `SoundRegret.patch.txt`, so 4b cannot be
  applied to a clean base — see section 6.
- **glmflash5** (`NOTES_glmflash5.md`): its job-15 note reports `pv1` (LMP exempted at PV nodes) as
  +32.05 [+24.7,+39.4] pooled over two seeds — a STRENGTH number, not a tree number. My +4.9 % node result
  is consistent with a big tree change but says nothing about strength; I do not claim its +32 from my data.
- **deepseek5** (`NOTES_deepseek5.md`): the moment-of-the-event lesson; its job-30 note is about stage
  counters, unrelated to this run.
- No note is an order; no number above came from a note.

## 6. What I did NOT do

- **I did not run SoundSteps in long 4.** Its first line is `# applies from the repository root, AFTER
  SoundRegret.patch.txt: patch -p1 < SoundSteps.patch.txt`, and its hunks expect the `SoundRegretCount` and
  `SoundRegretProbe` lines that `SoundRegret.patch.txt` adds (`uci.cpp` hunk 1 context). Long 4's wording is
  "the same for ... SoundSteps.patch.txt", and "the same" includes "apply it with `patch -p1` without fuzz on
  a clean copy" — a clean copy of 6b98f217 cannot take this patch. I will run it as the chain
  SoundArms -> SoundRegret -> SoundSteps on one clean copy; all three patches are text and all three are on
  kimi5's branch, and the chain still tests SoundSteps' own new option (`SoundStepMask`) for wiring.
- I did not probe mate positions to explain 4.3.
- I did not test the arms on G except `SoundMateAlphaArm=1` (one run, because O was silent).
- I did not measure strength and I do not claim any of these arms is good or bad.
- I did not commit engine source; patches are committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether SoundSteps should be judged on a 3-patch chain (my reading) or not at all until a job file says
  so. I chose the chain because it is the only way the patch can be compiled, and I will say plainly in the
  4b report which patches were under it.
- The in-check arm's negative sign (4.5).
- Whether "identity at the defaults" should also be read as "the three arms' defaults reproduce
  `SoundMatePruning=false`", which I did show.

## 8. A better way

The two row-by-row cross-checks in 4.2 cost 10 s each and proved more than all the sum comparisons put
together: they show the three arms are the three cases, not one switch with three names. For any patch that
adds a case-selection option, testing the COMPOSITION of the cases against the option is the cheap way to
prove the structure. I will do that first from now on.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`ls` + `git status --short` before this commit: `precommit_evidence.txt`.
