# PREDICTION — deepseek6, long 8 (long 7 for every patch that passed long 2 to 5)

Written before the first measuring command of long 8. Never edited after this commit.

## The patch sets under test, and why these

Long 8 says "long 7 for every patch that passed long 2 to 5, one at a time, with its options at their
defaults AND with each option moved once." The patch sets that passed long 2–5:

| # | set | tree | its new options |
|---|---|---|---|
| 1 | kimi5 `LmrGiveCheck` | `/agent/repos/p2` | `LmrGiveCheck` 0..4, default 1 |
| 2 | kimi5 `LmrCutNode` | `/agent/repos/p3` | `LmrCutNode` 0..4, default 2 |
| 3 | kimi5 `LmrTtPv` | `/agent/repos/p4` | `LmrTtPv` 0..4, default 1 |
| 4 | kimi5 `SoundArms` | `/agent/repos/p5` | `SoundPvArm`, `SoundInCheckArm`, `SoundMateAlphaArm`, each -1..1 default 0 |
| 5 | kimi5 `SoundSteps` (chain: SoundArms+SoundRegret+SoundSteps) | `/agent/repos/p6` | `SoundStepMask` 0..63 default 63 (plus SoundRegret's two, default false) |
| 6 | kimi5 `NodeLiterals` | `/agent/repos/p7` | eight, all at literal defaults |
| 7 | my `IirNoRoot` (written in long 6) | `/agent/repos/p9` | `IirRootExclude` 0..1 default 0 |

`IirNoRoot` is included because it is a patch I wrote and it passed its own long-6 chain of checks; if a
reader disagrees that it belongs in "long 2 to 5", the extra data costs nothing and is labelled.

Seven RelWithDebInfo builds with `-fsanitize=address,undefined -fno-omit-frame-pointer`, each in its own
build dir under `/agent/repos/work/l8/build-<name>`, each with `exe.sha256`.

## What long 7's test is, restated

Per patch set and per option setting: `go depth 10` on O (200 positions) and G (353) under S14, each position
in its OWN process (so a fatal report kills only that position and the exit-time leak check runs 553 times
per setting), counting lines matching `AddressSanitizer|LeakSanitizer|SUMMARY:|runtime error|
UndefinedBehaviorSanitizer`.

**Prediction: 0 sanitizer lines for every one of the seven patch sets, at the defaults AND with every moved
value.** Reason: none of these patches allocates, changes array bounds, changes index arithmetic, or touches
anything but integer search parameters; the base build was clean in long 7 (0 over 553 positions), and a
tunable at a legal value cannot make it unclean.

**Killed by:** any sanitizer line. If one appears, it gets its own table with the patch set, the option
setting, the position index, the fen, and the report text — and I will NOT call the patch "bad" from it without
reading whether the fault is in the patch or is a latent base-engine fault that the patch merely exposes
(a moved option can change the search path and reach a pre-existing fault; that distinction is the whole
reason long 8 exists).

## The moved values I will use (one per option, chosen to be the ones long 2–5 already proved are WIRED)

| set | moved values |
|---|---|
| LmrGiveCheck | `LmrGiveCheck=0` |
| LmrCutNode | `LmrCutNode=0` |
| LmrTtPv | `LmrTtPv=0` |
| SoundArms | `SoundPvArm=1` (the only arm with a large effect on O) |
| SoundSteps | `SoundPvArm=1;SoundStepMask=0` (the mask only bites with a case active) |
| NodeLiterals | `NullStaticBase=360` (the largest single effect: +8.9 % on O) |
| IirNoRoot | `IirRootExclude=1` |

Each moved value was measured in long 2–6 to change the O/S14 sum, so each is a real change of search path —
which is what makes it a meaningful sanitizer probe. The defaults runs are the controls.

## A second, cheaper known answer I will record per setting

The sanitizer build's depth-10 node sums are NOT published anywhere, so they are recorded data, not a
known-answer test. But there IS a known answer available for free: **the defaults run of each patch set must
have the same sum as the PLAIN base's depth-10 sums recorded in long 7** (O 3,809,466 and G 7,290,580), because
each patch is an identity at its defaults. A defaults run that differs from those two numbers is a finding
about that patch, and it is the one identity check long 8 can make for free.

| defaults run | predicted sum |
|---|---|
| O under S14, depth 10, any patch at its defaults | **3,809,466** |
| G under S14, depth 10, any patch at its defaults | **7,290,580** |

**Killed by:** any other number, which I would report as "this patch is not an identity at depth 10" even
though it was at depth 12.

## Scope I am limiting on purpose

Running 7 patch sets x (defaults + moved) x 2 sets x 553 positions = 15,484 positions under a sanitizer. At
the measured rate in long 7 (O 200 positions in 26 s, G 353 in 45 s) that is about 25 minutes of pure engine
time plus per-process overhead, which is acceptable. If any single setting runs past ~10 minutes I will let it
finish rather than sample it down, and I will say in the report which settings got the full 553.
