# Auditing the three things the report leans on hardest (S-F167)

`S-F166` audited the gate's fourteen checks and found twelve with a real catch, two without. The same question applies
to three things relied on **more heavily than they have been individually audited**: the decomposition, the guard
self-test, and the bench rules. Using the same rule — *proof of function, not proof of need* — here they are.

## 1. The decomposition — already stated in the FINAL

| instrument | real catches |
|---|---|
| `check_identities.py` | **0** |
| `check_table_identities.py` | **0** |
| `check_ratio_percent.py` | **1** (the fabricated `0.9090`) |

**One instrument has fired; two are proofs of function.** Stated beside the result.

## 2. The gate self-test — the same verdict, and it surprises me

The self-test asserts that each checker fails on known-bad input. Its **ten assertions are all against planted inputs by
design** — that is its purpose. But the audit question is different: **has it ever caught a real regression?**

Searching the record for occasions when the self-test *fired* gives three:

| occasion | what it caught | real or planted? |
|---|---|---|
| `a bad pipe in a row was ACCEPTED` | a checker regressed to always exit 0 | **planted** (I regressed it deliberately) |
| `check_pooled_spread PASSED on an empty directory` | the zero-count guard was defeated | **planted** (I disabled it deliberately) |
| `a future stamp was ACCEPTED` | the stamp check regressed | **planted** (I removed its guard deliberately) |

**All three were my own deliberate regressions.** So the guard self-test has **never caught a real defect** — it has
demonstrably worked three times, and never been *necessary*.

**This is not a criticism of it, and the distinction is the same one**: a self-test's job is to fire when a checker
regresses, and regression is rare by construction. Three demonstrated fires against planted faults is exactly what it
should have. But by the rule I applied to the identity checkers, **its protection is a proof of function** — and I would
not have said that before checking, because it *feels* like the most battle-tested thing in the gate.

## 3. The bench rules — enforced by nothing

This is the finding. The rule is stated in the FINAL:

> *Bench is valid for: pins, determinism, ablation direction, structural counters, and the pooled effect of one isolated
> toggle. Bench is NOT valid for: per-node cost, or the aggregate PC20 set. And always report the per-position spread.*

**No check reads a bench-based claim.** The gate's only bench-adjacent step is the opt-in `--with-honesty` pin run, which
verifies that four known numbers reproduce — that is a **determinism** check on the build, not an enforcement of the rule
about what bench may be used for. So:

| the rule | enforced by |
|---|---|
| bench is valid for pins / determinism / direction / counters / one toggle | **nothing** |
| bench is NOT valid for per-node cost or the aggregate PC20 set | **nothing** |
| always report the per-position spread | `check_pooled_spread.py`, but only for a pooled ratio in a `.txt`/`.md` file — **not** for a bench claim specifically |

**Three statements, one partially covered, two unenforced.** The bench rule is the most-relied-on and least-checked
thing in my record, and I had not noticed because it is written in the FINAL beside rules that *are* enforced.

## What this audit is worth

The three outcomes are three different states, and stating them separately is the value:

| thing | state |
|---|---|
| decomposition | **proof of function** with one real catch elsewhere — stated honestly in the FINAL |
| guard self-test | **proof of function** — three planted fires, never a real one |
| bench rules | **prose only** — one clause partly covered, two clauses with no check at all |

**The generalisable part: reliance and verification are independent.** A rule can be relied on heavily because it is
correct — the bench rule is correct, and I measured it myself (`S-C51`: the sign flip reproduces to a tenth of a point)
— and still be enforced by nothing. **Correctness of a rule and coverage of a check are separate questions**, and the
bench rule is the clearest case in this record of a correct rule with zero coverage.

Whether to build the bench enforcement is a real question I have not answered: it would need to read a bench claim plus
its workload plus the toggle set, which is close to the intent-parsing that failed three times tonight. **Recording the
gap is the honest move; inventing a check I cannot make precise is not.**
