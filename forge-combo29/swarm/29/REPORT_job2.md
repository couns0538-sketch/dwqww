# REPORT job2 - one speed patch that changes no node count (area 9, seat 29)

what was asked: ONE speed change as a TEXT PATCH that changes NO node count (bench 11, 13, 16 and perft 5
identical) and is faster; 10 runs of `bench 13` alternating base and patch, nodes per second each, mean and a
95 % interval of the ratio; each side built TWICE.
the answer: I built, proved and measured one such patch (`pinned_only_king_lines.patch.txt`). It changes no node
count and is bit-identical in score/PV/bestmove, but it is NOT measurably faster: paired ratio 1.0178 with 95 % CI
[0.9842, 1.0569], i.e. indistinguishable from noise, and an exact instruction count (callgrind) moves by only
0.056 %. I report that plainly instead of claiming a win. A second candidate (`__restrict`) was a dud and was
discarded without a report of its own.
how sure: high (two proof methods agree: bit-exact search output and an exact instruction count; the timing CI
spans 1.0 both ways).

## honesty numbers
Build: `/home/ubuntu/build/base/forge`, sha256 `e06310ec...6a83`, `id name Chess Engine Forge 6.4.24 candidate`.
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609 — all four match (HONESTY.txt).
Patch builds: `2442a980fed00320aed8a8a20edde027dab3e9d5e053ff984712db1b971832a0` (patchA and patchB are the same
bytes, so "two builds of one source" happened to be byte-identical here — see "what I am NOT sure about").

## a table: step | done-partly-not done | evidence file | result

| step | done? | evidence | result |
|---|---|---|---|
| profile candidates, pick a target | done | `raw_perf_flat_full.txt`, `raw_callgrind_annotated.txt` | eval 38.7 %, movepicking 25 %, TT 1.3 % |
| candidate 1: `__restrict` on the pawn-cache pointer | done, REJECTED | `raw_callgrind_lines.txt` | instruction count +0.006 % = no effect |
| candidate 2: pinned-only king-lines refresh | done | `pinned_only_king_lines.patch.txt` | applies `patch -p1` without fuzz |
| node counts unchanged (11/13/16, perft 5) | done | `raw_nodes_patched.txt` | 312866 / 862329 / 3024920 / 4865609 — identical |
| perft equivalence, 65 positions x depth 3,4 | done | `raw_equiv_perft.txt` | 130/130 agree, 0 differences |
| search equivalence, 40 positions x depth 10 | done | `raw_equiv_search.txt` | 40/40 agree; nodes, score, PV, bestmove identical |
| exact instruction count, base vs patch | done | `raw_ir_count.txt` | 4,513,768,536 -> 4,511,262,314 (-0.056 %) |
| call-count proof the patch does what it claims | done | `raw_call_counts.txt` | full refresh 804,371 -> 341,148; cheap refresh 786,795 |
| paired speed test, 2 builds per side, interleaved | done | `raw_paired_pinned.txt` | ratio 1.0178, 95 % CI [0.9842, 1.0569] = no speedup |
| a patch that IS faster | **NOT DONE** | — | see "what I did NOT do" |

## the patch

`pinned_only_king_lines.patch.txt` — unified diff against 6b98f217, applies at the repository root with

```bash
cd <a clean checkout of 6b98f217> && patch -p1 --dry-run < pinned_only_king_lines.patch.txt
# checking file forge-combo29/include/forge/board.hpp
# checking file forge-combo29/src/board.cpp
```

What it does: `Board::has_legal_move()` calls `is_legal()`, which needs only `king_lines_.pinned`. The existing
`refresh_king_lines()` also computes the discoverer set and five check-square sets (five magic lookups) and throws
them away. The patch adds a `king_pinned_valid_` flag and a `refresh_king_pinned()` that computes only `pinned`;
`is_legal()` and `is_legal_complete()` accept either cache state. `gives_check()` still forces the full refresh.
Invalidation is paired with the existing `king_lines_.valid = false` at every site, and `unmake_move` /
`unmake_null_move` set the flag from the restored `king_lines_.valid`.

Why it must be bit-identical: the value of `pinned` is computed by the same `single_blockers()` call on the same
board, and nothing else that the refresh computes is read on that path. Measured: 40/40 positions agree at depth
10 including the node count.

## the measurement (the part that decides it)

```bash
cd forge-combo29/swarm/29/job2
python3 paired_interleaved.py ~/build/baseA/forge ~/build/baseB/forge ~/build/patchA/forge ~/build/patchB/forge
```

| metric | value |
|---|---|
| design | 12 rounds, ABBA order, both sides built twice, 24 pairs |
| base median | 441.0 ms |
| patch median | 441.5 ms |
| patched/base mean ratio | 1.0178 |
| 95 % CI (paired bootstrap, 10000 resamples) | [0.9842, 1.0569] |
| verdict | INDISTINGUISHABLE |

The earlier non-interleaved design (10 runs of A then 10 of B) reported "+3.6 % / +8.6 % speedup". That was an
artefact: other swarm seats share these 4 cores and the patch builds happened to run in a quiet window. The
interleaved design, which alternates inside every round, shows the truth. I am reporting the interleaved number.

Exact instruction count (independent of machine load, so it cannot be fooled by drift):

```bash
# portable+(-g) builds of both sides, callgrind, bench 13
valgrind --tool=callgrind --callgrind-out-file=/tmp/cgx_portableg.out .../portableg/forge
valgrind --tool=callgrind --callgrind-out-file=/tmp/cgx_patchg.out    .../patchg/forge
# PROGRAM TOTALS: 4,513,768,536  vs  4,511,262,314   (-0.056 %)
```

-0.056 % of instructions cannot produce a 3 % speedup. The patch is real but tiny.

## findings
| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 29-F3 | 9 | A depth-independent 14 ms of every `bench N` report is one-time work inside the bench timer (the `Searcher` is constructed, and its 16 MB transposition table cleared 8 times, after `start` is taken), which is 3.2 % of a `bench 13` report and 1.0 % of a `bench 16` report, so nps figures from shallower benches are systematically understated relative to deeper ones. | `forge-combo29/swarm/29/job2/bench_fixed_cost.py` | NEW |
| 29-F4 | 9 | `Board::refresh_king_lines()` is called 804,371 times per `bench 13` and 779,027 of those come from `has_legal_move()`, which reads only the `pinned` field; the discoverer set and five magic-based check-square sets computed there are discarded on that path (a patch can avoid it, but it is worth only 0.056 % of instructions). | `forge-combo29/swarm/29/job2/raw_call_counts.txt` | NEW |

## suspicions, not proven
- The bench timer starting before the searcher is constructed (F3) could also be read as a *deliberate* choice so
  that `bench` numbers include realistic cold-table behaviour. I did not ask anyone; I only state what the code
  does (`src/uci.cpp:610` next to `src/uci.cpp:611`).
- `bench` also calls `clear()` per position (`src/uci.cpp:617`), so the 8 cleared tables are 8 x 16 MB of zeros.
  Whether the 14 ms is dominated by that or by the magic initialisation I did not separate: callgrind says the
  memset is 227 M instructions regardless of bench depth, which is the whole 14 ms and more, so memset is the
  dominant term.

## what I did NOT do
- **I did not find a patch that is actually faster.** That is the honest headline. The one candidate I proved is
  equal-but-neutral; job 3 is where a bigger lever belongs. I did not keep a patch that only looks faster because
  of measurement noise.
- No PGO/BOLT-style build change (that would change the build recipe, not the source, and the lock recipe is fixed).
- No `-march=native` comparison: the lock sets `x86-64-v4` explicitly and I did not want a speed claim that only
  exists because of a different `-march`.
- I did not profile with hardware events (`cycles`, cache misses): `perf_event_paranoid=2` blocks them for this
  unprivileged user, so all timing attribution is task-clock sampling plus exact instruction counts.

## what I am NOT sure about
- patchA and patchB came out byte-identical, so "two builds of one source differ by ~1.5 %" could not be observed
  on the patch side. Base A and base B were also byte-identical. The build-to-build variation in the timing table
  is therefore machine drift, not compiler nondeterminism, and my CI reflects drift only.
- The 95 % CI is wide (0.984–1.057) because the machine is shared; a smaller true effect than ~5 % could hide in
  it. The instruction count closes that hole for *this* patch (-0.056 % is definitively not a speedup) but not for
  a future patch.
- Whether `has_legal_move`'s witness path benefits at all in real games (as opposed to `bench`'s 8 positions): I
  measured only bench and 40 search positions.

times: see stamps.txt
