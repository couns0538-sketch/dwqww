# Item A - the GPU path (the R14 ROCm trainer, made residual) - READY, NOT RUN (no GPU window in this job)

Why not run: the GPU was booked by the npt keeper for the whole job (window to 2026-11-08 00:00 PC; live line s39, next
s40 at 15:48 Nov 3); no written release from Engine QA. Everything below was built and checked on the CPU without
loading the GPU runtime. The CPU fine-tune (o30_fit.py) produced this job's candidates instead.

## What exists now
| piece | where | check |
|---|---|---|
| private copy of the trainer library da426a49 (MIT; the owner's tree F:\bullet_hip\src untouched) | `D:\o30\bullet` | - |
| patch: `ValueTrainerBuilder::residual_base(f)` - the value mapper fills a dense input "base" per datapoint and the loss uses output + base; the saved net is the output without it; `DataReader` re-exported | `opus_30h/a/bullet_residual.patch` md5 b924aa06fe4c8486fbacf254fd85f9c0 | cleanroom_lint CLEAN; compiles (mock + ROCm) |
| trainer crate, R14's forge-v2-bullet + `r` mode: own record type (FPOS board, score, HCE, result), ForgeV2R inputs (king buckets + mirror exactly as include/forge/nnue_v2.hpp; maps one / rank4 / rank4x2), 8 piece-count output buckets, streaming FPOS / FHCE reader with the o30_data.py skip lists and jobA overrides, 8 shards mixed per chunk, deterministic per (seed, chunk) so a resume continues the stream; `rfeatures` self-check mode | `opus_30h/a/forge_v2_bullet_o30/` | feature lists + output bucket = o30_fit.py features() (itself = the engine through the scorer) on 2,000 rows x 3 maps (KB1, KB4, KB4 mirrored) and 2,000 rows of KB8 rank4x2 (2026-11-03 20:5x): 0 mismatches |
| mock build (CPU, compiles, runs `rfeatures`) | `D:\o30\target_mock\release\forge-v2-bullet.exe` sha256 941d8a2c5d5921dab26634b230802ef9a4db19db6a0deb53ccb60735afe7a9b2 (with rank4x2; the first build was dcf7845b) | 0 errors, 0 warnings, `build_bullet_o30.bat mock kb8` |
| ROCm build (links amdhip64_7 / hipblas / hiprtc07013; not run) | `D:\o30\target_rocm\release\forge-v2-bullet.exe` sha256 b1155cd44ebaeb43ef7a0585c9e15cb6d5197926aac4584f22a3fc8c4f4e8473 (with rank4x2; the first build was a217d2a9) | 0 errors, 0 warnings, `build_bullet_o30.bat rocm kb8` |
| exporter `export_v2r.py` (library layout -> FORGENN2 residual, KB map, mirror, OB8) | `opus_30h/a/` | synthetic checkpoints in the library layout -> exported KB4 mirrored net and KB8 rank4x2 net -> engine parity 10000/10000 x AVX2 / SSE / scalar, planted bug caught |
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
   shape) and KB8 rank4x2 (proven ready: `check_kbmap.sh rank4x2`, Rust features = Python features), 40 superbatches x
   1024 x 16384 = 671M positions each, lr 1e-3 cosine to 1e-5, wdl 0.4 (b = 0.6), from scratch; then the same
   net_pack.sh / net_final_checks.sh / INDEX.md flow as the CPU nets. (From scratch on the GPU vs the CPU's warm start
   from the lock net: the CPU nets reached S31 -5.6e-5 in 3.5e8 positions by starting AT the lock function; a GPU
   run from scratch has to beat that, so compare against n2e / n2L, not only against the lock net.)
3. Better labels next: the 50M relabel (R14-B relabel2.py) as an extra data source of the same reader (a second
   FPOS-like source), since the CPU fine-tunes say the lock net is converged on the 5k-node self-play labels.
