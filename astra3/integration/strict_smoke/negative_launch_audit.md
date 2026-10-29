# Negative strict-smoke launch-label audit

Reviewed 2026-10-29 08:26:58 UTC. No process was launched and no original receipt or log was edited.

**Conclusion: PASS for the user's unknown-option/exit-1 contract.** The original negative receipt remains FAIL because an extra harness assertion prohibited the text `Started game`. Fastchess emits that scheduling label before initializing either engine's options. The captured session sent **0 `go` commands and 0 `position` commands**, produced **0 `bestmove` responses**, and wrote a **0-byte PGN**. Both engine processes were launched for the UCI handshake and initialization; no chess search or played move is evidenced.

## Original evidence

- `unknown_option/stdout.bin:3` prints `Started game 1 of 2`; line 4 then names the exact rejected option: `Warning; integration-A doesn't have option Astra3UnknownOptionProbe`.
- `unknown_option/engine.log:9–14` shows the scheduling message precedes the first engine startup and `uci` request.
- `unknown_option/engine.log:234–252` shows engine-A configuration and the named warning at line 241. The unknown option itself is **not forwarded** to Forge.
- `unknown_option/engine.log:255–277` contains remaining initialization/readiness commands. Lines 286–293 contain `stop`/`quit` cleanup and normal engine exits. There is no intervening `position`, `go`, search info or `bestmove`.
- `unknown_option/exit.json` records returncode **1**, expected **1**, completed games **0**, original `pass:false`. `results.json` retains the initial overall `pass:false`. These were not relabeled or rewritten.

Parsed command counts from all original `[Engine] ... <---` records: `{"isready": 3, "quit": 2, "setoption": 10, "stop": 2, "uci": 2, "ucinewgame": 2}`. The parser counts complete protocol command tokens, so `ucinewgame` is not treated as `go`. These are analysis counts, not reconstructed original logs.

## Exact runner source explains the ordering

Runner commit [`ebfd64cb7fac80d4822c50b07dca4fe934779d21`](https://github.com/Disservin/fastchess/commit/ebfd64cb7fac80d4822c50b07dca4fe934779d21), binary SHA256 `91c2f9b6fafe8c2e86c25a2d2d291cbf7c8ab798b43798b9a6fb522e5d990509`; the fetched tracked source is unchanged.

1. [`roundrobin.cpp:94–98`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/matchmaking/tournament/roundrobin/roundrobin.cpp#L94) defines the start callback; [`output_fastchess.hpp:90–94`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/matchmaking/output/output_fastchess.hpp#L90) makes it print the label. [`tournament.cpp:224–229`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/matchmaking/tournament/base/tournament.cpp#L224) invokes that callback **before** `match.start(...)`.
2. [`match.cpp:332–380`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/matchmaking/match/match.cpp#L332) starts both engine processes and refreshes their options before entering the game loop. [`uci_engine.cpp:271–277`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/engine/uci_engine.cpp#L271) emits the named missing-option warning and returns without sending that option.
3. [`logger.hpp:76–84`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/core/logger/logger.hpp#L76) sets both `abnormal_termination` and `stop` when strict mode encounters this warning. Remaining initialization may finish, as observed. [`match.cpp:393–406`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/matchmaking/match/match.cpp#L393) checks `stop` before `playMove`, preventing a first turn. [`main.cpp:68`](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/app/src/main.cpp#L68) returns failure for abnormal termination.

## Corrected interpretation

Keep the original FAIL receipts and this addendum together. The user requested a named unknown option to cause exit 1, which is verified. Replace the extra human interpretation “no Started-game label” with the evidenced condition “no UCI search/played move and no completed PGN.” Do not claim that no engine process or game task was created. This result validates Fastchess's strict advertisement-based rejection; Forge's own unknown-setoption diagnostic is covered by the separate native protocol tests. No rerun is needed to resolve this label mismatch, and no Elo/strength conclusion follows.

## SHA256 of unchanged originals

| File | SHA256 |
|---|---|
| `unknown_option/stdout.bin` | `300b4f29839e55a8c52d9845342f6da914137bb153e8566e485960df8e42cd02` |
| `unknown_option/stderr.bin` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `unknown_option/engine.log` | `9ce81b739842b61d4e20b7b58ff87ec0f28b1768dd3dd334966eb64140b588c3` |
| `unknown_option/games.pgn` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `unknown_option/exit.json` | `1973ba95a0d20907984ab18418b75564566dbd9e745e70396e6800d2fe4e2fd4` |
| `results.json` | `6ce88139c7264913431d8ac5a2ed1b79c26900c1ea837f19e84e2b49818f91a4` |
| `commands.json` | `3a7e1d7ef5332786522a2b2ac1b2e5410551768b9bb64e8c9dd74029a4e04aae` |

IDEA_SOURCE: user A1 strict smoke requirement, preserved native runner evidence and the exact official Fastchess source; this is a read-only interpretation addendum.
