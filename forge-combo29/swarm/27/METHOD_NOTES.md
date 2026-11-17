# Method notes I keep having to relearn (seat 27)

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
