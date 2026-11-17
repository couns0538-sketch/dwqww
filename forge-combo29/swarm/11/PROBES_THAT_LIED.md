# HOW THESE PROBES LIED TO ME — nine ways a probe looked like an engine defect

**Contents:** Trap 1 (pawn on the king's square) · Trap 2 (the shell sent the `stop`) · Trap 2b (the harness window decided the outcome) · Trap 3 (a verdict read off a tuple) · Trap 4 (a parser keying on an optional field) · Trap 5 (a mislabelled FEN) · Trap 6 (a narrow band skipped by four sampled points) · Trap 7 (a null without its expected count) · Trap 8 (a "deterministic" metric that moves between identical runs).

Nine entries; trap 2b is a second occurrence of trap 2's root cause, which is why it carries a letter rather than a new number.

Seat 11. Every finding of mine that was wrong was wrong because of the probe, not the engine. These
nine are the ones general enough that anyone writing similar probes will hit them, so each is written
out in full: what I saw, what was actually true, the tell I should have read first, the fix, and the
corrected result. Every one was caught by a control, not by luck.

---

## Trap 1: the probe that put the pawn on the king's square

### What I saw
I was testing promotion generation. My probe reported:

```
push promo (e7-e8)
  engine 5 = py 5: True
  engine promos []
  py     promos []   same=True
```

An **empty** promotion list where I expected four entries. Read naively, that is "the engine does not
generate promotions" — a serious move-generation defect, and one that would have been my biggest find.

### What was actually true
My FEN was `4k3/4P3/8/8/8/8/8/4K3 w - - 0 1`. The black **king stands on e8**, so my pawn on e7 had
no square to promote to: `e7-e8` is blocked by the king. python-chess agreed with the engine
**exactly** — 5 legal moves, no promotions — which is what finally gave it away: the reference
implementation and the engine agreeing on an "empty" answer means the answer is right and my board is
wrong, not that both are broken.

### The tell I should have read first
`engine 5 = py 5: True` was printed on the same line as `promos []`. If the engine and the reference
disagree about nothing at all, there is no defect to find. I was reading the second column and
ignoring the first.

### The fix, and the corrected result
Pawns must be on `a7`/`h2` with the promotion squares **empty**:

```
push promo (a7-a8)      engine 9 = py 9:   a7a8b a7a8n a7a8q a7a8r          (identical to py)
push+capture promo      engine 13 = py 13: a7a8b/n/q/r  a7b8b/n/q/r          (all eight, identical)
black promo             engine 9 = py 9:   h2h1b h2h1n h2h1q h2h1r
promo with check        engine 9 = py 9:   a7a8b a7a8n a7a8q a7a8r
```

### The general rule
**When an "empty" or "zero" result surprises you, check that the probe can produce a non-empty result
at all before believing the zero.** A positive control board — one where the feature you are testing
MUST fire — is as necessary as the negative one. See S-F65.

---

## Trap 2: the probe whose own shell sent the stop it was testing for

### What I saw
I was testing whether `go infinite` at a terminal root ever volunteers a `bestmove`. My first probe
appeared to show a **fix**: the engine answered `bestmove 0000`, which is exactly the behaviour you
would want.

```
-- 8/8/8/8/8/6K1/8/Q5k1 b - - 0 1     (checkmated root)
readyok
bestmove 0000
```

### What was actually true
My shell pipeline was:

```bash
(printf 'uci\n...\ngo infinite\n'; sleep 5; echo stop; sleep 2; echo quit) | engine
```

The `stop` two seconds in **released the bestmove**. The engine never volunteered it. I had measured
"the engine answers on `stop`" — which was already known — while believing I had measured "the engine
volunteers" — which is the actual question, and whose answer is **no**, on both builds.

### The tell I should have read first
A `go infinite` search has no reason to end. A `bestmove` arriving from one, unprompted, is suspicious
by itself. The correct instinct is "what did I send that could have caused this?" — and the answer was
in my own pipeline, three tokens away.

### The fix, and the corrected result
The probe now sends **no `stop` inside the measurement window**, and includes an ordinary-board control
that must also stay silent:

```
wait window 6.0s with NO stop sent
  checkmate root    bestmove=None  at=NEVER  volunteered=False
  stalemate root    bestmove=None  at=NEVER  volunteered=False
  ordinary board    bestmove=None  at=NEVER  volunteered=False
```

Identical on base 6b98f217 and PC r15. The defect is real: `go infinite` at a terminal root never
volunteers a bestmove, on the engine the owner plays. See S-F26.

### The general rule
**A probe must not send the stimulus it is testing for.** If the harness sends `stop`, `quit`,
`ucinewgame` or any other command during a measurement window, write down exactly which command could
produce the observed output before believing it came from the engine. The control that saves you is a
board where the behaviour must NOT happen (here: an ordinary position, which also stays silent).

---

## Trap 2b: the harness window decided the outcome, not the engine (the same lesson, second occurrence)

### What I saw
Testing clock edge cases, one command reported:

```
go wtime 6000        -> TIMEOUT/ERR TimeoutError
go btime 6000        -> bm=g8f6  136 ms  legal=True
go wtime 6000 btime 6000 -> bm=g8f6  136 ms  legal=True
```

`go wtime 6000` alone timed out while its neighbours answered in 136 ms. Read quickly, that is a
**HANG** — the most serious class of defect file 6 recognises.

### What was actually true
It was searching normally and simply took longer than my 30 s window. Watching the raw output for 15 s
showed it reaching `depth 31`, **18.9 M nodes**, and then answering `g8f6` at ~11.8 s. The engine was
never stuck; my harness had decided the verdict by cutting it off.

### The tell I should have read first
The neighbours answered in 136 ms and this one did not — but a timeout is only evidence of a hang if
you have already shown the search is doing nothing. Here the right next step was to read the `info`
lines and watch the node count climb, which takes one command and would have taken thirty seconds.

### The fix, and the corrected result
Watch the node count instead of only waiting for `bestmove`. Corrected: not a hang, but a real and
practically important behaviour — **136 ms with both clocks vs ~12 s with only `wtime`**
(`checks/clock_edge.txt`, S-F78). It became one of the more useful protocol findings of the run, and
it would have been filed as a false hang.

### The general rule
**A timeout is not a hang until you have watched the search work.** A harness deadline is a property
of the harness. Before reporting a hang, capture the `info depth ... nodes ...` lines and check the
node count is advancing; if it is, your window is too short, not the engine too slow.

### Why this is Trap 2b and not a new number
Trap 2 was "the harness sent the stop it was testing for". This is the same root cause one layer out:
**the harness, not the engine, produced the observation.** Both were about a command the probe sent
during the measurement window (a `stop`, or a deadline that behaved like one). Twice makes it a
pattern, so it is recorded as a pattern.

---

## Six more, shorter, from the same folder (traps 3-8, after 1, 2 and 2b above)

**Trap 3 — reading a verdict off a tuple.** A defect-hunt loop reported 14 "defects" on a board where
every score was `('mate', 1)`. The score WAS found; my unpacking was `score, bm = s` where `s` was already
the `(kind, N)` tuple, so `score` became the string `'mate'` and `score == ('mate', 1)` was always false.
The tell: the *scores printed on the same lines* were correct and positive. Corrected: 0 defects
(`checks/defect_hunt_pc20.txt`).

**Trap 4 — a parser that keys on a field the engine only prints sometimes.** My MultiPV probe
counted lines with `multipv (\d+)` and reported "MultiPV 1: lines 0" — which reads as "the engine
emitted nothing". It emitted the lines; at MultiPV 1 the engine OMITS the `multipv` field (standard
UCI), so the regex matched nothing. The tell: `bestmove` came back and was legal, so a search had
clearly happened. The general rule: **before trusting a zero count, confirm the field you are
counting exists in the format at that setting** — and prefer parsing the invariant (`info depth ...
score ... pv ...`) over an optional field. See S-F74.

**Trap 5 — a mislabelled FEN is invisible if you trust the label.** I twice reported the engine wrong
about the piece-inventory rule because I had labelled an `8P+2R` board "8P+3R", and a board with 8 pawns
"7P". Both times the engine was right. The fix that generalises: **build the FEN from the intended counts
and re-derive the counts from the generated FEN before printing the label** (`inventory_probe.py`). See
S-F16, S-F25.

---

**Trap 6 — a switch's effect can live in a NARROW BAND, and four sampled points can miss it.**
Testing `FORGE_FIX_HARD_LIMIT_EMERGENCY` I tried `go wtime t btime t` at t = 11, 12, 15 and 30 ms, saw
no difference, and was ready to write "unmeasured — no probe distinguishes ON from OFF". Sweeping
every value from 11 to 60 instead, the effect appears at **t = 16, 17, 27, 28 and 31 — 5 of 50 values**,
and at t = 17 the MOVE itself differs (`g8f6` with the switch on, `a7a6` with it off, `a7a6` being the
unsearched first legal move the switch exists to avoid). The four points I had chosen were all outside
the band, and three of them were consecutive, which made the miss feel like evidence.
**The general rule: a negative result on a numeric or timing parameter is only as good as the grid you
sampled.** Before writing "no effect", sweep the whole plausible range at a fine step, not four
hand-picked points — and if you cannot afford the sweep, report "not observed on these N points",
naming them, rather than "unmeasured". (S-F91)

**Trap 7 — reporting a null without the expected count.** Testing `FORGE_FIX_ABORT_PUBLISH` I found 0
differing moves in 80 exact-node stops. That sounds like "no effect", but the switch's own author
measured a 73-in-19,800 rate (0.37 %), at which **80 stops would expect about 0.3 differing moves** —
so zero is the overwhelmingly likely outcome and carries almost no information. Reporting "0 of 80" as
though it were evidence would have been misleading; reporting "0 of 80, where 0.3 were expected, so this
sample cannot see the effect" is honest. **The general rule: a null result needs its expected count.**
Compute how many hits your sample should have produced at the effect size you are looking for; if that
number is below about 5, your null is uninformative and you should say so rather than claim absence.
(S-F92)

**Trap 8 — a node count under a CLOCK stop is not a deterministic quantity.** This is **not confined to
the narrow clock band** where I first found it: the same instability appears in a completely different
command form, `go movetime 50`, where five repeats of one binary gave node counts of **47,601 and
69,531**. So the rule generalises — anywhere a node budget is expressed as a *time*, the resulting node
count is not a quantity the engine controls and must not be quoted as a result. I reported that
`FORGE_FIX_HARD_LIMIT_EMERGENCY` made a near-expired clock deterministic, because one sweep showed the
shipped build stable at 601 nodes 5 of 5 while the switch-off build was not. A second seat repeated the
grid and then repeated each *differing value* eight times per build, and the correction is decisive: at
t = 17 and t = 27 the **shipped** build itself returns 601 OR 1257 nodes across repeats. My 5 of 5 was
luck. What is stable is the **move**, and that is the honest claim: the shipped build answered `g8f6` on
8 of 8 repeats at every value, while the switch-off build gave `a7a6` or `g8f6` at t = 27.
**The general rule: any table comparing node counts across builds under a clock stop needs a
repeat-against-itself check before it is believed** — and if a metric moves between identical runs of the
same binary, no comparison built on that metric means anything. Report stability of the thing that is
stable (here the move), not of the number that merely looks stable in one pass.

**Why this one is worth reading even though it is unglamorous:** the failure was not carelessness.
I ran a sweep, I repeated the differing values five times, and I got a clean 5 of 5 against an
unstable comparator. That is a *plausible single-pass result* — it looks like evidence, it reads like
evidence, and it was a coin landing right. The control that exposed it (repeat the SAME binary against
itself, not the two builds against each other) costs almost nothing, and I simply had not been running
it on clock-stop measurements. Worth adopting before writing any timing table. (S-F91, corrected by
seat 07)

**A companion rule to Trap 8 — the position set dominates any timing median.** The cleanest single
illustration: **fifteen identical clock searches on ONE FEN, same binary, same settings, ranged 143 to
661 ms — a 4.6x spread from nothing but when the timer happened to fire** (S-F100). One position, one
build, one thread, 4.6x. If you quote a single clock figure you are quoting one draw from that
distribution.

The rule itself: two medians for the same clock, same binary, came out four-fold apart — 238 ms over 20
varied G positions (several sparse endgames) and 147 ms over one middlegame repeated. Both were right. Sampling noise moved the median 2 %
across a twelve-fold change in n; the *position mix* moved it 100 %+. So state the position set with
every timing figure and never compare clock medians across studies that used different sets — the
slower-looking engine may just be playing harder positions. **Four independent measurements of the same
6s+0.06 clock on the same build, by two seats, gave medians of 100, 110, 147 and 238 ms — a 2.4x spread
with only the position mix differing** (S-F98). Anyone comparing two such rows would think one engine was
different; neither was. (S-F96b, S-F98)

**This is a structural problem, not a mistake any one seat can fix:** a report table that lists timing
medians side by side across seats is comparing incomparable numbers even when every row is individually
correct. Either the position set becomes a mandatory column, or the medians should not be tabulated
together at all.

**Never quote a clock-stop node count as a deterministic result.**

## The checkers get the same treatment
Every finding here that says "0 problems" or "all rows stable" rests on a tool, and a tool that has
never been shown to fail is a tool whose approval is worthless. So both of my checkers carry a planted
fault they must catch:
- `check_docs.py --selftest` plants an adjacent duplicate line, a splice artefact, a missing path and a
  duplicate heading — **4 of 4 caught** — so "0 problems across 9 documents" means something.
- `clock_check_selftest.py` runs the clock checker against a fake engine with a random node count and an
  alternating move — **correctly reported UNSTABLE** — so "all rows stable" on the real engine is a
  shown result.
- The same logic explains why my first `check_docs.py` run's **8 false positives** were useful: they
  proved the checker could see problems before I refined it to report zero.

**This is the easiest place to forget the rule: we plant faults in the engine all night and then trust
a script that has never been shown to fail.** The engine gets a planted hang, a planted race, a planted
heap over-read; the reporting tools usually get nothing. A checker whose failure mode has never been
demonstrated is the one part of a measurement chain that is taken on faith.

## The pattern behind all of them
Each trap produced a *plausible* engine defect from a *provably wrong* probe, and each was killed by a
control rather than by re-reading the code:

| trap | the control that killed it |
|---|---|
| pawn on the king's square | engine and python-chess agreed (5 = 5) — no defect can exist where two independent implementations agree |
| shell sent `stop` | an ordinary-board control that must also stay silent, and it did |
| tuple unpacking | the printed score was `('mate', 1)` on the very line the verdict called a failure |
| harness deadline treated as a hang | watching `info depth ... nodes ...` showed the count climbing to 18.9 M — the search was working |
| four sampled points missed a narrow band | sweeping every value 11..60 found the effect at 5 of 50 points, incl. a move change |
| a null without its expected count | 0 hits in 80 stops, where a 0.37 % rate predicts ~0.3 — uninformative, not absent |
| a "deterministic" metric that moves between identical runs | repeating each value 8x showed the node count varying on the same binary; only the move was stable |
| optional-field parser | `bestmove` came back legal, so a search had plainly run despite the zero line count |
| mislabelled FEN | re-deriving counts from the generated FEN instead of the intended label |

All seven traps are recorded in my findings as process notes (S-F65, S-F26) so they are not mistaken for
engine behaviour by anyone reading the table later.
