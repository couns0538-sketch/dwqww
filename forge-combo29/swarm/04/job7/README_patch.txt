DIAGNOSTIC TEXT PATCH — job7, seat 04

What it does: adds ONE diagnostic print to Searcher::search, after all helper threads are joined, so it
cannot affect the tree or the node counts. Prints:

  info string diagworkers n <k> nodes <n0> <n1> ... sum <S> total <T> argmax <i> maxshare <permille> hashfull <h>

  n        number of workers
  nodes    per-worker node count (worker 0 is the main thread)
  sum      their sum, which equals `total` (total_nodes() sums the same counters)
  argmax   index of the worker that did the most work
  maxshare the dominant worker's share of the total, in permille
  hashfull the shared table's fill at the end of the search

How to apply (against the PC r15 tree, i.e. after pc_r15.patch), from the repository root:
  cd forge-combo29
  patch -p0 < <this file>
How to build:
  cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_DIAG_WORKERS=1"

Verification I performed:
  * the patch applied to a fresh base+pc_r15 copy reproduces my instrumented src/search.cpp BYTE FOR BYTE
    (diff -q reports no difference);
  * the instrumented build still gives the three honesty pins unchanged:
    bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920.
  So the diagnostic is inert with respect to search behaviour. Without -DFORGE_DIAG_WORKERS=1 the added
  lines compile out and the source behaves exactly as before.

This is a DIAGNOSTIC patch, not a repair. It is committed as text only, per the rules.
