# R4-06 Finding 1: concurrent `attacks::init`

Base: `e04556ddc` (`integrate/combo29-all`). Branch: `grok47/r4-06-audit-f1`.
Audit read: `302a08a27` `forge-combo29/AUDIT_lock_source.md` finding 1 and `forge-combo29/tests_audit/proof_attacks_init_race.cpp`.

## Result

The base is already correct. No engine source change.

`forge::attacks::init` in `forge-combo29/src/bitboard.cpp` fills `KnightTable`, `KingTable`, `PawnTable`, the magic tables, `LineTable`, and `BetweenTable` inside `std::call_once`. That publication landed in `edc598b7c` and is present on `e04556ddc`. A second thread that constructs `forge::Board` waits until the fill has finished, then reads the tables. The fill itself is the same code as before `call_once`.

Pins stay on the default release build:

- bench 11 = **312866**
- bench 13 = **862329**
- perft 5 = **4865609**

No off-by-default option. The existing `call_once` does not change node counts, so there is nothing to hide.

## How the race was checked

AddressSanitizer and UBSan do not prove the absence of a data race. The check is ThreadSanitizer on `forge-combo29/tests_r4_06/concurrent_board_init.cpp`. The process does not construct a `Board` or call `attacks::init` before eight threads pass a barrier. Threads 0–3 then build the first boards together. Threads 4–7 wait 80–320 µs so they enter while a magic fill can still be running and after it has published. Each thread checks the 20 start moves, empty-board rook and bishop attacks against a geometric walk, knight a1, the 48 Kiwipete moves, and an attack-table fingerprint. The threads must agree. A mismatch returns 1. A ThreadSanitizer report exits 66 (`halt_on_error=1`).

Compiler: g++ 13.3.0. `/usr/bin/c++` is Clang 18 and cannot link `libstdc++` here, so the release configure used `CXX=g++`. CMakeLists.txt was not edited. The tests do not `#define` or `#undef` any `FORGE_*` macro. g++ was given the same `FORGE_SPD_*`, `FORGE_NNUE_HIDDEN`, and `FORGE_SEARCH_SPEED2` switches `CMakeLists.txt` already sets.

| Build | Result |
|---|---|
| `-fsanitize=thread`, `FORGE_SPD_SLIDER_PEXT=0` (magic search and its scratch arrays) | `PASS concurrent first init threads 8 fingerprint 6cb665f569fdae74`, exit 0, no ThreadSanitizer report |
| `-fsanitize=thread`, `FORGE_SPD_SLIDER_PEXT=1` (lock slider tables) | same pass line, same fingerprint, exit 0, no ThreadSanitizer report |

The two fingerprints match, so the PEXT and magic fills publish the same attack sets.

### The same test still sees the old race

Linked against `attacks::init` from `f0c240004` (`edc598b7c^`), which is the unsynchronized flag:

```cpp
static bool initialized = false;
if (initialized) return;
initialized = true;
```

ThreadSanitizer, same driver, `FORGE_SPD_SLIDER_PEXT=0`, exit **66**:

```text
WARNING: ThreadSanitizer: data race (pid=2648)
  Write of size 1 at 0x557d9ddd0a80 by thread T1:
    #0 forge::attacks::init() /tmp/bitboard_before_call_once.cpp:139
  Previous read of size 1 at 0x557d9ddd0a80 by thread T3:
    #0 forge::attacks::init() /tmp/bitboard_before_call_once.cpp:138
  Location is global 'forge::attacks::init()::initialized' of size 1
SUMMARY: ThreadSanitizer: data race /tmp/bitboard_before_call_once.cpp:139 in forge::attacks::init()
```

Line 138 is the read of `initialized`. Line 139 is the write, and it happens before the tables are filled. That binary is not in the tree. On `e04556ddc` the same driver does not report a race.

## Depth-10 searches

`forge-combo29/tests_r4_06/depth10_legal.cpp`, 200 searches, depth 10, Hash 16, one thread, lock switches (`FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `-march=x86-64-v4`), `-fsanitize=address,undefined`, `halt_on_error=1`, leak detection on.

Each best move is one of the root legal moves, and the king is not left in check (king moves and castling use `move.to` as the king's destination). Every PV move must pass the same check in sequence. A failure returns 1. A sanitizer finding aborts.

```text
search 1 depth 10 move d2d4 pv 11
...
search 200 depth 10 move g7h6 pv 11
PASS 200 depth-10 searches, every move legal
```

Exit 0. The log has no ASan, UBSan, or LeakSanitizer diagnostic.

## Release pins

```text
cmake -S forge-combo29 -B /tmp/forge-r4-pins -DCMAKE_BUILD_TYPE=Release
```

with `CXX=g++` (default march `x86-64-v4`, portable off). Then Threads 1, Hash 16, OwnBook false:

```text
info string bench depth 11 nodes 312866 time 258 nps 1212658
info string bench depth 13 nodes 862329 time 732 nps 1178045
nodes 4865609
```

## Files

- `forge-combo29/tests_r4_06/concurrent_board_init.cpp`
- `forge-combo29/tests_r4_06/depth10_legal.cpp`
- `forge-combo29/REPORT_r4_06.md`

There was no engine change. Nothing under `forge-combo29/src`, `forge-combo29/include`, or `CMakeLists.txt` differs from `e04556ddc`.

R4 DONE cfc321ec4c115434a55e4ab2b8d97266edccd6ee
