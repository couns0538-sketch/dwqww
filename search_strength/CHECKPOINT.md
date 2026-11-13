# Search-strength checkpoint 1

Date: 2026-11-13. This file is a measurement record. It is not an Elo result and it does not promote a candidate.

## Source identities

- Base branch: `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a` (subject: JOB E after the report, M9 result). This branch was cut from that commit.
- Working branch: `cursor/forge-search-strength-20261113-9558`. Nothing here is pushed to `main`, `lock/combo29-20261110`, the Fable branch, or another agent's branch.
- Lock the pins are taken from: `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`, recorded in `forge-combo29/LOCK.md`.
- Search-gap dossier that specified this probe: `fable52-search-gap-20261109` at `56a76b153bb88026f2d83d65df6e422b0f3298f9`. Read here: `FALSIFICATION.md` section 3, `NO_QUALIFIED_GAP.md`, `IDEA_SOURCE.md`, and `DEDUPE.md` (the ETC row and section 4). The dossier's own verdict remains **no qualified gap**. Its replica did not show a node saving (336 positions, 6 plies, node ratio 0.987, range 0.954 to 1.022).
- History-index agent, read and not written: `cursor/forge-history-index-20261113-712a` at `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0`. Files read: `docs/history-index/findings/SEARCH.md`, `HANDOFF.md`, `RESUME.md`. That index says not to write an ETC spec unless this counting run hits the "write the spec" line inside the real lock search. No other 2026-11-13 branch from the correctness, NNUE, or evidence agents was on `origin` at the fetch that found this index.
- A search of every fetched tip for `FORGE_ETC`, `EtcDepth`, and `enhanced transposition` found those strings only in the search-gap dossier and in that history index. No earlier implementation of this probe is in the fetched tips.

## What changed

Two compile switches, both default off, in `forge-combo29/CMakeLists.txt`:

- `FORGE_ETC_STATS`: count enhanced-transposition opportunities. It takes no cutoff.
- `FORGE_CONT4_READ`: add the ply-4 continuation history, which `update_continuation` already writes at half bonus, to quiet ordering. Wired in this checkpoint. Not built or measured yet.

`Board::plies_from_null()` is a const accessor used by the probe's repetition test. With `FORGE_ETC_STATS` off, search does not call it.

The probe sits after the node's own table cutoff and before static eval, at threshold depth 8, on non-PV cut nodes with no excluded move, a non-mate beta, and a half-move clock under 90. A child counts only when its table entry is upper or exact, usable at the child's clock, the score from the child's point of view is at or below minus beta, the child clock is under 90, and the child is not a repetition under `is_repetition(root_index)`. Depth rule: `depth - 1`, plus one for a safe check, and `depth + 1` for the hash move. `hits_loose` uses `depth - 1` for the hash move as well. `hits_hash_move` counts a hit whose first proving child, in move-picker order, is the hash move.

`key_after` returns false when the node has an en-passant square, the move is an en passant, or a double push would create an en-passant key. Those children are made and unmade. Every other child is probed from `key_after` with no make/unmake. `FORGE_ETC_AUDIT` (default 0, not a CMake option) also makes the fast-path children and counts key, clock, and repetition disagreements.

## Build

Portable cloud build, not the Windows lock recipe:

`cmake -S forge-combo29 -B <dir> -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`

g++ 13.3.0. `FORGE_PORTABLE` drops `FORGE_SPD_SLIDER_PEXT` and `FORGE_SPD_NNUE_ZMM`. CMake still sets `NDEBUG`, `FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `-O3 -ffp-contract=off -fno-fast-math`.

Binaries used for the numbers below live under `/tmp` and are not committed: `/tmp/forge-plain/forge` (both switches off) and `/tmp/forge-etc/forge` (`FORGE_ETC_STATS=ON` only).

## Tests that are node identity, not speed and not Elo

`forge-combo29/scripts/check_pins.sh` on both binaries. The script was read before it was run. It checks bench node counts and startpos `perft 5` only.

| Binary | Result |
|---|---|
| plain, switches off | `PINS MATCH combo29` |
| `FORGE_ETC_STATS=ON` | `PINS MATCH combo29` |

Net on, depths 11/13/16/20/22: 312866 / 862329 / 3024920 / 12389307 / 34048354. Net off: 375354 / 907205 / 2448617 / 13573040 / 24506465. Startpos `perft 5`: 4865609. Every timed rep below also printed those same node counts at depths 16, 20, and 22.

Kiwipete `perft 5` (`r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`) on the plain binary printed `nodes 193690690`, the count named in the dossier's section 5. `check_pins.sh` does not check it. The counting binary was not given a separate kiwipete run; perft does not enter the search.

Audit build, `-DFORGE_ETC_AUDIT=1`, bench 13 and bench 16, net on: `clock_mismatch`, `key_mismatch`, and `repeat_mismatch` were 0, and the hit counters matched the fast-path binary exactly (bench 13: 77 hits, 2348 below; bench 16: 1289 hits, 52694 below). The full pin suite on the non-audit binary also has `clock_mismatch` 0 at every depth. That counter is the slow path only. Depths 20 and 22 were not re-made move by move.

## Counters

`top_hits_fail_high / top_hits` is 1 at every row. The dossier's "stop and investigate" line (under 99%) does not fire on this bench set. Fail-high is compared with the beta passed into the call, before mate-distance pruning. That bar is at least as high as the beta the search uses after pruning.

Net on:

| Depth | Eligible | Lookups | Hits | Hits loose | Hash-move hits | Mate hits | Top hits | Below | Below/nodes |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 829 | 25548 | 9 | 69 | 4 | 0 | 9 | 579 | 0.185% |
| 13 | 3924 | 120191 | 77 | 300 | 13 | 0 | 77 | 2348 | 0.272% |
| 16 | 26486 | 727953 | 1289 | 2684 | 216 | 0 | 1221 | 52694 | 1.742% |
| 20 | 163630 | 4274472 | 19257 | 27503 | 3727 | 17 | 16593 | 674214 | 5.442% |
| 22 | 565961 | 13228812 | 105363 | 134959 | 23248 | 471 | 81280 | 3433490 | 10.084% |

Net off, same depths, below/nodes: 0.055%, 0.440%, 0.933%, 4.939%, 4.717%. Top-hit fail-high equals top hits in every net-off row as well. Mate hits are 0, 0, 0, 1, 3.

`key_after` was incomplete for 310919 of 4278215 children at depth 20 net on (7.27%), and 877703 of 13244881 at depth 22 (6.63%). Those children were still probed.

## Timing

This is a wall-clock comparison of two processes on one cloud vCPU (`taskset -c 0`), four interleaved repetitions, order plain/etc on odd reps and etc/plain on even reps. The clock is Python `time.perf_counter` around the whole process, including startup. It is not a lock NPS result, not a quiet-machine result, and not Elo. The engine's own `nps` field was not used.

Depth 16, milliseconds, plain then etc by rep: 1549.6/1633.1, 1636.2/1651.7, 1565.5/1659.1, 1568.2/1659.0. Pair ratios 1.0539, 1.0095, 1.0598, 1.0579. Mean 1.0453, sample standard deviation 0.0240, standard error 0.0120. Mean overhead about 4.5%. The node share under hit nodes is 1.74%. One pair was only +1.0%, so this depth misses the dossier's "uncertainty under one percentage point" bar.

Depth 20: 5904.2/6443.1, 6130.1/7285.9, 6207.3/6831.3, 6077.2/6775.8. Ratios 1.0913, 1.1885, 1.1005, 1.1150. Mean 1.1238, standard deviation 0.0442, standard error 0.0221. The smallest pair is still +9.1%, against a node share of 5.44%.

Depth 22: 16294.6/17504.9, 15943.3/17336.8, 16605.1/17944.4, 16561.5/17761.2. Ratios 1.0743, 1.0874, 1.0807, 1.0724. Mean 1.0787, standard deviation 0.0068, standard error 0.0034. Mean overhead 7.87%. The node share is 10.08%, which is 2.21 points higher. A rough 95% interval on the overhead is about 7.2% to 8.5%, so the gap's lower end is about 1.5 points. The point estimate clears the dossier's 2-point line; the interval does not.

An earlier probe that made and unmade every child, not pinned to one core and not the measurement used above, was slower: depth 16 pair ratios about 1.062, 1.086, 1.061, 1.022, and depth 20 about 1.096, 1.094, 1.097, 1.105. The `key_after` path replaced it after the audit.

## Decision

The dossier's rule applies to gate-game positions, weighted by time or nodes spent, as one set. No gate PGNs are in this checkout, so the rule cannot formally close the idea or demand a spec.

On the bench positions the dossier named:

- Depth 16 and depth 20: the share of nodes under proving children is smaller than the measured lookup time. That is the "close" direction. Depth 16 is noisy. Depth 20 is not: every pair costs more than the node share.
- Depth 22, which the rule does not single out: the point estimate goes the other way by 2.2 points, and the lower end of a rough interval is under 2 points.

No cutoff was implemented. `FORGE_ETC` and `EtcDepth` stay unused. Mate-score child entries were counted, as section 3 says, and were not used to change the tree. Section 6 would forbid using them in a later cutoff.

## Not done

- `FORGE_CONT4_READ` is compiled in only when requested. No binary and no node counts for it yet.
- No match, no SPRT, no fixed-node Elo.
- No 300-position gate sample.
- Threads above 1 and hash above 16 MB were not run. The bench searcher uses hash 16.

## Next

Measure `FORGE_CONT4_READ` against the plain binary: pins stay on the off build, and the on build is recorded as node counts and best moves on the eight bench positions. That is an observation about whether the unused ply-4 history changes ordering. It is not an Elo claim. Do not start an ETC cutoff from the bench numbers above.
