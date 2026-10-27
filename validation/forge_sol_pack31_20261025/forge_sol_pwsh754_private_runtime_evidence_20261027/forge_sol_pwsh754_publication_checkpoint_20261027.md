# PowerShell private-runtime publication view — 2026-10-27

DATA/SOURCE ONLY. This new owned tmp view contains all65 original small-manifest members plus the original manifest itself. Original absolute/relative paths, modes, sizes and SHA256 values map to publication payload paths. Every original and payload hash was reverified; all modes are preserved. No source byte was rewritten. No downloaded tar.gz, ELF, DLL, shared library, extracted runtime or private working-cache directory is included.

Both original file traces are below512KiB (largest417438B), so no gzip transformation was needed. The original75MB download and192MB runtime remain intact in the separate private runtime subtree. Runtime readiness does not imply any project/Windows/autonomy validation; those remain independently scheduled and unrun here. The transient empty home-directory startup side effect, rollback, private-XDG correction and failed/network checks are retained as exact original evidence.

Use forge_sol_pwsh754_publication_mapping_20261027.json for original→view identity. The original readiness report/checkpoint/launcher are under payload with their original names. This view performs no installation, engine/project script execution or Git operation. Root owns publication.
