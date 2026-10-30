# Astra A1 original data and evidence artifacts

All local data checks passed and **all six release assets are published** at
[astra-a1-data-results-20261030](https://github.com/couns0538-sketch/dwqww/releases/tag/astra-a1-data-results-20261030).
The [verified publication receipt](../validation/astra-a1-data/publication/verified_publication.json)
records every asset URL, byte size and SHA256, independently compared with
GitHub's uploaded-state metadata. The initial cloud HTTP401 is preserved;
repository Actions successfully delivered the exact original bytes instead.

The results archive preserves complete sealed filter/relabel directories,
including native request/response logs, decisions, retained-row provenance,
the deduplication index, manifests and original output/partial files. The failed
first attempt is a separate archive explicitly labelled **unsealed**; it is
evidence, not training input. The original 003 input archive remains in the
user's `data-sample-10m-20261030` release and is referenced by URL, size and hash.

## Recovery and verification

Use the exact source from `astra-a1-data`. Obtain the verified artifacts listed
in the final publication receipt. Keep downloads outside the repository and
outside any previously sealed output. Reserve room for downloaded chunks (if
used), the complete archive, and its extracted files; original spools and logs
are intentionally retained. Exact Linux baseline/current/historical helper binaries are included under `binaries/`; these are evidence binaries, not Windows executables. Tar stores regular files without execute bits: on Linux, restore execute permission only for the binary you intend to run after verifying its hash.

Run the blocks below from the checked-out repository in PowerShell 7 with Python
3.10 or later. Set these shared values for either download method. Use the actual
archive filename and whole-archive SHA256 from the final publication receipt;
the verified local archive hash is filled below and must also match the final publication receipt:

```powershell
$ErrorActionPreference = 'Stop'
$Archive = 'D:\astra_a1_downloads\forge_astra_a1_data_results_20261030.tar.gz'
$ExpectedArchiveSha256 = '148803c5a45a5e291c18f667b918100ec1fa1a8e08d5a74dfe430651b3f1418f'
if ($ExpectedArchiveSha256 -notmatch '^[0-9a-fA-F]{64}$') {
    throw 'Set ExpectedArchiveSha256 to the whole-archive hash in the final publication receipt.'
}
```

This release uses **two chunk assets**, because the complete archive is 2,329,781,152 bytes. Follow the chunk method below. The direct method applies only if you already possess the verified complete archive. Reserve at least 12 GB for download, reassembly and extraction.

Choose the applicable download method:

- **Direct archive asset:** download the complete archive to `$Archive`, then
  skip the chunk block and continue with the shared SHA256 check below.
- **Chunk assets:** the chunks are **not separately extractable archives**.
  Download every numbered chunk and `transport_manifest.json` into one NEW
  directory containing only those files, preserving their exact names. Keep
  this utility and the joined archive outside that directory. `$Archive` and
  `$Archive.partial` must not already exist. Run:

```powershell
$Parts = 'D:\astra_a1_downloads\parts' # Manifest + numbered chunks only.
python validation/astra-a1-data/transport_parts.py verify "$Parts\transport_manifest.json"
if ($LASTEXITCODE -ne 0) { throw 'Transport verification failed.' }
python validation/astra-a1-data/transport_parts.py join "$Parts\transport_manifest.json" "$Archive"
if ($LASTEXITCODE -ne 0) { throw 'Reassembly failed; retain evidence and partial files.' }
```

For **both** download methods, enforce the publication receipt's whole-archive
hash before extraction:

```powershell
$ActualArchiveSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash
if ($ActualArchiveSha256 -ine $ExpectedArchiveSha256) {
    throw 'Archive SHA256 differs from the publication receipt; do not extract it.'
}
```

The utility streams binary data, verifies every chunk and the whole archive,
rejects extra/missing/corrupt chunks, and never replaces an existing destination.
The source chunks remain intact. Joining retains a `.partial` hard link on
success; that name and the final archive share storage and are not independent
backups. The output volume must support ordinary hard links (for example NTFS).
Windows runtime remains unverified here. Do not join with text-mode commands.

Create a new extraction directory, extract the complete archive, and run the
read-only verifier. Its full-record mode checks the FPOS/FHCE headers and every
output FEN/record, as well as manifests and declared accounting. Store its log
outside the extracted sealed folder:

```powershell
$Extract = 'D:\astra_a1_downloads\extracted' # Must not already exist.
if (Test-Path -LiteralPath $Extract) { throw 'Choose a NEW extraction directory.' }
$null = New-Item -ItemType Directory -Path $Extract -ErrorAction Stop
tar -xzf "$Archive" -C "$Extract"
if ($LASTEXITCODE -ne 0) { throw 'Extraction failed.' }
$VerificationLog = Join-Path (Split-Path -Parent $Extract) ('full10m-verification-' + [Guid]::NewGuid().ToString('N') + '.json')
python tools/data/check_data_bundle.py "$Extract\completed\full10m" --full-records > "$VerificationLog"
if ($LASTEXITCODE -ne 0) { throw "Sealed dataset verification failed; see $VerificationLog" }
Get-Content -LiteralPath $VerificationLog
```

The deeper independent audit is Linux-only and also uses the original input
paths from the run. Its preserved receipt covers all native responses and the
supplied original holdout prefix;
[full10m_audit/AUDIT_USAGE.md](../validation/astra-a1-data/full10m_audit/AUDIT_USAGE.md)
documents its scope. Portable seal verification alone does not replay all native semantics.
Neither audit establishes training quality, game-level isolation or Elo.

IDEA_SOURCE: user-requested durable original evidence, same-project data formats
and publication contracts, and Python binary streaming/filesystem APIs.

## Published files

| File | Bytes | SHA256 |
|---|---:|---|
| [forge_astra_a1_data_results_20261030.tar.gz.part000000](https://github.com/couns0538-sketch/dwqww/releases/download/astra-a1-data-results-20261030/forge_astra_a1_data_results_20261030.tar.gz.part000000) | 1,800,000,000 | `9cee994b0933babed9eca05d8121a808b2c16cc0ca8568c63eedeedab22d7a3e` |
| [forge_astra_a1_data_results_20261030.tar.gz.part000001](https://github.com/couns0538-sketch/dwqww/releases/download/astra-a1-data-results-20261030/forge_astra_a1_data_results_20261030.tar.gz.part000001) | 529,781,152 | `150ee0160a8d6c0b07730a0b28d406d7c332597e3f558e15d770b0c423b71ef0` |
| [transport_manifest.json](https://github.com/couns0538-sketch/dwqww/releases/download/astra-a1-data-results-20261030/transport_manifest.json) | 698 | `2bfb4ac70b683580261de00d182ffc3a0948ae952e2c81b429a12a406679afe1` |
| [forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz](https://github.com/couns0538-sketch/dwqww/releases/download/astra-a1-data-results-20261030/forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz) | 94,455,551 | `beb2f5c265357071c3408457ca02622700bc925781661f2f9f8f76f5c25e2ca8` |
| [forge_astra_a1_data_results_20261030.tar.gz.receipt.json](https://github.com/couns0538-sketch/dwqww/releases/download/astra-a1-data-results-20261030/forge_astra_a1_data_results_20261030.tar.gz.receipt.json) | 67,470 | `e050cdb345985daeddfd2448c43b115b5bb41d40c9478f92671e620016c6b0aa` |
| [forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz.receipt.json](https://github.com/couns0538-sketch/dwqww/releases/download/astra-a1-data-results-20261030/forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz.receipt.json) | 12,524 | `41028197d97b175deb5dea12a12f7dca28627285af739b7274fa07b251109889` |
