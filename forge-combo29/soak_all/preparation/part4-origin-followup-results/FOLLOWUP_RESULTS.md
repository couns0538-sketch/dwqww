The later trace passes follow the recorded TT dependencies to an actual terminal checkmate at frame19871 and expose later quiet-futility events. Separate private guards show that the reported result changes when mate-valued TT scores cannot replace local static evaluation. These are observations for one pinned fixture, not a production fix, a fastest-mate certification, or a strength/speed result.

This snapshot contains eight later trace passes (`pass2/` through `pass9/`), two retained oracle query invocations, the completed static-evaluation counterfactual, the shared variant-preparation source as inert text, and the recorded post-native input verification. It excludes the already-published first pass and any subsequent r3-23 experiment.

| Recorded work | Engine search invocations | Oracle query invocations |
| --- | ---: | ---: |
| Eight later trace passes, each one baseline plus two traced repeats | 24 | 0 |
| Counterfactual: one baseline plus two runs each of off, QS-only, main-only, both | 9 | 0 |
| Oracle queries | 0 | 2 |
| This bundle | **33** | **2** |
| Earlier first pass, already published separately | 3 | 0 |
| Cumulative engine searches through this snapshot | **36** | — |

Across all nine observation passes, including the separately published first pass, there are **27 observer engine searches**; adding the9 counterfactual searches gives36 cumulative engine searches. This bundle contributes24 observer searches plus9 counterfactual searches, or33 new searches. Oracle query rows are counted separately: **11 + 53 = 64**, including repeated positions. Compilation, static comparison, preparation, and packaging are not engine-search or oracle-query invocations. Packaging executed none of the included native programs or helper scripts. [RUN_COUNTS.json.txt](RUN_COUNTS.json.txt), [TRACE_RUN_INVENTORY.json.txt](TRACE_RUN_INVENTORY.json.txt), the counterfactual run observations, and the exact command logs retain the counted records.

All 24 later trace executions completed with exit0/no timeout and retained the same depth13 output: **mate17, 25568 nodes, bestmove b3f3**, with the full reported PV

```text
b3f3 c2d2 f1f2 d2d1 f2e3 d1c2 e3e2 c2c1 f3c3 c1b2 e2d3 b2b1 d3d2 b1b2 c3f3
```

Every saved trace-pass comparison exited0 with all12 checks true, including complete stdout equality after removing only numeric time/NPS, repeated full trace equality after table-address relabeling, and presence of the selected writer subtree. Event counts for passes2–9 are respectively **704, 864, 896, 1170, 2216, 2396, 3931, 3969**; each retained trace-r1 sequence is contiguous. These fixture identity checks do not establish general instrumentation transparency under different timing or multiple search threads.

The expanded history continues the already-published frame23225 producer. Its limiting branch is `b2b1 d2d1 b1b2 f3d3 b2a1`, ending at white frame23233, ply14. That frame reads raw31987/Lower and returns31973 through MAIN_TT. The prior admitted writer is frame22377 at ply8/depth6; its four-frame continuation ends at frame22380 reading raw−31990/Upper, whose preceding writer is frame22252 at ply7/depth7. The later passes then expose the shorter mate-valued inputs used by that producer. The raw ledgers retain full keys, table/epoch/cluster/slot, histories, windows, and store-admission records; equal scores alone were not used to assign writers.

The selected subtree rooted at frame19727 contains145 frames and no mate-valued TT probes. Its terminal path is:

```text
19727 → 19728 → 19867 → 19868 → 19869 → 19870 → 19871
b1a1 d1c2 a1a2 d2d3 a2a1 d3a3#
```

Frame19871 is black qsearch at ply15, FEN `8/8/8/8/8/R7/2K5/k7 b - - 15 8`. Pass8 seq1999 records `SOURCE_LINE_1161`, the pinned qsearch checkmate return, value−31985. This is an observed terminal mate return rather than a mate-valued TT leaf. In the preserved positions, the black replies along this selected line are forced: `b1a1`, then `a1a2`, then `a2a1`; the final position has no legal reply and is in rook check. This supports a local at-most-six-ply strategy from frame19727. It does not prove the fastest mate there or a complete strategy from the original root. The rest of the145-frame subtree remains selective and contains ordinary-score TT returns, pruning, draw, and stand-pat returns.

The terminal value propagates into raw−31996/Upper at frame19867, raw31995/Lower at frame19728, and raw−31994/Upper at frame19727. The later110-frame producer rooted at22252 has seven pre-subtree mate probes spanning these **three** keys, including the positive Lower dependency consumed at22353. Treating only the two negative Upper keys as the complete external dependency set would omit that positive input.

Pass9 adds direct records of later move-pruning decisions without changing the saved output. [pass9/late-pruning-events.json.txt](pass9/late-pruning-events.json.txt) contains38 records:30 `LEGAL_PICKED`, **7 `FUTILITY_SKIP_TAIL`**, and1 `LMP_SET_SKIP_QUIETS`. For example, frame24347/seq3632 logs quiet move `d2c2`, depth2, alpha31982/beta31983, best31979, ordinary `static_eval=473`, and `skip_quiets=1` at pinned `search.cpp:1400`. Frame24358/seq3785 logs `d1c1`, depth5, alpha31979/beta31983, static_eval521, at the same futility site. These records establish that the existing futility path suppresses the quiet tail in the inspected later sequence; they do not identify a universally sufficient repair.

The oracle's first invocation covers11 second-pass mate-probe rows; all report `legal=1` and `bound_relation=1`. The second covers26 producer rows (all relation1) and27 later rows (**12 relation1,15 relation0**). Thus all64 rows report legal1, while49 report relation1 and15 relation0. These are printed row fields, not merely successful process exits; the harness does not fail its process on a false relation. It uses a KRK DTM table that explicitly ignores repetition history and the fifty-move rule. The later failures include Upper/Exact classifications that cannot be reported as matching global DTM bounds. They do not by themselves establish that the original positive mating deadline is too short or that every selective TT bound is sound. Exact query inputs, source, command logs, and outputs are retained under [oracle/](oracle/).

The private counterfactual adds two independent, default-off guards only at the qsearch/main sites where a mate-valued TT score could replace local static evaluation. It is distinct from disabling TT cutoffs and from the separate SoundMatePruning experiment.

| Private guards | Final reported score | Nodes | Seldepth | Bestmove |
| --- | --- | ---: | ---: | --- |
| Both off | mate17 | 25568 | 22 | b3f3 |
| QS only | cp547 | 29527 | 20 | b3f3 |
| Main only | mate18 | 24899 | 20 | b3f3 |
| Both on | cp546 | 29689 | 20 | b3f3 |

All nine counterfactual engine runs completed with exit0/no timeout/empty stderr. All four saved comparison commands exited0 with their checks true. Both-off normalized output matches the pinned baseline; its separately built binary is not byte-identical to baseline. Each setting repeats identically after numeric time/NPS removal. All full PVs and all comparison fields are retained in [static-eval-counterfactual/](static-eval-counterfactual/), including `observed-runs-and-comparisons.json.txt`. The score changes establish sensitivity to these guards for this fixture. A centipawn result, a changed mate number, or a longer/shorter PV is not treated as a correctness pass, and no guard was promoted to production.

The recorded post-native verification at **2026-11-14 17:37:08.226 UTC** reports all14 monitored source/header/baseline/object/build-recipe inputs unchanged. See [analysis/readonly-inputs-after-all-native.json.txt](analysis/readonly-inputs-after-all-native.json.txt). This checks the listed inputs, not every repository file. All compiled binaries/objects are excluded from publication and retained by SHA256 in the copy/exclusion inventories. Scripts are inert `.mjs.txt` copies and dependency files end in `.d.txt`; raw originals and active workspaces were not changed by packaging. Four stable independent review reports are retained under [independent-review/](independent-review/); their historical scope limits remain intact. Unfinished pass9/guard review reports were excluded.
