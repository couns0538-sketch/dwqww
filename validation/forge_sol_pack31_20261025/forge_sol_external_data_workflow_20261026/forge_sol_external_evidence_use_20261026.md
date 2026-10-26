# External evidence DATA objects — 2026-10-26

Actual local fixture: three cases PASS, with ordinary commit/push and a clean clone that has no alternates. No actual repository or credentials were touched. HTTPS download remains UNVERIFIED.

Root may place ONLY new large evidence-data blobs in an isolated /tmp object directory. Preserve existing primary objects and alternates; append the new alternate durably. For each data file, run hash-object -w --stdin with GIT_OBJECT_DIRECTORY pointing to external and GIT_ALTERNATE_OBJECT_DIRECTORIES to primary. Restore normal environment for update-index --add --cacheinfo 100644 OID PATH, then --skip-worktree PATH. Commit/push normally with gc.auto=0. Source patches, metadata, trees and commits stay primary.

Verify immutable remote bytes after push. Then save a primary metadata checkpoint pinning that artifact commit, raw URL, size, SHA256 and Git blob OID (fixture examples included). If /tmp is lost, run the V2 rehydrate helper without -O, using --metadata, --git-dir and --external-objects. It writes data objects only; it never edits primary objects, index, refs, alternates or working files. Never use --fixture-blobs in production.

Skip-worktree is local index state. Remote clones receive normal tracked files. Missing external storage makes local artifact reads fail until rehydration; keep the store until push and immutable verification succeed. No speed/Elo assertion.
