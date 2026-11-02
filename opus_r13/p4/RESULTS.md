# R13 Phase 4 - v2-feature nets with bullet (FORGENN2) - IN PROGRESS: CR fixes in (e23fca30 + CR final delta d884c23b), H256 parity PASS (R14 rerun); H768+ and training open

Branch `opus-r13-p4-v2nets` (from main). UNPROVEN: no net trained here yet; no Elo claim.

## Deliverables (this branch, opus_r13/p4/)
| file | what | state |
|---|---|---|
| forge_v2_bullet/ (Cargo.toml, src/main.rs) | bullet da426a49 trainer, stages a / b / c in one binary; own SparseInputType `ForgeV2` | written, build pending |
| export_v2.py | bullet raw f32 `quantised.bin` -> FORGENN2 (round(x*4096), overflow = error) via the crew's write_v2 | written |
| forge_nnue_v2.py | crew tool, unchanged copy of forge-bundle-int b7c17722 tools/nnue/forge_nnue_v2.py | copied |
| v2_eval.cpp | engine-side parity harness: forge::nnue::v2::load + refresh + evaluate (engine's own feature code) | written, build pending |
| eval_ref.py | trainer-side reference: numpy float32 replay of nnue::v2 on the exported file + the Rust feature lists | written |

## Design facts (checked in the sources)
- FORGENN2 (forge/nnue_v2.hpp, forge-bundle-int b7c17722): (inputs -> H) per perspective, SCReLU = clamp [0, 1] then square,
  side to move first, one linear output per bucket; cp = trunc(out * 400 / 2.25); weights int16 / 4096 (w1, wt, wp, b1:
  WeightScale; w2, b2: OutputScale, both 4096). Stages: a = 768 + 8 output buckets; b = a + O6 threats (9216, count-valued);
  c = b + O7 pawn pairs (1792). King buckets stay 1 (C4 not in the staged order).
- Output buckets: bullet MaterialCount<8> = (pieces - 2) / 4 = Forge's default map (forge_nnue_v2.output_layout(8)).
- bullet's ChessBoard is stored in the side-to-move frame (black to move: ranks flipped, colours swapped), so the side-to-move
  features use the stored squares, the other perspective square ^ 56 with colours swapped (same as bullet Chess768).
- FTP1 block-aware L1 permutation: does not apply to FORGENN2 (no int8 L1 layer after the hidden layer; the output is a
  dense dot of 2H floats, where the order of hidden units changes nothing). It applies to the HalfKA .nnue path.
- All three output paths of nnue::v2::output (AVX2, SSE, scalar) map hidden unit h to lane h % 16 and add the lanes in order,
  so the paths are bit-identical by construction and a float32 replay (eval_ref.py) can match them exactly.

## Finding: bullet da426a49 has no CPU training backend
Without the `rocm` / `cuda` features bullet's trainer uses `runtime::mock::MockGpu` (crates/gpu/src/runtime/mock.rs: "This is
a mock runtime! It can't actually do anything!"). So the prompt's "CPU-only smoke on 1M positions" cannot run with bullet;
every training run, the smoke included, needs a GPU window. CPU-side proof instead (no training needed): the program
compiles against the mock backend, and parity_v2.sh checks, per stage, a seeded random FORGENN2 net through the Rust feature
lists + float32 reference against the engine's own loader / features / kernel (v2_eval, AVX2 + SSE builds) on 10k FENs.

## CR R13 (crew Code Review of 59ad17c9) and fixes
| CR item | fix |
|---|---|
| parity_v2.sh always exits 0 (a mutation run proved it never fails) | every stage now exits 1 on any non-exact FEN, ERR line, line-count mismatch or all-zero evals; `PARITY PASS` only at the end; `PARITY_MUTATE=1` plants a +1 in the reference and must make it fail (to be shown in the run log) |
| export_v2.py rejects real bullet output (pad bytes are 'bullet', not zeros) | accepts exactly bullet's padding (crates/trainer/src/model/weights.rs to_quantised_buffer: repeating b"bullet" up to a multiple of 64) or no padding; anything else is an error |
| IDEA_SOURCE wrong: sfbinpack GPL-3.0, montyformat AGPL-3.0 | IDEA_SOURCE.md rewritten with a licence table from the crates' Cargo.toml: both are bullet_lib dependencies, trainer tool only, never in Forge source |
| H768+ parity still unrun | open: parity so far is for H = 256 (the R3 engine's compiled HiddenSize); H 768 / 1024 / 1536 need engine harness builds with -DFORGE_NNUE_HIDDEN=<H> and nets of that width - listed as TODO, no claim beyond H256 |

## Parity results (2026-11-01, after the CR fixes) - PASS at H = 256
| check | result | evidence |
|---|---|---|
| forge-v2-bullet compiles (bullet da426a49, mock backend, rustc 1.99.1, own CARGO_HOME / target dir) | 0 errors, 52 s | logs/cargo_build_mock.log |
| v2_eval harness on forge-bundle-int b7c17722: AVX2 (x86-64-v3) and SSE (x86-64-v2, 0 ymm/zmm instructions) builds | 0 warnings each | logs/harness_build_run.log |
| stage a (768 + 8 buckets), random net seed 13451: reference vs engine, 10k FENs | AVX2 10000/10000, SSE 10000/10000 exact, max diff 0 | logs/parity_run.log |
| stage b (+ O6 threats), seed 13452 | AVX2 10000/10000, SSE 10000/10000 exact (9978 non-zero evals) | same |
| stage c (+ O7 pawn pairs), seed 13453 | AVX2 10000/10000, SSE 10000/10000 exact (9981 non-zero evals) | same |
| planted bug: PARITY_MUTATE=1 (+1 on one reference value) | stage a 9999/10000 -> FAIL, exit 1 (the script can fail) | same |
Meaning: on random weights every feature index matters, so the Rust input type (piece-square, threats, pawn pairs, both
perspectives), the FORGENN2 layout written through write_v2 and the float32 reference all agree with the engine's own loader,
feature code and output kernel, on both SIMD paths. Not covered yet: H 768 / 1024 / 1536 (engine builds with that
FORGE_NNUE_HIDDEN) and a trained net (needs a GPU window: bullet has no CPU backend). Hashes: logs/artifacts.sha256.

## R14 (2026-11-02): CR final delta d884c23b + full cargo build + fresh H256 parity
Couns: "git apply C:\Users\Administrator\qa_crfix_astra_r10\r13_patches\p4_final_delta_ports_crfix.patch (md5 d884c23b) on
df79fb6e, check parity_v2.sh 9c124cc3, GPU_REQUEST.md 4246dfd5, main.rs 9ede6e56, full cargo build, rerun the 256 parity".
| check | result | evidence |
|---|---|---|
| patch md5 | d884c23b061896fb9d66256cc22bd400 | - |
| `git apply --check`, then `git apply` (worktree root, LF files) | clean, 3 files | - |
| result md5: parity_v2.sh / GPU_REQUEST.md / forge_v2_bullet/src/main.rs | 9c124cc3 / 4246dfd5 / 9ede6e56 = CR's values | - |
| older CR files p4_v2nets_crfix.patch (1e7b5d20), p4_v2nets_delta_crfix.patch (cc826b0a) | apply neither forward nor reverse on df79fb6e: their items were fixed in e23fca30 (table above); d884c23b ports the rest | - |
| full cargo build: fresh target dir D:\o14a\p4\target_mock, `--release --offline`, mock backend, CARGO_HOME = own copy, 2 jobs, CPUs 2-3 BelowNormal, tracked Cargo.lock unchanged | Finished in 46.84 s, 0 warnings, 0 errors; forge-v2-bullet.exe sha256 70cbae12be24316c... | logs/cargo_build_full_r14.log, logs/artifacts_r14.sha256 |
| legal-only FEN file (legal_fens.py: python-chess Board.status() == STATUS_VALID, run-only test oracle) | 10000/10000 legal, file byte-identical to fens10k.txt (sha256 457ecb48...) | logs/parity_r14_h256.log |
| H256 parity in a fresh work dir (run_parity_r14.sh refuses existing dirs; parity_v2.sh now always rebuilds ref_<s>.txt) | stage a / b / c: AVX2 10000/10000 and SSE 10000/10000 exact, max diff 0 (nonzero evals 9969 / 9978 / 9981), PARITY PASS, exit 0 | logs/parity_r14_h256.log |
| planted bug (PARITY_MUTATE=1, second fresh dir) | stage a 9999/10000 -> FAIL, exit 1 (as required) | same |
| random nets | byte-identical to the R13 nets (sha256 39e38df8 / c30e9cdd / 157d43ea; fnv1a64 15b924b9 / ac1e5682 / e0452809) | logs/artifacts_r14.sha256 |
| engine harness exes | unchanged R13 builds (v2_eval_avx2 d90efc87, v2_eval_sse c30b53f3; b7c17722 tree, -DFORGE_NNUE_HIDDEN=256) | same |

### Review milestone R14-P4-1 (structured self-review, NOT independent - no sub-agents in R14)
- Reviewed: the d884c23b diff (3 files) against df79fb6e, the trainer build and the parity run; candidate = tooling only
  (forge-v2-bullet.exe 70cbae12), no engine change.
- Findings: (1) parity_v2.sh still reuses `rand_<s>.nnue2` when it exists; harmless for parity (reference and engine read the
  same net) and the R14 runner only accepts fresh dirs - kept as CR wrote it (the md5 9c124cc3 is CR's checked file).
  (2) GPU_REQUEST.md still names F:\o13 run dirs; R14 forbids writes to F: (below its reserve) - the R14 request
  (opus_r14/b/GPU_REQUEST.md, Main item 1) uses C:/D: paths instead; this file stays as CR checked it.
  (3) main.rs: training argv 4..=9 matches `<stage> <binpack> <out> [hidden] [sb] [bpsb] [threads] [seed]`; unparsable
  numbers now panic instead of silently taking a default (CR's intent) - OK.
- Checks after: none needed (no fix). Next: H768 / 1024 / 1536 parity (block 2), then the GPU request.

## R14 (2026-11-02): parity above H256 - PASS at H 768 / 1024 / 1536
- Harness builds: nnue::v2 sizes everything with the compile-time HiddenSize (= FORGE_NNUE_HIDDEN, file `hidden` must
  match), and the R3 tree's embedded default net `src/nnue_weights.inc` static-asserts H = 256. So the H > 256 harnesses
  build from `D:\o14a\p4\r3_h` = the R3 tree copy without that one file (66 other files byte-identical, logs/r3_h_src.sha256;
  FORGE_HAS_NNUE = 0, which only removes the embedded default net; the v2 loader / features / output code is the same
  source). Same g++ flags as H256 (`-O2 -ffp-contract=off -fno-fast-math -static`, AVX2 = x86-64-v3, SSE = x86-64-v2):
  6 builds, 0 warnings each, SSE builds 0 ymm/zmm instructions (build_harness_r14.sh, logs/build_harness_r14.log).
- Runs (run_parity_hbig_r14.sh): per H a fresh dir, random nets of width H pre-generated with the R13 seeds 13451 / 13452 /
  13453, then CR's parity_v2.sh unchanged (md5 9c124cc3 checked in the log; it keeps the given net and always rebuilds
  ref_<s>.txt), forge-v2-bullet 70cbae12, the same legal-only 10k FENs.
| H | stage a (AVX2 / SSE) | stage b | stage c | result |
|---|---|---|---|---|
| 768 | 10000/10000 / 10000/10000, max diff 0 | 10000/10000 / 10000/10000 | 10000/10000 / 10000/10000 | PARITY PASS, exit 0 |
| 1024 | 10000/10000 / 10000/10000 | 10000/10000 / 10000/10000 | 10000/10000 / 10000/10000 | PARITY PASS, exit 0 |
| 1536 | 10000/10000 / 10000/10000 | 10000/10000 / 10000/10000 | 10000/10000 / 10000/10000 | PARITY PASS, exit 0 |
| 1536 planted bug (PARITY_MUTATE=1, own fresh dir) | 9999/10000 -> FAIL | - | - | exit 1, as required |
Nonzero evals 9986-9996 per stage (no all-zero output); hashes of the 6 harness exes and 9 nets: logs/artifacts_r14_hbig.sha256;
full log: logs/parity_r14_h768_h1024_h1536.log. Meaning: the trainer's feature lists + FORGENN2 layout + float32 reference
match the engine's own loader / features / output kernel at every width the GPU request uses. Not covered: a trained net
(needs a GPU window; bullet has no CPU backend).

### Review milestone R14-P4-2 (structured self-review, NOT independent)
- Reviewed: the r3_h copy (hash list: only nnue_weights.inc missing), build flags vs the R13 H256 builds, the parity runner
  (fresh-dir guard, seeds, unchanged parity_v2.sh), the log. Candidate = tooling only.
- Findings: the first build attempt failed on the embedded-net static_assert (expected after reading nnue.cpp; fixed by
  the copy without that file); the runner that ran had a sed-mangled comment line (control characters inside one `#` line,
  21 lines like the clean copy) - commands identical to build_harness_r14.sh. No other finding.
- Next: GPU request (R14 Main item 1, opus_r14/b/GPU_REQUEST.md).

## Next
GPU window request (R14 Main item 1, opus_r14/b/GPU_REQUEST.md); training only in a window Engine NNUE gives.

### Review milestone R14-P4-3 (20-minute review pass, structured self-review, NOT independent)
- Re-checked on origin: parity_v2.sh / GPU_REQUEST.md / main.rs still have CR's md5 9c124cc3 / 4246dfd5 / 9ede6e56; the
  parity and build claims above match logs/parity_r14_*.log and logs/cargo_build_full_r14.log.
- Found + fixed: opus_r14/b/GPU_REQUEST.md said "the runner checks them itself" - no run wrapper exists yet; reworded (the
  wrapper comes with the first window and must check before and during each run).
