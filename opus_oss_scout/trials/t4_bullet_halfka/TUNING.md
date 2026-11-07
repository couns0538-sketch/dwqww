# T4 bullet HalfKA: plan and PC-specific settings for a GPU window (owner: NNUE)

1. **Build** (CPU only, no GPU needed), the same recipe as `opus_30h/a/build_bullet_o30.bat`, but with upstream head and
   a new example:
   - Environment: VS 18 BuildTools `vcvars64`; Rust toolchain `F:\bullet_hip\rust\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin`.
   - `HIP_PATH=F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel` (read-only), `GCN_ARCH_NAME=gfx1100`,
     `CARGO_HOME` / `CARGO_TARGET_DIR` on a drive with >= 5 GB spare.
   - `cargo build --release --features rocm --example <k32h3>`, Idle, 1 job, mask 0x3.
2. **Example**: copy `examples/advanced/main.rs` and change it:
   - `BUCKET_LAYOUT` to 32 buckets, no pawn-pawn inputs;
   - L1 = 1024, L2 = 32, L3 = 32;
   - the npt skip term;
   - the npt quantisation scales from skill forge-halfka-parity-test ("The exact integer rules").
3. **Data**: point the loader at a COPY of a J1 binpack shard (never the live trainer's input), or convert FPOS to
   bulletformat with an own tool; bullet-utils' text path needs `FEN | score | result` lines.
4. **First GPU-window run** (only in an owner window; the npt line must be stopped by the owner, not by us):
   - batch 16384 (as npt) and 65536 (the RX 7900 XT has 20 GB);
   - loader threads 2 and 3 (`READ_THREADS` / `MAP_THREADS`; the 30-h job saw 2.8M -> 4.0M pos/s from 2 -> 3 feeding
     CPUs);
   - 1 superbatch for pos/s, then a 20-superbatch smoke to check that the loss falls.
5. **Acceptance**: export -> forge-halfka-parity-test (12k FENs exact) -> ON bench stability -> the crew's holdout
   scorer -> gate.
6. **Licence** before any distribution: the GPL-3.0 `sfbinpack` and AGPL-3.0 `montyformat` crates (RESULT.md).
