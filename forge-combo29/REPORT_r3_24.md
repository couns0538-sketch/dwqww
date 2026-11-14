# Report r3-24: hash-table duplicate shadow

- Repository: `github.com/couns0538-sketch/dwqww`
- Base: `origin/integrate/combo29-all` at `e04556ddc3a430b2e751159b0d46111ef56c8b89`
- Branch: `grok47/r3-24-tt-duplicate-shadow`
- Engine: `forge-combo29`

## Where the idea comes from

Audit finding 8 on read-only branch `audit/lock-source` at commit `302a08a272fbe8e8c4463731f3b9cd72d72d3f48`, in `forge-combo29/AUDIT_lock_source.md`. The failing sequence is the proof `forge-combo29/tests_audit/proof_tt_duplicate_shadow.cpp` on that commit. This branch does not modify `audit/lock-source`. That proof is kept, with a pass/fail check, at `forge-combo29/tests_r3_24/proof_tt_duplicate_shadow.cpp`. The two-thread form is `forge-combo29/tests_r3_24/proof_tt_two_threads.cpp`.

## What was wrong

`TranspositionTable::probe` remembers a slot, then search continues, then `store` writes only that slot. The slot can be stale:

1. A miss on `key_a` selects an empty slot.
2. A different key in the same 4-entry cluster is stored into that slot.
3. A later probe of `key_a` selects another slot and stores a deep entry.
4. The first search stores a shallow result through the original probe. `same_position` is false, so the depth guard does not apply, and a second copy of `key_a` is written.
5. The next probe walks the cluster from the front and returns the shallow copy. The deeper entry stays in the table and is never seen.

With `Threads` greater than 1 the main worker does not take the exclusive lease, so both workers use the locked `store`. One worker can hold a probe while the other fills that slot and writes the same position elsewhere. The original proof builds that slot sequence on one thread. The two-thread proof runs it on two threads.

## Change

In both store implementations (`store_body`, used when `FORGE_SPD_TT_NOTLS` is 1, and `store` in the other build), after the stripe lock is taken, the cluster is scanned for an occupied entry with this verification key. If one exists, that entry is the one updated. Otherwise the probe-time slot is used, as before.

The replacement rule is unchanged: an exact bound, a different position, `depth + 4` above the stored depth, or a generation change still replaces the payload. A shallow non-exact store therefore does not overwrite a deeper score once it is aimed at the real entry.

A same-slot store still refreshes the move when the new score is rejected. That is the old rule. A stale slot does not: a rejected shallow store leaves the deeper move, eval, depth, bound, and score alone. The first cut of this fix aimed the write at the right entry but still copied the shallow move onto it (the kept move was `8->16` with score 777). The pins were rechecked after that second change.

No UCI option. The fix is always on. The three default pins did not move.

`CMakeLists.txt` is unchanged. The tests are not CMake targets.

## Pins

Commands, with Threads 1, Hash 16, OwnBook false, and every other option left at default. `bench` builds its own 16 MB searcher. Measured with `g++` 13.3.0 and `CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. The machine's `c++` is Clang 18. That configure fails at link (`-lstdc++` is missing). Clang also does not see the C++ headers here, so the pins were not repeated with Clang.

Rechecked after the move-preserve change, on the same binary flags:

- `go perft 5` from the start position: 4865609
- `bench 11`: 312866
- `bench 13`: 862329

Same three numbers as before any edit.

## Proofs

Single-thread proof, ASan + UBSan, `FORGE_SPD_TT_NOTLS=1`: after the late shallow store, `probe(key_a)` is depth 14, score 777, exact, move `6->21`, pv still set, and the colliding key is still depth 3, score 15. The same run then checks the opposite order, where the stale probe carries the depth-14 exact store. Exit 0. The same file compiled without `FORGE_SPD_TT_NOTLS` also exits 0. On the unfixed table the late probe was depth 2, score -50.

Two-thread proof (`proof_tt_two_threads.cpp`), keys checked to share a cluster under the 1 MB multiply-high index:

- 20000 rounds on two threads of unordered probe/store, then a joined probe. ASan and TSan.
- 100 ordered interleavings: thread A holds the miss probe, thread B writes the colliding key and the depth-14 score, thread A stores depth 2. The kept entry is depth 14, score 777, move `6->21`, and the colliding key remains. ASan and TSan. The single-thread proof also checks that this rejected store leaves the pv bit set.
- The other order, single-threaded and 100 times on two threads: the stale probe is the depth-14 exact store, and a shallow entry is already in the other slot. The exact store replaces that shallow entry (score 777, move `6->21`, eval 100) and leaves the colliding key in place. ASan and TSan. The locked `store` path (no `FORGE_SPD_TT_NOTLS`) passes the same two-thread file under ASan.
- `Searcher` with 2 workers, depth 4, shared access and exclusive access. Both return a legal start-position move. Node counts move between runs (thread order). ASan and TSan, and again with `FORGE_SPD_TT_NOTLS` left at 0.
- UCI `setoption name Threads value 2`, Hash 16, OwnBook false, `go depth 4` from the start position printed `bestmove a2a3`.

## Not verified

- Node counts under Clang, or with Hash or Threads other than the single-thread pins. Two-thread search node counts are not stable and are not pins.
- Games or strength.
- A table that already contains two copies of one key. New stores will not create that pair; an older shallow copy in an earlier slot would still be what probe returns.
