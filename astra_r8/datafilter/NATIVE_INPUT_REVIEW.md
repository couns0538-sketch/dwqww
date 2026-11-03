# Native input boundary review — repair pending, UNPROVEN

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
