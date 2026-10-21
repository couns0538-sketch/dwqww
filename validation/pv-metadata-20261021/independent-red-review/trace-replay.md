# Independent saved PV trace replay

All 27 saved `PV_TRACE` FENs are structurally valid under python-chess, all 27 selected UCI moves are legal, and all 27 independently pushed positions remain structurally valid. Both logged in-check fields match the trace FEN in every row. This is a limited saved-log legality and accounting check.

Oracle: `python-chess 1.999` / `chess 1.11.2`, Python 3.12.14, `/workspace/.cloud-setup/venv/bin/python`. Bytecode writes disabled. No engine execution, compiler/build, Git operation, or source edit.

## Actual counts

| Quantity | Natural log | Worker probe |
|---|---:|---:|
| Search summaries | 8 | 0 |
| Summary events / reported singular calls | 716 | 2 |
| Changed metadata rows / reported changed total | 25 | 1 |
| Emitted trace rows | 25 | 2 |

The natural stdin requests `bench 11`; 11 is the requested benchmark depth. The raw stderr contains eight per-search summaries. The worker stdout contains four cases, of which two report one singular call each; its two trace rows include one changed and one unchanged PV metadata row. These counts are distinct.

## Per-search summary accounting

| Search | Events | Changed | Emitted | Actual trace rows |
|---|---:|---:|---:|---:|
| 1 | 52 | 2 | 2 | 2 |
| 2 | 128 | 2 | 2 | 2 |
| 3 | 119 | 11 | 11 | 11 |
| 4 | 76 | 0 | 0 | 0 |
| 5 | 62 | 0 | 0 | 0 |
| 6 | 22 | 0 | 0 | 0 |
| 7 | 69 | 1 | 1 | 1 |
| 8 | 188 | 9 | 9 | 9 |

Each summary has `changed == emitted == actual changed trace rows`; the maximum changed count is 11, below the 64-row cap. Thus no changed event counted by these summaries was lost to that cap. This does not independently prove that the instrumentation counted every actual engine event.

## First witness reconstruction

Starting from the standard initial board, `e2e4 e7e5 g1f3` is legal and produces the first trace FEN exactly:

```text
rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2
```

The selected `d7d6` is legal and produces a structurally valid board:

```text
rnbqkbnr/ppp2ppp/3p4/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3
```

This is an independently reconstructed legal path, not recorded engine move ancestry. The trace does not record all earlier engine moves or search history.

## Check-state field scope

Both logged `in_check_before` and `in_check_after` were compared to the original trace FEN, because they describe the caller-position metadata around the recorded operation. The independently pushed selected-move board is stored separately in JSON. One natural row starts in check: `f1f2` legally resolves it, so the pushed position has the opposite side to move and is not in check even though both logged caller fields are 1.

## Input identity

| Input | Bytes | SHA256 |
|---|---:|---|
| `actual-natural-bench11.stdin` | 49 | `40f79f18ebe835d98b425ff453dbb6840a7c0cf3ac8923b5d36c6c6836337022` |
| `actual-natural-bench11.stdout` | 60 | `41b63631e077ab292a46882267f90f501eef0e2e03ab79d5d1256b881ca5344f` |
| `actual-natural-bench11.stderr` | 8009 | `719689a11b6c129e51afb7d3d460805ff295aa92a737b9f805bd6168d6770082` |
| `actual-worker-probe.stdin` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `actual-worker-probe.stdout` | 251 | `4664802a50bb770ee23ef2a977a6d569d7b687d596a46642008c632d915191ae` |
| `actual-worker-probe.stderr` | 540 | `be69cbe945fc634fa26b6565c8076f30548d04ef9c73bd5f7e03bf7b95422033` |

All inputs are under `../red-attempt1/`. The JSON includes every replayed row, resulting FEN, actual summary association, probe case, and checks.

## Limits

- Only the saved emitted trace FENs and selected moves were replayed; no engine or search process was rerun.
- python-chess Board.is_valid checks structural validity of each board and does not prove a complete legal history for every FEN.
- The first witness opening is an independent legal construction; the raw engine trace lacks full move/search ancestry.
- Summary accounting shows all changes counted by these logged summaries were emitted. This cannot independently detect events that the instrumentation never counted.
- Probe singular_calls, natural summary events, changed metadata rows, and search-summary counts are separate quantities; they are not interchangeable.
- No verification of engine current_move scratch fields, scores, evaluations, or source instrumentation semantics is claimed here.
- No conclusion about all engine states/histories, GREEN behavior, search equivalence, speed, playing strength, Elo, or candidate acceptance follows from this check.
