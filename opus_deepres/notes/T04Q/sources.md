# T04Q sources (lock files and line ranges read; outside sources)
Lock = FD3A5190 source, read-only: C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean (own code).

| # | source | lines read | licence tier | what it gave | card |
|---|---|---|---|---|---|
| 1 | notes/T04/BUG_CHECKLIST.md, notes/T12B/TABLE.md, notes/CRITIC2.md, notes/T04M/TABLE.md | all | own notes | checklist rows 1-21, known items (bad_captures_, buffer inventory) | no card |
| 2 | lock include/forge/search.hpp | 1-408 (all) | own code | TT entry / score_usable, stack, history types, constants | no card |
| 3 | lock src/search.cpp | 1-1531 (all) | own code | TT probe / store, picker, histories, qsearch, search, ID / aspiration / TM | no card (rows A1-A21, B1-B12) |
| 4 | lock src/board.cpp | 18-100 (promotion SEE path), 558-575 (has_legal_move), 728-790 (make_move keys), 885-935 (repetition, insufficient material, see_ge head) | own code | key updates, repetition rule, stalemate witness | no card |
| 5 | lock include/forge/board.hpp | 160-172, 199 (grep hits 16-22, 84-91, 111-137, 183) | own code | captured_piece, piece_type(Empty) = 0 | no card |
| 6 | lock src/uci.cpp | grep `bestmove` / `0000` only (342, 365, 374) | own code | no-move root prints 0000 | no card |
| 7 | notes/SPEC_SEARCH.md 128-145; greps of cards/ and notes/ (has_legal_move, promotion, repetition) | as named | own notes | duplicate check: root repeat = T04F-03, has_legal_move cost = T05C-01, quiet-promotion capture-history asymmetry not listed anywhere | no card |
No outside source was read (no web fetch, no other engine).
