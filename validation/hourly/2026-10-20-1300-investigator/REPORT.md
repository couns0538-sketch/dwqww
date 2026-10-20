# Forge 6.4 — bug investigator checkpoint — 2026-10-20 13:00 CEST

**Priority:** P3 UCI consistency candidate (source control-flow established; real Forge execution pending).
**Main development ref:** `forge/6.4-hourly-20261019`
**Inspected SHA:** `356e863dbd86d2ce24b8ee9486d7406f1d525480`
**Primary source:** [src/search.cpp#L1194-L1219](https://github.com/couns0538-sketch/dwqww/blob/356e863dbd86d2ce24b8ee9486d7406f1d525480/src/search.cpp#L1194-L1219).
**Duplicate check:** repository issue searches for "terminal nodes", "zero node", and "node limit" returned no matching issues. Earlier node-budget report concerns SMP aggregation, not terminal-root zero budget.

## Finding

`Worker::search` handles terminal/adjudicated root positions (including stalemate) in the `if (root_candidates.empty() || root_drawn)` branch **before** checking `limits.nodes_specified && limits.nodes == 0`. This terminal branch sets `result.depth=1` and calls `emit(1, 0, {})` before `should_stop()`. With `go nodes 0`, `should_stop()` then returns true immediately, but the engine has already emitted a spurious `info depth 1` line despite having searched zero nodes.

The existing nonterminal `go nodes 0 searchmoves e2e4` regression in [tools/uci_regression.py#L159-L166](https://github.com/couns0538-sketch/dwqww/blob/356e863dbd86d2ce24b8ee9486d7406f1d525480/tools/uci_regression.py#L159-L166) explicitly requires **no** `info depth` records, establishing a clear inconsistency between root types.

## Minimal UCI reproduction

```text
uci
isready
position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1
go nodes 0
```

Expected under the existing zero-budget policy: `bestmove 0000`, **no** `info depth` search iteration. Source-implied actual: exactly one `info depth 1 ... score cp 0 nodes 0 ...` before `bestmove 0000`.

Control: `position startpos`; `go nodes 0 searchmoves e2e4` emits `bestmove e2e4` without a depth record.

**Test status:** Static source-level branch-path proof only. Git clone from this runtime failed DNS resolution (`Could not resolve host: github.com`), so **no native Forge execution, no performance test, no candidate fix**. No fake raw native transcript has been produced.

## Proposed isolated fix (NOT applied)

Handle the explicit zero-node budget before the terminal-root reporting loop, after root candidates are computed so fallback `bestmove` remains legal/appropriate. Preserve checkmate/stalemate result and `go infinite` terminal behavior. Run the new probe plus existing full UCI tests, CTest, ASan/UBSan where available. This P3 issue should not displace higher-priority SMP TT publication and rule-50 correctness work.

## Handoff

- **13:15 researcher:** verify UCI intended `go nodes 0` contract for terminal vs live roots; evaluate minimal control-flow reorder.
- **13:30 tester:** compile pinned SHA and run probe, preserve **raw UCI stdout/stderr**, confirm or reject the predicted `info depth 1` discrepancy and unaffected `go infinite` behavior.
- **13:45 developer:** make a guarded one-function patch **only if native probe confirms**, run UCI and CTest. Do not merge before review.

No merge or main-branch writes. All evidence is source-level unless specifically labelled otherwise.