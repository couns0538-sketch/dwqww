# Read-only review of new mate/TT branches

The frozen remote-head snapshot is `/workspace/work/all-run/branch-review-20261114/remote-heads.txt`, recorded 2026-11-14T13:51:59.287Z, SHA256 `3db56e68134fbbe774e65030a811322430819853d53f528d173a6961ff9c97b2`. This review describes that snapshot only; branch names can advance later.

| Branch | Exact snapshot tip | Finding |
| --- | --- | --- |
| `grok47/r3-21-mate-score-tt` | `e04556ddc3a430b2e751159b0d46111ef56c8b89` | Same commit as the pinned integration checkpoint; no added fix. |
| `grok47/r3-23-sound-mate-pruning` | `e04556ddc3a430b2e751159b0d46111ef56c8b89` | Same commit as the pinned integration checkpoint; no added fix. |
| `grok47/r3-24-tt-duplicate-shadow` | `305bfc30f05c4020ef01a6992f419d9b27a7cfe2` | One actual child commit of `e04556dd…`, implementing a targeted stale-probe-slot correction. |

The two mate-related branch names are placeholders at the inspected tips. Their names are not evidence of a completed mate-score or pruning fix. The current soak checkout at review start was `b98b2b797deacc5211fe1a75ace6354bb4fd3552`; its `src` and `include` trees match `e04556dd…` exactly. Pinned/working `src/search.cpp` SHA256 is `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819`. The r3-24 version is `64b1d6dc2f29e002692cda32c129112df48e0b0da8d70f27b4d397b260e1120f`.

## Exact r3-24 scope and code assessment

Commit `305bfc30f05c4020ef01a6992f419d9b27a7cfe2`, subject “Update a hash-table entry already in the cluster instead of a stale probe slot.”, has exactly parent `e04556ddc3a430b2e751159b0d46111ef56c8b89` and changes only these three text files:

- `forge-combo29/src/search.cpp`: 21 added lines, 2 removed.
- `forge-combo29/tests_r3_24/proof_tt_duplicate_shadow.cpp`: new, 75 lines.
- `forge-combo29/REPORT_r3_24.md`: new, 67 lines.

No header, build configuration, UCI option, mate encoding, qsearch or rule-50 condition changes occur in the commit.

The pinned implementation returns the first occupied matching verification tag (`src/search.cpp:295–304`, and the alternative implementation at `:372–381`). A miss records a replacement slot, which can become stale while search continues. Its store writes only that captured slot (`:329–343`, and `:398–412`). A later store may already have placed the same position in another slot of the cluster. The old store can then create a second shallow entry at the earlier slot; a subsequent first-match probe sees that shallow entry and hides the deeper one.

In the r3-24 source, `src/search.cpp:332–344` re-scans the four entries for an occupied matching `key32` before applying the existing move/payload replacement rules at `:345–353`. The alternative implementation has the same check at `:412–421`, before its existing rules at `:422–430`. The public locking route remains protected by its existing stripe-lock/lease logic; `store_owned` at `:362–365` calls the same changed body with `TakeLock=false` under its exclusive-lease precondition. That route does not acquire a stripe mutex, so the branch report's phrase “after the stripe lock is taken” is shorthand rather than literally true for every call.

The test gives a concrete, deterministic sequence at `tests_r3_24/proof_tt_duplicate_shadow.cpp:34–53`: reserve a miss for key A; place another colliding key in that slot; store key A at depth 14 in a later slot; then submit the initial shallow depth-2, upper-bound store. With the new scan, `depth + 4 > stored_depth` is false (6 > 14 is false), generation is unchanged, and the bound is not exact, so the deep score survives. Assertions at `:65–71` require depth 14 / score 777 / exact for A, and preservation of the other key at depth 3 / score 15 / exact. This is an actual implementation and a structurally relevant regression, not a placeholder or report-only claim. This review did not run it.

Important limits:

- The scan uses the existing 32-bit verification tag, not a stored full key. It does not eliminate TT hash aliasing. It chooses the first matching occupied entry; it does not repair a table already containing duplicates by selecting the deepest or deleting the others.
- The existing rule that an admitted new move can replace the move even when its shallow score payload is rejected remains in force (`r3-24 src/search.cpp:346`, `:423`). The test asserts score/depth/bound preservation, not that the returned move is the deep entry's original move. This patch does not establish exact score/move correspondence.
- The proof directly calls public `probe`/`store`, not `probe_owned`/`store_owned`, and is single-threaded. It does not directly stress the exclusive-owner path or live concurrent schedules. The shared implementation makes the owner path statically relevant, but that is not a runtime validation.
- The particular test keys share a cluster on the `__SIZEOF_INT128__` multiply-high implementation (`include/forge/search.hpp:188–202`): the tags are their different low 32 bits, and their identical high bits give the same cluster at Hash 1. On the fallback modulo-index implementation (`:193–195`, `:203–204`), these two keys have different modulo buckets and the same high tag; the intended stale-slot collision sequence is not exercised. An unfixed fallback build could pass this test. The reported GCC/x86 build uses the intended multiply-high case.
- If no matching tag remains in the cluster, the old captured slot remains the fallback. The change does not generally recompute the best replacement victim after an arbitrary intervening store.
- This is a cache-entry selection/information-preservation defect with a credible narrow correction. Its existence alone does not prove that any reported chess score or mating bound was false.

## Relation to Part 4

The existing investigation in `soak_all/mate_pv_investigation.md` concerns `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`. With NNUE off, unchanged lock and pinned merged both report mate 17 with the same 15-ply nonterminal PV. The independent KRK retrograde query established root DTM 15 plies and chosen-move DTM 17 plies, within the reported mate-in-17 upper bound of 33 plies. No false mating bound was demonstrated.

Its scratch trace identified a mate-valued TT upper bound replacing qsearch stand pat and then leaving through the final qsearch return without extending the PV (pinned `src/search.cpp:1088–1095`, `:1169`; report source table and trace give full context). r3-24 does not change these qsearch returns, TT score-to-ply conversion, PV reconstruction, or mate formatting. It may change what entries are retained in searches, but no trace links a duplicate-shadow event to this particular Part-4 endpoint, and no r3-24 run on that root was performed. The added regression contains ordinary scores 777 and -50, not a mate/PV test.

Therefore r3-24 is a separate TT-storage candidate, not an established repair of the Part-4 observation. The r3-21/r3-23 tips supply no additional mate fix to assess or duplicate.

## Relation to the eight required low-clock equality failures

The eight observed roots are corpus indices 3228, 9834, 10567, 11000, 12276, 12999, 14002 and 25354. The existing controlled investigation attributes their measured differences to requested t23 rule-50 behavior changes: restoring all six behavior families in scratch reproduces lock for every root; restoring the three TT behaviors alone does so for seven, with index 14002/fault090 the exception. All eight comparisons remain failures under the user's under-80 equality requirement.

Those t23 gates concern near-50 TT move eligibility, TT PV inheritance, qsearch TT cutoffs and three pruning clock guards (pinned `src/search.cpp:1069–1075`, `:1217–1224`, `:1268`, `:1393`, `:1480`). r3-24 changes none of them. It modifies TT storage earlier in the same file. No existing diagnostic traced duplicate-shadow formation in these eight roots, and none tested the r3-24 executable. Accordingly:

- The branch does not directly restore the demonstrated changed conditions.
- No evidence here shows that r3-24 makes any of the eight required comparisons pass.
- Its effect on those roots is unknown without a separate authorized build and comparison; no conclusion that it cannot affect them is implied.
- Reviewing this branch does not reclassify the eight failures, change the frozen experiment, or justify merging it into the ongoing job.

## Validation claims and review boundary

`REPORT_r3_24.md:36–44` claims before/after bench 11 = 312866, bench 13 = 862329 and startpos perft 5 = 4865609 under its stated GCC build. Lines 49–61 give an ASan/UBSan compile command and narrative passing result for the deterministic proof with and without `FORGE_SPD_TT_NOTLS`. These are branch-author claims read from the report, not runs independently performed or fully audited here. The committed report does not supply complete raw command/output transcripts for the pins and proof. It explicitly leaves live two-thread stress, other compiler/settings and games unverified at lines 63–67. No bench-16, optional NNUE-off pins, complete cumulative sanitizer suite, 200-search TSan run or full match validation is established by the inspected commit.

All required Git objects were already present; no fetch was necessary. This review used only read-only Git/object inspection and text reads. No branch/ref update, checkout, merge, build, native engine search, production-file edit or change to experiment state occurred. Review/evidence files exist only in `/workspace/work/all-run/branch-review-20261114/clock-review/`.

Evidence files retain actual shell commands and outputs: `initial.txt`, `target-index.txt`, `commits.txt`, `patch-and-base-source.txt`, `lines-and-overlap.txt`, and `provenance-and-limits.txt`. The initial narrow branch-name grep omitted the `grok47/` prefix and returned no matches; the corrected grep in `commits.txt` found all three exact names. This was an inspection-pattern mismatch, not evidence that the branches were absent.
