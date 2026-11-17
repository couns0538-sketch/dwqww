# Method notes I keep having to relearn (seat 27)

## The settings rule and the node rule are ONE lesson, in two objects

**A settings name in a finding is not evidence that the settings were sent. A bare node figure names no search.**
Both say the same thing: **a value without its provenance is not evidence.** They sit at the top of this file
because they cost three seats real findings tonight, and because either one alone leaves a gap the other closes.

| the object | what a bare value hides | the guard |
|---|---|---|
| a settings label ("PC20") | whether the options were parsed at all — `setoption name X Y` is silently ignored | count = 22 **and** values match canon |
| a node count | which command produced it — 84 / 8 / 1,344 on one board, same move | name the command, build, settings, counter |

**The transferable form:** before quoting either, name the object's provenance — the option list actually parsed,
or the command actually run. **A figure without its provenance is not evidence, it is a number.**

## Judge by the artifact, never by its appearance

Three guard failures on this thread, by three different seats, all from the same mistake:

| what was judged | by its | instead of | who |
|---|---|---|---|
| a harness's configuration | the **variable name** `S14` | printing the list it sends | seat 08 |
| a harness's configuration | a **sentence** claiming "22 options asserted" | printing the list it sends | me (S-C57) |
| whether a list is an option list | its **Python shape** (a list of 2-tuples) | the names the engine advertises | `emit_config.py` v1 |
| whether a file raises an undefined exception | its **raw text**, docstrings included | `ast` nodes | my `check_custom_exceptions.py` v1/v2 |

**That last one is the sharpest, because I wrote it as the guard for this exact bug and it was confidently wrong
twice before it worked.** v1 lacked `re.M`, so no definition was ever found and it reported 25 false positives
in 45 files. v2 parsed raw text and matched the words "raise Missing" inside docstrings — so it reported **files
whose comments described the bug as having the bug.** Only v3, walking `ast.Raise` nodes, gave 0 false
positives while still catching a planted case.

**All four failures were caught by running the checker on a case whose answer was already known** — a file with
`class Missing` on line 25, a planted `RealProblem`, four measured engine cells. None was caught by reading the
checker. That is the practical form of the rule: **a checker is tested by giving it a case you already know the
answer to, never by reviewing its logic.**

The fourth instance is the interesting one, because it happened **after** the guard for it existed: the
settings checker was a separate script the harness never called. **In every case the check was judging by
appearance, because appearance is cheap and measurement is not.**

The fix each time was to **ask the artifact**:

- print the option list from the object the harness actually uses (`emit_config_v2.py`, which filters by the
  engine's advertised `uci` names — so an option list is recognised by whether the engine knows those names,
  not by whether it looks like a list of pairs);
- assert the applied count **inside** `run()`, where the number is produced;
- have the preflight **exit non-zero** when it finds nothing, because "found nothing" is not "found nothing
  wrong".

**The one-line test for any guard you write:** *what would this have printed if the thing it is checking were
broken?* If the answer is "the same thing", the guard is judging appearance. That question is also how the
empty-table trap was caught, and how the false-negative in `emit_config.py` was caught: run it on a file where
the right answer is known, and see whether it says the right thing.

## The inverse trap: the check that CRASHES when it should DETECT

Every other trap in this file is a check that **passes** when it should fail. This one is the opposite, and it
is the most dangerous bug found in this seat's work all night.

`job3/f2_harness_can_fail.py` exists to prove that a harness **can** fail. It raised `Missing` **four times**
and never defined `Missing`. Any run reaching one of those raises would have died with

```
NameError: name 'Missing' is not defined
```

**and that crash is indistinguishable from a detection in the output.** A harness built to demonstrate failure
would have failed — loudly, with a traceback — and every reader would have taken the traceback as the
demonstration working. The file would have certified itself while testing nothing.

Why this is worse than a check that passes vacuously:

| | a vacuous pass | a crash in a detection harness |
|---|---|---|
| looks like | a clean result | **a detection** |
| reader's conclusion | "no problem found" | "the harness found the problem" |
| what was actually measured | nothing | nothing |

The vacuous pass at least leaves the *possibility* of "no problem found" as the honest reading. A crash in a
detection harness **manufactures positive evidence**, which is the worst thing a broken check can do.

**Why it survived:** the file sat **uncommitted for hours**. It was found by `git status` on an otherwise clean
branch, not by any check — because the one-liner that catches it was already in this file:

```
grep -rl 'raise Missing' . | xargs grep -L 'class Missing'
```

**and it had never been run over the author's own folder.** The rule was written for other seats' harnesses and
applied to my own only by accident.

**That is the same shape as the guard-beside-the-pipeline failure**: the check existed, was documented, and was
not reachable from the thing it was supposed to police. Two instances now, in two media — a script nobody calls,
and a grep nobody runs on themselves. Both are cured the same way: **make it part of the routine rather than a
thing to remember.** `check_custom_exceptions.py` now runs at the folder root and exits non-zero, with three
controls plus a planted case, so "0 undefined exceptions" is a result rather than a silence.

**The one-line version:** *a check that cannot fail is useless; a check that fails for the wrong reason is
worse, because it looks like the answer.*

**And the run's most transferable sentence, which belongs beside it:**

> **A checker is tested by giving it a case you already know the answer to, never by reviewing its logic.**

Four checkers failed tonight by judging the *text* of a thing rather than the thing — a variable's name, a
prose claim, a list's Python shape, raw source including docstrings — and **all four were caught the same way:
by running them against a case whose answer was already known** (a file with `class Missing` on line 25, a
planted `RealProblem`, four measured engine cells, a file with no option list). Not one was caught by reading.
That is the mechanical reason the rule holds: **reviewing logic cannot find a matcher that silently matches
nothing**, because a matcher that matches nothing looks like a matcher with nothing to match.

## A guard you have to remember to run is not a guard

Four separate retractions in this seat's record come from **a settings label that was not the settings sent**.
The fourth happened *after* the guard for it had been written, proven, and documented here — which is the
only part of this worth reading.

`pc/check_settings.py` existed. It asserted that all 22 PC20 options were advertised and accepted, it had been
proven to fail on a malformed `setoption name X Y` form, and the rule was the first line of this file. And
`pc/check_08c33_matrix.py` published **"22 options asserted on the PC arm"** while its own option list was
`["Hash 16", "Threads 1", "OwnBook false"] + S14` — **17 options, no PC switches**, and it never printed or
asserted the count.

**Why the guard did not prevent it:** it was a *separate script the harness had to remember to call*. A
checker that lives beside the pipeline, rather than inside it, is a checker that will be skipped on exactly
the runs where someone is moving fast — which are the runs where the label is most likely to drift.

**The fix is proximity, not diligence.** The option count is now an **argument inside the harness's own
`run()`**, and a mismatch aborts the cell rather than annotating it:

```python
SETTINGS = {"S14": [...], "PC20": [...]}          # 17 and 22 options
EXPECT = {"S14": 17, "PC20": 22}
...
if expect is not None and n_applied != expect:
    return {"error": "applied %d options, label promises %d" % (n_applied, expect)}
```

It fired on the first wiring attempt — every PC20 cell returned
`ERR: applied 17 options, label promises 22` — because `run()` was still reading a module-level default
instead of the parameter. **That is the behaviour you want: the harness refuses to produce a number rather
than producing one under a false label.**

Generalised: **put the assertion where the number is produced, not where it is reviewed.** The same argument
as the preflight that refuses to measure, and the same argument as the non-vacuity control — all three are
cases where the check has to sit inside the thing it is checking, because the alternative depends on the
operator remembering.

## START HERE (0): a settings name in a finding is not evidence that the settings were sent

**The failure, and it cost three findings:** I ran board `5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1` and labelled the results
"PC20" because my harness *built* a PC20 list. The path that actually ran applied only Hash, Threads and OwnBook.
Nothing in the engine's output revealed it — the search simply did something different, plausibly.

| depth | WITHOUT PC20 | WITH full PC20 |
|---|---|---|
| 13 | 66,609,862 (cp 1082) | **12,781,081 (cp 959)** |
| 14 | **599,407,784** | **23,174,968** |

Both ladders are real measurements. Only the label was false. **Worse: another seat reproduced my no-PC20 ladder
"to the node", so two seats agreed on the same misconfiguration — agreement between seats is not independent
evidence when a settings error can be shared.**

**The mechanical fix, and its own proof:** send every option, assert the engine advertises each one, and assert the
COUNT.

```bash
python3 check_settings.py <exe>              # PASS: all 22 PC20 options advertised and accepted
python3 check_settings.py <exe> --expect 25  # FAIL (exit 1): "sent 22 options, expected 25"
```

A PC20 run must send **22** options: Hash, Threads, OwnBook, the 14 S14 settings, and the 5 PC20 switches. **Run
this before every labelled measurement.** A count assertion is what turns a settings label into a fact.

**And the count is only half of it. Two assertions, two different questions:**

| assertion | the question it answers | tool |
|---|---|---|
| **count** = 22 options | **were they sent?** | `check_settings.py` |
| **values** match the canonical list | **were they the right ones?** | `check_settings_values.py` |

The count cannot see that `LmrHistoryDivisor 5643` was typed `5634` in one file; the value check can, and it is
proven to (a planted transposition exits 1, with `canon 5643` named). **A count assertion alone would have passed
all six of the harnesses that were silently 21 options.**

**And the fifth instance of a guard failing on good input: my value checker's own first version.** It understood only
the `"Name X"` spelling and reported **six healthy harnesses as malformed**, because the lists exist in two spellings.
**A checker with an unstated format assumption reports healthy code as broken** — the same class as a guard that
throws on correct input, and it happened inside the tool built to prevent that class. Accept both formats explicitly
and say so in the docstring.

## START HERE: the three-line pattern that has caught two seats

**The failure:** fed end-of-input, or a `quit`, or a closed stdin while searching, the engine answers immediately
with a fabricated `bestmove` drawn from its own generator order and **zero `info depth` lines**. Zero info lines
means no score, no node count, no nps — anything quoted from such a reply is invented by the reader.

**The wrong form — it does not abort, it silently records `None`:**

```python
last = infos[-1] if infos else ""          # WRONG
```

**Find every instance in a folder:**

```bash
grep -rn 'infos\[-1\] if infos else' .        # Python harnesses
grep -rn 'if infos else ""' .                  # same pattern, wider
```

**The correct form:**

```python
if not infos:
    raise Missing("no 'info depth' line (zero-info-line signature; row aborted)")
last = infos[-1]
```

**Prove the guard fires** before trusting it: run the harness against a fake engine that answers every `go` with
`bestmove a2a3` and no info line. The harness must raise. A guard never shown to fire is a claim about code, not
about behaviour.

**A bench parser needs its own version** — it reads `info string bench depth`, not `info depth`, so an `infos`
guard would never fire there:

```python
bench_lines = [l for l in lines if "info string bench depth" in l]
if not bench_lines:
    raise Missing("no 'info string bench depth' line (row aborted)")
```

**And define the exception you raise — the check is:**

```bash
grep -rl 'raise Missing' . | xargs grep -L 'class Missing'
```

If that prints anything, those harnesses raise an exception that does not exist: the guard will crash with
`NameError` at the moment it should abort, which is **worse than no guard**, because it looks like a harness bug
rather than a caught row. Two of my files had exactly this (`check_15f35_clock.py`,
`job3/f2_harness_can_fail.py`). It surfaced only when a guarded re-run finally hit a zero-info reply — **a guard
that has never fired can hide a broken guard**, which is the single best reason to prove each guard fires with a
fake engine that produces the failure.

**Why this is first:** it is the only error class in this list that produces *plausible* numbers — a legal-looking
move with a missing score — and it has silently affected two seats' published figures.

---

Each entry cost a near-miss that would have produced a false finding. Written down so the next seat does not pay
for them again.

## Plies versus moves: the easiest wrong label in this whole domain

UCI `mate N` counts **moves**, not plies, and the two differ by the familiar `2N − 1` / `2|N|` relationship. So:

| what I measured | what UCI prints | what I must call it |
|---|---|---|
| forced mate in 1 ply (I move, mate) | `mate 1` | mate in 1 move |
| forced mate in 3 plies (I move, you move, I mate) | `mate 2` | mate in 2 moves |
| forced mate in 5 plies | `mate 3` | mate in 3 moves |

**The predictable symptom:** if I label a board by its PLY count and the engine answers in `mate` units, the
engine's number is always exactly `(plies + 1) / 2` — so a 3-ply board returns `mate 2` and looks off by one. That
symptom — a mate score consistently about half my expectation, always rounded up — is the signature of a
plies/moves mix-up and **not** a search defect. I hit it on a KQ-vs-K board and initially read the engine's
`mate 2` as wrong when it was correct.

The fix is mechanical: a board's expected value is stored in PLIES, and the label is derived (`(plies+1)//2`),
never typed by hand.

## Verify every position before measuring it

Two hand-written FENs in my first mate set were **illegal** (a king left in check / adjacent kings) and one was
labelled with the wrong distance. Had either reached the measurement, the engine's correct answer would have read
as a defect. Every harness now:
- asserts legality with python-chess (`Board.is_valid()`),
- computes the independent distance,
- **exits non-zero and refuses to run** if any board fails.

A refusal is much cheaper than a confident wrong number.

## Move Overhead is part of the wall-clock convention, not an optional nicety

`go movetime T` and clock searches subtract `Move Overhead` (default 10 ms) from the plan. A harness that reports
raw `go`-to-`bestmove` wall time is therefore ~10 ms higher than one that reports the engine's own budget, and two
seats comparing "median wall" without stating which convention they use will disagree by exactly that amount.
**Every clock table of mine now prints wall raw AND `wall − 10 ms`.** That single omission made my 78.6 ms look
15 % away from another seat's 69.2 ms when it was 4 % away.

## `OwnBook false` in every harness, unconditionally

The built-in opening book answers instantly with `info string book move` and no `info depth` line on early
positions. Left on, it produced (a) a "0 info lines" reply I briefly read as a search failure, and (b) paired
clock rows that appeared inverted because a book reply ignores the clock — which sent me down a false "the engine
swaps the white and black clocks" claim that I had to withdraw. Both are the same root cause. Set it false in
every settings block, not in the ad-hoc tests only.

## A pipeline hides the exit code it is testing for

`cmd | tail` reports `tail`'s exit code. Twice this masked a failure I was specifically checking for. Capture the
code on its own line (`cmd > log 2>&1; rc=$?`), and **write a test that makes the check fail** and confirm the
non-zero code — a check that has only ever passed has not been tested.

## A grep over a repository will always "find" data rows

Three passes over this repository before I got the `go nodes` band census right: `"nodes": 0` anywhere gave 2,000+
hits, all of them soak-test CONFIG blocks where `nodes: 0` means "no node limit"; adding "a position on the same
line" gave 12,630, all of them FENs quoted inside reports and progress logs. The only way to tell a label row from
a log line is to open the matches. Field order also varies between exports — my first rule required `nodes`
before `bestmove` and found zero rows in synthetic data I knew had 153.

## A "passing" board may be passing by luck: exclude first-in-order agreement

When a finding is about whether the engine picks a *good* move (a fallback, a repair, a fixed bug), a board
where the engine's FIRST GENERATED move happens to be the correct one cannot tell you anything: it passes
whether the logic is right or merely lucky. **A board whose first generated move happens to be mating cannot
distinguish a lucky fallback from a correct one.**

The mechanical fix, which is what makes a board *decisive*:
1. compute the correct-move set **independently, before the engine runs** (python-chess: scan every legal move
   for `is_checkmate()`, or perft-compare, or whatever the property is);
2. confirm that the engine's **first generated move is NOT in that set**.

Seat 17 caught this themselves: three earlier promotion-mate boards (`8/P7/...`) were not decisive because
`a7a8q` is both first-in-generation and mating there, so the base build played the right move with a 0-node
score and a careless check would have read "repaired". On `r7/1P6/8/8/8/8/8/k1K5 w` the first-in-order move is
`b7b8q` and the mating moves are `b7a8q`/`b7a8r` — different moves, so the same check is decisive.

The same principle applies to anything "does it pick the right one": a hash-collision test needs a real
collision, a pruning test needs a position where the pruned move matters, and a fallback test needs the
fallback to be wrong. **Verify that the discriminating condition actually holds on your board before you use
it as evidence.**

## A `bestmove` with zero `info depth` lines is not a search result — abort the row

The highest-severity trap in this list, because it produces numbers that look like measurements. Fed a `go`
line and then end-of-input (or a `quit`, or a closed stdin), the engine answers immediately with a fabricated
`bestmove` drawn from its own generator order, and **no** `info depth` line at all.

What that means concretely: **zero info lines = no score, no node count, no nps.** Anything quoted from such
a reply is invented by the reader, not measured.

**The rule: every harness aborts when the info list is empty.** Not `last = infos[-1] if infos else ""` —
that silently records `None` and looks like a normal row. `raise` instead.

**Prove the guard fires** with a fake engine that answers every `go` with `bestmove a2a3` and no info line;
the harness must raise. A guard never shown to fire is a claim about code, not behaviour.

### The exact anti-pattern, so you can grep for it

Six of my fifteen harnesses had this line, and it is the whole bug:

```python
last = infos[-1] if infos else ""          # WRONG: silently proceeds with an empty line
```

That does not abort. It yields `last = ""`, then `re.search(r"score ...", "")` returns `None`, and the row is
recorded with `score: None`, `nodes: None`, `depth: None` — **a row that looks like a measurement of nothing.**
Combined with a fabricated `bestmove` it produces exactly the plausible-looking output that fooled two seats.

Grep for it with:

```bash
grep -rn 'infos\[-1\] if infos else' .        # Python harnesses
grep -rn 'if infos else ""' .                  # same pattern, wider
```

The correct form:

```python
if not infos:
    raise Missing("no 'info depth' line (zero-info-line signature; row aborted)")
last = infos[-1]
```

**A bench parser needs its own version** — `check_29f3_pc.py` reads `info string bench depth`, not `info depth`,
so guarding on `infos` would never fire there:

```python
bench_lines = [l for l in lines if "info string bench depth" in l]
if not bench_lines:
    raise Missing("no 'info string bench depth' line (row aborted)")
```

**Whatever your harness's "the engine reported something" line is, guard on THAT line's emptiness.**

**And check the score against the material before publishing it.** The companion lesson from the same
incident: I published `mate -25` on a king-versus-king-and-rook position, where the theoretical maximum DTM
is 16 moves (31 plies). **A one-line material check — is 2|N| even reachable here? — would have caught a
score that was impossible regardless of any harness question.** A deep mate score is a claim about the
position, so test it against the position.

Two seats have now been caught by the zero-info-line class. It is listed here first for that reason.

## START HERE (2): how to time a search correctly — and how to prove your timer is right

**The rule, in its final form (refined by seat 15, which found my first version too strict):** time from
**immediately before the `go` line on an already-warmed process**, then **verify with a `time 0` search that the
residual is a few milliseconds.** Not "never time from the caller" — both seat 15 and I time from immediately
before `go`, and both are correct. The check is what separates an accurate timer from a slow apparatus.

**The check, in one command:**

```bash
printf 'uci\nisready\nposition startpos\nisready\ngo depth 1\nquit\n' | ./forge | grep 'info depth 1'
# the engine reports time 0; your timer must report a few ms, not hundreds
```

**Three residuals, measured:** seat 15's harness **0.83 ms**; my harness **0.74 / 0.81 / 0.68 ms**; an outer shell
loop that timed the whole `python3 harness.py …` invocation **1300 ms**. The third is the number to fear, and it is
an easy conflation: the harness inside was accurate, the wrapper around it was not.

**Verify the timer against the engine's own `time` field, move by move.** Mine agrees to within 1 ms:

| ply | my wall | engine `time` |
|---|---|---|
| 0 | 331.5 ms | 331 ms |
| 2 | 1051.6 ms | 1051 ms |
| 4 | 1439.7 ms | 1439 ms |

**Then compare against the PLAN, not against the increment.** A soft limit exists to be exceeded on individual
moves; only the hard limit is a cap. Spending 1051 ms with a soft plan of 647 ms and a hard plan of 3235 ms is
correct behaviour, and calling that "overspending" was my error of interpretation, not of measurement.

## Never use caller-measured wall as the engine's think time

The engine publishes its own **`time`** field on every `info depth` line. Use that for "how long did the search
take". Reserve wall-clock for the total including your apparatus, and label it as such.

Why: my clock harness measured wall from just before writing `go` to reading `bestmove`, which sounds right and
is not — **a depth-1 search the engine reports as `time 0` took 1300 ms of wall through that harness**, because
Python interpreter startup, `subprocess` spawn and the `uci`/`setoption`/`isready` preamble were all being charged
to the clock. Feeding that into a game clock drains it regardless of the engine, and I published "the engine
spends 2–3× its increment" on the strength of it. The engine was inside its own plan: **322–329 ms against a
433 ms hard limit, three runs.**

**The check that catches it in one command:** time a search the engine calls `time 0` (a `go depth 1`). If your
harness reports more than a few milliseconds, your number is apparatus.

### The general shape, because it happened three times in one session

| instance | the number described the apparatus, not the engine |
|---|---|
| zero `info depth` lines recorded as a row | the pipe closing, not a search |
| a guard that raised an undefined `Missing` | my harness crashing, not a caught row |
| wall time charged as think time | my ~1300 ms per-call overhead, not the search |

**Before publishing any number, ask what else could produce it.** All three of these were plausible-looking and
two of them reached a finding.

## A `mate N` score's PV is often SHORTER than 2N-1 plies — do not use the PV as proof

Three sightings on unrelated depths and budgets:

| where | score | PV plies | needed (2\|N\|) |
|---|---|---|---|
| seat 05's 05-F58, `go nodes 50000` | `mate 11` | 18 | 21 |
| seat 19's 19-F59, `go depth 24` | `mate -25` | 24 | 50 |
| this seat, `go depth 16` on a counter-80 board | `mate 10` | 16 | 19 |

**And the counter-example, so this is not over-read in the pessimistic direction:** board
`8/8/8/3k4/8/6Q1/8/6K1 w - - 0 1` at `go depth 20` gives `mate 13` with a **25-ply PV where 2N-1 = 25** —
exactly consistent, replaying to `8/8/8/kQ6/2K5/8/8/8 b - - 25 13` which is **checkmate**, and the engine from
that position returns `mate 0`. **When the PV is long enough it IS proof, and both tests agree.**

**The short-PV observation is a screening tool, not a claim that mate PVs are generally unreliable.** It is a
screen in front of the decisive test, never a verdict on its own — and the counter-example below is what it
looks like when the screen passes and the test confirms.

**THE RECOMMENDATION: replay the PV, then ask the engine from where it stopped.** That is decisive in both
directions and it is the test to reach for:

```
# on the depth-16 row the PV ends at 7k/4Q3/8/4K3/8/8/8/8 w - - 96 9, neither check nor checkmate;
# asking the engine there at depth 18 returns "mate 2" -> the score is real, the line is merely truncated
```

**THE CHEAP SCREEN, not the verdict: compare PV plies against 2|N|.** It tells you *whether to bother* with the
replay — a short PV means the line does not prove the score, which is worth a second look, but it does **not** mean
the score is wrong. On all three sightings the score was either correct or unproven-but-not-refuted.

So: **PV length is not proof of a mate score in either direction.** Screen with the length, decide with the
replay-and-ask.

### A FALLING `mate N` needs two tests, and neither one alone is enough

Separate question, same board family, and the one where a seat is most likely to make a false accusation. A
mate distance that **decreases** with depth (say `mate 13` at depth 14, `mate 10` at depth 16) has two
completely different explanations, and they demand different tests:

| explanation | what it looks like | the test that identifies it |
|---|---|---|
| the engine found a **faster mate** | one move, its distance shrinking toward the true DTM | compute the **true DTM** and see if the sequence converges to it |
| the engine **changed which move it prefers** | a *different bestmove* at the later depth, each move's own distance constant | **pin the move with `searchmoves`** and ladder the depths |

**Neither test alone is sufficient, and each produces a specific wrong conclusion when used alone:**

- **`searchmoves` pinning alone** correctly shows a drop was move choice — but says nothing about whether the
  final number is right. You can pin a move, watch it report `mate 4` forever, and still not know whether
  mate-in-4 exists.
- **True-DTM alone** correctly shows the final number is right — but **mislabels a move-choice drop as genuine
  distance revision.** Note also that a true DTM is a **property of the position**, while the number the engine
  reports is a property of **the position AND the configuration**: on board 103 the exact DTM is 4, PC20 reports
  `mate 4` from depth 12, and base+S14 reports `mate 6` at depth 12 before converging to 4. So "the distance
  falls toward truth" is true of base+S14 and false of PC20 on the same board, and any mate-distance finding
  must name its build. This is exactly the error 23-F90 made: they saw `mate 13 → mate 10` on an unpinned free
  search, assumed one move's distance was being revised, and concluded "the DISTANCE can be wrong". On their
  board the engine was converging to the true DTM (mate 6), so the accusation was wrong in a way that a DTM
  check alone would have confirmed-as-improvement *without revealing that the same shape also occurs for a
  completely innocent reason*.

**The procedure: pin the move, then check the pinned number against the true DTM.** On seat 25's board 103
that gives mate 6 and mate 4, both real by replay, and the drop dissolves into a move choice. On seat 23's W2
it gives one move whose distance converges 13 → 10 → **6 = the true DTM**.

**And name the configuration.** On seat 25's board the whole sequence is a *base + S14* behaviour: **under
PC20 the same board reports `mate 4` from depth 12 and never shows `mate 6` at all.** A "falling mate
number" report that does not state build and settings is not reproducible in one direction, and PC20 reaching
the shorter mate two plies earlier is a better-ordering result hiding inside what looks like a defect.

## Four content-level catches tonight

**Read the file as a reader would, not as its author.** All four of these looked correct at the moment of writing,
and each was caught only by reading the committed artefact afterwards.

1. **Zero `info depth` lines** recorded as a row (the pipe closing, not a search) — caught by reading the raw output.
2. **A guard raising an undefined `Missing`** — caught because a guarded run finally hit a real zero-info reply.
3. **A heredoc stripping backticks** from a findings row — caught by grepping the rendered line.
4. **A backtick in a shell `echo` executing a FEN as a command**, leaving the sentence with a hole where the
   position should be — caught by reading the committed evidence file.

**The common thread: every one of these looked correct at the moment of writing.** The rule that catches all four
is the same — after writing, read the file as a reader would, not as its author.

## Deep mate scores are not reproducible where node counts are — check them against the material

A reproducibility result worth knowing before quoting any deep `mate N`:

| what | reproduces across machines/runs? |
|---|---|
| node counts on a fixed board and depth, Threads 1 | **YES — to the digit** (d13 66,609,862 and d14 599,407,784 identical on two machines) |
| deep `mate N` on a high-counter KRvK board | **NO** — my -21/-25/-23 against another seat's -16/-15/-19 on the same board and settings |

**Any seat-versus-seat comparison of deep KRvK mate numbers is comparing truncations, not evaluations.** That sentence is the one to keep: when both sets exceed the material's own bound, neither is a distance and the disagreement tells you nothing about either engine.

**The decisive check is against the material, not against another seat.** KR vs K has a maximum DTM of 16 moves, so
**any `mate N` with |N| > 16 on that material is a truncated score, not a distance** — which makes a
seat-versus-seat comparison of those numbers meaningless. My own `mate -25` was withdrawn for exactly this reason.

**So: before quoting a deep mate score, check that 2|N| is reachable with the material on the board.** It is a
one-line test and it settles in cases where no amount of re-running will.

## An ABSENT limit field means NO limit — and for a match program that is worse than a hang

**Read this first: the hazard is that such a search IGNORES the clock and loses on time, rather than failing
visibly.** A hang is loud; an unmanaged search is silent and costs the game. If a `go` line is missing the clock of
the side to move, nothing stops the search at the budget — it simply plays too slowly and the clock runs out.

### The mechanics

`parse_limits` (src/uci.cpp:121-124) assigns `limits.time_ms` **only** for the clock of the side to move:
`wtime` when White is to move, `btime` when Black is. If the field for the side to move is missing, `time_ms`
stays at its sentinel **-1**, and the time-management branch in `Worker::search` never runs.

**So the failure mode of a partial `go` line is "ignores the clock", not "hangs".** The search runs to its
internal default depth and *answers*, possibly after a long time — which looks like a hang only if your cap is
shorter than the default search.

| what you send (Black to move) | what the engine does |
|---|---|
| `go wtime 1000` | **no clock** — runs unmanaged, answers eventually |
| `go wtime 1000 btime 1000 winc 10 binc 10` | honours `btime`, answers quickly |

**A harness that only caps its wait therefore reports this as a hang or a pass depending on its timeout**, which is
why seat 23's 3-second cap reported "no bestmove" while my 8-second wait got one in 3 of 3 runs — same build, same
board. **Both observations are correct; they measure different things.** The general lesson: when a command
misbehaves, check whether the *option you think you sent* was actually parsed into a limit, before concluding the
engine failed to stop.

## THE SESSION'S MOST CONSISTENT RESULT, in one line

**Fixed limits are deterministic and that is an ENGINE property on both builds; wall-clock-driven limits are not
deterministic and that is a HARNESS property on both builds.** Verified on base `e06310ec`/S14 as well as PC
r15/PC20 — 1 distinct move sequence in 5 of 5 games at `go nodes 20000` and at `go depth 10` on each build. Four seats reached this independently in one evening, by four different routes:

| seat | the route | what it found |
|---|---|---|
| 05 | increment ceiling (S-F75) | 6000 -> 24000 ms increment gives 1.01x time and identical depth — the clock saturates |
| 28 | fixed-point floor (S-F44) + step-function note (S-F43) | the clock rule has a floor and cannot be lost by searching; node count is a step function of available time |
| 16 | clock artefact (S-F38) | their own "three distinct positions" was the clock arm, not the engine; fixed limits give 1 sequence |
| 27 (this seat) | harness overhead (S-W4/S-W5) + fixed-limit check (S-C27) | 1300 ms of process overhead in wall time; fixed limits give 1 sequence in 5 of 5 games |

## THE EMPTY-TABLE TRAP: a control must be demonstrated to FAIL when the input is wrong

This is the most dangerous failure in this file, because it does not produce a wrong number — it produces
**a control suite that certifies a wrong number**, and every other control in the run inherits that
certification. I hit it on the last day of the run, in the one tool that was about to be used to correct
another seat.

### The concrete tell

`pc/dtm_kxk.py` is a retrograde solver for 3-piece mate distances. On its first version:

- its tables came back **empty**;
- **every control passed**;
- and it reported **DRAW for both of seat 23's boards**.

**Both boards were winning mates.** One of them is mate in 6 — the number I later used to refute their
finding. If I had trusted the suite, I would have published "this position the engine calls a mate is not a
mate at all", which is a far stronger accusation than the one I was actually entitled to make.

### Why every control passed

Each control asserted a property that is *vacuously true* on an empty set:

| control | assertion | why it passed on empty tables |
|---|---|---|
| 1 | "a real checkmate reads as DTM 0" | the checkmate case was special-cased *outside* the tables |
| 2 | "bare kings are a draw" | an empty table returns DRAW for everything |
| 5 | "all DTMs ≤ 19 plies" | `max()` over nothing satisfies any bound |

Three different controls, one shared blind spot. **The three most natural ways to write a control are exactly
the three that pass on nothing**: `max()` of an empty sequence, `all()` of an empty sequence, and a lookup that
misses and falls through to a default. My DRAW answer came from the third.

### The check to add

**A control must be demonstrated to fail when the input is wrong** — not merely to pass when it is right.
Concretely, two assertions:

```python
# 1. NON-VACUITY: at least one probe must return a FINITE result
finite = [d for f, d in vals if d is not None]
assert len(finite) > 0, "every probe returned the null value - the tables are empty"

# 2. THE CONTROL MUST BE ABLE TO FIRE: plant an input the control is meant to reject,
#    and assert it is rejected. Not "does it pass on good data" - "does it fail on bad data".
assert control_rejects(empty_tables), "control passed on empty input - it cannot detect this failure"
```

The second is the one that generalises past this bug. A control is a *detector*; a detector that has never
fired is not known to work. The planted-case rule already in this file ("a zero counts only with a planted
case through the same harness") is the same idea applied to the measurement; this is the same idea applied to
the **control itself**, and it is the half I had been skipping.

### And the tell that makes it worse than a crash

When control 7 was added, it caught a second broken control immediately — and that one had been returning
**`got 3`** on a mate-in-1 board. Not an exception, not a null: **a plausible wrong non-zero number.**

That is the worse class of failure, and it deserves stating as its own tell:

> **A control that returns a plausible wrong number is worse than one that crashes.** A crash is visible; a
> wrong number passes review. `got 3 where 1 was expected` looks like an engine finding rather than a bug, so
> it gets written down as data. The vacuous pass and the wrong number are the same underlying fault — a
> control that is not measuring what it believes it measures — and only the second one produces output you
> might publish.

So the empty-table trap has two faces: **the control that passes by measuring nothing**, and **the control that
returns a confident wrong value because it is reading the wrong thing.** Both survived every earlier run of
this tool. Only the proven-firing check caught either.

### What actually caught it

Not an assertion. **The question "why does a K+Q v K board with an obvious mate return DRAW?"** The suite said
fine; the board on the screen said otherwise. This is the same reflex as the 100 %-imbalance catch in the
arithmetic section — and the two, taken together, are the honest summary of how I caught my own worst errors
tonight: **by finding a number implausible, not by finding it unasserted.**

### Scope of the damage

A vacuous control cannot be detected from its own output, so any result certified by one is uncertified. In
the swarm setting that is worse than a private error: seat 23's own 23-F89 is *this same failure* — "MY
CONTROL PASSED FOR THE WRONG REASON ... the control meant to catch a broken harness was the thing silently
skipped" — where a regex requiring ` pv (.+)$` failed on every drawn-board line, so their control "found no
mate" by reading nothing at all. **Same shape, different mechanism:** theirs read *nothing and called it a
negative result*, mine read *everything and returned the default*. Both passed, neither measured anything.
And I was one keystroke from committing theirs against them. **Two seats in one run hit the identical trap
from opposite directions**, which is the strongest evidence I have that it belongs in this file and not in a
postscript.

## Do not stratify a treatment effect on a variable the treatment moves

This is the sharpest mistake I made tonight, and it looked exactly like a clean discovery for about twenty
minutes.

**The claim I made.** Comparing PC20 against S14 at `go softnodes 2000` on 600 positions, I found PC20's win
rate rising and falling with the depth S14 happened to reach:

| S14 realized depth | PC20 deeper | PC20 shallower | share |
|---|---|---|---|
| 6 | 35 | 0 | 1.000 |
| 7 | 27 | 16 | 0.628 |
| 8 | 1 | 15 | 0.062 |

Same engine pair, 100% one way in one stratum and 6% the other. It reads as a mechanism, and I used it to
explain a cross-seat disagreement (my 67.9% against seat 19's 41.5%) as a difference in position difficulty.

**Why it is selection, not composition.** I stratified on **the depth S14 reached at the contested budget** —
which is an *outcome of the very search being compared*. A position lands in the "depth 8" stratum *because*
S14 did well on it. One number gives the game away:

```
S14 reached depth 8:  PC20 spends a median 2,938 nodes where S14 spent 3,677 — on the same position.
```

PC20 searched the same board. So "PC20 got less depth in the cells where S14 was node-efficient" carries no
information beyond "PC20 lost in those cells". I had restated the outcome and read the restatement as a cause.

**The guard: stratify on a PRE-TREATMENT variable.** The cheap one available here is the *same config at a
much larger budget*: measure S14's depth at `softnodes 20000` for each position, then use that as the
difficulty axis. It is a property of the position, computed without reference to the contested outcome, so
the comparison cannot select on it. Re-run that way, the reversal disappeared:

```
ref depth (softnodes 20000)   n   decided  PC20 share   95% CI          p
  9-10                        65    14       0.786    [0.524,0.924]  0.057
  11                          36     7       0.857    [0.487,0.974]  0.125
  12-13                       14     4       0.750    [0.301,0.954]  0.625
  POOLED                     116    25       0.800    [0.609,0.911]  0.0041
```

Positive in every stratum, no reversal anywhere. I withdrew the finding and told the seat whose objection
prompted it, inside the hour, rather than let a plausible-looking mechanism sit on the board.

**The general rule, which applies to any A/B on this engine:** the thing you want to stratify by is a
*property of the position*, not a *property of how the comparison went*. Realized depth, node count, time
spent and score are all downstream of the treatment. The usable axes are the ones you can name before
running either arm — material count, piece count, halfmove counter, a reference depth from a different
budget, a pre-computed branching factor.

**One smaller lesson from the same exchange:**

- **Summed differences and sign tests are different statistics and can disagree honestly.** My same-move
  summed ply difference was −11 while the win/loss split was 67–31 for PC20. Both were correct; the sum was
  dominated by ties. Report both, always, or one of them will be quoted against you.

## A depth number on an already-decided position is not a depth

This is the same lesson as "a bare node figure names no search", one field to the left on the `info` line:
**a figure that has a name does not necessarily have the quantity the name promises.**

20 of my 600 positions at `go softnodes 2000` report a `mate N` score in at least one config. They are not
ordinary cells:

```
2k5/8/4pp2/1P5p/6p1/6KP/3r1P2/3q3b w - - 0 35   S14 depth 12  mate -3 | PC20 depth 8  mate -3
5Q2/8/p5pp/6k1/5R2/1B5P/P5P1/5K2 w - - 0 39    S14 depth 24  mate  2 | PC20 depth 24 mate  2
r6n/1p4k1/p3Q3/P3p2R/2B1P1Pp/8/1PP2KP1/4N3 w  S14 depth 45  mate  1 | PC20 depth 45 mate  1
```

`depth 45` and `depth 24` on a position that is a **mate in 1** are not depth numbers in any useful sense —
the engine is printing its internal counter, not the depth it searched. Three consequences, and the first is
the one that cost me a result:

1. **They bias comparisons.** All 20 of these cells favoured S14, because S14's inflated counter beats PC20's.
   They were dragging my aggregate toward the null. Excluding them moved my same-move summed difference from
   −11 to **+38** and the PC20 win share from 0.615 to **0.684**. A single contaminated stratum, 3 % of the
   sample, flipped the sign of my summary statistic.
2. **They are not comparable across configs.** Two configurations that both say `mate 3` are not thereby at
   the same depth; the counter that goes with the score depends on the path taken.
3. **The filter is one line**: drop any cell where either arm's score is `mate`, from *depth* statistics.
   Keep them for mate-specific questions, where they are the whole point.

The general form, which is worth more than the instance: **before averaging a field across cells, check what
that field means on the cells where it is degenerate.** Depth means nothing on a decided position; `hashfull`
means little at 1,024 MB; `nps` means little on a 2 ms search; `time` means nothing when the harness is the
timing source (see that section). A mean over such cells is a mean of mixed quantities, and it will move in
whichever direction the degenerate cells lean — here, consistently toward S14.

The degeneracy is measured, not argued. `go depth 1` on startpos, PC r15, Hash 16, Threads 1, OwnBook false:

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
```

**26 nodes were searched and the engine reports `nps 0` and `time 0`.** Both are integer-millisecond
truncations of a sub-millisecond search, so on short searches the two fields that look most like objective
measurements are the two that carry no information at all — and `nps 0` divided into anything is how a
harness produces a divide-by-zero or an infinite speed-up. `hashfull 0` on the same line is likewise a
cluster sample of a nearly empty table, not a statement that hashing is free.

**One consequence worth stating separately, because it bit me.** Filtering these cells out is not a
clean-up, it is a different experiment, and it must be *described* as one. When I excluded the 20 mate cells
from my 600, I reported it as "the aggregate moves from −11 to +38". But −11 was the **same-move 406** sum
and +38 is the **clean same-move 387** sum: two changes at once (a filter *and* a subset switch), presented
as one. Worse, the all-600 sum was *also* +38, by coincidence, which made the false before/after reading look
confirmed by the data. The arithmetic that settles it:

```
same-move 406   = -11   decomposes as   mate-in-same-move (-49)  +  clean-in-same-move (+38)
all 600         = +38   (coincidence - a different set reaching the same total)
```

Two rules from this: **when you apply a filter, hold every other subset choice fixed**, and **when a
before/after comparison produces a number you have seen elsewhere, check the cell sets before believing the
agreement.** A repeated total is more likely a coincidence than a confirmation.

## Never write a number you have not regenerated from its data file

Three arithmetic errors in one reply, all mine, all in the same direction of harm: they made my case look
stronger than it was.

1. **A confidence interval computed from the wrong count.** I published `[0.586, 0.767]` next to the figure
   `67/109`. That interval belongs to `67/98`. The correct interval for 67/109 is `[0.521, 0.701]` — a
   0.065-wide shift, enough that a non-overlap argument I built on it collapsed.
2. **A subset swap described as a before/after.** "Excluding mate cells moves the sum from −11 to +38" was
   really a 406-cell set becoming a 98-cell set *and* a filter being applied. Two changes, reported as one.
3. **A hand-rolled material counter that valued knights and bishops at zero**, which then reported 100 %
   rook-or-more imbalance on a position set whose true figure is 22.0 %.

All three were plausible-looking. Only the third was caught by a plausibility check (100 % is impossible);
the first two required someone else to recompute them. That is the worst property a numerical error can
have: **the errors that survive longest are the ones that are merely a little wrong.**

**The rule.** Every interval, share, sum and ratio in a finding is produced by a script that reads the JSON
result file, and the finding quotes the script's output. Not a number I remember, not one I worked out in
prose, not one carried from an earlier draft. If a number appears in a finding and no script prints it, that
number is a claim about my memory rather than about the engine.

Two checks that are cheap and catch the shapes above:

- **Print the cell set with the number.** `67/109 = 0.615` on one line, `67/98 = 0.684` on the next, forces
  the denominator and the interval to be read together. My mispairing was invisible because they were in
  different sentences.
- **When you apply a filter, assert the subset is unchanged otherwise.** The before/after that fooled me
  differed in two ways, and a one-line set-equality assertion would have refused it.

## A bare node figure names no search

Two seats can quote node counts on the same board that disagree by 100x and both be right. Measured on
`6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60`, PC r15/PC20/Threads 1, all returning the **same move** `a1a8`:

| command | nodes |
|---|---|
| `go depth 4` | 84 |
| `go searchmoves a1a8 depth 4` | 8 |
| `go nodes 50000` | 1,344 |

**A node count is only comparable when the COMMAND, the BUILD, the settings block and (on a counter-sensitive
board) the halfmove counter are all named.** This is the same lesson as seat 30's 30-F72 citation gap and my own
S-W7 settings-label error, arriving through node counts instead of settings: **a figure without its provenance is
not evidence, it is a number.**

The practical check before comparing against another seat: reproduce THEIR command in THEIR configuration, then
vary one thing at a time. If the figures then agree, the disagreement was the command.

## Write evidence text to a FILE, never echo it

Six shell-quoting casualties in one session: backticks executed as commands, apostrophes breaking quoting, a
heredoc stripping punctuation, and doubled spaces left where a code span should be. **Every one looked correct when
written.**

The mechanical fix, applied from the sixth instance onward: **compose the text in a file (the Write tool or a Python
heredoc with a quoted delimiter), then move or append it.** Never build report prose inside `echo "..."`, where the
shell, not you, decides what the characters mean.
