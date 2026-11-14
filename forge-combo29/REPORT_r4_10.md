# R4-10 — `setoption` values with spaces or the word `value`

Finding 10 from `audit/lock-source` at `302a08a2` says `setoption` drops spaces in a value and stops at the word `value`. Reproduced on base `e04556ddc3a430b2e751159b0d46111ef56c8b89`. The base already keeps those values. No engine source change.

## What the parser does

`forge-combo29/src/uci.cpp` reads the first word after `value` with `operator>>`, then `Book File` and `NnueFile` append the rest of the line with `std::getline`. Joining those two pieces keeps internal spaces, tabs, and a later `value` token. Whitespace immediately after the `value` keyword is the separator, so a leading run is not part of the path. Trailing spaces and `\r` are stripped. That is the same path text as the audit's proposed `getline` for these two string options.

The proposed replacement was not applied. It would not change `Book File` or `NnueFile`, and it would reject a spin such as `Hash value 16 extra` instead of reading `16`. No advertised option name contains the token `value`. The name scan still treats the first `value` token as the UCI separator.

## Proof

`forge-combo29/tests_r4_10/run.sh` configures CMake with no `-DFORGE_*` override and links AddressSanitizer and UndefinedBehaviorSanitizer. `forge-combo29/tests_r4_10/check.py` exits non-zero on a failed check. Leak detection stayed on. The run printed no sanitizer diagnostic and exited 0.

String values that loaded a 16-byte book (`with 1 entries`) or opened an NNUE file (`nnue: wrong size`, which is only printed after the file opens):

- `my   book.bin` (three spaces, the finding's trigger)
- `a  b.bin`
- `value book.bin`, `my value.bin`, `a  value  b.bin`, `value value.bin`, `Bar value Baz`
- `tab<TAB>name.bin`
- the three-space path again with trailing spaces on the command, trimmed back to the same path
- extra spaces after `value` before `plain.bin`, treated as the separator
- `nnue value.bin`

The one-space path `my book.bin` was not created. The engine answered `cannot load book` for that exact path, so the three-space load was not a collapsed name. `<empty>` restores the built-in book and net with no diagnostic. `Hash 16`, `Threads 1`, `Move Overhead 10`, `OwnBook false`, `Ponder false`, and `Clear Hash` are quiet. `Not A Real Option` is still `unknown option`.

Pins, same process:

- `bench 11` = `312866`
- `bench 13` = `862329`
- `position startpos` / `go perft 5` = `4865609`

Two hundred `go depth 10` searches, each checked against `go perft 1` for that position. Every `bestmove` was in the legal list. Samples: search 1 `d2d4` (20 legal), search 100 `a7a5` (35), search 200 `c5d4` (34). Elapsed 36.5s.

`CMakeLists.txt` was not edited.
