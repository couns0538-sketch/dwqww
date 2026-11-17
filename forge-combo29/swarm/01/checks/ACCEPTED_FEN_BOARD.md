# My accepted-invalid FENs parse to the intended board — unlike S-C84 (S-C59)

After confirming seat 27's `S-C84` (an illegal FEN searches the *previous* position), the obvious follow-up in my own area
is: **do the 38 accepted-but-invalid FENs I recorded in `S-F1` also search the wrong board?** That would make them the
same class of hazard. **They do not, and the reason matters.**

## The test

`S-F1`'s rule is digit-summing: a rank holding two adjacent digits is accepted if the digits *sum* to 8. If the sum is
correct, the parsed board is the intended one. If a malformed rank could sum to 8 while placing pieces differently, the
FEN would silently describe another position.

Method: perft 2 as the board fingerprint, comparing every accepted variant against the canonical form. Discriminating
position chosen so that a shifted king changes the count (`7k/8/8/8/8/8/8/4K3`, king on e1, perft 2 = **15**).

| rank string | files (sum) | perft 2 | verdict | board |
|---|---|---|---|---|
| `4K3` (canonical) | 8 | **15** | accepted | reference |
| `4K111` | 8 | 15 | **accepted** | **same** |
| `4K21` | 8 | 15 | **accepted** | **same** |
| `4K12` | 8 | 15 | **accepted** | **same** |
| `21K4` | 8 | 15 | **accepted** | **same** |
| `12K4` | 8 | 15 | **accepted** | **same** |
| `11K4` | **7** | 400 | **diagnosed** (`invalid FEN`) | — |
| `4K1111` | **9** | 400 | **diagnosed** (`too many squares in FEN rank`) | — |

**Every accepted variant sums to exactly 8 and produces perft 2 = 15 — the same board. Every rejected one sums to 7 or
9.** So digit-summing is not a lax check that lets a wrong board through; it is a *different but correct* way of reading
the same rank.

## Why this matters to the comparison with S-C84

| | `S-C84` (illegal FEN) | `S-F1` (adjacent digits) |
|---|---|---|
| diagnosed? | **yes**, one `info string` | **no** |
| board searched | **the PREVIOUS position** | **the intended position** |
| consequence | a fabricated row that looks like a measurement | the correct answer, from a FEN a strict parser would refuse |
| severity | **high** — the answer describes a different position | **low** — the answer describes the position you meant |

**So the two are opposite in consequence, and the similarity is only that both accept input a strict parser refuses.**
`S-C84` is dangerous because the board is wrong; `S-F1` is benign because the board is right. Reporting them as one class
would have inflated my own finding to the severity of theirs.

**And the benign case is the one with no diagnostic**, which is the interesting inversion: the engine says nothing for
the accepted-but-correct parse and *does* say something for the illegal one — and then searches the wrong board anyway.
**The diagnostic is not a guide to whether the answer is about your position.**

## The sweep, done rather than named as a limit

The limit above said the general claim needed a sweep. Here it is: take every accepted FEN from `job1/results.jsonl`
that has **adjacent digits inside a rank**, canonicalise each rank by collapsing digit runs into their sum, and compare
perft 2 of the original against perft 2 of the canonicalised form.

```
cases with adjacent digits inside a rank: 38
same: 38  differs: 0
```

**Every one parses to the board its digits describe.** So the result is not a single-position accident: digit-summing is
a consistent, correct reading of this malformed shape, across all 38 recorded cases.

**And the sweep caught my own counting error, which is the part worth recording.** My first extraction found **37** and I
was about to write "37 of 37, not the 38 I had been quoting". The bug was in my selector:

```python
for rank in fen.split("/")[:-1]:     # WRONG: drops the LAST rank
```

`fen.split("/")` includes the side-to-move field as its final element, so `[:-1]` looks right — **but I applied it to the
full FEN, which drops rank 1, not the side field.** One case had its adjacent digits in rank 1 and was silently excluded.
Correcting the selector to split the board field first gives **38**, matching the recorded figure exactly.

**The lesson is `Trap 0` in its purest form and it happened in the act of checking a number**: my first instinct was to
report the discrepancy as a finding about the record ("37, not 38"), and the discrepancy was mine. **Before reporting
that two counts disagree, suspect the new counter** — the recorded number had survived a 20,000-FEN sweep, and mine had
survived ninety seconds.

## What I am not claiming

* Not that `S-F1` is harmless in every respect. A strict consumer comparing FEN strings would still see a mismatch, and
  a harness that stores the FEN it sent beside a result is storing a string the engine did not literally parse. That is a
  bookkeeping hazard, not a search hazard.
* ~~Not that all 38 of the recorded cases parse correctly~~ — **SWEPT, and all of them do.** See below.
* Not that digit-summing is a defect. It reads a legal intent unambiguously; the question was only whether it could read
  it *wrongly*, and in this test it cannot.
