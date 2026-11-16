# REPORT — seat 30, area 10, check 30-C1: seat 01's S-F5 (halfmove >= 100 hides a mate in 1)

## 1. Three lines
**Asked:** reproduce seat 01's finding S-F5 — with `halfmove_clock >= 100` in the FEN the engine
adjudicates the root as a draw, searches 0 nodes, and misses a mate in 1 (`bestmove f2f3`,
`score cp 0`), while the identical board at halfmove 99 gives `score mate 1` / `bestmove a1a8` /
126 nodes.
**Answer:** **CONFIRMED, exactly as stated, on both my release and my ASan+UBSan build, with
identical numbers.** Beyond their finding: the shortcut is side-blind and mate-blind (a black
mate-in-1 at halfmove 100 is missed the same way), it collapses every position at halfmove 100
(not only mates), and their proposed patch fixes the mate but deletes the real fifty-move draw.
**How sure:** certain (one fresh process per case, fully synchronised, two builds, controls that
show the harness detects a difference).

## 2. Honesty numbers
Release `6b98f217`, sha256 `e06310ec…6a83`: bench 11 = 312866, 13 = 862329, 16 = 3024920,
perft 5 = 4865609 (HONESTY.txt).
ASan+UBSan build used for the second pass: sha256 `a3614d4f…f677c`, `nm __asan_` = 35,
`__ubsan_` = 15, no sanitizer env vars set (out_asan/meta.json).
Patched build (seat 01's patch on my scratch copy): sha256 `81c52608…37c9`,
bench 11/13/16 and perft 5 **unchanged** (out_fix_honesty/honesty.txt).

## 3. Step table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `check1/prediction.txt` (commit `02b797853`) | 5 predictions with kill conditions |
| my own harness written from their sentence | done | `check1/check_s01f5.py` | one process per case, waits for bestmove |
| run on release build | done | `check1/out_rel/table.tsv`, `results.json` | S-F5 reproduced |
| run on ASan+UBSan build | done | `check1/out_asan/` | identical to release |
| controls (no-mate board, quiet board) | done | `check1/out_rel/results.json` rows norook_*, quiet_* | harness sees differences |
| black-to-move extension (my P5) | done | `check1/out_rel/results.json` rows black_mate1_* | confirmed |
| apply their patch and re-run | done | `check1/out_fix/`, `s01_fix_under_test.patch.txt` | mate fixed at every counter |
| honesty of the patched build | done | `check1/out_fix_honesty/honesty.txt` | all four numbers unchanged |
| consequence of the patch on real draws | done | `check1/out_consequence/consequence.json` | draw adjudication LOST |

## 4. The finding, with the exact command that shows it again
`python3 forge-combo29/swarm/30/check1/check_s01f5.py <exe> <outdir>`

| case | score | bestmove | nodes | python-chess mate in 1 |
|---|---|---|---|---|
| mate1_hm0 | mate 1 | a1a8 | 126 | a1a8 |
| mate1_hm97 | mate 1 | a1a8 | 126 | a1a8 |
| mate1_hm98 | mate 1 | a1a8 | 126 | a1a8 |
| mate1_hm99 | mate 1 | a1a8 | 126 | a1a8 |
| mate1_hm100 | cp 0 | f2f3 | 0 | a1a8 |
| mate1_hm101 | cp 0 | f2f3 | 0 | a1a8 |
| mate1_hm150 | cp 0 | f2f3 | 0 | a1a8 |

Board: `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - <hm> 1`. Cause, read in the source:
```
2250:    // Terminal or adjudicated roots: report without searching.
2251:    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
2252:                                               board.is_insufficient_material());
2253:    if (root_candidates.empty() || root_drawn) {
```
(`/agent/repos/base/forge-combo29/src/search.cpp:2250-2253`)

## 5. Beyond their finding (mine, 30-F7)
- **Side-blind.** `black_mate1_hm99` -> `mate 1` / `a8a1` / 126 nodes; `black_mate1_hm100` ->
  `cp 0` / `f7f6` / 0 nodes. The mating side is the side to move, and it is still missed.
- **Mate-blind and score-blind.** `quiet_hm0` = +13 cp (1,755 nodes), `quiet_hm99` = +6 cp
  (1,216 nodes), `quiet_hm100` = **cp 0, 0 nodes**. Nothing about the position changed except the
  counter, and the engine stops evaluating it at all.

## 6. Their fix, and what it costs (my 30-F8)
Patch `check1/s01_fix_under_test.patch.txt` deletes the `halfmove_clock() >= 100` term. Applied with
`patch -p2 --fuzz=0` to a scratch copy: **every** mate case now answers `mate 1` / `a1a8` at every
counter, `bench 11/13/16` and `perft 5` unchanged. **But** the fifty-move draw at the root is gone:

| case | base | patched |
|---|---|---|
| draw_claimable_hm120 `6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 120 1` | cp 0, 0 nodes | **cp 10, 425 nodes** |
| draw_claimable_hm150 (same, 150) | cp 0, 0 nodes | **cp 10, 425 nodes** |
| draw_claimable_hm99 (same, 99) | cp 0, 781 nodes | cp 0, 781 nodes |
| insufficient_hm150 (KN v K) | cp 0, 0 nodes | cp 0, 0 nodes (still caught) |
| kqvk_hm120 `8/8/8/4k3/8/8/8/K1Q5 w - - 120 1` | cp 0, 0 nodes | cp 0, 144 nodes |

So the correct repair is narrower than the one proposed: the shortcut must not fire when the side to
move has a mate available (or, at minimum, when the position is not actually drawn), rather than being
deleted. That is a design statement, not a measured fix — I did not build it.

## 7. Suspicions, not proven
- `insufficient_material` survives the patch (KN v K still 0 nodes), so the *other* half of the
  shortcut is intact; only the counter branch is affected. Consistent with the code, but I tested one
  insufficient-material board, not a battery.
- Whether the engine's own `draw_leaf_score`/`DrawJitter` path (search.cpp:2256-2258) ever intends to
  report a non-zero score near the counter is unclear to me; I did not test DrawJitter > 0.

## 8. A harness fault of mine, recorded, not hidden
My first version of this check (`check_s01f5.sh`, deleted after use) piped `quit` immediately after
`go depth 6`. The engine aborted every search, so every counter looked like a missed mate,
including halfmove 0 — which contradicted seat 01's own hm-0 row and exposed the bug. The corrected
harness waits for each search's `bestmove`. Had I not had their row to compare against, I would have
reported a false REFUTES.

## 9. What I did NOT do
- I did not run seat 01's `analyse_halfmove.py`; I wrote my own harness from their sentence and FENs.
- I did not design or test the narrower repair (mate-aware shortcut).
- I did not test this under TSan (no threads involved in this path).

## 10. What I am NOT sure about
- Whether a mate at halfmove exactly 100 should be scored `mate 1` by rule — FIDE's fifty-move claim
  is a claim, and the engine's own comment at search.cpp:1301 says a mate on the hundredth half-move
  still wins. I report what the engine does, and that the two counters that differ by one give
  opposite answers.

## 11. Times: see `check1/out_rel/stamps.txt`.
## 12. Last command — `git status --short` and `ls`
see `check1/last_cmd.txt`.
