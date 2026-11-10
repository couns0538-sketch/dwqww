# Opening-book legal-list reuse experiment

Status: UNPROVEN optimization, disabled by default. No speed or strength claim.
Date: 2026-11-10 UTC. Base review branch HEAD when tested: ed2030a236b66ec0d02cc5d90973fb9e48bb8a53.
Compiler: g++ (Debian 14.2.0-19) 14.2.0.

`FORGE_BOOK_LEGAL_REUSE=1` generates a legal list once when the Polyglot key has at least one matching entry, then uses the original decoder logic against that list. Missing keys still skip generation. Candidate iteration, duplicate-weight saturation, stable ordering and probe selection are unchanged. The original path remains under `#else`. Public decode_move is unchanged; its logic is duplicated in a private experiment helper so the baseline stays intact.

## Reproduction

From forge-combo29 run `tests/book_reuse_check.sh`. It builds temporary binaries with:

`g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -Iinclude`

The book tests additionally specify `-DFORGE_BOOK_LEGAL_REUSE=0` and then `=1`, linking `tests/book_legal_reuse.cpp src/board.cpp src/bitboard.cpp src/book.cpp`. The board audit links `tests/book_board_audit.cpp src/board.cpp src/bitboard.cpp`. Executables run with `ASAN_OPTIONS=detect_leaks=0`. No leak-check claim.

Equivalent individual compile/run commands were executed successfully for each of these three executables before committing. Observed output:

- Switch 0: `PASS book candidate/reference cases=509 exhaustive_encoding_positions=9 seed=20261110`
- Switch 1: `PASS book candidate/reference cases=509 exhaustive_encoding_positions=9 seed=20261110`
- Board audit: `PASS positions=17401 moves=499310 seed=20261110`
- No ASan or UBSan diagnostics. `git diff --check` passed for book.cpp.

The book test compares exact move records, weights and order against a reference using unchanged public decode_move for every entry. Nine positions exhaust all 65,536 encodings, covering both-color castling and promotions, legal/illegal EP, double check and mate. Another 500 seeded random-game positions exercise sampled invalid encodings plus every legal move, duplicate saturation, equal-weight stable ordering, empty books and absent keys. No independent chess implementation is used, so shared baseline defects are outside this equivalence test.

The board audit was initially compiled from stdin. Its full logic was preserved from that tool-call text, formatted and given explicit ignored-return casts, then rerun from the committed source to reproduce the same counts. It tests generated pseudo-legality, gives_check versus make/in_check, reconstructed FEN/hash/pawn-hash/checkers, exact make/unmake state and has_legal_move. It does not compare against an independent move generator.

## Remaining gates

Independent patch review, full lock-flag build and prescribed benchmark/node pins are still required for promotion. No runtime benchmark, NPS result or Elo result is asserted. These unit tests use header defaults apart from the experiment switch, not every combo29 build switch. Keep the experiment disabled until the required validation is completed.
