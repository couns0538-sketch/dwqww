# T4 bullet for the K32H3^ HalfKA shape - RESULT (design check; no build, no GPU)

State: **design done, nothing built or run in this job.** Reasons:
- The GPU is busy (the npt trainer at 62-84 % compute; npt holds the GPU to Nov 8), and bullet has no CPU backend
  (README: "Training is supported on NVIDIA (`cuda`), AMD (`rocm`) and Apple Silicon (`metal`) GPUs").
- The bullet ROCm build itself is already proven on this PC (R14 P4 `D:\o14a\p4\target_rocm`, 30-h job
  `build_bullet_o30.bat`, snapshot of 2026-11-03).
- CPU time in this job went to T1b; a cargo build would have broken the 2-thread cap. Owner items below.

## Licence finding (applies to every bullet build, including the crew's)
`crates/bullet_lib/Cargo.toml` at upstream head 5d701776 (2026-11-05) depends on these crates.io crates:
- `sfbinpack` 0.6.4: GPL-3.0, Disservin/binpack-rust.
- `montyformat` 0.9.2: AGPL-3.0, official-monty/Monty.
- `viriformat` 2.0.1: MIT.

A built trainer therefore contains GPL / AGPL code. That is fine as an internal tool; nets are data. Do not copy any
bullet code into Forge, and do not ship a trainer binary without reading those terms.

## Can bullet express npt's K32H3^ net? (from `examples/advanced/main.rs` at 5d701776)

| npt K32H3^ piece (skills forge-halfka-parity-test, forge-nnue-pipeline) | bullet building block in the advanced example |
|---|---|
| HalfKA inputs, 32 king buckets, horizontal mirroring | `ChessBucketsMirrored::new(BUCKET_LAYOUT)` with a 32-entry layout (identity map = 32 buckets) |
| `^` factoriser (virtual features, folded into the real weights at export) | `l0/fac` weights `(L1, 768)` repeated over buckets, added in `SavedFormat::id("l0/psqt").transform(...)` |
| FT L1 1024 with pairwise product of the two halves, clamp 0..255 | `ft(...).crelu()` of each half, multiplied: `ft(0, L1/2) * ft(L1/2, L1)` |
| l1 -> [squared, linear] activations | `l1_out.concat(l1_out.abs_pow(2.0)).crelu()` |
| l2 32 -> l3 output, plus the skip `s1[L2-2] - s1[L2-1]` | `l2`, `l3` affine layers; the skip needs `slice` of `l1_out` added to the output (graph ops exist: `slice`, `+`) |
| quantisation (FT int16, l1 int8 at 2^14 / 2^7 shifts, ...) | `SavedFormat::...round().quantise::<i16/i8/i32>(scale)` per tensor |
| output buckets (if the npt line uses layer stacks) | `.select(output_buckets)` with `MaterialCount::<8>` |
| data: J1 binpacks (`F:\forge_j1_data\*.binpack`, 34 B / record, no chaining) | `SfBinpackLoader` (the GPL crate above) or own conversion to bulletformat |

The missing piece is an **exporter** to the exact nnue-pytorch `.nnue` container that Forge's `EvalFileHalfKA` reads
(header + architecture hash + per-layer layout + LEB128-compressed FT). bullet's `SavedFormat` writes raw quantised
tensors. A short own program (or a `SavedFormat` post-step) must write the npt layout. The parity harness of skill
forge-halfka-parity-test (12,000 / 12,000 exact) is then the acceptance test.

## Throughput references (measured by the crew, not by this job)
- npt K32H3^ L1 1024, batch 16384 on this GPU:
  - R11: ~200k pos/s steady (on R11's CPUs).
  - Production: 20 x 152.5M positions in 2 h 27 min, about 346k pos/s (skill forge-nnue-pipeline).
- bullet v2 nets (a much smaller input layer) on this GPU: 2.8M pos/s with CPUs 4-5 feeding, 4.0M with CPUs 3-5
  (30-h job). That gap does not carry over to HalfKA L1 1024; only a GPU-window run can say.

## Verdict
- Feasible as a design: every K32H3^ piece has a bullet equivalent in the upstream advanced example.
- Open:
  - an exporter (M, ~1 day) + parity;
  - one GPU-window throughput run;
  - the owner's view on the GPL / AGPL crates inside the trainer.
- **UNPROVEN**: no speed number for HalfKA in bullet on this PC.
