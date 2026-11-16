# HOW THESE PROBES LIED TO ME — two harness traps, both of which looked like engine defects

Seat 11. Every finding of mine that was wrong was wrong because of the probe, not the engine. Two of
those traps are general enough that anyone writing similar probes will hit them, so they are written
out here in full. Both were caught by a control, not by luck.

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

## Three more, shorter, from the same folder

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

## The pattern behind all four
Each trap produced a *plausible* engine defect from a *provably wrong* probe, and each was killed by a
control rather than by re-reading the code:

| trap | the control that killed it |
|---|---|
| pawn on the king's square | engine and python-chess agreed (5 = 5) — no defect can exist where two independent implementations agree |
| shell sent `stop` | an ordinary-board control that must also stay silent, and it did |
| tuple unpacking | the printed score was `('mate', 1)` on the very line the verdict called a failure |
| optional-field parser | `bestmove` came back legal, so a search had plainly run despite the zero line count |
| mislabelled FEN | re-deriving counts from the generated FEN instead of the intended label |

Both traps are recorded in my findings as process notes (S-F65, S-F26) so they are not mistaken for
engine behaviour by anyone reading the table later.
