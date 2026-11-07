# T4 bullet HalfKA - commands used (read-only; no binary was produced, so there is no SHA256SUMS)

- Upstream head: `gh api "repos/jw1912/bullet/commits?per_page=1"` -> 5d70177680437b0ddf958bd4722d95afa78b0c,
  2026-11-05T12:05:42Z.
- Backends: `gh api repos/jw1912/bullet/readme`: "Training is supported on NVIDIA (`cuda`), AMD (`rocm`) and Apple
  Silicon (`metal`) GPUs".
- Dependencies: `gh api repos/jw1912/bullet/contents/crates/bullet_lib/Cargo.toml` and `.../crates/utils/Cargo.toml`.
  Licences from `https://crates.io/api/v1/crates/<name>` (User-Agent `oss-scout-licence-check`):
  - sfbinpack: GPL-3.0, max 0.6.5;
  - viriformat: MIT, max 3.0.0;
  - montyformat: AGPL-3.0, max 0.10.0.
- Data formats: `gh api repos/jw1912/bullet/contents/docs/3-data.md` (SfBinpackLoader, MontyBinpackLoader,
  ViriBinpackLoader, DirectSequentialDataLoader; bullet-utils converts text `FEN | score | result`).
- Network graph: `gh api repos/jw1912/bullet/contents/examples/advanced/main.rs` (lines 84-175 read: inputs, factoriser,
  pairwise FT, concat with `abs_pow(2.0)`, `select(output_buckets)`, SavedFormat quantisation).
- The crew's existing ROCm build recipe (read-only): `D:\o30\wt\opus_30h\a\build_bullet_o30.bat`.
