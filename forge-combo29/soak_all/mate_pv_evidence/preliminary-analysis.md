# Part 4 early read-only investigation

No engine, repository test, branch, or old soak worktree was changed. Four tiny engine searches were run: the reported FEN once on each binary with default NNUE, then once on each with NNUE disabled. All exited 0 with empty stderr. The one independent retrograde query used the unchanged t12 oracle class, not the t12 engine-search loop.

## Reproduction

FEN: `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`.
Both runs explicitly used Threads 1, Hash 16, OwnBook false, fresh `ucinewgame`, then `go depth 13`.

| Setting | Exact lock | Merged |
| --- | --- | --- |
| Default UseNNUE=true | cp 449, 50362 nodes, b3b5, 18-ply PV | Same |
| UseNNUE=false | mate 17, 25568 nodes, b3f3, 15-ply PV | Same |

Thus the reported mate line needs the missing `UseNNUE=false` setting. It is inherited from the lock, not introduced by these merges.

Lock binary SHA256: `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
Merged binary SHA256: `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e`.
Source inspected at HEAD `b1675de751153e6b80e5c99779805956c22912cc`; concurrent parent work affected report/test-driver files only in the observed status.

Reported PV:

```
b3f3 c2d2 f1f2 d2d1 f2e3 d1c2 e3e2 c2c1 f3c3 c1b2 e2d3 b2b1 d3d2 b1b2 c3f3
```

## Independent mating assessment

The t12 KRK retrograde algorithm is independent of Forge's alpha-beta search, although it uses the same attacks/board primitives. The scratch probe includes the existing t12 source unchanged, renames its original main, and calls only its oracle plus board legality operations.

- Root exact DTM: **15 plies** (mate in 8 moves).
- `b3f3`: forces mate in **17 plies** (mate in 9 moves).
- The optimal root move found by the oracle is `b3e3`, 15 plies.
- Every move of the published 15-ply PV is legal.
- PV endpoint: `8/8/8/8/8/5R2/1k1K4/8 b - - 15 8`; Black has three legal moves and is not in check.
- Exact DTM from that endpoint: **6 plies**. The shown continuation can therefore finish in 21 total plies under optimal continuation.
- UCI `mate 17` is in moves, corresponding here to a reported bound of 33 plies; it is not a claim of mate after 17 plies.

The oracle therefore does **not** show an overclaim of a forced mate, a nonmating chosen move, or an impossible mate bound. The reported distance is loose compared with the exact DTM. The incomplete PV alone is not a correctness failure.

## Relevant code paths

All references below are `forge-combo29/src/search.cpp`.

| Mechanism | Lock lines | Merged lines |
| --- | --- | --- |
| Reset qsearch PV length on entry | 996 | 1048 |
| Return a TT score at non-PV cutoffs without reconstructing a PV | 1016-1019; 1165-1169 | 1075-1079; 1226-1231 |
| Replace qsearch stand-pat eval with a usable TT bound/exact score, including mate values | 1032-1044 | 1092-1104 |
| Copy only the child PV actually searched | 1091-1094; 1444-1447 | 1151-1154; 1526-1529 |
| Store score and PV separately after a completed root iteration | 1689-1697 | 1809-1814 and emit logic |
| Format mate distance and print available PV as-is | 190-196; 1576-1579 | 198-204; 1672-1682 |

The PV buffers carry searched moves, while TT entries carry scores/bounds and one move, not a full mate continuation. In particular, a quiet qsearch PV node may inherit a mate-valued TT stand-pat and return no child PV. This supplies a concrete explanation for a legal nonterminal PV prefix accompanying a mate score. The exact leaf return site in this execution was **not instrumented**, so this is a source-based mechanism analysis rather than a traced proof of one specific return instruction. The mate score conversion itself uses the normal signed ply adjustment in `score_to_tt`/`score_from_tt`.

## Recommendation

Do **not** add a mate-suppression patch or a default-off engine fix based on this reproduction. No genuine mate-bound correctness failure was established. A full-PV reconstruction feature would be a different task and can create cycles or misleading continuation if implemented by blindly chasing TT moves. A targeted under-60-line correctness fix would require a separate concrete failing position/bound or runtime trace showing an unsound bound operation.

## Evidence and investigation failures

- `repro-transcript.txt`: default-NNUE exact commands, inputs, outputs, exit statuses.
- `repro-nnue-off-transcript.txt`: NNUE-disabled reproduction, including the reported mate line.
- `oracle_probe.cpp`: scratch-only query driver around the unchanged source oracle.
- `oracle-correct-defines-transcript.txt`: successful oracle compile/query and all per-PV-state DTM/legality results.
- `inspection.txt`: source inspection and line references.
- The first scratch oracle compile omitted the engine's feature definitions, including PEXT, while linking its precompiled board/bitboard objects. That inconsistent harness segfaulted (exit 139); the original command/output is retained in `oracle-transcript.txt`. Rebuilding only the scratch harness with matching engine definitions passed. This was not an engine UCI crash.
- An exploratory ripgrep command mentioned nonexistent `include/forge/types.hpp`; its error is preserved in `inspection.txt`.

No claim is made about all mate scores, all positions, or the absence of other search bugs.
