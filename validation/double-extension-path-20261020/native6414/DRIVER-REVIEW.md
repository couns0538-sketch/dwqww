# Independent native validation driver review

No blocking static adaptation issue found. Reviewed frozen candidate
`21538ec5416c909fc98a08688242a0b3b9710b25` against parent source
`cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`. This review ran no compiler,
engine, CTest, benchmark, sanitizer or Git mutation; it does not establish a
passing build, correct search policy or Elo gain.

Exact full-file comparisons confirm:

- `run-frozen-validation.py` changes only the explicit repository root, frozen
  commit, isolated source/build paths and source-evidence filenames.
- `run-actual-api.py` and `active-uci-edges.py` change only repository-root
  resolution, required because this evidence directory is one level deeper.
- `actual-api-concurrency.cpp` is byte-identical to the proven parent driver:
  SHA256 `25813c23a296b86bc90c045c3f123bfc82db2ed0404cc8de8b069156280e42b1`.

The full build driver retains complete Git export of CMake/LICENSE/src/include/
tests/bench/tools, tar-byte and exported-file checks, refusal to overwrite build
or result directories, serial j2 builds, full nine-CTest assertion, checked
phase exits, separate raw stdout/stderr and source/six-binary hash comparisons.
Release keeps strict x86-64-v3/znver5 flags, no fast-math, contracted FMA or LTO.
ASan/UBSan retain leak detection and halt settings. TSan retains real compiler
and linker instrumentation plus its default deadlock detector; the CMake ASan
option is correctly off for that separate profile. No assertion was removed.

The API driver must be invoked with this candidate's frozen source root and
matching core; its unchanged input-hash and result gates then establish the
compiled ABI provenance. The active-UCI driver retains all eight mutation
edges and complete legal-bestmove, readiness, capture, shutdown and sanitizer
checks. It imports the recorded trusted helper from the checkout, so preserve
that helper's hash in execution evidence as in the parent workflow.

The frozen engine-source diff contains exactly CMake/UCI version labels and
the reviewed path-counter repair in search.cpp. Its SHA256 is
`e766f20fb1fe21262b8ba45f46987fee949340f9af0f92ec296db5c158028bad`, identical
to the independently reviewed proposal. Headers, tests, NNUE and other engine
sources are unchanged. There is no weakened test to accommodate the candidate.

Only this review file was written. Execution results remain the responsibility
of the separate native validation run; search changes do not require complete
PV parity outside the explicitly controlled bench/signature checks.
