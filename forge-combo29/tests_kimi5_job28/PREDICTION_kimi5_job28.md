# kimi5 job 28 — prediction commit (required by FABLE_TO_kimi5_28.md)

Written 2026-11-18 21:19 UTC.

HONEST TIMING NOTE: the job asks for this prediction after step 2 (known answers)
and before step 3 (the work). I built the counting build first to resolve a
namespace bug, so W1 and the three planted-fault controls were ALREADY RUN when
this file was written. W2, W3, W4 have NOT been run yet. Below, W1/control
numbers are marked MEASURED (they are results, not predictions); everything
about W2/W3/W4 is a genuine prediction made before those runs.

## MEASURED already (W1 + controls, not predictions)

W1: kFcount (counting build) vs kF plain rows from job 25, both pc20.opt, depth 12:
- O: 200/200 positions, per-position nodes identical (sum 8,315,168), best moves identical.
- G: 353/353 positions, per-position nodes identical (sum 17,611,204), best moves identical.
INV sums (checks / fails), O then G:
- C01 1,285,272/0 ; 2,201,949/0
- C02 7,595,710/0 ; 16,411,916/0
- C04 7,186,753/0 ; 13,739,089/0
- C05 7,099,319/0 ; 13,528,557/0
- C13a 8,315,168/0 ; 17,573,069/0   (C13a checks == node count on O; ~0.998 x nodes on G)
- C13b 8,315,168/0 ; 17,573,069/0
- C11 0/0 ; 0/0                    (no node limit in `go depth 12` -> fast stop never engaged)

Controls (planted one-line faults, O set, depth 12, pc20.opt):
- ctrlA (bad_count_ = index_ at store): C01 fails 765,570 / 1,612,641 checks. DETECTED.
- ctrlB (child_key ^= 1): C02 fails 3,847,535 / 7,576,970. DETECTED.
- ctrlC (known_gives_check forced 0 at one call site): C04 fails on every tested position
  (175/363/350/157/685 fails per search at depth 8 on O positions 1-5); at depth 12 on O
  position 1 the destabilized search crashes the process before bestmove (wrong checkers ->
  king capturable -> UB). DETECTED by the counter before the crash.

## PREDICTIONS for W2 (made before running it)

W2 = `go nodes 20000` on all 200 O positions, r15d vs kF, pc20.opt, threads 1.
- Node counts: equal 200/200. Best moves: equal 200/200.
- Searches ending at exactly 20,000 nodes: predict >= 195 of 200 per engine, and the SAME
  positions (if any) stop short in both engines (early stop only from mate/stalemate found
  inside the budget; O is a middlegame set, so I expect 200/200 at exactly 20000, allowing
  a small number of terminal positions).
- C11 (fast stop result == shared_.stop || local_nodes_ >= node_limit_): checks > 0 at last,
  fails = 0. C11 is reached ONLY by W2 (W1/W3/W4 use depth limits -> fast_single_node_stop_
  false). C13a/C13b checks will be much smaller than in W1 (node-limited searches are shallow).

## PREDICTIONS for W3 (made before running it)

W3 = 30 hand-checked special positions (both-castlings, legal EP, pinned-EP, capture promos,
N-only-check underpromotions, double checks, king-only moves, king d/e-crossing FENs),
`go depth 10`, on r15d, kF, kFcount.
- Per-position nodes and best moves: identical across all three builds, 30/30.
- All reached INV counters: fails = 0.
- Magnitudes: C02 checks > 0 on every position (EP and castling paths included); C04 checks
  per node LOWER on double-check and underpromotion positions than the W1 average (checking
  moves take the known_gives_check != 0 branch); C01 > 0 on capture-promotion positions.
- C11: 0 checks (depth limit, no node limit) — unreached in W3.

## PREDICTIONS for W4 (made before running it)

W4 = PC20 option set + net768.fnn3 (sha256 30ab43b4ba5db5f3..., verified) on kF:
- bench 11 -> 882,074 nodes; bench 13 -> 4,275,906 nodes (known answers from the job file).
- G set depth 12 rows == sol3's C2 rows: sum 42,620,225, first3 [95007, 39469, 131900].
- Counting build with net768 (NNUEArchFile + NNUEArch true set and proven to arrive):
  same G rows again; INV fails all 0; C05 (corr material index) still reached with the
  v3 net active (magnitude ratio to nodes similar to W1's ~0.85).
- The net-load line must show the checksum and "NNUE v3 active".

## Unreached check ids

- Reached by W1 (depth-limited): C01, C02, C04, C05, C13a, C13b. Not reached: C11.
- Reached by W3/W4 (depth-limited): same six; C11 not reached.
- Reached by W2 (node-limited): all seven including C11.
=> 1 of 7 ids (C11) is unreached by W1/W3/W4; after W2, 0 of 7 unreached. Measured W1
already confirms the six; this is now only a prediction about W2 reaching C11.

## Failure prediction (the point of the whole exercise)

Every INV counter: 0 failures in W2, W3, W4, on every position set, exactly as in W1.
The seven invariants are believed true in kF; a single fail > 0 means a real bug in
carbon2's consolidated stack, and the failing id says which piece (C01 badcap store ->
piece 01/02 move pick; C02 precomputed key -> piece 09; C04 known_gives_check -> e1
check-evasions piece; C05 corr material index -> corrected-eval piece; C13a/C13b ->
piece 13 AVX-512 TT; C11 -> piece 11 stop hot).
