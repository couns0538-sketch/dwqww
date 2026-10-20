# One-mask replacement for the 6.4.15 SEE king-safety filter

Status: source-only design ready for review. No prototype source, compilation, engine execution, archive, match, or production change has been made. The proposed mechanism has an exact-equivalence proof; a runtime gain is not established.

The bounded goal is to preserve every `see_ge` decision made by frozen 6.4.15 while reducing its repeated attack-query work. Source reference: `8d303e4`, `src/board.cpp` SHA-256 `d8c5066db1381e03a72e2baceb65553277020880c78d84007db2e11ff2d46705`. This hash matches the inspected current source. Ownership is limited to this experiment directory and a separately authorized outside-source export; existing evidence, production, tests, docs, ledger, and Git are untouched.

## Selected change

Replace only the current per-non-king-origin `square_attacked_with_occupancy` loop with a mask of forbidden origins computed once per exchange ply. Keep the LVA order, all same-value-origin choices, occupancy updates, threshold exits, promotions, EP initialization, result parity, and king branch byte-for-byte unchanged.

At one exchange ply, define:

- `O`: current virtual occupancy, with the target occupied.
- `K`: the current side's original king square.
- `A`: current non-king recapture origins, already intersected with `O`.
- `L = O & ~target_bb`: available original enemy-piece origins. This equals the old helper's `~removed`; excluding the target is essential even though the target is occupied.
- `P`: live enemy bishops/queens on an empty-board diagonal from `K`, union live enemy rooks/queens on an empty-board orthogonal line from `K`.

The mask has two cases:

1. A live enemy pawn, knight, or king attacks `K`, or any `p` in `P` has no occupied square strictly between `K` and `p`. Every non-king recapture is rejected. The existing king bit is retained for the unchanged king branch.
2. Otherwise, union every singleton `between(K,p) & O` into `forbidden`, and remove only those origins from `stm_attackers`.

Recompute from current `O` on every exchange ply. Do not cache a pin set from the initial board. Do no additional work if `A` is empty.

Illustrative replacement, confined to the existing filter site:

```cpp
const Bitboard king_attackers = stm_attackers & pieces(stm, King);
if ((stm_attackers & ~king_attackers) != 0) {
    const Color enemy = opposite(stm);
    const int king = king_square(stm);
    const Bitboard live = occupancy & ~square_bb(to);
    const Bitboard queens = pieces(enemy, Queen) & live;
    bool checked =
        (attacks::pawn(stm, king) & pieces(enemy, Pawn) & live) != 0 ||
        (attacks::knight(king) & pieces(enemy, Knight) & live) != 0 ||
        (attacks::king(king) & pieces(enemy, King) & live) != 0;
    Bitboard pinners =
        (attacks::bishop(king, 0) & ((pieces(enemy, Bishop) & live) | queens)) |
        (attacks::rook(king, 0) & ((pieces(enemy, Rook) & live) | queens));
    Bitboard forbidden = 0;
    while (!checked && pinners != 0) {
        const int pinner = pop_lsb(pinners);
        const Bitboard blockers = attacks::between(king, pinner) & occupancy;
        if (blockers == 0) checked = true;
        else if (!more_than_one(blockers)) forbidden |= blockers;
    }
    stm_attackers = checked ? king_attackers : stm_attackers & ~forbidden;
}
```

The spelling above is a design excerpt, not compiled prototype code. `attacks::pawn(stm, king)` intentionally matches the reference helper's `attacks::pawn(opposite(enemy), king)`. Empty-board bishop/rook calls are only geometric alignment masks. No `line` lookup, new table, helper API, source refactor, or extra hoisting optimization is needed.

## Exact-equivalence proof

For every candidate origin `a` in `A`, the existing predicate asks whether an enemy piece attacks `K` under `O_a = O ^ square_bb(a)`, with the same removed mask for all candidates. Because `a` is occupied, this XOR only deletes `a`. Because it is a friendly non-king origin in a valid board, it is not an available original enemy-piece origin. Because it attacks the target, `a` is not the target itself.

Enemy pawn, knight, and king attacks depend on piece masks and fixed geometry, not occupancy. Their available masks equal `L` and are independent of `a`. Any such check therefore rejects every candidate in both algorithms.

For a live aligned enemy slider at `p`, let `B = between(K,p) & O`. The reference helper sees that slider after deleting `a` exactly when:

```
between(K,p) & O_a == 0
```

Since `O_a` deletes exactly one occupied bit, this condition holds exactly when `B` was empty or `B` was the singleton `{a}`. If `B` has two or more bits, deleting one cannot clear the ray. Unaligned enemy sliders can never attack `K` in either algorithm. Thus:

- an empty `B` rejects all candidates;
- unioning singleton `B` values rejects exactly the origins for which the reference helper finds a newly exposed slider;
- no other origin is rejected.

The mask therefore preserves the complete surviving attacker set, not merely the first LVA. The unchanged piece-type/`lsb` selection chooses the same origin and makes the same occupancy update. By induction, all subsequent exchange states, threshold exits, and returned results match the reference.

The proof tolerates an initially pseudo-legal move and pre-existing off-target check: deleting a friendly origin cannot remove a live non-slider checker or block an already open slider ray when the target was occupied already. A check by the target occupant is correctly absent from both predicates because `L` excludes the target ghost before either query.

## Required invariants and edge cases

- **Target remains occupied:** it can remain a ray blocker for a capture along a pin. Removing it to construct `L` must not remove it from `O` used by `between`.
- **Target ghost is excluded:** every enemy piece-type mask is intersected with `L`, not merely `O`. The original captured piece on the occupied target must never become a live pinner or non-slider checker.
- **Departed/consumed pinners are absent:** all original enemy origins not in current `O` are excluded by `L`. Recompute each exchange ply so newly exposed and released rays follow the current position.
- **EP:** the existing initial occupancy has already removed both the initial moving origin and the actual captured pawn square. The mask uses that same occupancy without special cases.
- **Promotions:** the exact-equivalence goal retains the reference's initial promotion handling and inherited recapture-promotion limitation. This change must not turn an expected limitation into an unrecorded different result.
- **King bits survive all-candidate rejection:** use `king_attackers`, not zero. The original king branch receives the same geometric `attackers` and has unchanged behavior, including pinned enemy defenders.
- **King square stays fixed while this filter runs:** initial king moves terminate at the unchanged threshold exits because `SeeValue[King] == 0`; virtual king recaptures terminate in the unchanged king branch before updating occupancy.
- **No check-free precondition:** pawn/knight/king checks and zero-blocker slider checks must be handled explicitly. A mask containing only absolutely pinned friendly pieces would fail this contract.
- **Strict between semantics:** existing `BetweenTable` excludes both endpoints, as established by `src/bitboard.cpp` initialization. Candidate deletion never removes a live enemy slider endpoint.

An independent source-only proof review by a second agent found no counterexample. It specifically checked target ghosts, EP, consumed origins, initial/virtual king moves, pre-existing check, strict-between semantics, and retaining the king bit. This is corroborating reasoning, not runtime parity evidence.

## Operation-count comparison

Let `N` be the number of non-king candidate origins at one visited exchange ply and `S` the number of available geometrically king-aligned enemy sliders. These are source-level logical counts, not measured instruction counts or timings.

| Work per exchange ply | Existing filter | Proposed mask |
| --- | --- | --- |
| Work when `N == 0` | None | None after one guard |
| Pawn / knight / king geometry tests | Up to `N` of each, with short circuit | At most one of each, with short circuit |
| Occupancy-dependent bishop / rook king queries | Up to `2N`, typically both for every safe candidate | Zero |
| Empty-board bishop / rook alignment lookups | Zero | Two if `N > 0` |
| Between lookups / blocker classifications | Zero | At most `S`; early stop on an existing slider check |
| Origin removal from surviving set | Per failing candidate | One final mask operation |

For `attacks::bishop/rook(king, 0)`, the magic index expression algebraically reduces to zero; those calls are geometric table reads without an occupancy-dependent index. No claim about compiler output is made before compilation.

The favorable case is several candidate origins and few live aligned enemy sliders: repeated full king queries become one non-slider test set plus a short/no slider loop. `N == 1` with several aligned sliders can be worse: the extra `between` work may exceed two indexed slider lookups. The proposal reduces repeated attack-query work but does not guarantee lower total cost for every position. Exact result parity alone cannot establish a speed gain.

## Validation after explicit root build clearance

No validation command below has been run for this design. Preserve the frozen 6.4.15 source and all existing evidence before creating an isolated candidate export.

1. Compare the proposed and reference **complete surviving attacker masks**, including every candidate origin, on every recorded SEE exchange state in the immutable 304-case API corpus and the 12 added coverage fixtures. Do not compare only final return values; early threshold exits can hide a bad mask.
2. Compare actual `see_ge` outputs at the frozen threshold grid and each authored expected value's adjacent boundary, plus actual `static_exchange` values. Compare against 6.4.15 exactly. Retain the two expected promotion limitations as reference behavior rather than claiming a universal oracle pass.
3. Add bounded deterministic mask-level cases for every blocker cardinality (0, 1, 2+) in all eight ray directions; multiple aligned sliders; singleton blocker equal to target; all non-king candidates rejected with king retained; existing pawn/knight/king check; removed pinners; target ghosts; and EP-opened rays. Exercise occupied candidate origins on and off king rays, and pseudo-legal initial positions with pre-existing check.
4. If masks and actual APIs agree, collect deterministic work counts (`N`, `S`, full-query counts, between counts) separately from wall time. Preserve any mismatch before fixing the isolated prototype. Do not treat counts as NPS or strength evidence.
5. Only after those gates should root decide whether calibrated performance measurement and full-engine integration gates are useful. Shared-host timing noise and a full-engine strength comparison remain separate questions.

Recommendation: proceed with this single mask implementation only after root's existing builds finish and root grants build clearance. The proof is compact enough to justify a bounded isolated parity trial. Do not combine it with threshold, LVA, king, promotion, or search-behavior changes.
