# What CAN and CANNOT be audited on the loaded net (S-F172)

The coordinator's ask was to run seat 75's six-question sanity audit over the loaded net. **Part of it is answerable and
part of it is not, and the boundary is the finding.** Getting this wrong in either direction produces a fabricated result:
extending the audit would have meant testing a random-weight net for material sanity; refusing outright would have thrown
away `S-C61`'s valid result.

## The distinction

| property | what it depends on | testable on a random-weight net? |
|---|---|---|
| **symmetry** | bucket indexing, perspective flip — **code structure** | **yes** — `S-C61`: 0 of 353 |
| **sign convention** | side-to-move relative — code | **yes** |
| **terminal scores** | mate/stalemate detection — code | **yes** |
| **material sanity** | **what the weights mean** | **no** |
| **horizon behaviour** | the search, mostly code | partly |

**Random weights are uniform in [−64, 64] by construction** — `make_v3_testnet.py` draws them from splitmix64. A net whose
weights mean nothing cannot be asked whether its evaluation of `KB vs K` is *correct*; the question has no answer.

## The evidence for the boundary, not the argument

**`K vs K` should evaluate to 0** — a bare-kings position is a draw by insufficient material.

| net | `K vs K` | `KNN vs K` (should be 0) | `KBN vs K` (should be > 0) |
|---|---|---|---|
| built-in, trained | **25** | 198 | 215 |
| v3, **random weights** | **171** | 416 | 649 |

**The random net is worse in every cell, which is exactly what random weights should produce.** That is the proof the
distinction is real rather than a convenient excuse: if material sanity were a structural property, a random net would
score it as correctly as a trained one. It does not.

**And note the built-in net is not perfect either** — `K vs K` gives 25 rather than 0, and `KNN vs K` gives 198 rather
than 0. That is seat 75's `75-F7` question 3 finding (`KB vs K` −147, `KNN vs K` +187), seen from a different position
set. **Their finding is about the built-in net and stands.**

### The six questions, itemised

| # | seat 75's question | depends on | answerable on a random net? |
|---|---|---|---|
| 1 | material monotonicity | what the weights mean | **no** |
| 2 | symmetry | code structure | **yes — done, 0 of 353** |
| 3 | dead material | what the weights mean | **no** |
| 4 | sign convention | code | **yes** |
| 5 | horizon | mostly the search | **partly** |
| 6 | terminal scores | code | **yes** |

**Three fully, one partly, two not.** Written as a table rather than a sentence because I got the sentence wrong first.

## What this means for the audit

**The structural half has been done on the loaded net**: symmetry, 0 of 353 (`S-C61`). **The semantic half cannot be done
with the net I have**, and the reason is not a missing tool — it is that the test net was published *for determinism*, not
for evaluation quality. Its purpose is to make every machine compute the same numbers, and it does that perfectly.

**To audit material sanity on the loaded net you need the owner's trained net.** That is a file nobody on this swarm has,
which is why file 7 published a deterministic stand-in instead. **So the honest request is to the owner: run the six
questions in `75-F7` against the PC's net**, and the harness to do it already exists on seat 75's branch.

## What I am not claiming

* Not that the v3 path is materially unsound. **The random-weight numbers say nothing either way**, and reading them as a
  defect would be the mirror of my earlier mistake of reading numbers from different runs against each other.
* Not that seat 75's six questions are unanswerable. **Three of the six are fully answerable on a random net**
  (symmetry, sign convention, terminal scores), **one partly** (horizon, which is mostly the search rather than
  the net), and **two not** (material monotonicity, dead material — both semantic). **I first wrote "four of
  six" here without counting**, which is the same error as the S-F171 branch claim and the 37-vs-38 sweep: a
  number asserted from memory, in a section about checking numbers. The itemised count is below.
* Not that the test net is deficient. **It is doing exactly the job it was published for**: identical bytes everywhere,
  so a timing or identity comparison means the same thing on every machine. It was never a net whose evaluations were
  meant to be judged.
