# Recoverable Forge 6.4.20 evidence archive

The complete archive and one actual scratch recovery both passed. The unchanged
trusted helper verified the archive; a fresh independent audit passed **9,912
checks** with zero findings. The separately authorized restore completed once
with exit 0 and empty stderr. An independent read-only recovery audit passed
**6,089 checks** with zero findings.

The snapshot contains **1,889 original files**, **303,693,001 original bytes**,
and **306 original directory modes**. Including preparation provenance, the
archive has **1,937 payload files** and **304,819,625 uncompressed bytes**.
Original hashes, sizes, file modes and nanosecond timestamps matched before
copying, after staging, after archiving and during the independent archive audit.
All originals, staging, earlier archives and the recovered tree remain retained.

## Archive identity

The combined ZIP is 113,855,291 bytes, SHA-256:
`ee1bdd21707175cd57107a3a4a1c1daacd106975974b53d40338f0b9f1a22f7e`.
It is stored as two ordered raw parts, below GitHub's 100 MiB file limit:

| Part suffix | Bytes | SHA-256 |
| --- | ---: | --- |
| `zip.part0001` | 67,108,864 | `44de1a6ff175ecf9ae74b93e31663d312393b1b380ca8bef92a7d52cefad01d9` |
| `zip.part0002` | 46,746,427 | `f7e7e3bddd083e01ac9bd051f47774195c78e26f3d87bc7c5634f18df0d42398` |

The external manifest SHA-256 is
`9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478`.
[RESULTS.json](RESULTS.json), [ARCHIVE-SHA256SUMS](ARCHIVE-SHA256SUMS) and
[FINAL-VERIFICATION.json](FINAL-VERIFICATION.json) record the exact names,
identities, original execution receipts and verification boundaries. No redundant
oversized ZIP is retained.

## Preserved scope

The frozen candidate is `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`; consumed
parent 6.4.19 is `61f598056572dfade6994af8ad2e38817cd28aa3`. Scope includes:

- Complete candidate prototype, label/refinement failure history and root proofs,
  including the actual Windows publication receipt exactly once.
- All 75 native source files, three complete 163-file build trees and 243 closed
  native evidence files, including original raw sanitizer and runtime outputs.
- All 72 Windows source files, full build/runtime evidence, expanded release and
  original 14,531,624-byte Windows ZIP.
- The frozen root instructions, three development documents and experiment index.
- Closed actual-five producer captures and their exact executed `461a65` helper.
- Explicitly consumed parent source, engine, core, NNUE object and proof receipts.

Future performance packages, monitoring and coordination are excluded. The
root's 15 hash bindings and exact frozen inventory define this snapshot. Later
document updates do not alter these saved versions. No previous complete archive
was recopied or overwritten; no file was deleted, ignored or untracked.

All consumer preflight failures, four previous driver versions and exact change
diffs are retained. Native modes extend the earlier schema. Authenticated TAR
`0664` metadata and actual extracted-source `0644` modes remain distinct records;
producer files were never edited to fit the consumer. The 112-row prototype
manifest retains its original historical coverage.

## Verified recovery

The actual restore destination is
`/workspace/.cloud-setup/forge20-recovery-check-attempt1`. It was absent before the
one authorized execution. The helper verified all parts and payloads before
creating the tree. The independent audit then checked every recovered byte, all
1,889 original file modes and nanosecond timestamps, and all 306 directory modes.
It found exactly 1,937 files and 326 mapped/structural directories, with no extra
files or symlinks. The 48 provenance files use `0600` permissions.

The ZIP helper itself records generic `0600` permissions. To recover executable
permissions, use the embedded mode map through the reviewed helper and choose a
NEW nonexistent absolute destination:

```text
python3 -B restore_new_scratch.py --parts /path/to/archive-complete --destination /tmp/forge20-recovery-new --manifest-sha256 9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478
```

The helper SHA-256 is
`1efc0d1998d33973eed109e28e042ed047237ffc3ddcc94d4651ef3eb91050fc`.
Eight synthetic safety tests also passed. Original absolute paths were not
write targets according to the reviewed helper, pinned command and completed
receipts; this is a static scope check, not a syscall trace. The recovery audit
opened no live originals or later development documents.

[Independent archive audit](INDEPENDENT-ARCHIVE-AUDIT.json) and
[independent recovery audit](INDEPENDENT-RECOVERY-AUDIT.json) contain the full
checks. Their raw stdout/stderr and exact executed scripts are preserved beside
them. These final verification sidecars were created after the immutable archive
and are retained directly in the repository; they are not recursively archived.

No engine, compiler, Git, benchmark or game was executed by this archival task.
Native 36 CTests / 56 parity / 8 active-UCI checks and Windows 11 Wine / 1,538
artifact checks belong to the original preserved evidence. This work proves
local byte and permission recovery; it makes no new correctness, NPS, Elo,
native Ryzen hardware, Stockfish strength or remote-publication claim.
