# S02 — the artifacts worth handing on, ranked by portability

Written so a reader can use each one without tonight's context. Order is what I would hand to the next swarm.


## 0. `check_s23f27/COMBINED_RULE.md` — which comparisons are SAFE (read this first)
**A position is budget-safe only if its answer is FORCED or its top-two margin is LARGE.** Quantified: of the
positions that changed move between budgets, **94 % (16 of 17) had a margin within 30 cp** (seat 23's rows, median
14 cp); and at an identical ZERO margin, forcedness decides completely — **found mates changed 0 % (0 of 6) while
quiet ties changed 67 % (2 of 3)**. That second half is the mechanism: a mate in 1 is found at every budget, so no
extra search can flip it, whereas a quiet tie is re-broken at every depth. Use it before comparing results across
budgets, modes or depths; the file also states the one denominator I could not compute, so nobody inherits a
number I did not measure.

## 1. `check_s17f1/TRIGGER_TABLE.md` — the portable one
**Four ways to make this engine answer `bestmove 0000` on a position with legal moves**, the one-line guard that
covers all four, and the detector for auditing after the fact. Self-contained; needs no other file. The key
distinction is that the guard must be about the LIST ("omit `searchmoves` if no legal move is in it"), not about
any individual move NAME — a name-validating guard misses the empty-restriction case, which is the one a GUI hits
by accident with a stale move list.

## 2. `FINAL_HEADLINE.md` — the mode rule
**Across search modes only same-depth results are comparable.** `go nodes` vs `go softnodes` genuinely pick
different moves at the same nominal budget (3/12 cells at 9-15 cp; seat 19 measured 18.4 % at 2-12 cp), while the
clock and the node mode agree once they reach the same depth (all of `depth`, `nodes`, `movetime` return the same
move at depth 13). So: mix no modes, and never compare different depths. This is the single most reusable sentence
I produced, and it came out of the 19-F48 thread.

## 3. `GUI_GUIDANCE.md` — what a GUI must defend against
Per finding: what the engine does TODAY, whether it warns, and what the GUI must do. The headline is an asymmetry:
two defects are completely SILENT (S-F3 `ponderhit` on a non-ponder search; S-F4 a `go` naming only the
opponent's clock), so the only defence is GUI-side, while the third (`Clear Hash` with a value) does warn. Also
states explicitly that the silence is this build's behaviour, not a contract.

## 4. `OPEN_ITEMS.md` — O-3, a match the owner can actually run
The ~5 % clock utilisation question, specified so it can be settled with games rather than more measurement:
`TmSoftDivisor` 22 vs 10, no other change, same exe both sides, 400 games with colours reversed, evidence band
45.1-54.9 % (±4.9 %, ±34 Elo), with an escalation ladder to 1,000 and 1,750 games if a smaller effect is expected.
Includes the measured depths behind the choice (22 → depth 19, 10 → depth 21).

## 5. `softnodes/RECONCILE_s13f7.md` — the overshoot distribution
`go nodes N` / `go softnodes N` overshoot N, because the stop is at an iteration boundary. Measured over 31 cells:
median 1.30x, 90th percentile 1.72x, maximum 2.24x on my 28 cells; median 1.39x, 90th 2.06x, maximum 2.64x
including seat 13's three worst; hard-capped at 4x. Practical rule: **size a resource budget from the median or the
90th percentile, not from 1x and not from the cap.**

## 6. `clock_6s/CLASS_SAMPLE.md` — the clock mechanism
A move's wall time IS the last completed iteration's cost (Spearman rho 0.998, 17 of 20 boards within 2 %), the
engine uses only 3.3-5.8 % of a 6 s clock, and a hard-limit cut is identifiable after the fact by a
wall-to-last-iteration ratio near 2.4. Includes my own withdrawn class-median claim, kept visible rather than
quietly deleted.

## 7. `HARNESS_INVALIDATION.md` — the one about method
Records that a whole job run was WITHDRAWN because the harness piped stdin and every bestmove came from the
19-F12 fabrication path, naming exactly what was invalidated and what was re-run. Worth reading before writing any
UCI harness for this engine.

## what is deliberately NOT a deliverable
The individual fault counts from job 1 / job 2 / job 3 on the base tree. They are valid and committed, but they
describe the base tree and the owner plays the PC build; the durable content is the method and the rules above.
