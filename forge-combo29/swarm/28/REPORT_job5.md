# REPORT_job5 — a candidate patch that closes BOTH drawn-root doors, honesty unchanged

## What was asked
Nothing in the brief. This job exists because my S-C1/S-F4 and seat 20's S-F13 both showed that seat 01's
patch (remove only the `halfmove_clock() >= 100` term) leaves the repetition door open. A correct fix has
to close both, and it must not change the four honesty numbers.

## The answer
A **5-line patch** (`search.cpp.patch.txt`) removes the two *claimable* draw terms from the root shortcut
and keeps the one *automatic* draw:

```cpp
-    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
-                                               board.is_insufficient_material());
+    // SEAT 28 JOB 5 CANDIDATE PATCH (2 lines -> 1): the fifty-move and repetition terms are removed
+    // from the root shortcut. ... Insufficient material stays: that draw IS automatic.
+    const bool root_drawn = !legal.empty() && board.is_insufficient_material();
```

It applies with `patch -p1 --fuzz=0`, builds with the standard recipe, **keeps all four honesty numbers
identical**, finds the mate through **both** doors, and still adjudicates K v K as drawn.

## How sure
Very high on the behaviour (a base-vs-patched table for five cases, each binary the same harness); high on
the honesty numbers (pasted below, each from a fresh process); **not** sure the patch is policy-correct —
that is Fable/Opus's decision, not mine. The speed cost is below what this machine can resolve (see T9).

## Process state
Every search: fresh process per case, `ucinewgame` + `isready` before each `go`, `OwnBook false`,
Threads 1, Hash 16. Equivalent to a fresh process by `job4/state_check.py`.

## Honesty numbers with the patch (`out_honesty/`, pasted)

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 453 nps 1903596
info string bench depth 16 nodes 3024920 time 1485 nps 2036983
nodes 4865609
```

versus the base build in `job0/`: 312866 / 862329 / 3024920 / 4865609 — **all four identical**. Patch
sha256 `4ac1095de67c683e…` versus base `e06310eca3368556…`, so the binaries differ as they should.

## The behavioural table — `verify_patch.py` (`verify_patch_out.md`)

| case | binary | bestmove | nodes | depth | bestmove is mate-in-one |
|---|---|---|---|---|---|
| hm99 | base | a1a8 | 126 | 6 | True |
| hm99 | patched | a1a8 | 126 | 6 | True |
| hm100 | base | f2f3 | 0 | 6 | False |
| hm100 | **patched** | **a1a8** | **126** | 6 | **True** |
| rep3 | base | f2f3 | 0 | 6 | False |
| rep3 | **patched** | **a1a8** | **126** | 6 | **True** |
| kvk | base | a1b1 | 0 | 6 | False |
| kvk | patched | a1b1 | 0 | 6 | False |
| kqk | base | b1b8 | 3007 | 6 | False |
| kqk | patched | b1b8 | 3007 | 6 | False |

- **T6/T7 SURVIVE**: the patched engine finds the mate at halfmove 100 and on the third repetition, with
  the same 126 nodes the base engine uses at halfmove 99 — i.e. it does the normal search.
- **T8 SURVIVES**: K v K is still answered with 0 nodes (insufficient material kept), and a normal K+Q
  search is untouched (3007 nodes both binaries), so the patch is narrow.

## Speed cost (T9)
Ten alternating `bench 13` runs, base vs patched (`out_ab/ab_summary.txt`): nodes identical (862,329)
every time; time median 444 vs 462 ms, ratio 1.0405, **95 % bootstrap interval [0.9712, 1.1018]**, which
contains 1.0. My own S-C2 showed this machine cannot resolve a bench difference below ~5 % with a single
run, so the honest reading is **no measurable cost, and no measurable speed-up either** — the patch is
about correctness, not speed. T9's "no more than 2 %" was a guess I cannot verify; the interval is the
real answer.

## The step table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction alone before measuring | done | `prediction.txt` (own commit) | 8/9 survived, T9 inconclusive |
| patch as a text diff, applies with `-p1 --fuzz=0` | done | `search.cpp.patch.txt` | T1 SURVIVES |
| build with the standard recipe | done | `out_honesty/` + sha256 | builds, differs from base |
| four honesty numbers unchanged | done | `out_honesty/*.txt` | T2-T5 SURVIVE |
| both doors closed | done | `verify_patch_out.tsv` | T6/T7 SURVIVE |
| automatic draw still honoured | done | `verify_patch_out.tsv` (kvk) | T8 SURVIVES |
| cost | done | `out_ab/ab_summary.txt` | not resolvable on this box |

## Findings

**S-F17 — removing the fifty-move and repetition terms from `root_drawn` (keeping only insufficient
material) fixes BOTH no-search doors and leaves the four honesty numbers identical, with no measurable
speed cost.**
Shows again:
```
cd forge-combo29/swarm/28/job5
patch -p1 --fuzz=0 < search.cpp.patch.txt    # in a copy of 6b98f217
python3 verify_patch.py <base-exe> <patched-exe> /tmp/v.tsv
```
Raw: `verify_patch_out.md`, `verify_patch_out.tsv`, `out_honesty/`, `out_ab/`.

**S-F18 — the reason the shortcut is wrong as written, stated precisely for the owner.** Fifty-move and
threefold repetition are draws a player may CLAIM, and the side to move is not obliged to; insufficient
material is a draw regardless. The code treats all three the same, so it forfeits a mate that is still
available. That asymmetry is the defect; the patch is the smallest change that restores it.

## Suspicions, not proven
- Whether removing the shortcuts costs anything in real games on repetitious positions. The shortcut
  exists to answer instantly at a repeated root; the patched engine now searches there. I measured no
  cost on bench (ordinary positions) but did not measure a game with many repetitions.

## What I did NOT do
- **Did not commit the patched source** — only the `.patch.txt`, per the rules.
- Did not run the patched engine through the whole job 1-4 suites; only the honesty pins and five
  targeted cases.
- Did not decide the policy. If Fable/Opus prefer the shortcut for repeated positions, a narrower patch
  (skip the shortcut only when a mate-in-one exists) is possible and I have not written it.

## What I am NOT sure about
- Whether `is_insufficient_material()` alone is the right set to keep; e.g. a dead position by other means
  is not covered, but neither was it before.
- Whether seat 01's or seat 20's patch is preferred over this one; mine is the minimal form I could test.

## Prediction score
T1-T8 SURVIVED. T9 was **inconclusive**: the 95 % interval [0.9712, 1.1018] contains 1.0, so "no more
than 2 % cost" is not demonstrated and neither is a cost. Reported as such rather than as a pass.

## Times: see `stamps.txt`. Last command output: `last_command.txt`.
