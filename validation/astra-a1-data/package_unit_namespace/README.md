# Unified portable archive namespace regression

The prior packager treated file names and directory names separately. A directory A/child.txt and a file a could both be archived successfully, although their destination paths collide on Windows. Distinct A and a directories, and case aliases of implicit ancestors across separate mappings, were also accepted.

Tests were added before the fix. red.stderr records three concrete failures across 23 tests: file/directory collision, two explicit case-alias directories, and differently capitalized implicit parents. Same-spelling shared implicit parents and already-rejected file-ancestor mappings were checked at the same time. The old packager and that first test revision are preserved.

The repair validates one casefold namespace for all files, all explicit directories, every implied ancestor, and the built-in manifest. Exact-spelling shared implicit ancestors remain valid; case aliases, file/directory conflicts, file ancestors and duplicate explicit directories are rejected before source hashing or archive creation. Direct archive writing and archive verification also call the same validator.

Two further low-level checks cover file-ancestor/duplicate-explicit rejection and rejection by the writer before creating a file. green.stderr and green_optimized.stderr each record all 25 tests passing; commands, source/test hashes and final snapshots are retained. Earlier package_unit evidence is untouched. All fixtures are synthetic, with no live engine/dataset/Git/network activity.

IDEA_SOURCE: final-review Windows casefold file/directory collision reproduction and user portable-evidence contract.
