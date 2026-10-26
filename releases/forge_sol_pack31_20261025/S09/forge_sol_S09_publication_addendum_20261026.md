# S09 publication addendum — 2026-10-26

Use `sha256sum -c forge_sol_S09_SHA256SUMS_20261026.txt` from a complete downloaded delivery folder. This standard checksum file covers every original packet file plus this addendum. The original `MANIFEST_20261026.txt` contains purpose descriptions after a tab; it is a preserved descriptive manifest, not GNU sha256sum input. The original JSON manifest remains unchanged and valid.

Large DATA files are ordinary tracked Git files and are included in normal clones and immutable raw downloads. This cloud working tree omits selected large data bodies using Git's local skip-worktree index flag, with their objects in a separate temporary object store. All source, commits, trees and existing objects remain in primary storage. No old source or data was removed. Successful push and immutable byte verification, recorded separately, establish durable publication.

If the temporary object store disappears, use the pinned post-publication recovery metadata with the supplied V2 evidence rehydration helper. That helper checks exact bytes, SHA256 and Git blob OID and restores data objects only; it does not modify engine source, refs, the index or primary objects. The helper refuses optimized Python because its integrity checks require assertions. Ordinary fresh clones have no dependency on this cloud-local alternate store.

The original native report's pre-publication status is historical once the immutable publication receipt exists. All source/native correctness scopes and UNVERIFIED Windows, GPU, real-holdout, speed and Elo conclusions remain as reported. Continue S10 after publication verification; this is not completion of the finite queue.
