# kimi5 job 34 — Step 1 reading (on my chain = 6b98f217 + pc_r15 + history_age + count27 + age_split + split_counter, i.e. job 33's counting copy; line numbers are that tree's)

1. **Where the node's alpha, depth and lmr_depth stand at the test.**
   `Worker::search(Board&, SearchStack* ss, int depth, int alpha, int beta, bool cut_node)` — src/search.cpp:1855:
   `depth` and `alpha` are the node's own parameters; `alpha` stands in the function's local and is raised only at
   :2430 (`alpha = score;`), so at the test it is the node's current alpha after the earlier moves of the same loop.
   `lmr_depth` is computed at src/search.cpp:2223 (`const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));`).
   The test itself is the `if (lmr_depth <= tune::HistoryPruneDepth)` block at src/search.cpp:2244-2253, with the
   counting/logging call at :2246 and the prune (`history < history_prune_threshold`, `continue`) at :2247-2252.
   The threshold is built at :2229-2231 (−2220·depth·3/4 with TtPruneV2 and not improving, else −2220·depth).

2. **The function that writes a FEN.** `std::string Board::fen() const` — src/board.cpp:371. The F and P lines use it
   (the P line at the node's loop end prints the same node's `board.fen()`, matched to the record by the node key).

3. **Where the value of a SEARCHED quiet move is compared with alpha after its last re-search.**
   The move's last re-search is the full-window PV re-search at src/search.cpp:2405-2407
   (`score = -search_child(board, ss + 1, new_depth, -beta, -alpha, false);`); after `board.unmake_move` (:2408)
   the final value is first compared with alpha at :2417 (`if (score > alpha)`), and alpha is raised at :2430.
   The job-34 hook (`hp34_value_hook`, log-only) sits between :2408 and the abort check, so it reads the same final
   `score` that :2417 compares. A move that passed the history test but is skipped later (SEE quiet prune :2254,
   the extinguish tight-futility continue :2292, or a cutoff before it) never reaches the hook and flushes as r=-1.

4. **Known answer C on my chain (move at the test is already LEGAL).** r15d's form (`search.cpp:2228`,
   `if (!picker.last_move_known_legal() && !board.is_legal(move)) continue;`) DIFFERS on my chain: there is no
   `last_move_known_legal()` helper here (it came with the r15d-only patches). My chain's main loop
   (`MovePicker::Mode::Main` at :2142, loop head :2172) has the plain guard
   `if (!board.is_legal(move)) continue;` at **src/search.cpp:2178**, before the pruning block (:2222) and the test
   (:2244). Same guarantee, different line and no fast path: every move passes `board.is_legal`.
   So the oracle must meet 0 `illegal move` lines.

5. **Known answer D on my chain (printed score = internal value).** `format_score` at src/search.cpp:361-370:
   `"cp " + the score` (:369) and `mate n` with `n = (MateValue - |score| + 1) / 2` (:364-366). Same code as r15d's
   354-360, shifted by my chain's earlier lines. A logged `a=` (internal alpha) and a printed `cp` are the same unit.
