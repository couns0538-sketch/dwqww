# Astra A1 original data and evidence artifacts

Publication is pending until the completed 10M run passes its independent checks.
The final publication receipt will identify actual GitHub asset URLs, byte sizes
and SHA256 values. A local archive or a planned URL is not verified publication.

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
are intentionally retained.

Run the blocks below from the checked-out repository in PowerShell 7 with Python
3.10 or later. Set these shared values for either download method. Use the actual
archive filename and whole-archive SHA256 from the final publication receipt;
the placeholder deliberately prevents extraction before that value is supplied:

```powershell
$ErrorActionPreference = 'Stop'
$Archive = 'D:\astra_a1_downloads\forge_astra_a1_data_results_20261030.tar.gz'
$ExpectedArchiveSha256 = 'REPLACE_WITH_WHOLE_ARCHIVE_SHA256_FROM_FINAL_PUBLICATION_RECEIPT'
if ($ExpectedArchiveSha256 -notmatch '^[0-9a-fA-F]{64}$') {
    throw 'Set ExpectedArchiveSha256 to the whole-archive hash in the final publication receipt.'
}
```

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
