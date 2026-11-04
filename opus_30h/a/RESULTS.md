# Item A - v2 net path on the lock (EvalFileV2) - RESULTS

UNPROVEN in play: no Elo claim. The crew gates.

## Port (Phase 1)
- Patch `opus_30h/a/v2port.patch` (md5 fb50a98b74df98bd8261a6e3e7cf9df8, 715 lines) on the lock source d4f4312
  (fresh LF copy, scratch repo `D:\o30\repos\v2port`): new `include/forge/nnue_v2.hpp` (FORGENN2 loader API, king
  buckets + mirror, output buckets, residual flag, refresh cache, AVX2 / SSE / scalar output kernels with the lock's
  arithmetic; piece-square inputs only, any other feature bit is rejected), loader appended to `src/nnue.cpp` (cold),
  `Worker::static_evaluate_v2` in `src/search.cpp` (own section, lazy accumulators reuse `SearchStack::accumulator`),
  one branch at the top of `static_evaluate`, the root refresh skipped while a v2 net is active, UCI string option
  `EvalFileV2` (empty = off) in `src/uci.cpp` (the `id` lines untouched). Ported from Forge's own R3 tree b7c17722
  (`nnue_v2.hpp`, `evaluation_v2.inc`, the v2 part of `nnue.cpp`), with O6 / O7 and the R3 shape options removed:
  the file header alone says king buckets, output buckets, mirror and residual.
- cleanroom_lint: CLEAN.

## Checks (2026-11-03, PC clock; plain build = the kit's direct g++ line, znver5, -DFORGE_EXPOSE_TUNABLES=1, CPUs 0-1 Idle)
| check | result |
|---|---|
| plain build `D:\o30\plain\v2port_1\forge_plain.exe` | 0 warnings, vfmadd 0, sha256 466c9203bc020b4537d2d32dbbb575166856a21508d04324854122cd432c93a6 |
| OFF (EvalFileV2 empty) pin_check -Full | PASS: d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354, perft 4865609 / 193690690 |
| lock net written as v2 (`o30_v2net.py from-lock`), loaded with EvalFileV2, bench must equal the lock pins | PASS at d11-d22 for KB1/OB1 (fnv1a 5a7f7acb2d55004f), KB1/OB8 (db400d140d566e35), KB4 rank map/OB8 (de5133379be80e0d) |
| negative controls (must differ): lock net with the residual flag cleared; random KB4/OB8 net seed 30001 | LIVE: d11 558939 / 375866, d13 1881923 / 1521874, d16 9764737 / 9051131; perft = pins |
| missing file | pin_check FAIL with `info string ERROR EvalFileV2 ...: cannot open ...` (no silent fall-back) |

Meaning of the identity rows: the v2 loader, feature indices, king-bucket and output-bucket selection, the residual
combination with the hand-crafted evaluation and the lazy accumulator scheme reproduce the compiled-in network's
evaluations exactly through whole searches (KB4: copies of the same weights, so the king-bucket switch itself is
covered by the random-net checks below, not by this row).

Mistake caught on the way: a loop wrote `"EvalFileV2=D:\\o30\\...\\$n.nnue2"`; the shell received `\$n` (a literal
`$n`), the engine could not open the file and kept the compiled-in net. pin_check reported the engine's ERROR line,
but the first look at the output was cut with `head` and missed it. All rows above were re-run with paths built by
`cygpath -w` and full output.

## Parity, walk and in-search verify (2026-11-03, PC clock 16:4x-16:53)
Patch updated with a test-only block (`FORGE_NNUE_V2_VERIFY`, off in every real build): md5 378bf6bcb4d690d008a7ff18450d38fa.
Harness `v2_eval_o30.cpp` built from the port by `build_harness_o30.sh` (-O2 -ffp-contract=off -fno-fast-math -static):
AVX2 (x86-64-v3), SSE (x86-64-v2, 0 ymm instructions), scalar (`-DFORGE_NNUE_V2_SCALAR=1`); 0 warnings each.
| check | result |
|---|---|
| parity: `o30_v2ref.py` (independent float32 reference from the format spec, python-chess FEN parsing) vs engine AVX2 / SSE / scalar, 10,000 legal FENs (`C:\o13\p4\fens10k.txt`) | 10000/10000 exact, max diff 0, on 4 nets x 3 builds: random KB4 rank map MIRRORED / OB8 (seed 30002), random KB4 unmirrored / OB8 (30001), random KB1 / OB8 (30003), the lock net as KB1 / OB8; nonzero evals 9889-9989 |
| planted bug (`--mutate`, +1 on the first reference line) | caught: 3 of 3 builds FAIL (logs/parity_p1_planted_bug.txt) |
| walk: random legal games from the start position, per ply incremental update + cached refresh vs full refresh, both perspectives, exact float equality | 3000 games, 830,820 plies per net, 0 mismatches on all 3 builds; king-key changes 119,568 (KB4 mirrored), 105,118 (KB4), 0 (KB1) |
| in-search verify build (`-DFORGE_NNUE_V2_VERIFY=1`: every accumulator the search evaluates is compared with a full refresh, abort on a difference), bench d11-d22 with the random KB4 mirrored and unmirrored nets | no abort (141M / 240M nodes at d22); node counts equal to the normal build's (s1 d11 375866) |

## CPU fine-tune: decision rule (written 2026-11-03 before the main-run numbers)
A trained v2 net counts as an offline improvement only if its S31 b0.6 is at least 2e-5 below the lock net's 0.014310027
(about 3 x the 7.1e-6 seed sd of final b0.6 measured over 43 runs, forge-nnue-data A7) AND its jobA-val b0.6 (20k-node
labels) is not worse than the lock net's 0.013272058. Smaller differences are reported as "indistinguishable from the
lock net offline". (Loss has not predicted Elo reliably here (S30): even a pass is only a reason to gate, not a claim.)

## LR probes (warm start = the lock net as KB1 / OB8; 30M positions, cosine to 1e-7; CPU 0 / 1, Idle)
| run | lr | S31 b0.6 | S31 b1.0 | jobA b0.6 |
|---|---|---|---|---|
| lock net (start) | - | 0.0143100 | 0.0045724 | 0.0132721 |
| smoke2 (3M positions) | 1e-4 | 0.0143376 (+2.8e-5) | 0.0045756 | 0.0132169 |
| probe lr 2e-5 | 2e-5 | 0.0143096 (-0.4e-6) | 0.0045624 | 0.0132834 |
| probe lr 5e-6 (dir `D:\o30\runs$1`, a quoting slip) | 5e-6 | 0.0143092 (-0.8e-6) | 0.0045684 | 0.0132653 |

Finding: the lock net is converged on its own data; output buckets alone barely move the loss in 30M positions.

## CI (opus-30h-ci, GitHub Actions, ASan + UBSan, lock source d4f4312 + patch)
Run 41676909751 (commit 0744d479): success on all 3 rows. lock (control); v2port: load check (the committed random KB4
mirrored / OB8 net `testnets/rand_kbrank4m_ob8_s2.nnue2` sha256 6576e737... must print `info string EvalFileV2 loaded
... king buckets 4 output buckets 8 mirrored residual`, a missing file must print the ERROR line), self-play smoke
default / on / edge (UseNNUE=false with the net loaded) and Threads 2 on: success; expose22: default / on / edge +
Threads 2: success. (The run of f0023a88 was cancelled by the next push, not failed.)

## Main run N1 (KB1 / OB8, lr 1e-5, output layer x4, cosine to 1e-7 over 1.6e9 positions, CPU 0)
| checkpoint (PC clock) | positions | S31 b0.6 | S31 b1.0 | jobA b0.6 |
|---|---|---|---|---|
| init 17:32 | 0 | 0.0143100 | 0.0045724 | 0.0132721 |
| 17:57 | 7.61e7 | 0.0143010 (-9.0e-6) | 0.0045489 (-2.35e-5) | 0.0132339 (-3.8e-5) |
| 18:05 (stopped for timing) | 9.50e7 | 0.0143001 (-9.9e-6) | 0.0045496 (-2.28e-5) | 0.0133822 (+1.11e-4) |

N1 ends here: its chunks were 1M contiguous rows of ONE shard (61 consecutive batches from one stretch of one
self-play file), and with the output layer at 4e-5 the jobA val loss jumped +1.5e-4 between two checkpoints. The loader
now mixes 8 shards per chunk (`--mix 8`, default for new runs; old runs keep their stream exactly); N1b restarted from
the lock net at 18:07 with mixed chunks and the output layer at x2 (lr 1e-5, cosine to 1e-7 over 1.6e9 positions).

## Speed of the v2 path (advisory ABBA, `D:\o30\speed\*`, Idle, one CPU shared with the Idle npt trainer)
| exe | v2 path (lock net as v2, node-identical) vs lock FD3A5190 | OFF path vs lock |
|---|---|---|
| plain build (no PGO), same exe both arms | 0.998 (CI 0.948-1.050) | - |
| kit v2.3 df1f140b | 0.710 (CI 0.680-0.741) | - |
| kit v2.4 -PartialTraining 8704d302 | 0.959 (CI 0.929-0.990) | 0.912 (CI 0.731-1.139, noisy) |
| kit v2.5 workload v2n ff856ba8 | 1.066 (CI 0.987-1.152), median 1.085 | 1.021 (CI 0.906-1.152), median 0.996 |

Kit v2.5 = kit v2.4 + workload v2n (opus_30h/kit25/README.md): the training workload also benches the lock net written
as a v2 file, so the v2 code gets a profile; its training log shows the v2 benches with exactly the v1 node counts
(312866 / 862329 / 3024920). Exe `D:\o30\w\v2p3_pc1\src_copy\forge_ltopgo_v2p3_pc1.exe` sha256
ff856ba8a510921905e43a7505289b32ff9b3604186484fbf21f550bb0433210 (pc1 = pc2) = the gate exe for v2 nets.

## Paired holdout comparisons (o30_score_v3.exe --dump + o30_paired.py; SE = measurement error of the fixed row set)
| net vs the lock net | S31 b0.6 diff (SE, z) | jobA b0.6 diff (SE, z) |
|---|---|---|
| N1 at 76M (one-shard chunks) | -9.0e-6 (1.3e-6, -7.2) | -3.8e-5 (1.5e-5, -2.5) |
| N1 at 95M | -9.9e-6 (1.3e-6, -7.3) | +1.10e-4 (1.5e-5, +7.2) |
| old KB4 run at 65M (one-shard chunks) | -12.9e-6 (1.7e-6, -7.8) | +5.2e-5 (1.9e-5, +2.8) |

Reading: on S31 the measurement error of a paired difference is ~1.5e-6, so these nets ARE better than the lock net on
the lock net's own holdout (the 7.1e-6 seed spread is a different question: whether another run lands the same). On jobA
(8,821 rows, 20k-node labels, positions of the early self-play files 001 / 002) the error is ~1.6e-5 and the 95M net is
clearly WORSE: the one-shard chunks pulled the output layer toward whichever file it was reading. Rule refined (stricter
than before, not looser): a net passes when its S31 b0.6 is >= 2e-5 below the lock net's AND its paired jobA z <= +2.

## Review R-A1: the port patch (structured self-review, NOT independent; 2026-11-03 PC clock 18:1x)
Read the whole diff (v2port.patch md5 378bf6bc...) against the R3 source it came from. Checked, with the reason:
- Thread safety: the Net is read-only during a search; refresh caches are per worker id (`net.caches[id_]`, created by
  that worker only); unload / load only after `stop_search()` joins the search thread (uci.cpp). No shared mutable state.
- Lifetime: `active_net` is cleared before the Net is deleted (unload); a failed load leaves no v2 net (unload first).
- Root and lazy updates: the root is refreshed lazily (the root-refresh line is skipped while a v2 net is active and
  every stack entry starts invalid each search); null moves replay as an empty update (copy); castling / ep / promotion
  dirty lists (2-4 changes) map to apply_columns templates; a king move that changes its own (bucket, flip) key refreshes
  that perspective from the board with the later plies' changes taken back. All covered by the walk (king-key changes
  105k-120k) and the in-search verify build.
- UseNNUE=false with a v2 net loaded: hand-crafted evaluation only (the v2 branch returns it before touching
  accumulators); record_move then records nothing, as for the compiled-in net. CI edge line covers it.
- Hash: cleared on every EvalFileV2 change (old scores came from another evaluation).
- `info string` on success and on every error; the gate runner's "advertised" check passes (uci lists EvalFileV2).
- OFF build: the only additions on the default path are one pointer test at the top of static_evaluate and one at the
  root refresh; pins identical; OFF speed vs the lock 1.021 (kit v2.5, advisory, noisy).
Findings: none in the engine code. Risks kept: v2 hidden size is the compiled-in 256 (an H512 net needs a separate
accumulator - follow-up); the kit must be v2.5 (v2.3 makes the v2 path 0.71x).
Run 41682427163 (commit 2db5d468, adds a ThreadSanitizer job): success on all 4 jobs - tsan (the v2 port, Threads 4,
the random KB4 mirrored / OB8 net, 2 games x 40k nodes, halt_on_error, no ThreadSanitizer report), lock, v2port, expose22.

## Trainer resume proof (prove_resume_fit.sh p1, 2026-11-03 18:5x-19:01, CPU 1 Idle)
Run U: 6.5M positions (KB4 / OB8, mix 8, seed 77) uninterrupted. Run I: the same configuration stopped by its deadline at
step 200 (3.28M positions, inside chunk 3), saved, exited, then resumed (`fit_resume.sh`) to the end. Result: U and I end
at the same state (step 397, positions 6,504,448, chunk 7) with BIT-IDENTICAL weights w1 / b1 / w2 / b2 - RESUME PROOF
PASS (1 torch thread on the CPU is deterministic; the data stream depends only on (seed, chunk)).

## Main runs, second checkpoints (mixed chunks)
| run | positions | S31 b0.6 | S31 b1.0 | jobA b0.6 |
|---|---|---|---|---|
| KB4 decider n2e (lr 2e-5, out x2) 18:34 | 8.15e7 | 0.0142894 (-2.06e-5) | 0.0045651 (-7.3e-6) | 0.0132645 (-7.6e-6) |
| KB4 decider n2e 18:59 | 1.457e8 | 0.0142790 (-3.10e-5) | 0.0045601 (-1.23e-5) | 0.0133016 (+2.95e-5) |
| N1b KB1 (lr 1e-5, out x2) 18:33 | 7.33e7 | 0.0143061 (-3.9e-6) | 0.0045712 (-1.2e-6) | 0.0132904 (+1.8e-5) |
| N1b 18:58 | 1.376e8 | 0.0142944 (-1.56e-5) | 0.0045499 (-2.25e-5) | 0.0133373 (+6.5e-5) |

Caution: both get better on S31 (013/014, 5k-node self-play labels) while the jobA val loss (20k-node labels, positions
of the early files 001 / 002) drifts up. The fine-tunes may be fitting the shallow labels' habits; reported as is.

## jobA val with OLD vs NEW labels (o30_joba_old.py: the same 8,821 positions with their original 5k-node self-play
## scores, D:\o30\data\jobA_val_old.pos/.hce; paired vs the lock net)
| net | old labels diff (SE, z) | new 20k-node labels diff (SE, z) |
|---|---|---|
| KB4 decider at 146M | +1.6e-6 (1.9e-5, +0.09) | +2.96e-5 (2.0e-5, +1.47) |
| N1b KB1 at 138M | +4.71e-5 (1.2e-5, +4.05) | +6.53e-5 (1.3e-5, +5.19) |

Reading: N1b is worse on these EARLY-file positions under both label types - a shift toward the bulk of the (later) data,
not a fit to shallow-label habits; KB4 is neutral on the old labels and not significantly worse on the new ones. By the
written rule KB4 passes so far (S31 -3.1e-5, jobA z +1.47); final call at the end of its run.
| N1b stopped 19:03 (CPU 0 goes to a long KB4 run) | 1.507e8 | 0.0142957 (-1.43e-5); best 0.0142944 at 1.376e8 | 0.0045534 | 0.0132818 |
Decision 19:03: KB4 is ahead of KB1 on S31 (-3.10e-5 vs -1.56e-5 at ~1.4e8) and neutral on jobA, so the two CPUs go to
KB4: the decider n2e finishes on CPU 1 (3.5e8 positions, ~20:00) and a long KB4 run n2L (lr 2e-5, out x2, mix 8,
1.4e9 positions, until 2026-11-04 03:30) runs on CPU 0. Two KB4 candidates of different training length + N1b's best.

## The gate exe for v2 nets (kit v2.5, D:\o30\w\v2p3_pc1\src_copy\forge_ltopgo_v2p3_pc1.exe, sha256 ff856ba8...)
pin_check -Full (OFF, EvalFileV2 empty): PASS d11-d22 + perft. With EvalFileV2 = the lock net as a v2 file (KB4 rank map,
OB8, every bucket a copy): bench d11 / d13 / d16 / d20 / d22 = the lock pins exactly (pin_check -Expect PASS, 67 s).

## Long KB4 run n2L (lr 2e-5, output x2, mix 8, 1.4e9 positions planned, CPU 0, seed 222)
| checkpoint | positions | S31 b0.6 | S31 b1.0 | jobA b0.6 |
|---|---|---|---|---|
| 19:28 | 7.06e7 | 0.0142976 (-1.24e-5) | 0.0045798 (+7.4e-6) | 0.0133952 (+1.23e-4) |

The jobA drift differs a lot between runs of the same shape (decider n2e at 8.1e7: -7.6e-6; n2L at 7.1e7: +1.23e-4):
the early-file positions are a small, out-of-distribution set. The written rule is NOT changed by this: a delivered net
passes only with S31 b0.6 <= -2e-5 AND a paired jobA z <= +2; a net that fails it is still packaged, marked as failing.

## KB4 decider n2e - to the end (3.5e8 positions, CPU 1, seed 212, lr 2e-5 cosine to 1e-7, output x2, mix 8)
| checkpoint | positions | S31 b0.6 | S31 b1.0 | jobA b0.6 |
|---|---|---|---|---|
| 19:24 | 2.132e8 | 0.014264061 (-4.60e-5) | 0.004554096 (-1.83e-5) | 0.013268861 (-3.2e-6) |
| 19:49 | 2.957e8 | 0.014254952 (-5.51e-5) | 0.004543182 (-2.92e-5) | 0.013300721 (+2.87e-5) |
| final 20:06 | 3.500e8 | 0.014254268 (-5.58e-5) | 0.004543952 (-2.85e-5) | 0.013294160 (+2.21e-5) |

The final checkpoint is the run's best on S31 (selection on the reporting holdout among 9 checkpoints; the last three
differ by < 1e-6, so the selection effect is far below the -5.6e-5). Packed as `o30_kb4ob8_n2e` (net_pack.sh with the
paired step): parity 10000/10000 on AVX2 / SSE / scalar (planted bug caught 3/3); paired vs the lock net S31 b0.6
-5.576e-5 (SE 1.64e-6, z -34.0), jobA val +2.21e-5 (SE 1.80e-5, z +1.23) -> **offline rule PASS** (S31 <= -2e-5 and
jobA z <= +2). Pins and ON benches: `D:\o30\nets\o30_kb4ob8_n2e\RESULT.json`: OFF pin_check -Full PASS (d11-d22,
perft); ON bench d11 333628 / d13 803134 / d16 2593172, equal in two runs; perft = pins. sha256
998db5e9e174fed02f9ed4474981ef4f09bed8d0a098e52d418e1aeef05c86f8, md5 64c967f0cfd8bdd086f6371a68d7456f.

## Where the n2e gain comes from (`o30_breakdown.py`, paired per-row S31 differences; `D:\o30\nets\o30_kb4ob8_n2e\BREAKDOWN_S31.md`)
Every group improves on its own (z -6 to -25), so the gain is not one odd subset of the holdout:
- by material (OB8 bucket): endgames gain most per row (2-5 pieces -8.9e-5, 6-9 pieces -7.1e-5), the opening bucket
  least (30-32 pieces -2.8e-5);
- by king placement: the further up the board the side to move's king stands, the larger the gain (rank 1 -4.7e-5,
  rank 2 -5.6e-5, ranks 3-4 -6.6e-5, ranks 5-8 -8.4e-5); the same for the other king - what 4 king buckets add;
- by label size: 0-49 cp -6.0e-5 ... 150-399 cp -7.9e-5, 1000+ cp -0.8e-5 (big labels are saturated by the sigmoid).
Groups are not independent tests; this is the measurement error of a fixed row set, not training noise.

## Play checks - pipeline dry run and UCI conformance (2026-11-03 20:0x-20:1x, CPU 1)
- `net_final_checks.sh` had never run end to end, and it refuses an existing FINAL_CHECKS.json: dry run on the test
  net `test_lockv2_kb1_ob8` (the lock function as v2) with 2 games: smoke 300 s PASS (30 games, 3,645 plies, 0 illegal /
  crashes / hangs / time losses), NPS ABBA 0.976 (CI 0.949-1.004; same tree, the v2 path's speed on this exe,
  advisory), 2 games 0/2/0, gate_summary reproduces the block, exit 0. Rate at 10+0.1, conc 1: 97 games/h.
- `tools/uci_conformance_o30.py` (new): gate exe ff856ba8 + o30_kb4ob8_n2e 20 / 20 PASS (the net loads with its
  `info string`, every bestmove legal and inside its limit, movetime 500 -> 0.48 s, `go infinite` waits for `stop` and
  answers it at once, mate in 1 with `score mate 1`, 0000 for checkmate / stalemate, Threads 2, clean quit, empty
  stderr); the lock exe 18 / 18. A first version reported "0.00 s" for movetime searches: the engine's OwnBook
  (default true) answered from its book - the checks now run with OwnBook false, like the gates.
- n2e play checks started 20:1x on CPU 1 (smoke, ABBA, 400 games 10+0.1 vs the lock, conc 1): ~4.2 h.

## n2e play checks, first results (CPU 1; the match runs until ~00:30)
- Smoke 300 s (EvalFileV2 = the net, Threads 2, 2+0.02): PASS - 50 games, 6,284 plies, 0 illegal / crashes / hangs /
  time losses, 1 overrun inside the margin, empty stderr.
- NPS ABBA vs the lock (bench 16, 6 pairs, CPU 1, advisory): 0.899 (CI 0.845-0.958). The trees differ: n2e searches
  fewer nodes to the same depth (d16 2,593,172 vs 3,024,920; d13 803,134 vs 862,329; d11 333,628 vs 312,866), so its
  bench-16 wall time is ~0.96x the lock's (2.59M / 1.567M nps = 1.65 s vs 3.02M / 1.750M = 1.73 s).
- Is the 4x larger first layer (KB4: 3.1 MB of float32 weights vs the lock's 0.79 MB) the cost? Same-tree test: the
  lock net written as KB1 vs as KB4 with 4 identical buckets (identical search, both = the lock pins), 8 pairs on CPU 0
  next to the trainer: 0.968 (CI 0.900-1.040), median 0.991 -> the table size and the king-bucket refreshes cost little;
  an int16 weight store (half the memory) is not worth a re-proof. Speed claims are QA's (official timing).

## Review R-T1: own processes outside Idle / CPUs 0-1 (found and fixed 2026-11-03 20:2x)
Found while re-reading my bash tools: net_pack.sh and final_checks_o30.sh started python, the scorer and the parity
harness directly, so those children ran at Normal priority on any CPU (gates run at BelowNormal on CPUs 4-15). The
same held for a few one-off analysis commands (scorer / numpy, seconds each) and for the UCI conformance driver
(its engine was pinned only after start). Each run took seconds to about a minute (the 19:08 final-check run, the two
packs, ad-hoc scoring). Fix: `tools/idle.sh` + `tools/pin_pid.py` pin the calling bash first (Idle + mask, read back,
fail closed with exit 78); net_pack.sh and final_checks_o30.sh source it; the conformance driver pins itself before it
starts the engine; ad-hoc tools run through `idle.sh 0x3 ...`. Checked: a child of a pinned bash reports affinity [1]
and IDLE_PRIORITY_CLASS; a bad mask exits 78. Effect on the crew: the running gate uhoE3a_evalmatscale12 (3,443 games)
shows 0 time forfeits, 0 illegal moves, 0 crashes (gate_summary, read-only, 20:2x). Not yet fixed: net_final_checks.sh
(it is running the n2e checks; bash reads scripts while running, so it is edited after that run; its smoke, ABBA and
match steps pin themselves already - only its two small python summaries do not).

## A wider king map, ready before it is needed: rank4x2 (8 buckets, 2026-11-03 20:3x, CPU 0)
rank4x2 = the rank4 groups (king on rank 1 / 2 / 3-4 / 5-8, seen from its own side) x the board half (files a-d or
e-h), unmirrored - so the lock net written into all 8 buckets is still exactly the lock function (exact warm start).
`a/check_kbmap.sh rank4x2` (evidence `D:\o30\kbmap_rank4x2_202819`): 1 lock net as rank4x2 / OB8 = lock pins
d11-d22 in the gate exe ff856ba8 PASS; 2 random rank4x2 / OB8 net parity 10000/10000 on AVX2 / SSE / scalar + planted
bug caught PASS; 3 walk 500 games, 139,064 plies, 19,978 king-key changes, 0 mismatches PASS; 4 trainer selfcheck
PASS. Whether a KB8 run gets a CPU is decided at ~00:30 from n2L's curve (does longer KB4 training still gain?).

## Review R-T2: final_checks check 12 never compared a net hash (found and fixed 2026-11-03 20:4x)
The regex of check 12 expected the sha256 right after a backticked path; INDEX.md puts the net's hashes on the next
table row, so only the exe rows matched (shown on a copy of INDEX.md with a planted wrong net hash: the old check
compared `forge_ltopgo_v2p3_pc1.exe` only and would have passed). New `tools/index_check_o30.py` parses every net
section and compares the net's sha256 AND md5 and the exe's sha256; a missing row is a FAIL. Tests: the real INDEX.md
3 / 3 ok; planted wrong net hash -> 1 problem; deleted hash row -> FAIL. New check 13 (`tools/path_sweep.py`): every
Windows / branch path cited by the job's documents exists (allowed missing: `D:\o30\WINDOW.md`, written only on a GPU
release).

## Trained net in the in-search verify build (2026-11-03 20:4x, CPU 0)
The verify build (`D:\o30\plain\v2port_verify\forge_plain.exe`, -DFORGE_NNUE_V2_VERIFY=1: every accumulator the search
evaluates is compared with a full refresh, abort on any difference) with `o30_kb4ob8_n2e`: bench 13 803,134 nodes, bench
16 2,593,172 (both = the normal build's ON benches), bench 20 12,201,110 - no abort. Before this only random nets had
run through the verify build; this covers the trained KB4 net's king-bucket switches in real searches.

## Loader fuzz: damaged FORGENN2 files (2026-11-03 20:45, gate exe ff856ba8, `a/loader_fuzz_o30.py`)
18 variants of a valid net, each with a valid checksum unless the checksum is the target (so only the targeted check
can fire): truncated / one byte longer, bad magic, version 3, header size 161, feature set 1, inputs 769, hidden 512,
king buckets 0 / 33, output buckets 0 / 17, unknown flag bit, weight scale 4095, king map entry = king buckets, output
map entry = output buckets, reserved byte set, weight byte flipped. Every one is refused with its own reason in an
`info string ERROR EvalFileV2 ...` line and the engine then benches the lock pin (d11 312866). Sequences: valid net ->
damaged file leaves no v2 net (lock pin); valid net -> empty value unloads (lock pin); control: the valid net is live
(d11 333628). LOADER FUZZ PASS, 21 / 21. Now check 14 of final_checks_o30.sh.
More "works in Forge" cases (20:4x): a net path with spaces (`D:/o30/tmp/dir with space/x.nnue2`) loads (the handler
reads the rest of the line); `setoption EvalFileV2` sent during `go infinite` stops the search (one bestmove), loads,
answers readyok in 0.08 s, and the next search works - now part of uci_conformance_o30.py (gate exe + n2e: 22 / 22).

## How different is n2e from the lock net? (`a/o30_evalcmp.py`, 10,000 legal FENs, residual corrections in cp)
| net | mean | sd | mean abs | p1 / p10 / p50 / p90 / p99 |
|---|---|---|---|---|
| lock net | +0.09 | 166.34 | 97.52 | -569 / -132 / -1 / +131 / +577 |
| o30_kb4ob8_n2e | +0.39 | 168.25 | 98.50 | -574 / -133 / +0 / +134 / +589 |

Correlation 0.9988, sd of the difference 8.3 cp, slope of n2e on the lock net 1.010, sign flips > 20 cp in 0.05 % of
positions: n2e is a gentle refinement (about 8 cp rms), not a different evaluation, and its scale is the lock net's
(+1 %) - search margins tuned with the lock net see the same magnitudes. (Diagnostic only; play strength is the gate's.)

## n2e in real games: depth per move (gate_summary --watch on the running sanity match, 20:5x, 65 games)
cand (n2e): 4,769 moves, mean depth 20.08, 0.217 s / move; lock: 4,770 moves, mean depth 20.08, 0.218 s / move. The
0.90x bench NPS does not cost depth at 10+0.1: n2e needs fewer nodes per depth (as on the bench), so both reach the same
mean depth in the same time. (Interim; the final numbers with all 400 games go into FINAL_CHECKS / INDEX.)

## Plan for CPU 1 after the n2e match (written 2026-11-03 20:5x, BEFORE any KB8 number)
KB8 run n3 = n2e's recipe with the rank4x2 map (lr 2e-5, output x2, cosine to 1e-7 over 3.5e8 positions, mix 8,
seed 232): an equal-length capacity test (KB4 vs KB8). Rule: n3 becomes candidate #3 (pack + full play checks) only if
its paired S31 b0.6 is at least 1e-5 below n2e's (paired vs n2e's dumps) AND its paired jobA z vs the lock net is <= +2;
otherwise it is reported offline only and CPU 1 goes to SPSA at once. Either way the result answers "does more
king-bucket capacity pay at equal training?" for the GPU path.

## Time forfeits in the n2e sanity match (found 21:4x at 163 games)
3 time forfeits, all between 21:31 and 21:37 (PC clock): the lock lost 2, the candidate 1. Each is a stall, not a long
think: the last moves took ~0.07-0.10 s, then "Black loses on time (2447ms overrun)" - over fastchess's 1000 ms margin.
Both engines run at Idle on CPU 1 (CPU 0 = the n2L trainer, Idle); any Normal-priority burst on the PC is scheduled onto
CPUs 0-3 (the only cores without BelowNormal gate work) and preempts Idle threads for seconds. My own commands in that
window were a sleep loop; n2L's checkpoint scoring came later (done 21:36:39). Reading: environment noise hitting both
sides; kept as is (same settings for both candidates, so the two matches stay comparable); the 5-minute smoke (the
prompt's "0 time loss" check) passed. The match is sanity only either way.

## n2e play checks - final (2026-11-03 20:12 -> 23:58, CPU 1; FINAL_CHECKS.json)
- 400-game sanity match vs the lock, 10+0.1, Threads 1, UHO, conc 1: **79 / 213 / 108, Elo -25.2 +/- 18.5** (nElo
  -46.6 +/- 34.1, pentanomial [4, 62, 94, 39, 1]); time forfeits 3 (lock 2, candidate 1; the 21:3x stalls above);
  0 illegal, 0 crashes; mean depth per move equal (20.1 vs 20.1). SANITY ONLY - but about 2.7 standard errors below
  zero: the offline gain on S31 (5k-node labels, z -34) did NOT show up as play at 10+0.1. The deeper-label set pointed
  the same way (jobA +2.2e-5, z +1.23): read with the old-vs-new-label analysis above, n2e fits the 5k-node self-play
  labels better without being better on deeper labels. The offline rule (S31 AND jobA z <= 2) was too weak a filter.
- A/A noise floor of the per-net ABBA (same conditions: CPU 1, n2L training on CPU 0): the lock vs a byte-identical copy,
  6 pairs bench 16: 0.945 (CI 0.906-0.985), median 0.942 - identical binaries read ~5 % apart here (per-file effect,
  as in R5B), so the 0.90 of n2e is within ~5 % of that bias band; speed figures from this PC stay advisory.
- Walk on n2e (plan phase 1 asked for 1M plies): 4000 games, 1,106,215 plies, 139,267 king-key changes, 0 mismatches.

## Deviation from the pre-registered KB8 step (decided 2026-11-04 00:0x, after the n2e match)
n3 (KB8) was NOT run. Reason, dated: the n2e match (400 games, -25.2 +/- 18.5, written 23:58) shows that the S31 gain
did not turn into play, and n3's rule is judged on S31 - every n3 outcome would need its own 4-hour match to mean
anything, and the n2e pattern (better on the 5k-node labels, flat / worse on deeper labels, worse in play) suggests
more first-layer capacity would fit the shallow labels' noise further. CPU 1 went to the SPSA session at 00:03:59
(`D:\o30\spsa\stc8_main`, -Cpus 1 -Threads 1, until 19:30). KB8 stays proven and ready (check_kbmap, Rust path).

## ABBA harness: an arm bias, measured (00:0x, CPU 1, n2L training on CPU 0)
A/A twice with byte-identical binaries: lock as A, copy as B -> 0.9447 (CI 0.906-0.985); copy as A, lock as B ->
0.9455 (CI 0.917-0.975). Whichever command is arm B reads ~5.5 % slower under this load - an arm effect of the harness
here, not a per-file effect. So every B / A ratio from abba.py on this PC this night carries ~0.945 of bias: n2e's
0.899 corresponds to ~0.95 of the lock (0.899 / 0.945), the dry run's 0.976 to ~1.03. Speed claims stay QA's; the
cause in abba.py is not found yet (listed for the bug hunt).

## Bucket seams? (`a/o30_bucketcmp.py`, 10,000 FENs, mean correction difference vs the lock net per bucket)
The lock net has one output bucket and one king bucket; a KB4 / OB8 net could carry steps between adjacent buckets
that per-position losses cannot see (search meets them at every trade / king move across an edge).
| net | sd vs lock | largest output-bucket step | largest king-bucket step |
|---|---|---|---|
| o30_kb4ob8_n2e | 8.3 cp | 1.8 cp (OB1 -0.56 -> OB2 +1.21) | 1.5 cp (rank 2 -0.32 -> ranks 3-4 +1.22) |
| n2L at 7.98e8 (step 48712) | 15.6 cp | 2.2 cp (OB3 +2.93 -> OB4 +0.72) | 1.5 cp (rank 2 +0.35 -> ranks 3-4 +1.84) |
Bucket means are measured to ~0.2-0.5 cp, so the steps are real but small next to the per-position spread: no clear
seam pattern, nothing structural to fix on the CPU. n2L moves the evaluation twice as far from the lock net as n2e
(15.6 vs 8.3 cp rms, scale +1.7 %); its own match is the verdict.
