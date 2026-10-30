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
outside any previously sealed output. Reserve room for both the archive and its
extracted files; original spools and logs are intentionally retained.

If the main archive fits one GitHub asset, check its SHA256 against the receipt
before extraction. If it exceeds the limit, its transport chunks are **not
separately extractable archives**. Download all numbered chunks and
`transport_manifest.json` into one NEW directory containing only those files.
Keep this utility and the joined archive outside that directory:

```powershell
# Run from the checked-out repository with Python 3.10 or later.
$Parts = 'D:\astra_a1_downloads\parts' # NEW directory: manifest + numbered chunks only.
$Archive = 'D:\astra_a1_downloads\forge_astra_a1_data_results_20261030.tar.gz'
python validation/astra-a1-data/transport_parts.py verify "$Parts\transport_manifest.json"
if ($LASTEXITCODE -ne 0) { throw 'Transport verification failed.' }
python validation/astra-a1-data/transport_parts.py join "$Parts\transport_manifest.json" "$Archive"
if ($LASTEXITCODE -ne 0) { throw 'Reassembly failed; retain evidence and partial files.' }
Get-FileHash -Algorithm SHA256 -LiteralPath $Archive
```

The utility streams binary data, verifies every chunk and the whole archive,
rejects extra/missing/corrupt chunks, and never replaces an existing destination.
The source chunks remain intact. Joining retains a `.partial` hard link on
success; the output volume must support ordinary hard links (for example NTFS).
Windows runtime remains unverified here. Do not join with text-mode commands.

Create a new extraction directory, extract the complete archive, and run the
read-only verifier. Its full-record mode checks the FPOS/FHCE headers and every
output FEN/record, as well as manifests and declared accounting. Store its log
outside the extracted sealed folder:

```powershell
$Extract = 'D:\astra_a1_downloads\extracted' # Must not already exist.
$null = New-Item -ItemType Directory -Path $Extract -ErrorAction Stop
tar -xzf "$Archive" -C "$Extract"
if ($LASTEXITCODE -ne 0) { throw 'Extraction failed.' }
python tools/data/check_data_bundle.py "$Extract\completed\full10m" --full-records
if ($LASTEXITCODE -ne 0) { throw 'Sealed dataset verification failed.' }
```

The deeper independent audit is Linux-only and also uses the original input
paths from the run. Its preserved receipt covers all native responses and the
supplied original holdout prefix; `full10m_audit/AUDIT_USAGE.md` documents its
scope. Portable seal verification alone does not replay all native semantics.
Neither audit establishes training quality, game-level isolation or Elo.

IDEA_SOURCE: user-requested durable original evidence, same-project data formats
and publication contracts, and Python binary streaming/filesystem APIs.
