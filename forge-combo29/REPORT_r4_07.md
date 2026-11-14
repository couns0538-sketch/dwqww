# R4-07 finding 3

Base `e04556ddc3a430b2e751159b0d46111ef56c8b89`. Audit text and proof read only from `audit/lock-source` at `302a08a272fbe8e8c4463731f3b9cd72d72d3f48`, finding 3 and `forge-combo29/tests_audit/proof_go_mate_cap.cpp`.

## Result

Already correct on this base. No engine change. `CMakeLists.txt` was not edited. No new `FORGE_*` switch.

Finding 3 says `go mate N` caps depth at `2N-1` and therefore misses two forced mates, and that it also stops when the side to move is being mated. On this base the audited positions are solved inside that cap, and a negative mate score does not end the search.

`Worker::search` still limits `go mate N` with `mate_moves * 2 - 1` (`src/search.cpp` lines 1653-1654). Late-move reductions are already skipped when `mate_moves_ != 0` (line 1480), as are the other forward-pruning cuts guarded the same way, so a full-width search to `2N-1` plies is enough for these mates. The iteration break (line 1906) is `score >= mate_in(mate_moves * 2 - 1)`, which is a positive mate in at most N moves. A negative mate score does not satisfy it.

The lock-source proof printed `h2b8` cp `907` and `f6b6` cp `-81`. Reproduced here, the same calls print the mating moves:

```text
mate-in-2 go mate 2 depth=3 best=a1a6 score=31997 mate=2
mate-in-2 go depth 6 depth=6 best=a1a6 score=31997
mate-in-3 go mate 3 depth=5 best=f8c5 score=31995 mate=3
mate-in-3 go depth 6 depth=6 best=f8c5 score=31995
being-mated go mate 6 depth=11 score=-31998 best=a2a1 continued=1
own-mate go mate 6 depth=3 cap=11 score=31997 mate=2 best=b1c2
pins bench11 312866 bench13 862329 perft5 4865609
depth10 searches 200 legal 200
PASS r4_07 go mate
```

`being-mated` is `8/8/8/8/8/2R5/k7/2K5 b - - 0 1` with `go mate 6`. Depth 2 already reports `score mate -1`. The search continues through depth 11. `own-mate` is mate in 2 with `go mate 6`; that search stops at depth 3 because the mate is ours.

Pins `312866`, `862329`, and `4865609` match. Two hundred depth-10 searches returned a legal move every time.

## Test

`tests_r4_07/go_mate_test.cpp`, run by `tests_r4_07/run_asan.sh`.

The script uses the existing combo29 lock definitions from the tests_t22 address/undefined-sanitizer recipe (`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all`, hidden size 256, the same speed switches). Those are not a new override. A failed check returns 1. Sanitizer errors do not recover.

```bash
forge-combo29/tests_r4_07/run_asan.sh
```

Exit code 0. Wall time about 70 seconds.
