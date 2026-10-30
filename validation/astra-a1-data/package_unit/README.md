# Package utility synthetic regression evidence

Initial normal and optimized 16-test logs and their command/source hashes are copied unchanged from /tmp/astra_a1_package_verification_q995_h28 into initial_16_tests/.

The reserved manifest collision regressions were added before the repair. red.stderr records four failures across 18 tests: an uppercase auxiliary file, an uppercase directory prefix, and lower/uppercase manifest-prefix descendants were incorrectly accepted. The original source and new regression tests are preserved beside the logs.

The repair reserves the first archive-prefix component case-insensitively and seeds the file-name collision set with the built-in manifest name. green.stderr and green_optimized.stderr each record all 18 tests passing. Exact commands and source/test SHA256 hashes are in their corresponding command JSON receipts. The repaired source is also preserved here.

All fixtures are synthetic and small. No full 10M archive, native workload, Git operation or network publication was performed by these tests. Fixture directories are retained under /tmp/astra_a1_package_unit_*; original data directories were not used or modified.

IDEA_SOURCE: parent review of portable case-insensitive archive-name collisions and user evidence-preservation contract.
