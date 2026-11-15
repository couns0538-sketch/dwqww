# Warm-position coverage of the current PC-parity tree

This review covers the frozen equality corpus and the currently recorded extended UCI self-play batches at source `d9a8587df8ad4d0ff1231632cb1ac72b590c04bf`. It ran no engine and changed no source, checks, Git, or root state. `EVIDENCE.txt` pins all26 source files, the examined harnesses, and four actual raw transcripts. Counts are a snapshot while question0017 is pending.

**What is exercised.** The equality driver creates a fresh engine process for each comparison search and destroys it afterward (`/workspace/work/parity-equality-preparation-v3/search_compare.cpp:143–153,176–183`). Its search helper sends `ucinewgame` and then `position fen` (`uci_process.hpp:423–434`). Thus both100,000-position stages test cold roots. Their search trees still use lazy descendant accumulators, re-searches and reused stack frames within each search; “cold roots” does not mean every descendant evaluation is rebuilt. Equality of root move/score/nodes is useful end-to-end evidence, but does not compare every intermediate network value.

The UCI self-play harness instead keeps one engine process for the batch (`/workspace/work/parity-softnodes-depth64-v2-preparation/softnodes_play.cpp:163`), resets only before each game (176–178), and sends the entire advancing `position startpos moves ...` history before each search (192–203). No `ucinewgame` or Clear Hash is sent between game moves. Actual recorded commands show:

| Batch index/settings | Searches | Searches preceded by another search since the last ucinewgame | Existing batch status |
|---|---:|---:|---|
|0,ASan+UBSan,T1,options off|7636|7584|passed|
|6,ASan+UBSan,T1,HindsightDepth+MateAlphaGuard on|7878|7822|passed|
|2,ASan+UBSan,T2,off|191|189|item4 failure; zero accepted-clean coverage|
|8,ASan+UBSan,T2,on|117|115|item4 failure; zero accepted-clean coverage|

This is actual no-newgame, warm-TT/history coverage on successive game positions. The T2 observations remain separate from accepted coverage. Every search has a position-history command; there were no Clear Hash commands in those four transcripts.

**What “warm accumulator” must not imply.** In the engine, `position startpos moves` reconstructs the board from startpos and replays the moves (`forge-combo29/src/uci.cpp:24–67`); it does not advance a persistent search accumulator. Every ordinary Worker search invalidates every stack accumulator and refreshes the root (`src/search.cpp:2302–2313`), even without ucinewgame. Lazy updates then occur inside the new search (`static_evaluate`,1062–1114; `record_move`,1117–1131; `record_null_move`,1158–1164). Consequently these runs exercise repeated reuse/reset of worker storage and warm search state, not preservation of a live NNUE accumulator across root searches. Neither examined harness is a repeated same-FEN warm-root parity comparison against the reference.

**Remaining value-consistency limitation.** The self-play checks inspect UCI labels, score range, legal moves and sanitizer diagnostics (`softnodes_play.cpp:203–218`). They never compare the lazy/fused network result or accumulator arrays with `nnue::refresh` plus an independent evaluation at the same node. The production evaluator's fallback refresh (search.cpp1082) is not such an oracle: it chooses a computation path, rather than comparing two paths. Sanitizers can expose invalid memory/undefined behavior, but a valid-memory wrong feature sum can remain silent. No per-move-kind or null-move NNUE equality coverage is instrumented in these harnesses. Existing imported branch reports or test sources should not be counted as a newly executed per-node consistency check in this job.

Safe final-report wording: “Cold-root search parity plus persistent-process, no-newgame self-play exercised the imported lazy NNUE path. Root accumulators refresh at every search. No independent per-node incremental-versus-full NNUE value check was run by these harnesses; the recorded T2 contract failures remain excluded from clean coverage.”
