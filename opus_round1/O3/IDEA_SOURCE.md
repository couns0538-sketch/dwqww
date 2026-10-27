# IDEA_SOURCE: O3 search.cpp no-op refactor

| change | idea source | code copied? |
|---|---|---|
| Split of the search into move picker / history / TT / time management / qsearch / main search / iterative deepening / UCI info modules | General engine-architecture practice; the same concern split is visible in the public layout of open-source engines such as Stockfish (`movepick`, `history`, `tt`, `timeman`, `search` files) and described on the Chess Programming Wiki pages "Move Ordering", "History Heuristic", "Transposition Table", "Time Management", "Quiescence Search", "Iterative Deepening". | No. Every line of moved code is Forge's own (moved verbatim from the AL1 s198 search.cpp); the new glue (`ThreadData`, `HistoryTables`, `timeman::allocate`, `timeman::soft_limit_factor`, `write_iteration_info`) was written for this job. |
| Per-thread state struct (`ThreadData`) separated from the shared state (`SharedSearchState`) | Lazy SMP description on the Chess Programming Wiki ("Lazy SMP": shared hash table, thread-local search state). | No. |
| Compiling the modules as one translation unit (the `.inc` modules are included by `src/search.cpp`) | Own decision to keep the PC build recipe (8 fixed .cpp files in `2_build/build_windows.ps1` and the gate scripts) and the hot-path inlining unchanged ("unity build" technique). | No. |
| Move-picker / history / time-management unit tests | Own tests; reference formulas re-derived from the lock source. | No. |

No behaviour change is intended or observed (bench, 50-position depth-18 identity); no Elo claim.
