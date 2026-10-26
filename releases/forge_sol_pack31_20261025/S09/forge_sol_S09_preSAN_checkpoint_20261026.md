# S09 release/parity checkpoint — 2026-10-26

Status at 2026-10-26T18:39:48.582278+00:00: Release/native parity,
converter and full-sample CPU evaluation are complete. Two separate static
ASan/UBSan builds are in progress. This checkpoint is not an ASAN PASS or a
playing-strength acceptance. Final publication and sanitizer results remain pending.

## Exact baseline and implementation

Reference code: `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`.
Unchanged default h256_e12 weights SHA256:
`74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`.
The new original-L reference executable exactly reproduced canonical
`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`.
Lprime and B retain their prior known-failure labels; B also retains the buffer repair.

The supplied, CR-passed `fc_buckets8_h256e12.patch` is an unchanged prerequisite,
SHA256 `ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704`.
The source preparer selects its original core/header/test/helper payloads, omits
its replicated-net asset so the original one-head net remains the default, and
integrates its original CMake declarations using unique existing anchors.
It does not claim the complete original patch literally applied to every base.
The newly authored engine delta is only the 27-line contract/validation-target
change. The old combined repackage is retained as a failed/superseded preparation,
not delivered as a newly implemented core feature.

There is no new UCI option and no phantom output-bucket build switch. The trainer
CLI defaults to `--buckets 1`; its `--buckets 8` output and replicated native eight-
head include are explicit offline inputs. Existing float accumulators, NNUE update
arithmetic, search, TT and move ordering were preserved. Quantized include storage
continues to be dequantized to float; no int16 accumulator was introduced.

| New patch | SHA256 | Diffstat |
|---|---|---|
| `forge_sol_S09_native_delta_20261026.patch` | `4e148af7db21b9531bb89353ad89323b501421c0f0ecff4a673b79a5a2ff9cc7` | 2 files, +27/-0 |
| `forge_sol_S09_trainer_20261026.patch` | `a939d3ad959948764d558b8ad213d93842cfdabd2c92caafa256bc63d28e0042` | 1 files, +38/-13 |
| `forge_sol_S09_documentation_addendum_20261026.patch` | `41da83e6b653d06c56ab17f466cb9de0bb38c0eda7460999e4ad84a43b447785` | 2 files, +32/-0 |

Docs are additive, and GNU patch `-p1 -F0 --dry-run` passed on L/Lprime/B without
changing them. The new engine delta also passed the recorded GNU zero-fuzz series
checks on all three bases. Git apply checks remain a root publication gate.

## Build and correctness

GCC14.2 C++20 Release, one compiler job:
`-O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`.
FORGE_NATIVE/IPO/sanitizers/PGO/LTO were OFF for these Release builds.
Every new main executable's first runtime was bare `bench 11` then `quit`, with
308972 nodes and no prior UCI. Complete source and artifact inventories remained
unchanged, and owned compiler/runtime groups closed normally.

Lprime main: `1d351b8e1bf1ab8e54821d108b9be10909a55da7167d7f5126c9eaf5fac0792a`.
B main: `dbd6dc21481e24fcb1589c01962a3813945bb0b77f2d72b6318779b88150bf3c`.

| Check | Fixed reference | Lprime actual | B actual | Status |
|---|---:|---:|---:|---|
| d11 | 308972 | 308972 | 308972 | PASS |
| d13 | 745494 | 745494 | 745494 | PASS |
| d16 | 2460422 | 2460422 | 2460422 | PASS |
| d20 | 11901452 | 11901452 | 11901452 | PASS |
| d22 | 31111774 | 31111774 | 31111774 | PASS |
| Startpos perft5 | 4865609 | 4865609 | 4865609 | PASS |
| Kiwipete perft5 | 193690690 | 193690690 | 193690690 | PASS |
| NNUE object/NNUE ELF/whole ELF FMA | 0 | 0 | 0 | PASS |
| Full configured CTest | all registered | 16/16 | 17/17 | PASS |
| Existing known diagnostics | four only | four, no FAIL | four, no FAIL | PASS |
| Typed UCI/ready/EOF and legal T1/T2 search | unchanged contract | PASS | PASS | PASS |

The WAC pins remain f6h5/661. The two original promotion cases remain source-bound
known findings (c6d7/c3d2, score642 at d1); no expected values were silently changed.
The previous buckets8 trained-net null-pruning failure did not appear in either
full default-net suite. No newly trained eight-head net is being accepted here.
Raw bench NPS values are diagnostic only: other fixed-work jobs ran concurrently.
No controlled speed comparison, Windows qualification or Elo result is claimed.

## Native parity and converter

The candidate-independent corpus contains 1000000 unique FEN4 positions generated
by fixed-seed20261026 legal Python-chess API walks, not self-play match games.
Original gzip SHA `e06bf2de476f1819ab098b854d718ff1b528c49c60ee9edbfd82206b99798a42`;
raw52261200 bytes SHA `0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6`.
The sealed native input memfd had all four immutable seals (value15).

Default-one-head vs original lock: exactly 1000000 roots/rows,
zero NNUE/HCE integer-CP differences; full original output bytes compared, and
fresh vs accumulator memcmp passed on each row. Each original stream is
24165624 bytes SHA `f002909f482c3ea330545499ef4cc036bd9231c632a361ca936952b64ed24447`,
with its own preserved original gzip stream. Plies=0 does not claim incremental
transitions on those million rows. It also does not claim cross-core float words
were serialized on those million rows.

Converter: first10000 exact original FEN lines, then up to eight legal plies per
root, 89804 actual rows. All10000 roots matched; NNUE/HCE CP
max difference0 and fresh/incremental accumulator memcmp mismatches0. All eight
piece-count bands were exercised: [1393, 14411, 19124, 13596, 10317, 9363, 8094, 13506].
The converted include is `1c579f08bc2cb8b10b976162cd3319fd041401bee17d8830d0e449fa300ab1e5`.
A real native contract confirmed available/residual/H256/stored_heads=8.
Six non-NNUE objects were reused only after their source/header/flags and actual
original archive member bytes were bound. A new nnue.cpp object used only the
literal converted-include override, in a new derived archive. This is a helper
qualification, not a new full-engine build or another full-Std claim.

Separately, the unchanged original `tools/nnue_snapshot.cpp` driver serialized
all accumulator float words and NNUE CP for six edge-FEN walk families plus
100000 synthetic activation cases. Original, default-head candidate and stored8
candidate outputs were byte-identical: each41903752 bytes SHA
`c084e1f2c0115a5cbd19a9d9083ef1faf93c3174024ecc01c7863f70ab32df13`.
The stored8 check compared its new raw output to retained original reference
bytes; no reference stream was reconstructed from summaries.

## Trainer and full sample evaluation

Fifteen unchanged source/export assertions passed again from this delivery
folder with an audit hook denying access to original workspaces, using the local
pinned original v3b dependency. Single-bucket exports are byte-identical at equal
parameters/configuration. That does not mean CLI recipe defaults were unchanged.
Observed f006 defaults are batch8192/lr0.000707/warmup300/blend_end0.6/seed25/
48epochs/H256residual/final-full-validation. Unspecified values remain v3b defaults;
the log display is not a recovered complete high-precision configuration file.

The full-sample CPU process exited normally after52.32s: all50000 supplied
synthetic h000 rows,98 batches, final336 rows, no dropped tail. Actual f006 include
was loaded through original parser/layout, with unchanged v3b reader and targets.
One-vs-replicated-eight Torch max logit delta `3.814697265625e-06`
was within the preregistered1e-5; first-batch bias control changed512/512 rows.
MSE one-head `0.12416724592633246`, eight-head `0.12416724590392758`,
HCE-only `0.04558598686496771`. These are synthetic-stand-in diagnostics, not
training-gain or accepted-net generalization evidence. All input hashes remained
unchanged, both atexit markers were observed, and summed peak RSS was264425472B.

The earlier three-training-step/export probe remains an overall150-second
watchdog FAIL, despite its completed inner512-row proof. The new normal-exit
full50000-row evaluation does not rescue that failed process. Default DirectML
optimizer/GPU execution, actual013/014 holdouts, eight-head training quality and
crew/CR adoption are UNVERIFIED. No GPU training or gate queue was changed.

## Remaining gate and next action

Static O2g ASan/UBSan LP and B builds/runtimes are active/pending. Runtime uses
leak detection, unlimited virtual address space for ASAN shadow, an owned-RSS
limit instead of RLIMIT_AS, complete configured CTest and small perft/UCI checks.
Finish those gates, seal original raw logs/results and the delivery manifest,
then publish and continue to S10. S23 remains dropped. No Elo or speed claim.
