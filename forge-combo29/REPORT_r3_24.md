# Report r3-24: hash-table duplicate shadow

- Repository: `github.com/couns0538-sketch/dwqww`
- Base: `origin/integrate/combo29-all` at `e04556ddc3a430b2e751159b0d46111ef56c8b89`
- Branch: `grok47/r3-24-tt-duplicate-shadow`
- Engine: `forge-combo29`

## Where the idea comes from

Audit finding 8 on read-only branch `audit/lock-source` at commit `302a08a272fbe8e8c4463731f3b9cd72d72d3f48`, in `forge-combo29/AUDIT_lock_source.md`. The failing sequence is the proof `forge-combo29/tests_audit/proof_tt_duplicate_shadow.cpp` on that commit. This branch does not modify `audit/lock-source`. The proof is kept, with a pass/fail check, at `forge-combo29/tests_r3_24/proof_tt_duplicate_shadow.cpp`.

## What was wrong

`TranspositionTable::probe` remembers a slot, then search continues, then `store` writes only that slot. The slot can be stale:

1. A miss on `key_a` selects an empty slot.
2. A different key in the same 4-entry cluster is stored into that slot.
3. A later probe of `key_a` selects another slot and stores a deep entry.
4. The first search stores a shallow result through the original probe. `same_position` is false, so the depth guard does not apply, and a second copy of `key_a` is written.
5. The next probe walks the cluster from the front and returns the shallow copy. The deeper entry stays in the table and is never seen.

That happens when a helper thread, or a nested search of the same position, stores `key_a` before the outer store. The proof builds that slot sequence on one thread.

## Change

In both store implementations (`store_body`, used when `FORGE_SPD_TT_NOTLS` is 1, and `store` in the other build), after the stripe lock is taken, the cluster is scanned for an occupied entry with this verification key. If one exists, that entry is updated. Otherwise the probe-time slot is used, as before.

The existing replacement rule is unchanged: an exact bound, a different position, `depth + 4` above the stored depth, or a generation change still replaces the payload. A shallow non-exact store therefore does not overwrite a deeper score once it is aimed at the real entry. A store that is not admitted still replaces the move on that entry. That was already the same-position rule; it is not a second copy.

No UCI option. The fix is always on. The three default pins did not move, so there was no reason to leave it off.

`CMakeLists.txt` is unchanged. The test is not part of the CMake target.

## Pins

Commands, with Threads 1, Hash 16, OwnBook false, and every other option left at default. `bench` builds its own 16 MB searcher. Measured with `g++` 13.3.0 and `CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. The machine's `c++` is Clang 18. That configure fails at link (`-lstdc++` is missing). Clang also does not see the C++ headers here, so the pins were not repeated with Clang.

Before the edit:

- `go perft 5` from the start position: 4865609
- `bench 11`: 312866
- `bench 13`: 862329

After the edit, same three numbers.

## Proof

```text
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_r3_24/proof_tt_duplicate_shadow.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_tt_duplicate_shadow
```

Result: after the late shallow store, `probe(key_a)` is still depth 14, score 777, exact, and the colliding key is still depth 3, score 15. Exit status 0. The same source compiled without `FORGE_SPD_TT_NOTLS` (the locked `store` path) also exits 0. On the unfixed table the late probe was depth 2, score -50.

## Not verified

- A live two-thread race. The proof is the slot sequence, run on one thread, not a stress test of `Threads` greater than 1.
- Node counts under Clang, or with Hash or Threads other than the pin settings.
- Games or strength.
