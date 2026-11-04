# Item A - the GPU path (the R14 ROCm trainer, made residual) - READY, NOT RUN (no GPU window in this job)

Why not run: the GPU was booked by the npt keeper for the whole job (window to 2026-11-08 00:00 PC; live line s39, next
s40 at 15:48 Nov 3); no written release from Engine QA. Everything below was built and checked on the CPU without
loading the GPU runtime. The CPU fine-tune (o30_fit.py) produced this job's candidates instead.

## What exists now
| piece | where | check |
|---|---|---|
| private copy of the trainer library da426a49 (MIT; the owner's tree F:\bullet_hip\src untouched) | `D:\o30\bullet` | - |
| patch: `ValueTrainerBuilder::residual_base(f)` - the value mapper fills a dense input "base" per datapoint and the loss uses output + base; the saved net is the output without it; `DataReader` re-exported | `opus_30h/a/bullet_residual.patch` md5 b924aa06fe4c8486fbacf254fd85f9c0 | cleanroom_lint CLEAN; compiles (mock + ROCm) |
| trainer crate, R14's forge-v2-bullet + `r` mode: own record type (FPOS board, score, HCE, result), ForgeV2R inputs (king buckets + mirror exactly as include/forge/nnue_v2.hpp), 8 piece-count output buckets, streaming FPOS / FHCE reader with the o30_data.py skip lists and jobA overrides, 8 shards mixed per chunk, deterministic per (seed, chunk) so a resume continues the stream; `rfeatures` self-check mode | `opus_30h/a/forge_v2_bullet_o30/` | feature lists + output bucket = o30_fit.py features() (itself = the engine through the scorer) on 2,000 rows x 3 maps (KB1, KB4, KB4 mirrored): 0 mismatches |
| mock build (CPU, compiles, runs `rfeatures`) | `D:\o30\target_mock\release\forge-v2-bullet.exe` sha256 dcf7845b1316198686aba58b1e2fa010518eb597d080c65f6574e508372ec616 | 0 errors |
| ROCm build (links amdhip64_7 / hipblas / hiprtc07013; not run) | `D:\o30\target_rocm\release\forge-v2-bullet.exe` sha256 a217d2a973a2d199f9bcb465b2dd6423916dae3da32470c71be29f5c1e8e96fc | 0 errors, `opus_30h/a/build_bullet_o30.bat rocm` |
| exporter `export_v2r.py` (library layout -> FORGENN2 residual, KB map, mirror, OB8) | `opus_30h/a/` | a synthetic checkpoint in the library layout -> exported KB4 mirrored net -> engine parity 10000/10000 x AVX2 / SSE / scalar |
| override files for the Rust reader | `D:\o30\data\override_npy\` (o30_data_npy.py) | 988,336 rows (461,965 + 526,371) |

## Commands for the first window (after Engine QA's written release, quoted into D:\o30\WINDOW.md)
Environment as `build_bullet_o30.bat rocm` (vcvars64, HIP_PATH = the npt venv's SDK read-only, PATH with its bin dirs,
GCN_ARCH_NAME=gfx1100); checks before and during the run as in R14's GPU_REQUEST.md (window note, keeper says npt not
running, no production python on the GPU, RAM >= 8 GB, D: >= 51 GB).
1. 10-minute smoke (the one thing the CPU could not check: the layout of a REAL saved file):
   `forge-v2-bullet.exe r D:/o30/data D:/o30/gpu/smoke one 0 256 2 64 2 30001 0.001 0.4 8`, then
   `export_v2r.py <out>/<checkpoint>/quantised.bin smoke.nnue2 --kb-map one`, `o30_score_v3.exe --net smoke.nnue2 ...`
   (the loss must be near the trainer's printed loss) and `parity_o30.sh` (engine = reference).
2. Main runs (~2-3M positions / s expected from R13's 2.30M at H1024 stage a): KB4 rank map (the CPU decider's best
   shape) and KB1, 40 superbatches x 1024 x 16384 = 671M positions each, lr 1e-3 cosine to 1e-5, wdl 0.4 (b = 0.6),
   from scratch; then the same net_pack.sh / net_final_checks.sh / INDEX.md flow as the CPU nets.
3. Better labels next: the 50M relabel (R14-B relabel2.py) as an extra data source of the same reader (a second
   FPOS-like source), since the CPU fine-tunes say the lock net is converged on the 5k-node self-play labels.
