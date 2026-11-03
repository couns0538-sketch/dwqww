# Native input boundary review — implemented and verified, UNPROVEN

Current status: the boundary and identity repairs below are implemented. The
affected 131-test run passes, including actual installed-native tensor comparisons.
Focused recheck approved broader verification, now complete: 544 tests plus
11 subtests PASS; all 999,953 selected rows pass current native-input admission
in 57.807 seconds with zero canonical-argument changes. Maximum halfmove is 99,
ply 299 and fullmove 150; scores span -3000..3000. This pass allocates no native
batches and makes no loader-throughput claim. Both new v8 CPU preflights and
strict published verification PASS, preserving the complete v7 file set/hashes.
Evidence: evidence/extension5h/verified_v8/input_repair_validation. Final review
remains scheduled. Historical inspection/planning notes explain the chosen scope.

Read-only inspection on 2026-11-03 found a mismatch between valid Forge FEN
text and the installed npt parser. Forge accepts repeated ASCII spaces/tabs and
signed-64-bit counter input. The installed npt parser splits only on a single
literal space, ignores a failed FEN parse in its fromFen wrapper, and parses
clocks with std::stoi before storing them in narrower integer fields. The
original Python adapter currently passes the input FEN unchanged. Its separate
score/ply guards do not prevent these native-boundary cases.

The focused reviewer confirmed these reachable paths by inspection. No unsafe
native reproduction or installed code modification has been performed. The
affected installed source is
`F:/opus_scratch/r6/nnue-pytorch-amd/data_loader/cpp/lib/chess.h`, Position::trySet
and Position::fromFen, called from `cpp/training_data_loader_abi.cpp`. Its
GPL/AGPL implementation is inspected for semantics only; no code is copied.

The smallest planned repair is in the original local Python adapter's input
admission. After normalized-record validation, construct only the ABI argument
with single ASCII spaces and decimal clock strings. Preserve the original FEN
and all metadata. Require halfmove clock 0..255 and normalized zero-based ply
0..65534; native internal ply is one greater. White fullmove32768 fits; Black
fullmove32768 does not. Reject excess counters without clamping or resetting.
Validate every row before the single native batch allocation.

This is input correctness, not a native loader, throughput, search or speed
change. All installed npt files and the DLL remain read-only and hash-pinned.
The current selected self-play data is unchanged. Native representability of
the entire selected cohort will be checked explicitly; current source-admission
scans do not establish it.

Authored regressions cover whitespace/decimal normalization, both turn colors,
original metadata preservation, all counter boundaries, rejection before ABI
entry and a later invalid row preventing the whole batch allocation. Unsafe
counter cases use a monitored/mock ABI boundary, not a deliberate host crash.
Actual canonical-versus-noncanonical native tensor comparisons run only after
the input repair. Tests remain queued while the two corpus audits use both CPU
slots. No pending repair is called accepted.

Once reviewed and verified, the handoff migration must admit only the exact
local npt_adapter.py path in addition to the previously reviewed local files.
Installed-runtime restrictions remain intact. A new v8 directory will carry
fresh full-cohort admission, both CPU recipe preflights and strict verification;
the protected `extension3h_20261103/handoff_v7` directory remains untouched.

The same input-boundary review found two independent identity races. RowFile
hashes the source, indexes it separately, then records the later size/mtime;
an intervening rewrite can become the new accepted baseline. Its fetch checks
only the path before reading. The planned repair binds complete file identity
before/after indexing and the opened handle before/after each read, retaining
the same offsets and sampler. This is metadata-based mutation detection between
batches, not a claim to rehash the entire dataset for every batch.

The entry point also discards the verified manifest digest before Context loads
the manifest again. Context hashes a separate later read rather than the exact
bytes it parsed. The planned repair binds the verifier's identity before either
RowFile is constructed, hashes the parsed bytes, and rechecks the original path
before preflight PASS or delegation. The reviewer confirmed both paths and
required handle checks so temporary path redirection cannot evade path-only
checks. Deterministic temporary-fixture mutation tests are authored; no original
dataset or manifest is mutated by those tests.

The per-batch identity check is deliberately a file/handle metadata check.
Python 3.12 on Windows still reports creation time in st_ctime; it is not a
portable last-change clock, and nanosecond fields do not imply nanosecond
filesystem precision. Keep the device/file identifier and size/mtime checks,
compare the actual opened handle, and run healthy Windows cases as well as
mutation cases. Initial/final content hashes establish indexed input identity;
metadata checks do not promise detection of adversarial same-size writes with
restored timestamps. See the [Python 3.12 stat contract](https://docs.python.org/3.12/library/os.html#os.stat_result).

Actual verification exposed an additional platform distinction: for one healthy
fixture the path's st_ctime_ns equalled birth time, while fstat's st_ctime_ns
reported a later change time. The first repair therefore rejected that fixture.
A deterministic regression reproduced it; the corrected adapter retains all
path fields and compares the handle's device/file ID, size and mtime, omitting
only handle ctime on Windows. Unix handle ctime remains checked. Failed evidence
is preserved and the corrected affected suite passes.
