# Stockfish master history at a new search

Official Stockfish master was fetched with depth 1, a single branch and no tags. Commit `5d03b6e578a5eedc822e4563bdbb89e762fc2a59`. The UTC clock after the fetch and ref checks read `2026-11-18T03:52:46Z`.

Each active worker entering iterative deepening inside a game fills its low-ply table with 102 and multiplies each entry of its main (butterfly) table by 729/1024 before the first iteration. The C++ expression multiplies first and divides as integers, with truncation toward zero (`src/search.cpp:338–345`). If the main worker has no root moves, it returns before starting helpers or entering iterative deepening (`src/search.cpp:218–228`).

| History storage | Start of a new search inside a game | Initialization in `Worker::clear()` |
| --- | --- | --- |
| `mainHistory`, per worker | Scale every entry for both colors, `src/search.cpp:340–342` | Fill −5, `src/search.cpp:714` |
| `lowPlyHistory`, per worker | Fill 102, `src/search.cpp:338` | Fill occurs at iterative entry, `src/search.cpp:338,713–735` |
| `captureHistory`, per worker | Retain, `src/search.cpp:202–228,281–345` | Fill −742, `src/search.cpp:715` |
| `ttMoveHistory`, per-worker scalar | Retain, `src/search.cpp:202–228,281–345` | Set 0, `src/search.cpp:729` |
| `continuationHistory`, shared per NUMA node | Retain entries. New stack frames point to the existing sentinel, `src/search.cpp:300–312,338–345` | Fill −586 in all four sub-tables by the first worker on the NUMA node, `src/search.cpp:717–727` |
| `sharedHistory.pawnHistory`, shared per NUMA node | Retain, `src/search.cpp:202–228,281–345` | Fill each worker's share with −1338, `src/search.cpp:720` |
| `sharedHistory.correctionHistory`, shared per NUMA node, with pawn/minor/white-non-pawn/black-non-pawn fields | Retain, `src/search.cpp:202–228,281–345` | Fill each worker's share with −5, `src/search.cpp:719`; all four fields follow the assignment in `src/history.h:157–168` |
| `continuationCorrectionHistory`, per worker | Retain entries. New stack frames point to the existing sentinel, `src/search.cpp:300–312,338–345` | Fill 5, `src/search.cpp:731–733` |

Worker members are declared in `src/search.h:330–339`. The NUMA grouping and shared storage are in `src/history.h:197–215,249–251`. `position` rebuilds the board and move-state list (`src/uci.cpp:494–517`, `src/engine.cpp:195–214`). `go` starts thinking (`src/engine.cpp:153–158`). The root setup initializes per-search state (`src/thread.cpp:332–349`). `ucinewgame` takes the separate clear path through `Engine::search_clear()`, `ThreadPool::clear()` and `Thread::clear_worker()`.

## Verbatim source

`src/search.cpp:300–312,338–345`
```text
   300	    Stack  stack[MAX_PLY + 10] = {};
   301	    Stack* ss                  = stack + 7;
   302
   303	    for (int i = 7; i > 0; --i)
   304	    {
   305	        (ss - i)->continuationHistory =
   306	          &continuationHistory[0][0][NO_PIECE][0];  // Use as a sentinel
   307	        (ss - i)->continuationCorrectionHistory = &continuationCorrectionHistory[NO_PIECE][0];
   308	        (ss - i)->staticEval                    = VALUE_NONE;
   309	    }
   310
   311	    for (int i = 0; i <= MAX_PLY + 2; ++i)
   312	        (ss + i)->ply = i;
   338	    lowPlyHistory.fill(102);
   339
   340	    for (Color c : {WHITE, BLACK})
   341	        for (int i = 0; i < UINT_16_HISTORY_SIZE; i++)
   342	            mainHistory[c][i] = mainHistory[c][i] * 729 / 1024;
   343
   344	    // Iterative deepening loop until requested to stop or the target depth is reached
   345	    while (rootDepth + 1 < MAX_PLY && !threads.stop
```

`src/search.cpp:712–736`
```text
   712	// Reset histories, usually before a new game
   713	void Search::Worker::clear() {
   714	    mainHistory.fill(-5);
   715	    captureHistory.fill(-742);
   716
   717	    // Each thread clears its part of the dynamically-sized shared histories.
   718	    // The constant-size continuation history is initialized by thread 0 of each NUMA node.
   719	    sharedHistory.correctionHistory.clear_range(-5, numaThreadIdx, numaTotal);
   720	    sharedHistory.pawnHistory.clear_range(-1338, numaThreadIdx, numaTotal);
   721
   722	    if (numaThreadIdx == 0)
   723	        for (bool inCheck : {false, true})
   724	            for (StatsType c : {NoCaptures, Captures})
   725	                for (auto& to : continuationHistory[inCheck][c])
   726	                    for (auto& h : to)
   727	                        h.fill(-586);
   728
   729	    ttMoveHistory = 0;
   730
   731	    for (auto& to : continuationCorrectionHistory)
   732	        for (auto& h : to)
   733	            h.fill(5);
   734
   735	    refreshTable.clear(network[numaAccessToken]);
   736	}
```

`src/search.cpp:202–228`
```text
   202	void Search::Worker::start_searching() {
   203
   204	    accumulatorStack.reset();
   205
   206	    // Non-main threads go directly to iterative_deepening()
   207	    if (!is_mainthread())
   208	    {
   209	        iterative_deepening();
   210	        return;
   211	    }
   212
   213	    main_manager()->tm.init(limits, rootPos.side_to_move(), rootPos.game_ply(), options,
   214	                            main_manager()->originalTimeAdjust);
   215	    tt.new_search();
   216	    main_manager()->updates.onStart();
   217
   218	    if (rootMoves.empty())
   219	    {
   220	        main_manager()->updates.onUpdateNoMoves(
   221	          {0, {rootPos.checkers() ? -VALUE_MATE : VALUE_DRAW, rootPos}});
   222	        main_manager()->updates.onBestmove(UCIEngine::move(Move::none()), "");
   223	        return;
   224	    }
   225
   226	    // Main thread starts non-main threads, and begins own search
   227	    threads.start_searching();
   228	    bool uciPvSent = iterative_deepening();
```

`src/uci.cpp:137–142`, `src/engine.cpp:153–165`, `src/thread.cpp:99–103,257–265,332–349`
```text
   137	        else if (token == "position")
   138	            position(is);
   139	        else if (token == "ucinewgame")
   140	            engine.search_clear();
   141	        else if (token == "isready")
   142	            sync_cout << "readyok" << sync_endl;
   153	void Engine::go(Search::LimitsType& limits) {
   154	    assert(limits.perft == 0);
   155	    verify_network();
   156
   157	    threads.start_thinking(options, pos, states, limits);
   158	}
   159	void Engine::stop() { threads.stop = true; }
   160
   161	void Engine::search_clear() {
   162	    wait_for_search_finished();
   163
   164	    tt.clear(threads);
   165	    threads.clear();
    99	// Clears the histories for the thread worker (usually before a new game)
   100	void Thread::clear_worker() {
   101	    assert(worker != nullptr);
   102	    run_custom_job([this]() { worker->clear(); });
   103	}
   257	void ThreadPool::clear() {
   258	    if (threads.empty())
   259	        return;
   260
   261	    for (auto&& th : threads)
   262	        th->clear_worker();
   263
   264	    for (auto&& th : threads)
   265	        th->wait_for_search_finished();
   332	    for (auto&& th : threads)
   333	    {
   334	        th->run_custom_job([&]() {
   335	            th->worker->limits = limits;
   336	            th->worker->nodes = th->worker->tbHits = th->worker->bestMoveChanges = 0;
   337	            th->worker->nmpMinPly                                                = 0;
   338	            th->worker->rootDepth                                                = 0;
   339	            th->worker->rootMoves                                                = rootMoves;
   340	            th->worker->rootPos.set(pos.fen(), pos.is_chess960(), &th->worker->rootState);
   341	            th->worker->rootState = setupStates->back();
   342	            th->worker->tbConfig  = tbConfig;
   343	        });
   344	    }
   345
   346	    for (auto&& th : threads)
   347	        th->wait_for_search_finished();
   348
   349	    main_thread()->start_searching();
```
