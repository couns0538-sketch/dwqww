# Bounded hosted Linux TT strength test

Status: **Reviewed source gates passed; prospective single-push launch ready**. Candidate Forge 6.4.12 source
`8865666cc0ab4961cd507bae40ff6ce44e9319df` is frozen against Forge 6.4.11
`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`. Release, ASan/UBSan and TSan each
passed all nine full-engine CTests, including perft and UCI regression. Seven
actual public-API concurrency/cleanup groups passed in all three profiles;
eight active-UCI lifecycle edges passed under TSan. Default TSan deadlock
checking remained enabled. All eight Windows/Wine checks and an independent
artifact audit passed. Exact proof-file hashes are frozen in protocol.json.
The final `--require-ready` receipt records the source/review launch gate.
These correctness and mocked package checks provide no host-readiness,
speed or Elo evidence. No launch is performed by preparing this package.

The candidate opts the UCI single-worker path into an exclusive TT lease only
at exact Threads=1. A coarse gate, atomic request and sequential drain of 1024
stripes amortize locks while coherently blocking foreign TT accessors. At most
two locks are held. Shared/default API callers and SMP retain striped access
plus the gate flag check. Network, search, evaluation and replacement policy
remain unchanged. Source-export hashes and the original runtime diff are in
`validation/tt-strength-20261020/`. Changed non-build match helpers and the
counter diagnostic are separately visible in that inventory.

The unchanged native bench signature is 419798 (Windows/Wine 351063), and all
six cold/warm parent comparisons agree exactly. The counted 8204 versus 706157 mutex operations are
not an NPS or playing-strength result. The first all-stripes prototype
`a5d2fcb` remains preserved on its failed branch: correctness checks passed,
but TSan exceeded its 64-held-lock tool limit. The revised gated design passes
a default-limit TSan smoke check and the full-engine and actual-API suites above.
The original design and failed tool-capacity attempt remain preserved.

Both frozen sources build serially with GCC 14, generic x86-64-v3, identical
strict flags, `-ffp-contract=off`, no fast-math or LTO, and full CTest. Preserve
source exports, compile commands/cache, full test logs, actual engine/core and
pinned Fastchess `60d7a7a26c6b0582a15c112fb29a1829bef2adb3` bytes before timing.
Matches execute those archived binaries; every frozen input is finally rehashed.

The unchanged gross operational A/A gate runs two excluded fresh-process
bench11 warmups then three baseline/baseline pairs, 419798 nodes each, 30 seconds
total, CPU and wall median ratios 0.95..1.05 and every ratio 0.85..1.15. Failure
stops before games with no retry. Then four identical normal deterministic
color-swapped baseline A/A pairs use 10000 nodes/move and tc=inf. Neither gate
measures a 3% speed difference or supplies Elo evidence. The separate strict
NNUE performance A/A failure remains retained, is not retried and supplies no
TT speed result.

One uninterrupted serial native logistic SPRT tests H0=0/H1=+5 Elo,
alpha=beta=.05, equal 2+0.02, Threads1, Hash32, MoveOverhead10, OwnBookfalse and
restarton. Runtime handshakes require Ponderfalse and empty Book File defaults;
no Book File option is sent. Natural stopping is one native boundary or 1024
complete pairs/2048 games. A 300-minute emergency stop invalidates acceptance.
No adjudication, move cap, screen, retry, reset, resume, pooling, trimming or
outcome filter is allowed. A cap without boundary is inconclusive; H1 does not
prove a minimum +5 Elo gain.

Fresh 4 A/A plus 1024 SPRT positions are reserved from the original
[official-stockfish/books](https://github.com/official-stockfish/books)
`8moves_v3.pgn.zip`, commit `a804a97e709f40aa75a00f9d19e84915b7a3a45c`, SHA256
`7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e`.
All 34700 games are legally replayed for 16 plies. The 31603 strict EP-none
positions are filtered against all 42 frozen historical registries and unused
tails, the explicit 164-position confirmation cohort, and all 1028 reserved
NNUE strength positions belonging to active job 39348571407, launch 563bd406.
The resulting 30575 eligible positions are ranked using selector string
`20261020-tt-exclusive-drain-strength-v1`; the first four go to A/A and next
1024 to SPRT. CLI seed 20261022 reranks only those reserved pools. Original
source indices, selection/ranking hashes and exact runtime order/EPD hashes
are frozen in `provenance/`. No EP normalization or engine/outcome selection
occurs. This Stockfish 2013 self-play suite is not a balanced or representative
human opening corpus. Copied `research-*`, `check-output.json` and original
`check_openings.py` document historical upstream research; use the TT verifier
below for this reservation.

Fastchess warn-level engine communications preserve both sides' full UCI I/O.
The incremental scanner rejects warnings/errors, non-normal games, crashes,
timeouts, illegal moves, orphan pairs/processes, changed inputs and observed
output deletion/replacement/truncation. Independent audits require normal
unique paired games, exact opening prefix/full selection, matching native
pentanomial counts, one native acceptance for a decision and a finite final LLR
matching the independent 0/+5 likelihood. Finally rehash runs on success,
fault, signal and deadline. Only owned process groups are stopped; all original
raw PGNs, UCI, logs and failed attempts remain preserved.

The sole trigger is push to `forge/hosted-tt-strength-20261020-*`, attempt1.
There is no dispatch, schedule or retry. Job/build/match bounds are 330/6/310
minutes on ubuntu24.04. This bounded automation may outlive chat; it guarantees
no continuous agent or chat scheduler. Linux results do not establish native
Windows, Ryzen or Stockfish superiority. Platform hard loss may prevent cleanup.

Raw evidence always uploads. Original source/binary/PGN/log files are also
ZIP-archived outside the input tree with sizes and per-file SHA256. ZIPs over
64 MiB split into fixed 64 MiB byte parts with archive/part hashes, verified
reassembly and payload hashes. Fresh `results/tt-strength-RUNID-ATTEMPT`
branches preserve archives/manifests and cannot retrigger the launch workflow.
Raw PGNs are never reconstructed.

No-engine preparation commands are in
`validation/tt-strength-20261020/ROOT_CHECK_COMMANDS.md`.
