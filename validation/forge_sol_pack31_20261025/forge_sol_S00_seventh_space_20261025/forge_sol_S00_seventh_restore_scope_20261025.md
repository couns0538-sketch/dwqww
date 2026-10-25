# Seventh closed-cache preservation, 20261025

Metadata only is in Git. The 32 lossless gzip payloads remain LOCAL ONLY under `/workspace/forge-pack24-20261025/forge_sol_S00_seventh_space_20261025/payloads/`; they have not been uploaded or copied into this checkpoint. Restore depends on those retained local payloads.

The original verified map records 32 physical hardlink groups / 57 path aliases, 145771276 physical raw bytes and 116506602 bytes reclaimed. Python and independent GNU gzip decoding/SHA checks preceded raw-cache replacement. The source files, logs, main/helper ELFs and experiment evidence were retained. This concerns only closed legacy core/compiler caches, not accepted source or ongoing native work.

Use the exact restore-map path, original SHA256, mode and alias grouping to restore selected files into a NEW private destination. Verify the compressed-file hash and full decompressed bytes/SHA before use. Do not overwrite a live build or assume a new machine has the local payloads. No cache archival is performed by this metadata checkpoint.
