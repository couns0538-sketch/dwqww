# Chess Engine Forge 6.0.0 implementation summary

Full rewrite of `src/board.cpp`, `src/search.cpp` and the evaluation
(`src/eval.cpp`, `src/eval_params.cpp`, `src/eval_params_table.inc`) with new
headers `include/forge/bitboard.hpp`, `include/forge/eval.hpp`,
`include/forge/eval_params.hpp`. `src/uci.cpp` gains `bench`; `tests/tests.cpp`
was rewritten; `tools/tune/` adds the position extractor and Texel tuner;
`tools/uci_regression.py` no longer asserts evaluation-specific scores. The
evaluation table was refitted on 22,000 self-play games. See `CHANGELOG.md`
and `validation/release-6.0.0/`.

---

# Chess Engine Forge 5.31.0 implementation summary

Accepted exactly one behavior change from validated 5.30.0: `src/search.cpp` `Searcher::alpha_beta()` raises the late-quiet LMR floor from 9 to 10. New `tests/tests.cpp` focused zero-window regressions fail on the exact unchanged baseline, pass on candidate, and cover adjacent boundary and board/hash/history restoration. Version-only `src/uci.cpp`, `CMakeLists.txt` and release documentation updates are separate from engine behavior. All GCC, Clang, ASan+UBSan, engine/match/UCI/ponder/perft gates pass. Deep search performs more nodes; no Elo claim. Windows PE is Zen 4 cross-compiled and verified but not native Windows/Wine tested. Source/checksum and repeat Windows build evidence are retained outside this source tree.

---

# Forge 5.29.0 implementation summary

The only engine behavior change from exact validated 5.28.0 is UCI pondering:
`SearchLimits::ponder`, monotonic atomic `Searcher::ponderhit` time origin,
`go ponder` / `ponderhit` state synchronization, gated publication, and optional legal
`bestmove ... ponder ...` prediction. The UCI Ponder option is functional; the engine
remains single-threaded and ships with **no opening book**.
See RELEASE_STATE.md, VALIDATION.md and validation/5.29.0-ponder-evidence/.
