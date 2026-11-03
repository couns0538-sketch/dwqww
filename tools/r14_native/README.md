# Native legal-chain helper

This original C++17 helper implements standard-chess legal moves and bounded
existential reachability. It has no engine-library dependency and never reads
datasets itself. The parent owns input identity, resource admission, row parsing,
authentic game provenance, and final separation verdicts.

## Build and quick check

Run `Build-Native.ps1 -OutputName chain_native_r01.exe` from PowerShell. The script
uses the existing compiler at `C:/msys64/ucrt64/bin/g++.exe`, one compilation unit,
Idle priority, owned temporary storage, and hidden GPU devices. It restores process
environment and priority afterward and refuses an existing output name. The
result is statically linked, so it needs no compiler-directory runtime on PATH.

Set `R14_NATIVE_EXE` to the absolute candidate path and run the independent
runtime against `D:/a14/tests/r14_native/test_native.py`. The fixture suite uses
the external chess package only as an oracle; no package source was copied.
Review a frozen source/executable identity before the million-pair audit.

## Streaming protocol

Default mode is `--pairs`. Each input line is seven tab-separated fields:

`id<TAB>fen1<TAB>white_result1<TAB>fen2<TAB>white_result2<TAB>K<TAB>node_limit`

Use all six FEN fields. Results must numerically equal 0, 0.5 or 1. The row adapter
must supply K=8 and a node limit of 100000 normally, or 1000000 for the separately
recorded critical-boundary retry. The CLI accepts K in 1..64 and positive node
limits up to 1000000000, but this does not authorize exceeding the task budget.
Clocks are nonnegative integers up to 1000000000; fullmove must be positive.

Each line produces one JSON object containing `id`, `status`, `reason`, `nodes`,
and `witness` (an array of UCI moves). Replies are flushed before waiting for the
next input line. The child does not create threads, files, subprocesses or GPU
contexts. Invalid rows yield `UNKNOWN` / `invalid_input` and processing continues.
Exit 0 means transport completed; it does not mean rows passed. Invalid command
arguments exit 2; stream I/O failures exit 1. Input records must fit in RAM.

- `REACHABLE` / `legal_witness`: an exact-state legal path of the exact positive
  absolute-ply difference was found with equal White results.
- `UNREACHABLE` / `result_mismatch`, `nonpositive_ply_gap`, or
  `exhaustive_no_path`: the required continuation is contradicted. The last
  category includes proven necessary-condition pruning.
- `UNKNOWN` / `gap_exceeds_k` or `node_limit`: no negative proof is claimed.

`nodes` counts visited states including the root, endpoints, and pruned states;
the count never exceeds the supplied cap. A budget-exhausted branch is never
memoized as disproved. Memoization stores full FEN strings with exact equality,
so hash collisions do not change a verdict. Its scope is one input pair.

`--moves` accepts `id<TAB>fen`. A valid response has `id`, `status: "OK"`, and
`moves`, sorted by UCI. Every move has `uci` and its complete successor `fen`.
Malformed inputs use the same `UNKNOWN` error object as pair mode.

## State semantics and limits

The board preserves castling rights, raw en-passant target (including a legal
double-push target when no capture is possible), halfmove clock, fullmove number,
and side to move. Standard king/rook castling, en passant with discovered checks,
promotion choices, and king safety are included. FEN parsing checks syntax,
piece/king counts, pawn back ranks, castling pieces, en-passant geometry, and
the king of the side that just moved. It does not claim complete retrograde
legality validation of arbitrary FEN positions.

Absolute ply is `2*(fullmove-1)+(black_to_move ? 1 : 0)`. Search uses that exact
depth, never an arbitrary shorter connection. Pruning uses monotone castling
rights, material/pawn counts, halfmove-clock necessity, and a lower bound on
own moves required to fill missing target-piece squares, with one extra target
square allowed for castling. Move ordering affects speed only.

Reachability is standard legal-move reachability, without original game history
or adjudication evidence. A found path does not establish that it was played,
that two rows came from the same original game, or that a segment is authentic.
In particular, `gap_exceeds_k` and search exhaustion must never become certified
game boundaries. Full source/target strings and row IDs remain parent evidence.
