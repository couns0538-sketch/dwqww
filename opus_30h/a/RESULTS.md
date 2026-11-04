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
