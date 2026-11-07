# T4 bullet HalfKA - commands used (sources read-only; one compile-only build, hashes in SHA256SUMS)

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
- Build (21:45-21:46): `git clone --depth 1 https://github.com/jw1912/bullet.git dl/bullet` (5d701776), then from PowerShell `& cmd.exe /d /c "C:\opus_5h\oss_scout\tools\t4_build_bullet.bat r1"` -> `cargo build --release --features rocm -p bullet_lib --example advanced` (environment in the .bat). A first attempt from Git Bash with `MSYS_NO_PATHCONV=1 cmd //d //c ...` never ran: cmd got `//d //c` literally and exited.
