Source-only next-opportunity review, 2026-10-20 UTC

Inspected checkout HEAD f7341e3047aa7b98e6a9de9587a3656b00ecf811;
production candidate20 fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e.
Read AGENTS.md, current NEXT_EXPERIMENTS/EXPERIMENT_LEDGER, current pawn-span
prototype report and actual evaluation/search call sites. No engines, builds,
timings or Git mutations. This note is the only added file.

Candidate19's qualified hosted throughput result remains workload-only. The
18vs17 strength run is separate;20's full frozen validation was still pending
in the inspected docs. Neither proposed item has execution evidence. No new
proven playing-strength defect was found. These are bounded exact-behavior
speed hypotheses, not replacements for the completed SEE, MovePicker, qsearch,
root accounting, PSQT or pawn-span changes. Targeted current docs/validation
search found no existing implementation of either mechanism below.

1. Nearest-own-pawn distance: fixed radius queries instead of scanning every pawn.

src/eval.cpp:269-274 scans every own pawn for BOTH kings on every classical
static evaluation, including pawn-cache hits (cache only skips pawn structure at
400-417). Worker::static_evaluate at src/search.cpp:605-609 reaches the classical
runtime evaluator in the default residual-NNUE path, so this work remains active.
The exact function is Chebyshev distance (include/forge/bitboard.hpp:95-100).

Small independent candidate: precompute per-square masks of squares with distance
<=radius. For a nonempty pawn bitboard, a binary search of radius0..7 needs three
mask-intersection decisions to recover the exact minimum; radius7 need not be
stored (64*7*8=3584bytes). Preserve the no-pawn branch and current add call.
A singleton-pawn direct square_distance path can avoid worsening sparse endings;
freeze that choice before timing. This adds no score cache or invalidation policy,
changes no weights, and does not alter score-addition order or trace coefficients.

Testable hypothesis: it reduces king-distance work in multi-pawn middlegames.
First compare the actual helper to the unchanged explicit min-over-pawns oracle:
all64 king squares x64 singleton squares, both colors, empty/sparse/dense/doubled
pawn sets and full corpus. Include distance0 in the pure helper oracle even though
legal boards exclude overlapping king/pawn. Require identical public cached,
uncached and full traced evaluations, then exact parent1T cold/warm search trees.
Only then measure a frozen calibrated hosted workload; added table loads/branches
may lose, especially with few pawns. No speed or Elo prediction is established.

2. Retain queen diagonal/orthogonal attack components for WeakQueen.

src/eval.cpp:131 calls attacks::queen; include/forge/bitboard.hpp:147-149 expands
that to bishop(square,occupied)|rook(square,occupied). The same queen iteration
then calls BOTH functions again at eval.cpp:190-191 for WeakQueen. Preserve the
two components from the first computation and consume them at the later site.
Keep the existing queen-exclusion and directional attacker-type masks; simply
intersecting the combined queen mask with enemy bishop|rook is WRONG because
it would count bishop-on-file/rook-on-diagonal attackers. Existing rook mobility
also uses x-ray occupancy (line129), so it is not interchangeable with the normal
rook rays at172/176. Do not broaden this candidate to those cases.

First remaining action is generated-code inspection on the frozen actual core:
these calls are inline and the compiler might already eliminate repetition.
Discard the proposal if that is so; source repetition alone is not measured work.
If loads/index arithmetic survive, a tiny explicit-reuse prototype should preserve
all95 current public/cache/runtime/full-trace oracle positions plus diagonal/file
sliders, opposing queens, blockers and promoted multi-queen fixtures. Require
parent1T tree parity and an independently calibrated whole-workload gain before
calling it faster. This is lower priority than item1 and may be too small to retain.

Next action: after20's independent native clearance, inspect queen generated code
and freeze ONE isolated distance-query candidate against20; do not combine them
or alter the running18 strength experiment. No new run is authorized by this note.
