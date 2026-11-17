# STATUS — swarm/matelabels

**State: measured, self-tested, cross-checked. Complete for the 300-label sample.**

## Headline

300 engine-emitted `mate N` labels, uniform random sample from the repo's own
search corpus, one fixed recorded configuration. **238 verified: 176 exact,
62 wrong, 0 under-stated, 0 wrong-move. 62 unverifiable.**

* **Wrong rate among verified: 62/238 = 26.1%**
* **Unverifiable rate: 62/300 = 20.7%**
* **All 62 errors are over-statements** (claimed mate further away than truth).
* **35 of 48 independently confirmed errors are off by exactly one move.**
* **PV-length filter would have caught 9 of 62 = 14.5%.**

## Done

| item | state | evidence |
|---|---|---|
| Four honesty pins | **4/4 match** | `evidence/gate.md` |
| Trap 1 (`quit` into live search) reproduced | yes, and it *fabricates a different move* | `evidence/engine-refusal-and-trap.txt` |
| Oracle written independent of forge | yes — own board, movegen, attack, search | `scripts/mate_oracle.cpp` |
| Oracle movegen validated | **25/25 perft** vs published **and** python-chess | `evidence/oracle-perft.json` |
| Known-answer suite | **7/7**, expectations *computed* by a 2nd solver | `evidence/oracle-selftest.json` |
| Planted-wrong oracle | **caught 6/6** | `evidence/oracle-selftest.json` |
| End-to-end verifier test | 20/21; **0 wrong called EXACT, 0 honest called WRONG** | `evidence/e2e-label-test.json` |
| 300 labels harvested | yes, 5,473 scanned, 0 engine refusals | `evidence/corpus-300-labels.json` |
| Labels reproduce | **300/300 bit-for-bit** on re-run | `scripts/add_seldepth.py` |
| `seldepth` recorded | **300/300**, min 12 / max 38 | `evidence/corpus-300-labels.json` |
| Two-halves verification | **300/300 attempted**, 238 decided | `evidence/verdicts-300.json` |
| Independent cross-check of every wrong label | **48 confirmed, 0 disputed**, 14 undecided | `evidence/crosscheck-wrong-labels.json` |

## Bugs found in my own work (all fixed, all recorded)

1. **A recalled fixture was wrong.** "Scholar's mate, mate in 1" is only `Qxf7+`.
   Fixed by computing expectations with a second solver instead of remembering them.
2. **A parity bug in my cross-check** made 10 correct "overstated" verdicts look
   like oracle errors — loss distances live on even plies and I stepped odd. This is
   the most instructive failure of the seat: it produced a *plausible* wrong number
   and was only visible through the disagreement count.
3. **An end-to-end fixture bug** (synthetic rows had no mating move, so half (A)
   could not pin) made the verifier look broken when the fixture was.

## Not done — see FINDINGS.md §7

* **One configuration only** (depth 12, MultiPV 1, Threads 1, Hash 32). §4 records
  the error as configuration-specific, so **this rate does not transfer**. A
  MultiPV-3 sample is the obvious next step and was not taken.
* `go mate N` not exercised (you note it is a different search).
* No engine root-cause work — `search.cpp:1434` already dated elsewhere.
* 14 of 62 wrong labels are cross-check-undecided (pysolve could not settle them at
  its 9-ply cap); they rest on the oracle alone and are flagged per row.

## Reproduce

```bash
# engine (from the audit base)
cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 .. && \
  LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j4
# oracle
g++ -O2 -std=c++20 -o oracle scripts/mate_oracle.cpp
g++ -O2 -std=c++20 -o oracle_broken scripts/mate_oracle_planted_wrong.cpp
# validate, then measure
python3 scripts/perft_check.py        # must print ALL PERFT MATCH
python3 scripts/oracle_selftest.py    # must print SUITE VALID
python3 scripts/harvest_labels.py
python3 scripts/add_seldepth.py
python3 scripts/run_verify_parallel.py
python3 scripts/e2e_label_test.py     # must print 0 falsely-EXACT
python3 scripts/analyze.py
```

## Time

Sampling, verification and cross-check complete. Deliverable pushed on
`swarm/matelabels`.
