# scripts — what each one is for, and the path it takes

Every script takes its engine path from `argv` or an environment variable, and writes its
output under `/tmp/fx` by default. Nothing writes into the repository.

## The measurement chain

| script | role |
|---|---|
| `pins.py` | the four honesty pins. `bench N` on **stdin**; a separate `perft` mode because `go perft` ends with a bare `nodes N` and **no** `bestmove`. |
| `solver.py` | exact retrograde solver. The oracle. Symmetry group is a parameter: 8 maps without pawns, **2** (rank-preserving) with a white pawn. |
| `build_tables.py` | builds KK/KBK/KNK/KRK/KQK and asserts four classical values (KQK 10, KRK 16 moves; KBK/KNK zero wins). |
| `build_kpk.py` | builds KPK over the piece tables, and checks the classical max DTM of 28 moves. |
| `fixtures.py`, `make_fixtures.py` | position generators. Built by construction, validated with python-chess, KQK/KRK stratified across DTM buckets. |
| `kpk_sample.py` | the stratified KPK sample (pawn file × pawn half × verdict). |
| `oracle.py` | validates the drawn-root predicate against the binary **and** proves the validator can fail, with two planted faults. |
| `parallel.py` | the runner: one process per slice, JSONL out, `--search-timeout` per search. |
| `aggregate.py` | every number in `FINDINGS.md`, re-derived from the JSONL. |
| `ladder.py` | depth ladder on the positions that FAILED, so "horizon effect?" is answered on the right positions. |
| `clock_band.py` | the clock band and its cost: the same board at ten clock values, one command. |
| `game.py` | one game: both-engine and oracle-attacker arms, full move list, every bail and timeout recorded. |
| `uci.py` | the driver. Reads every search to `bestmove`; a runaway search gets UCI `stop`, never `quit`. |
| `predicates.py` | the engine's drawn-root predicate, reimplemented. |

## Three traps these encode, each of which produced a wrong number first

1. **`bench` prints one `info string bench depth ... nodes N ...` line.** A reader waiting
   for a line that *starts* with `nodes` never returns. That is a hang, not a pass — and it
   is silent on the way in.
2. **`quit` into a live search** makes this engine abort and fabricate `bestmove a2a3` with
   zero info lines. `stop` is the only correct way to end a search early.
3. **A refused FEN manufactures a pass**, because the engine stays on the previous position
   and the driver silently re-searches it. Every fixture is validated before use.

## Two traps that produced a *plausible* wrong number, which is worse

- **The oracle refused to promote.** A promotion leaves the KPK table; scoring that child as
  "unknown" ranked it as bad, so the oracle shuffled a pawn on a7 for 100 plies and "failed"
  178 of 192 won cells. Caught only because the control had to hit 192/192.
- **The KBK/KNK arms were vacuous.** Half the positions had the bare king to move, and
  `board.is_game_over()` is True for *every* KBK/KNK position even with a move available, so
  all 40 games ended at ply 0 and looked like a clean 20/20 draw. The stop condition is now
  "no legal move".

## Paths

`FORGE_EXE` / `--exe` sets the binary. Outputs default to `/tmp/fx`:
`tables.json`, `kpk_table.json`, `fixtures.json`, `kpk_sample.json`, `prod/<cell>/*.jsonl`.
Relative `--out` values are relative to the working directory; nothing escapes it.
