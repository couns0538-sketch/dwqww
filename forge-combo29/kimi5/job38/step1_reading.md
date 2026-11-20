# kimi5 job 38 — Step 1 reading (no runs). Chain: 6b98f217 + pc_r15 (sha256 d6bd72c5…), the plain
build tree of Step 0 (= job 34's base). All lines are src/search.cpp of that tree unless said otherwise.
r15d's line numbers from file 38 in parentheses. Verified by opening each site on 2026-11-20.

## The six sites of K2
1. **Late-move rule (LMP)**: `if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving))
   skip_quiets = true;` — **2122**, inside the pruning block, before the futility tests; no in-check guard
   (Lc counts the same set at in-check nodes, where the evasion picker never reads skip_quiets).
   `lmp_threshold` at **319-321** (improving: LmpBase + depth²; else half). (r15d 2272.)
2. **Quiet futility**: the `quiet && !gives_check && prunable` branch at **2131**, futility test at
   **2132-2137** (`!in_check && lmr_depth <= FutilityDepth && static_eval + FutilityBase +
   futility_improving + FutilityMultiplier * lmr_depth <= alpha`), fire at **2138-2141**: trace, quiet_fail,
   `skip_quiets = true` (2139), `continue` (2141). (r15d 2283-2293.)
3. **History prune**: **2143** `if (lmr_depth <= tune::HistoryPruneDepth && history < history_prune_threshold)`,
   fire (quiet_fail + `continue`) at **2144-2145**. FE = reaches with lmr_depth <= HistoryPruneDepth, F = fires.
   (r15d 2294.)
4. **SEE prune of a plain quiet**: **2147** `if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth *
   lmr_depth))`, fire at **2149-2151**. SR = QP − Q − F reaches this test. (r15d 2299.)
5. **Capture futility**: in the `else if (prunable)` branch (**2153**), **2156-2163**: gated on
   `tune::CaptureFutilityBase > 0` (2156) — 0 under PC20, so CF = 0 on every set. (r15d 2307-2316.)
6. **Noisy SEE**: **2166-2167** `if (!(picker.last_move_see_nonnegative() && see_threshold <= 0) &&
   !board.see_ge(move, see_threshold))` with `see_threshold = -SeeNoisyMultiplier * depth` (2165); the
   picker-good-capture exemption (NS) is the first disjunct; fire (`continue`) at **2176**.
   `last_move_see_nonnegative` at **780** (true only for a Main-mode GoodCaptures return). (r15d 2318-2328.)

The pruning block's gate (B): **2096-2097** (`!sound_mate_case && mate_moves_ == 0 &&
halfmove_clock + depth < 100 && !root_node && best_score > -MateInMaxPly && has_material &&
!bare_king_mode`). `prunable` at **2126** (`!tt_prune_v2_ || move != tt_move`). QP branch 2131,
NR branch 2153. (r15d 2247-2248, 2277, 2282, 2304.) The move loop is **2071**
(`while (!(move = picker.next(skip_quiets)).is_none())`); `excluded` skip 2072, root-list skip
2073-2075, `is_legal` 2077 (this chain has no `last_move_known_legal()` fast path, as job 34 noted).

## Which picker stages read skip_quiets (MovePicker::next, 682-775)
READ: Killer1 (**714**), Killer2 (**718**), CounterMove (**722**), GenerateQuiets (**727**),
QuietMoves (**731-739**). NOT READ: GoodCaptures (695-709), BadCaptures (743-748),
QsGenerate/QsCaptures (750-760), EvasionGenerate/Evasions (763-772). MainTT/QsTT/EvasionTT
(684-688) hand the TT move out first and never read it. (r15d 737-764; same answer.)

## A quiet check is hidden like any other quiet once skip_quiets is set
YES. Quiet checks live in the quiets list (`generate_quiets`, **1003-1011**,
`generate_pseudo_legal(buffer_, GenMode::Quiets)`), and are handed out ONLY in the QuietMoves
stage, which is skipped whole when skip_quiets is true (**731** `if (!skip_quiets)`). The
check-preserving filter at **735** (`quiet_tail_closed_ && !board_.gives_check(move)`) runs only
inside that stage. So with skip_quiets set, quiet checks are never handed out: HLc/HFc count them.
(r15d 755-764; same answer.)

## Where promotions without capture are generated (HP = 0)
With the captures. board.cpp **493-498**: `promo_push = pawn_push(us, promoting) & empty` is inside
`if constexpr (!quiets_only)` (492), so it is emitted in Captures mode as Quiet-flagged promotions;
the picker's `generate_captures` calls `generate_pseudo_legal(buffer_, true)` (**980**). Captures
and promotions are handed out regardless of skip_quiets (GoodCaptures/BadCaptures don't read it), so
a legal capture or a non-capture promotion is never hidden at a WL/WF node: HP = HC = 0. Consistent
with K2's NRp > 0 (quiet promotions reach the loop through the capture stages).

## K3: T is 0 on every set (confirmed on this chain)
The picker's MainTT case (**684-688**) returns `tt_move_` before any other stage, so the TT move is
always move_count 1 at its node; at that moment `best_score` is still −Infinite, so the block gate's
`best_score > -MateInMaxPly` (**2097**) is false and the TT move never ENTERS the block. Every later
move has `move != tt_move`, making `prunable` (**2126**) true at every block entry. If tt_move is
none, prunable is trivially true. So T = 0 on any set, for the same reason as theirs (their 710-714,
2248, 2277). The B4 comment at 2124-2125 says the same.

## For K7
- Root skips a move not in the list: **2073-2075** (`root_node && root_restricted_ && none_of(root_moves_)`).
  (r15d 2224.) `root_moves_`/`root_restricted_` are set from `limits.search_moves` at **2475-2476**.
- A restricted root is not stored: **2367** `if (excluded.is_none() && !(root_node && root_restricted_))`
  gates the `store_tt` at 2368. (r15d 2518.)
- The line that then takes a ply off: **2033** `if (mate_moves_ == 0 && !in_check &&
  depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;` (r15d 2184). A
  restricted root is never stored (2367), so tt_move is none at every iteration; the root is a PV node;
  IirDepth = 2 under PC20 (pc20_all1024.opt) — so `go depth D searchmoves …` searches the root at D−1.
  At an in-check root (K7 position 2) the `!in_check` guard fails and no ply is taken (their go-depth-7
  note). Step 0's twelve cells match theirs exactly, which is the behavioural proof.
