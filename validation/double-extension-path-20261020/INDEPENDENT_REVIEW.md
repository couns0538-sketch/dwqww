# Independent review: double-extension path repair

**No blocking source defect found. Suitable for an isolated candidate and full
validation; this review does not accept a strength gain.** Reviewed frozen
`cecf0b9e3af5602053bcaf5c5d16ffc09f58850d` and the unapplied search-only patch
SHA256 `5efa616730df7e5824937031cd159b80918e0bb73cfce67e5b33d30a8e003d9e`.
Proposed search.cpp SHA256:
`e766f20fb1fe21262b8ba45f46987fee949340f9af0f92ec296db5c158028bad`.
No engine, compiler, timing experiment or Git mutation ran during this review.
Only this review file was written.

## Path semantics and recursion

The parent frame stores the count for the outgoing edge selected by its caller.
Copying that value into a stable local at positive-depth entry establishes the
current call's inherited budget, before any pruning recursion. Initializing the
current frame there is necessary: a move-loop-only assignment cannot protect
null or ProbCut calls that occur earlier.

- Ordinary PVS, LMR and full-depth re-searches receive the same selected edge
  count. Assigning inherited plus `(extension == 2)` for every searched move
  removes stale sibling state for single, zero and negative extensions.
- Null and ProbCut edges consume no double extension. Entry initialization keeps
  the current frame at the inherited count when these calls pass it to children.
  A ProbCut qsearch may change its child frame, but does not alter this parent's
  count; subsequent positive-depth search initializes that child again.
- There are two same-ply main-search recursion sites: high-depth null verification
  and excluded-move singular verification. Each reuses and can mutate the caller's
  current frame. Both restores are necessary and correctly occur immediately
  after return, before continuation or an aborted return. The stable local stays
  valid across either call because descendants do not change the parent frame.
- Double-extension eligibility uses the stable inherited local, retaining the
  existing `<= 6`, non-PV and score-margin conditions. With the initialized root
  count zero, inherited plus one therefore stays at most seven along a correctly
  accounted path. No depth, reduction, singular margin or tuning limit changed.

Root search uses stack_[4] and its allocated, zero-initialized sentinel parent;
existing private regression callers use stack_[5]. The new parent read is valid
for these entry points, including positive-depth terminal/aborted calls. A
nonempty excluded move changes move eligibility, not the inherited path budget.

The depth<=0 guard remains before the new assignment. That is safe for the
current call graph: qsearch never reads double_extensions and never reenters
positive-depth main search. Every later positive-depth reuse initializes its
frame at entry. Root terminal/preflight returns before recursion likewise leave
no extension consumer; the next full worker search initializes the stack.

## Evidence checked and limits

The V2 diagnostic shadow is independent of the real frame values: it starts at
zero, copies through null/ProbCut edges and adds one only for an actually selected
double extension. Same-ply verification retains the incoming shadow value.
Only this read-only diagnostic shadow and bounded journals are added by the
instrumentation. I independently summed all eight raw DE_SUMMARY records in
both stderr files and matched their saved command summaries.

Both runs covered 292,878 selected children, 6,520 single extensions, 184 double
extensions and 930 singular attempts. Baseline records show 151 same-ply changes,
159 single-parent mismatches, 5,038 child-path mismatches, 691 null-parent
mismatches, 313 ProbCut-parent mismatches and 4,138 incoming-parent mismatches.
All these counters are zero with the proposed patch. The same unchanged invariant
assertion records baseline exit1 and candidate exit0.

Crucially, eligibility-threshold mismatches were **zero in the baseline too**.
Both benchmark signatures remain 419,798 nodes; these samples demonstrate the
bookkeeping repair, not a changed decision, faster search or stronger play.
The trace did not demonstrate an actual count-over-seven decision. The proposed
boundary behavior follows from the source invariant; targeted inherited-count
6/7 coverage would strengthen regression protection. The bounded T1 trace does
not replace a complete new-source build, CTest, sanitizers, multiworker checks,
Windows validation or fresh paired equal-time strength evidence.

The proposed patch is limited to this one accounting variable and preserves the
clock reconciliation, TT ownership/coherence, NNUE/evaluation and existing search
thresholds. It should remain a separate candidate until those gates complete.
