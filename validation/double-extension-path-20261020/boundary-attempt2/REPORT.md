# Double-extension inherited-count boundary fixtures

**Actual synthetic-state RED/GREEN reproduced; no normal-root overflow or strength gain is claimed.** Frozen baseline is `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`; the proposal uses the reviewed search-only path-accounting repair, with identical diagnostic instrumentation. Both variants seed only the root-parent sentinel and independent shadow initial count. Unset environment retains ordinary count zero. Tuning values remain unchanged.

All six native engine cases exited zero; total subprocess wall time was 11.790139 seconds against the unchanged 60-second aggregate diagnostic guard. These durations are operational limits, not performance measurements.

| Variant / inherited seed | Bench nodes | Double extensions | Maximum true / stored count | Over-limit child states | Eligibility mismatches |
| --- | ---: | ---: | --- | ---: | ---: |
| Baseline / 0 | 419798 | 184 | 6 / 6 | 0 | 0 |
| Proposal / 0 | 419798 | 184 | 6 / 6 | 0 | 0 |
| Baseline / 6 | 421350 | 117 | 8 / 7 | 281 | 4 |
| Proposal / 6 | 421339 | 115 | 7 / 7 | 0 | 0 |
| Baseline / 7 | 335836 | 0 | 7 / 7 | 0 | 0 |
| Proposal / 7 | 335836 | 0 | 7 / 7 | 0 | 0 |

The independent shadow derives path counts from actual selected extensions and recursive edges rather than copying production counters. In the count-six baseline fixture, a stale stored count six permits another double extension when the independent current path is already seven. One captured example is legal `f6e4` at ply seven in `r3k2r/p1pp1pb1/Bn3np1/3p4/4Q1N1/2B4p/PPP2PPP/R3K2R b KQkq - 0 4`. The resulting true count is eight while the stored count remains seven. The 281 total includes downstream child states after a breach; it does not mean 281 independently authorized double extensions.

The proposal has zero observed counters in every mismatch class for seeds zero, six and seven. Seed six permits a further double extension but no path exceeds seven; seed seven performs none. Seeded proposal cases still exercise 292375 / 233863 selected children and 909 / 776 singular attempts. Margin-qualified denial opportunities were not counted separately, so the seed-seven maximum initialized at seven alone is not proof that every branch of its eligibility guard was exercised.

Independent python-chess replay/arithmetic checks pass all **1503 bounded trace rows / 4509 assertions**. They check valid FENs, legal real candidate moves, the explicit no-move sentinel on entry/null metadata, and each recorded mismatch or over-limit condition. This is not a full game replay. The unchanged `assert-boundary-results.py` returns one for baseline and zero for proposal.

The completed baseline compile/core/link were hash-verified and reused without rebuilding. Only proposal search.cpp was compiled; six other core archive members are byte-identical to frozen baseline and the original UCI object was reused. Every exported file except the declared diagnostic search.cpp matches the frozen Git export; final source, engine, core and original baseline-input hashes agree.

Two harness failures are retained without changing their original bytes:

- Attempt1 stopped with `BrokenPipeError` in a progress print after successful baseline link, before any engine case. Attempt2 resumes at proposal compile and writes progress to a durable file.
- Attempt2 completed all six engine cases, then its original oracle wrongly demanded a baseline overflow at seed seven. The actual synthetic overflow occurs at seed six. Its `commands.json` remains `FAILED_OR_INCOMPLETE`. `audit-completed.py` independently qualifies the completed captures against the intended count-seven invariant, records the old assertion failure, and performs no engine replay. `FINAL-BOUNDARY-RESULTS.json` is the authoritative final qualification.

Reproduce the preserved offline budget assertion with:

```sh
python3 -B assert-boundary-results.py --commands commands.json --variant baseline
# Expected exit 1: actual captured budget/bookkeeping failures.
python3 -B assert-boundary-results.py --commands commands.json --variant proposal
# Expected exit 0.
```

`audit-completed.py` preserves exact inputs and output hashes. Its recorded helper commands already ran; use a fresh output directory before repeating a complete audit because original oracle output files are opened exclusively. No production files, Git refs, match settings, source tuning values or original outputs were modified by this task. The corresponding production candidate still requires its own frozen build and complete regression validation.
