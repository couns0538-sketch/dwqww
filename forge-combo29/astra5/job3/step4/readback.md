# Depth 16 on position P

The instrumented PC executable reproduced every compared depth, best move, score and node count with the trace off. Its 20 PC20 and 16 + 16 single-switch rows passed before three fresh, trace-enabled depth-16 searches. All three traced rows also passed. See `rows/trace-parity.txt`.

| PC build, PC20 plus option | Root index of g3g6 on first search of it at iteration 16 | LMR depth | Black’s window | Black null probe depth | Black null result | Actual root result |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| Defaults | 22 | 11 | [−737, −736] | 0 | −291 | f6h5, +736 cp, 182707 nodes |
| SingularDepth 20 | 4 | 14 | [−639, −638] | 2 | −31997 | g3g6, mate 2, 71678 nodes |
| QsSeeMargin 500 | 4 | 14 | [−642, −641] | 2 | −31997 | g3g6, mate 2, 205800 nodes |

**PC20.** Three earlier aspiration passes cut off on f6h5. In the final pass, move 22 entered the reduced search with a depth-11 budget. Black's null probe reached depth zero. White's quiescence search, in the window [736,737], immediately returned a depth-zero upper transposition-table bound of +291 before static evaluation or the move picker. Its score of −291 cleared Black’s beta of −736, so the unverified null return prevented either real reply from entering the move loop. At the root, +291 fell below the incumbent +736 and failed the condition for a full-depth re-search. The earlier visit at iteration 11 reached the same position with no TT hit. Quiescence outside check exhausted its captures-only picker at +291 after a corrected static evaluation of +147. Its alpha was +354, so the code stored an upper bound. Quiet Qh7# was outside the picker. See `rows/trace-pc20.events.txt`, lines 253–256 and 465–492.

**Both switches.** Move 4 received three more plies at the first reduced call. After the null, White's depth-two main search saw a depth-zero upper bound (+138 under SingularDepth 20, +291 under QsSeeMargin 500). The depth check prevented an immediate TT cutoff. Each search tried g6h7 as its third move and confirmed checkmate. Consequently both null probes returned −31997 for Black, below beta. Both continued directly to real moves. The two mate leaves were g3g6 c6e5 g6h7 and g3g6 f7g6 e5g6 in each arm. See `rows/trace-singular.events.txt`, lines 377–395, 407–409 and 440–442, and `rows/trace-qs_see.events.txt`, lines 359–377, 389–391 and 422–424. Each final PV was g3g6 c6e5 g6h7. The selected path trace identifies the immediate lost search at iteration 16. It leaves open which earlier off-path decisions moved g3g6 up the root order. The trace shows no quiescence SEE skip of a tracked move. The separate ProbCut SEE filter did skip e5g6 at some visits, after which the ordinary move loop searched it.

**Uninstrumented PC source.** `src/search.cpp:1762` dispatches depth zero to qsearch. Lines 1653–1657 permit a qsearch upper-bound return at or below alpha. Lines 751–760 generate only captures in the non-check quiescence picker and lines 1745–1751 store the resulting bound. Main-search cutoff at line 1847 requires the TT depth to cover the requested depth. Lines 1943–1966 set the null reduction and test its result, and lines 1972–1976 return without verification below depth 14 unless the threat guard intervenes. Lines 2252–2279 reduce a later move and require a score above alpha for a full-depth retry. In check, the engine represents its own static evaluation as unavailable. The trace labels that field `search_static=NA` and separately logs an independently recomputed raw static score on entry, including when a TT return precedes evaluation.

From a job 3 checkout with the patched executable at TRACE_EXE, the original position ladders under step1 and step3, and the working directory set to step4:

```sh
python3 trace_check.py ../ladder.py "$TRACE_EXE" ../step1/PC20.tsv ../step3/singular.tsv 16 new-rows --also ../step3/qs_see.tsv
python3 inspect_trace.py new-rows/trace-pc20.events.txt 16
```

The ladder's parent directory locates the job 1 harness. Set ASTRA5_JOB1 to its directory if running apart from the normal checkout. Each trace ID has one entry and one return. The three iteration summaries validate all ID pairs before presenting the final root iteration.
