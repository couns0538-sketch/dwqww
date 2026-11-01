# NNUEWideOutput exactness argument

The production change retains float data, network bytes, accumulator layout,
feature update order, clamp operands, multiplication/addition order, and final
scalar conversion. It changes only how independent lanes are packed into vectors.

Old lane j is stored in AVX2 group j/8, element j%8. New lane j is AVX512 element j.
Both visit hidden indices j, j+16, ..., j+240 in that order. At each index:
clamp ours/theirs to [0,1]; round each square; round each product with its output
weight; round the sum of the two weighted terms; round its addition to the lane.
After the loop, both start at b2 and add lanes 0 through 15 in order, multiply by
400, divide by 2.25, clamp and truncate to int. No horizontal reduction is used.
The kit retains -ffp-contract=off -fno-fast-math. No integer requantization occurs.

All 512-bit input loads are unaligned. Only the existing alignas(64) local lane
array is stored with an aligned 512-bit store. HiddenSize is a multiple of 16;
the fixed network is 256. Accumulator and weight object sizes/alignment are unchanged.

The flag is false by default. UCI setoption already stops and joins search before
modifying it. No new per-node logging, allocations, synchronization or production
counters. Diagnostic counters and float snapshots exist only under
FORGE_NNUE_DIAGNOSTICS, never in the kit's production builds.

The differential harness compares every accumulator float bit against fresh refresh,
all sixteen output lane bits and pre-conversion output bits OFF/ON, returned NNUE
integers, HCE and combined residual-plus-HCE clamped integers. Its unchanged-lock
build provides a separate digest reference. Production bench pins cover integration
with Worker's incremental PSQT path; the harness does not claim to invoke that private path.
