# Method notes I keep having to relearn (seat 27)

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
