# sol3 — Job 11 TT path counts and repetition oracle

**Step 0 passed.** The retained r15d, k11v, k13 and net768 hashes matched. Carbon2 piece 14 at `6ad99573aaf631d4dca979f8185258e1f84ae76b` matched SHA-256 `2f4ae29379db7b77a6d826fdc3b4cdb04d47a311eeac6a8dc715fac38f88657b`. k14 built to `8d43d75191dd33639b5fcb0e31980480a91837595ac96502ed9e6c43ec7e2986`. The PC20 runs loaded net768 checksum `30ab43b4ba5db5f3`. [Input pins](sol3/job11/stage0/input_hashes.txt) · [Build](sol3/job11/stage0/build_14.txt) · [Raw pin readback](sol3/job11/stage0/pins.txt)

| Build | Default bench 11 | Default bench 13 | Default perft 5 | PC20 net768 bench 11 | PC20 net768 bench 13 |
| --- | ---: | ---: | ---: | ---: | ---: |
| k13 | 312866 | 862329 | 4865609 | 882074 | 4275906 |
| k14 | 312866 | 862329 | 4865609 | 882074 | 4275906 |

```text
patching file include/forge/board.hpp
patching file src/board.cpp
patching file src/search.cpp
```

**Prediction grade.** I forecast 33 million probes and 20 million stores. The totals were 35.43 million and 16.38 million, with more matched store destinations than forecast (36.08% versus 25%). The full-miss share was close (0.1133% versus 0.11%). The first helper call was game 0, ply 59, later than the forecast of ply 20. B1 and all four B2 cells matched as predicted. The scan count was 9.73 million versus about 9 million, and 41.98% entered the vector loop versus 5% forecast. C1, C3 and C4 stopped in the first warm-up at game 0, ply 8, before the forecast of ply 16. C2 stopped at game 1, ply 88, before the forecast of ply 130. Optional C5 completed without a mismatch, as predicted. The standalone prediction was pushed at `c9c9bec3623d473f918f111d366fb4cc566e3e6a`. [Prediction](sol3/job11/prediction.txt) · [Checkpoints](sol3/job11/stamps.txt)

### Part A owned-table path coverage

The k13 counting build matched the original k13's seven warm pins and all timed rows. I summed 8613 counter lines, one per search including warm-up. The warm workload used PC20, Threads 1, Hash 16 MiB, MultiPV 1, net768, 60 games generated with seed 20261117, eight opening plies, max 300 plies and `go softnodes 2000` with 8000 hard cap. [Counting patch](sol3/job11/partA/count_tt_paths.patch.txt) · [Build and command](sol3/job11/partA/run.meta) · [Raw per-search lines](sol3/job11/partA/observed.engine.stdout.txt) · [Summing command](sol3/job11/partA/sum_counts.py) · [Totals and first helper call](sol3/job11/partA/totals.json) · [Row comparison](sol3/job11/partA/readback.json)

| Operation | Path | Count | Share of operation |
| --- | --- | ---: | ---: |
| Probe | Hit | 18318413 | 51.70% |
| Probe | Miss with empty slot | 17073669 | 48.19% |
| Probe | Miss in full cluster | 40146 | 0.1133% |
| Probe | Total | 35432228 | 100% |
| Store selection | Matched slot at store time | 5908666 | 36.08% |
| Store selection | Empty supplied slot | 10449445 | 63.80% |
| Store selection | Unmatched occupied supplied slot | 20330 | 0.1241% |
| Store selection | Total | 16378441 | 100% |
| Full-cluster helper | Returned slot 0 | 12636 | 31.48% |
| Full-cluster helper | Returned slot 1 | 11129 | 27.72% |
| Full-cluster helper | Returned slot 2 | 9701 | 24.16% |
| Full-cluster helper | Returned slot 3 | 6680 | 16.64% |
| Full-cluster helper | Total | 40146 | 100% |

The store re-finds a match or uses the supplied slot from its earlier probe. It ran 20296 unmatched stores using a slot originally proposed by a full-cluster miss. This provenance count and the 20330 occupied selections measure the destination at different points in the search. There were zero matched stores whose destination had moved from the supplied slot. The first full-cluster helper call occurred in game 0, ply 59. That search made two full-cluster calls, both returning slot 0, and one carried through to a store. The Job 10 replacement control first changed a recorded output at game 1, ply 143. [Counter definitions](sol3/job11/partA/count_tt_paths.patch.txt) · [Per-search table](sol3/job11/partA/counters.tsv) · [Job 10 control](sol3/job10/step3/C2/warm_gate.txt)

### Part B1 k14 warm workload

The same PC20 net768 workload on k14 matched k13 and the k13 counting build in all 8612 timed rows. [Run command and hashes](sol3/job11/B1/run.meta) · [Independent return and trace readback](sol3/job11/B1/readback.json)

| Builds | Searches | Last-iteration nodes | Legacy trace | Terminal | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| k13, k13 counting and k14 | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |

### Part B2 cold hard-node labels

I applied the Job 5 probe to k14, with a 133-line offset reported by `patch` and no fuzz or reject. k14f SHA-256 is `217bb1a24a497ed1dc326e0451820859c7a20b447fd5f61a15c72eb9ee1d84bc`. The four PC20 cells used Threads 1, Hash 16 MiB, MultiPV 1 and the exact 389-FEN fixture and reset sequence from Job 7. B2 uses embedded AL1 s198 and N2 uses net768. [Build and probe receipt](sol3/job11/B2/build_and_helper.sha256.txt) · [Raw-label checker](sol3/job11/B2/check_cold.py)

| Node limit | Cell | k11f/k14f rows equal | k11f at limit | k14f at limit | Above limit |
| ---: | --- | ---: | ---: | ---: | ---: |
| 50000 | [B2](sol3/job11/B2/50000/B2/gate.txt) | 389/389 | 389 | 389 | 0 |
| 50000 | [N2](sol3/job11/B2/50000/N2/gate.txt) | 389/389 | 389 | 389 | 0 |
| 250000 | [B2](sol3/job11/B2/250000/B2/gate.txt) | 389/389 | 388 | 388 | 0 |
| 250000 | [N2](sol3/job11/B2/250000/N2/gate.txt) | 389/389 | 389 | 389 | 0 |

Both B2 arms again completed fixture row 165 at depth 64 with 220357 nodes, `g1h1` and `mate -4`. [Both raw lines and FEN](sol3/job11/B2/below_limit.txt)

### Part B3 differential repetition check

The B3 scratch build retained the old scan and its separate Cuckoo table helpers. The k13 and r15d source sections for the legacy scan and helpers were byte-identical. The wrapper checks each parity-based scan against that legacy result. At entry to each of the four repetition hooks, it also requires false from the old scan when the old halfmove filter permits the check and the new prefilter rejects it. The original scan guards still determine whether the new scan runs. B3 exited **0** with **zero** difference lines and all 8612 recorded timed rows identical to B1. [Legacy source check](sol3/job11/B3/legacy_scan_source.txt) · [Oracle patch](sol3/job11/B3/repetition_oracle.patch.txt) · [AVX-512 macro](sol3/job11/B3/avx512_macro.txt) · [Exit](sol3/job11/B3/observed.engine_status.json) · [Trace comparison](sol3/job11/B3/readback.json)

| Counter | All 8613 searches | 8612 timed searches |
| --- | ---: | ---: |
| New scan calls | 9726410 | 9726307 |
| True answers | 712154 | 712143 |
| Calls entering the eight-at-a-time loop | 4082690 | 4082690 |
| Candidate checks within that loop | 893313 | 893313 |
| Candidate checks in the scalar tail | 557245 | 557234 |
| Old scan calls for prefilter rejections | 361911 | 361909 |

The count includes one line per search, including warm-up. Vector entry means at least one eight-at-a-time iteration. Candidate counts record calls to the validation predicate after a prefix match. The first vector entry was game 1, ply 81. The first vector candidate check was game 1, ply 88. [Raw counters](sol3/job11/B3/observed.engine.stdout.txt) · [Per-search counter rows](sol3/job11/B3/counters.tsv) · [Totals](sol3/job11/B3/totals.json)

### Part B4 one-line repetition controls

I froze all five control diffs in one commit before building them. Each used B3's PC20 net768 warm workload and the same legacy scanner. The four required controls each emitted one difference line, with legacy true and current false, and exited with code 3. The driver records the game and game ply for the in-flight search. The UCI mismatch line records the internal search ply and FEN. [Freeze and run order](sol3/job11/stamps.txt) · [Exact patches](sol3/job11/B4) · [Mismatch checker](sol3/job11/B4/check_control.py)

| Arm | Planted change | Exit | First phase | Game | Game ply | Internal ply | Old / new |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| [C1](sol3/job11/B4/C1/gate.txt) | Monotonic prefix push in `make_move` | 3 | Warm-up | 0 | 8 | 4 | 1 / 0 |
| [C2](sol3/job11/B4/C2/gate.txt) | Check adjacent lane in the eight-at-a-time loop | 3 | Timed | 1 | 88 | 7 | 1 / 0 |
| [C3](sol3/job11/B4/C3/gate.txt) | Flip one bit of the scalar tail target | 3 | Warm-up | 0 | 8 | 4 | 1 / 0 |
| [C4](sol3/job11/B4/C4/gate.txt) | Erase the penultimate prefix in `unmake_move` | 3 | Warm-up | 0 | 8 | 4 | 1 / 0 |
| [C5 optional](sol3/job11/B4/C5/gate.txt) | Flip one bit of the null-move prefix delta | 0 | No stop | | | | |

Optional C5 emitted zero mismatch lines and matched all 8612 timed rows and every counter row from B3. Sensitivity to this optional null-push fault was not shown. [C5 trace comparison](sol3/job11/B4/C5/readback.json) · [Counter comparison](sol3/job11/B4/C5/counter_comparison.txt)

## Facts

- I built in CMake Release with GCC 14.2.0, Debian libstdc++ from GCC 14.2.0-19 and `-march=x86-64-v4`. The B3 executable SHA-256 is `1735756130519c24be0beb45d6c3e8d9ac322af8500a7549edb99071fd280f1d`. The oracle patch applied cleanly and reproduced the prepared scratch tree. [B3 build](sol3/job11/B3/build.txt) · [Patch receipt](sol3/job11/B3/patch_apply.txt)
- The replacement helper ran at probe time. The store counters describe where each store would write before admission checks, including when the earlier proposed slot has changed. [Part A diff](sol3/job11/partA/count_tt_paths.patch.txt)
- The four B3 prefilter checks run at hook entry. The direct warm roots replay at least eight ordinary moves and therefore already satisfy both additional prefilter conditions whenever their halfmove clock reaches three. Prefilter totals count hook visits. [Oracle patch](sol3/job11/B3/repetition_oracle.patch.txt) · [Warm position commands](sol3/job11/B1/trace.jsonl)

## Suspicions

The number of roots with a long reversible window underestimated how often the scan reached such positions inside the search. The scan samples are weighted by search traversal and the draw-bound gates. The null-push bit flip can cancel from compared prefixes because the since-null bound keeps the comparison on the same side of that move.

## What I did not do

I ran no speed test or strength match. The source builds and controls stayed in the scratch workspace. The branch contains text evidence, harnesses, and diffs.

## What I am not sure about

More than one thread, Hash sizes other than 16, a game clock, speed (no timing in this job), the PC's own net and compiler, and a build without AVX-512 (there only the loop after the block runs).

The four positive controls show the checker can detect the specified faults on this workload. The optional control tests one offset mutation of the null push. [Raw failure records](sol3/job11/B4) · [UTC checkpoints](sol3/job11/stamps.txt)
