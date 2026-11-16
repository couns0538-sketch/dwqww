# Audit of all nine 08-F findings against "does it assume plan = M-10 was actually spent?"

Prompted by seat 16's REFUTES of the movetime rule. For each finding: does it depend on the PLAN being spent,
and if so is that dependence visible to the reader?

| finding | assumes plan = spent? | verdict |
|---|---|---|
| 08-F1 (clock tail: p99 4x median) | NO. It is a statement about measured wall time spread, and it compares wall against the plan only to say "past soft". Since a clock stop overshoots (not undershoots) soft, "past soft" is conservative. | stands unchanged |
| 08-F2 (movetime spends T-10) | YES, and it is TRUE on the wall clock: +1.4..2.3 ms over plan in 12/12 rows. It was INCOMPLETE: it did not say the kept iteration is early. | restated with planned + achieved + last depth |
| 08-F3 (a book move in the timing set) | NO. The book answer is 0.02-0.36 ms regardless of any plan. | stands unchanged |
| 08-F4 (baseline repeatability) | NO. Two runs of the same thing. | stands unchanged |
| 08-F5 (reserve-empty -> 1-ply emergency) | NO. It is about a branch that runs when the plan is EMPTY. Also re-confirmed: 40/40 clocked rows are consistent, and probe_no_clock.py shows depth 1. | stands unchanged |
| 08-F6 (1 ms hard limit overrun) | NO. It counts wall against a 1 ms hard limit, and the measured overrun is the process floor. | stands unchanged |
| 08-F7 (no search exceeded the clock) | NO — it is the absence of an overrun, so any undershoot makes it safer. | stands unchanged |
| 08-F8 (movestogo 1/2 land on the 792 ms hard limit) | PARTLY: it says "p99 792.80 / max 792.88 = ON the hard limit". That is wall time hitting the hard limit, which the movetime-style hard check does honour. It does NOT claim the soft plan was spent. | stands, with the note that achieved time may be lower on the rows that did not hit the hard limit |
| 08-F9 (engine spends 55-79 % of soft) | YES, and this is exactly the assumption seat 16 attacked. Under an iteration-boundary stop the "achieved" time IS the whole story and the plan is never reached. | restated as planned vs achieved |

## The one sentence that was wrong in spirit
08-F9's original phrasing "the engine spends only 55-79 % of its own planned soft limit" reads like the engine
chooses to use less. It actually CANNOT do better when one iteration is a large slice of the budget: it stops at
the last boundary and overshoots by up to a whole iteration on other positions. The restatement gives both
numbers so the reader sees the granularity.

## Does any of this affect the honesty numbers or the raw data?
No. The timing harness reads `bestmove` from stdout with `time.monotonic()` and never parses the engine's `time`
field for a latency number. The `time` field appears only in job4, explicitly labelled as the engine's own field.
