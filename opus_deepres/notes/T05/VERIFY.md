# T05 adversarial verify (start 23:20 PC clock, stop 23:45)

Format: card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION | evidence

## Lint, licence rows, lock greps
- all | card_lint.py cards/T05/*.md | CONFIRMED (0 findings, 0 PENDING on all 4 cards) | tools/card_lint.py run 23:21
- licences.md | Stockfish ff7cee4244 GPL-3.0 row | CONFIRMED (re-run identical) | tools/licence_at.py official-stockfish/Stockfish ff7cee4244 --row
- licences.md | llvm-project b537630299 row (tool says MIT, hand correction Apache-2.0 WITH LLVM-exception) | CONFIRMED tool row identical; hand correction checked below | tools/licence_at.py llvm/llvm-project b5376302... --row
- T05-01 | forge_has 'unique_ptr<float|/ WeightScale' = 3 hits nnue.cpp:47, :59, :61 | CONFIRMED | tools/forge_has.sh
- T05-01 | lock refresh src/nnue.cpp:84-97, update :99-157, :59 float(NnueW1)/WeightScale | CONFIRMED | lock src/nnue.cpp (239 lines)
- T05-03 | forge_has 'large_page|MEM_LARGE|madvise|huge' = 0 hits | CONFIRMED | tools/forge_has.sh
- T05-02 | static_evaluate src/search.cpp:599-621, root refresh :1367, weights() src/nnue.cpp:53-68 | CONFIRMED | lock src/search.cpp (1531 lines), src/nnue.cpp
- T05-04 | lock prefetches only the child TT cluster: src/search.cpp:847, :1126 | CONFIRMED (forge_has 'prefetch' = 5 hits: search.hpp:112 comment, :125-127 TT::prefetch, search.cpp:847, :1126) | tools/forge_has.sh 'prefetch'
- T05-04 | record_move src/search.cpp:623-630, called before make_move, computes the dirty pieces | CONFIRMED (comment line 624-625, dirty_pieces at 627) | lock src/search.cpp
