# Complete causal evidence archive

The completed, single cold/warm baseline diagnostic is preserved in
`archive-complete/forge-baseline-time-forfeit-causal-20261020-complete.zip`.
All originals and the independent staging tree remain present. Archiving ran
no engines, searches, games, builds or matches and changed no production or Git
files. This receipt does not change the diagnostic's unresolved original-hosted
cause or make a speed/strength claim.

## Identity and verification

| Item | Bytes | SHA256 |
| --- | ---: | --- |
| Complete ZIP | 3,713,161 | `7683500f3509c0ed19d3e5a4ff7c975844d6281509ce6d8e1b48227d148ea7de` |
| External manifest | 68,666 | `94ebd09e736ffcc483c1a6c542586499674ed4cd522977389af3548cfcd73dc9` |
| Archive RESULTS.json | See receipt | `530d4754414c8f2b24c6ff9890b359187e879ed26db761958a0cb9494997c62a` |
| Unchanged trusted archiver | See manifest | `952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c` |

The archiver byte-matched `HEAD:.github/hosted-tt-strength/archive_results.py`
before use. Its default 64 MiB maximum part size was set explicitly to
67,108,864 bytes. One ZIP was sufficient; there are no split parts.

The unchanged trusted CLI created and verified the ZIP. Its independent
`verify_archive()` invocation then reassembled the physical output, checked
its complete SHA256, compared internal/external manifests, rejected unexpected
or duplicate members, and read/decompressed every payload to verify size and
SHA256. All 291 payload files matched the independently hashed staging tree.
Every archived original also matched its live file before staging, after
staging and after archive verification. A final receipt readback checked the
published archive and manifest hashes. Both driver and archiver stderr are
empty; their return codes are zero.

## Scope

The 287 live originals total 12,987,019 bytes:

| Group | Files |
| --- | ---: |
| Complete causal validation tree at archive start | 113 |
| Complete instrumented source-v2 tree | 70 |
| Complete instrumented build-v2 tree, including executable/core and intermediates | 100 |
| Three original hosted inputs bound by PROTOCOL/READY | 3 |
| Trusted archiver | 1 |

The causal tree includes the baseline Git TAR, original compile failure,
cleanup and registry RED/GREEN fixtures, prior snapshots, final protocol and
READY, root clearance, root execution/analysis commands and outputs, both
complete runtime captures, phase analysis, RESULTS and REPORT. Source/binary,
core, compile-command/cache and original-input identities were checked against
the frozen records before staging. The source remains baseline `c5cbf97` plus
telemetry; executable SHA256 remains `861bb31fc0bf07fe95aa0e06d28facff0af3722285c23536879d4c99b2ee65a1`.

The external input roots are:

```text
/workspace/.cloud-setup/forge-forfeit-causal-source-v2
/workspace/.cloud-setup/forge-forfeit-causal-build-v2
/workspace/dwqww/validation/tt-strength-20261020/final-audit/game85-baseline-original-input.txt
/workspace/dwqww/validation/tt-strength-20261020/final-audit/game85-original-protocol.log.gz
/workspace/dwqww/validation/tt-strength-20261020/final-audit/forfeit-exchange.json
```

Staging is outside all input trees at
`/workspace/.cloud-setup/forge-forfeit-causal-archive-stage-20261020`.
The only causal-tree exclusions are this new receipt and `archive-complete/`
itself, preventing recursive archival. All failed attempts remain. No symlinks
were followed or archived. Directory paths, empty directories and original
permission modes are recorded in the included provenance inventory.

The ZIP stores original files under `files/payload/`, followed by each original
absolute path without its initial slash. Four additional
`files/archive-provenance/` records preserve the staging driver, original
file/directory identities and modes, exact archive command and staging checks.
The total payload is 13,137,513 bytes. The ZIP's internal `manifest.json` is
additional archive metadata.

## Commands and restoration

The executed staging driver was:

```sh
/workspace/.cloud-setup/venv/bin/python -B \
  validation/time-forfeit-causal-20261020/archive-complete/archive_complete.py \
  > validation/time-forfeit-causal-20261020/archive-complete/driver.stdout \
  2> validation/time-forfeit-causal-20261020/archive-complete/driver.stderr
```

The driver executed the unchanged trusted archiver with these exact arguments:

```sh
/workspace/.cloud-setup/venv/bin/python -B \
  /workspace/dwqww/.github/hosted-tt-strength/archive_results.py \
  --input /workspace/.cloud-setup/forge-forfeit-causal-archive-stage-20261020 \
  --out /workspace/dwqww/validation/time-forfeit-causal-20261020/archive-complete \
  --name forge-baseline-time-forfeit-causal-20261020-complete \
  --split-size 67108864
```

Exact command/exit records, stdout/stderr, complete before/after inventories,
payload manifest and verification result are retained in `archive-complete/`.
The source staging driver is retained for review, not for overwriting this
completed archive; it refuses stage/receipt reuse.

To restore, first verify the external manifest with the unchanged archiver's
`verify_archive(manifest_path)`. Concatenate manifest `parts` in listed order
when there is more than one; this archive has a single normal ZIP. Extract into
a new directory, preserving `files/`. Originals are under
`files/payload/workspace/...`; do not overwrite live originals. Use
`files/archive-provenance/LIVE-FILES-AND-MODES.json` to recreate recorded empty
directories and apply recorded permission modes before running a restored
executable. Verify each restored file's size/SHA256 against the inventory.

## Precisely scoped ignore candidates

All three live raw files below byte-match their verified archive payloads.
The paths, sizes, SHA256 values and exact ZIP members are recorded in
`archive-complete/IGNORE-CANDIDATES.json` and `RESULTS.json`. These are
recommendations only; no ignore rule was applied and no original was removed.

```gitignore
/validation/time-forfeit-causal-20261020/baseline-source.tar
/validation/time-forfeit-causal-20261020/diagnostic-attempt1/warm/engine-events.jsonl
/validation/time-forfeit-causal-20261020/diagnostic-attempt1/warm/manager-events.jsonl
```

Their sizes are respectively 3,502,080, 1,545,718 and 912,874 bytes. Retain the
readable phase analysis, runtime summaries, reports and all smaller fixtures.
