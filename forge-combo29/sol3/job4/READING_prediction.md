# Job 4 Step 2 — source reading and prediction

Source is the reconstructed k11 tree with the stop-hot patch SHA-256 `c00d8d79e70d70afcee6dd45459eb833db7d39c991bd23cb508db65f65c31b9e`. Line numbers refer to that tree unless k10 is named. This reading was prepared before any search in the Step 3 cells.

## Limits and fast-path selection

The defaults are depth 64, zero `nodes` with no node limit specified, soft mode false, and no clock (`include/forge/search.hpp:29–39`). `src/uci.cpp:255–273` sets depth for `depth` and the node value and specified flag for `nodes` or `softnodes`. It sets `soft_nodes` only for `softnodes`. `src/uci.cpp:860–865` uses that parser, copies the UCI MultiPV setting and sets the clock origin only for clocked requests.

| UCI command | Hard node limit | Finished-iteration target | `fast_single_node_stop_` at a searchable root |
| --- | ---: | ---: | --- |
| `go depth 10` | No node limit | None | False |
| `go nodes 20000` | 20000 | None | True |
| `go softnodes 2000` | 8000 | 2000 | True |

`src/search.cpp:3026–3045` initializes the node limits and sets the four-times hard cap for soft mode. `src/search.cpp:3050–3064` leaves effective clock limits zero for these commands. `src/search.cpp:3263–3265` enables the fast branch with no parent, MultiPV 1, one worker, a specified node limit and no effective hard clock. `go depth 8` follows the depth-only branch too. Terminal and restricted-empty roots can return through `src/search.cpp:3172–3192` before the guard is evaluated, so the fast path does not participate in those roots.

## Count ownership and readers

- `src/search.cpp:1894–1901` initializes `total_nodes()` from this worker’s `local_nodes_` and adds published counts only for another worker. The `info depth` emitter uses that total at `3092–3098` and prints it at `3132–3133`. MultiPV 1 leaves the node override unset (`3085–3090`) and emits at `3523–3524` after a completed iteration.
- The normal iteration result uses `total_nodes()` at `3442`. After the loop, `3611–3612` writes the current local count to the atomic and assigns `total_nodes() + extra_nodes_` to final `SearchInfo.nodes`. `extra_nodes_` is initialized to zero at `3005` and its alternate-line additions sit under the MultiPV branch starting at `3443`. The early result uses `total_nodes()` at `3187–3188` as well. The soft target is tested against the local total after completed iterations at `3533–3537`. `3623–3631` emits the final total in the distinct `info string softnodes nodes ...` line. The UCI worker at `src/uci.cpp:430–449` emits the result’s `bestmove` and optional ponder move.
- The sole load of the published `nodes_` is `Worker::nodes()` at `include/forge/search.hpp:482`. Its sole caller in this tree is `src/search.cpp:1894–1901`, which excludes the current worker. `3686–3692` includes one worker in the tested configuration, and `3719–3733` resets the counts and starts no helper. There is no live reader of this atomic in any tested one-thread, MultiPV-1 search. `should_stop()` publishes at `1943–1948`; its limit decision at `1904–1915` uses `total_nodes()`. The parent case passes unpublished local nodes and is inactive here.
- k10 calls the full stop check every node with a specified node limit (`src/search.cpp:2135,2287` in k10). k11’s `include/forge/search.hpp:649–656` checks the same stop flag alone at nonmultiples of 1024 below the cap, and calls the full test at every multiple of 1024 and at or above the cap. Both search entry sites check before incrementing `local_nodes_` (`src/search.cpp:2132–2140,2277–2292`). No external `stop` or clock is sent, and the test hook defaults to zero (`src/search.cpp:80–84`). The reduced publication cadence has no count consumer in this contract.

## Predictions before Step 3

| k11 compared with k10 | Expected equal rows | Expected differences |
| --- | ---: | --- |
| B2, built-in `go nodes 20000` | 389/389 | None |
| B3, built-in `go softnodes 2000` | 389/389 | None |
| N2, net768 `go nodes 20000` | 389/389 | None |
| N3, net768 `go softnodes 2000` | 389/389 | None |
| ND, net768 `go depth 8` | 389/389 | None |

For P, I predict ND stays identical. Both caps are nonmultiples of 1024. Changing `<` to `<=` admits one additional counted entry at the cap if the search reaches that check. If search reaches a subsequent checked entry at cap plus one, the limit guard fails and calls the full test immediately. A root-level full check may also stop the search. The reported hard-node row will usually remain identical because interruption keeps the last completed iteration (`src/search.cpp:3406–3442`). A row could change if the additional work completes an iteration. My prediction for this fixture is zero visible B2 or N2 row changes, which would fail the requested P gate. The soft cells may expose the fault in their final `info string softnodes nodes ...` totals for searches that reach the hard cap. I will preserve and inspect those totals separately from the declared rows.

Recorded 2026-11-18T08:58:01Z using the cloud clock.
