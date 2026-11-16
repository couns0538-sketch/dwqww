# kimi5 job 6, Part 1: prediction from the code only (base 6b98f217, plain tree, no job-4/5 patches)

All line numbers are `src/search.cpp` at 6b98f217 unless a header is named. Constants
(include/forge/search.hpp 71-75): MaxPly 128, Infinite 32001, MateValue 32000,
MateInMaxPly 31872, ValueNone 32002. HistoryMax 16384 (search.cpp 175),
CorrectionLimit 32*256 = 8192 (search.hpp, CorrectionGrain 256).

The six asserts: the default CMake build defines FORGE_SPD_TT_NOTLS=1 and
FORGE_SPD_PREFETCH_EARLY=1 (CMakeLists 32-35; the header defaults at search.hpp 21-24 and
board.hpp 30 are only fallbacks), so all six are compiled in the default build and all six
are compiled OUT again in release (NDEBUG). 438/487 guard that probe_owned/store_owned run
only under the table's ExclusiveLease (taken only when single-threaded, 2712-2714 - the
Threads 4 run below exercises the locked path instead). 1515/1976 guard that the
incremental board.key_after equals the post-make key. 1986 and 2376 guard the root effort
array. The invariant list covers what each assert guards (V5/V13/V16/V17/V18 below).

V1  alpha < beta at entry of search() (1550) and qsearch() (1416), both in [-Infinite, +Infinite].
    Call HOLDS. Every call site passes a proper window by construction: null-window sites
    (x-1, x) at 1684, 1714, 1734, 1765-1767, 1937, 2014, 2024; wide sites (-beta,-alpha)
    at 2034 and root 2414 with alpha < beta kept by the aspiration loop (2416-2436:
    initial window >= 2*AspirationDelta >= 8 since the parameter floor is 4, uci table
    line 134; fail-low sets beta = (alpha+beta)/2 which stays > alpha when the window is
    >= 2). Clamps at 2407-2408 keep both inside [-Infinite, +Infinite]. AspCappedReopen
    (default off) re-opens with capped_fail_low/high which clamp to +-Infinite only.
V2  every score returned by search()/qsearch() inside the mate range; ValueNone never
    returned, compared as a score, or stored as a score.
    Call HOLDS. Leaf returns are constants in range (draw 0/jitter +-8 at 1569/1570/1424-1425,
    mated_in 1537/2072, alpha after mate-distance pruning 1574 which was clamped to
    >= mated_in(ply)). tt returns are guarded `tt_score != ValueNone` (1451, 1638) and
    score_from_tt (187-198) maps a band-crossing value to ValueNone, never to a number.
    best_score starts at -Infinite (1796) and is replaced only by child scores (2043),
    and move_count > 0 guarantees at least one child score. ValueNone (32002) is a marker
    on ss->static_eval/raw_eval only; every arithmetic read is guarded (see V8).
    Verified at the 11 child-score receiving sites (1520, 1684, 1714, 1734, 1765, 1767,
    1937, 2014, 2024, 2034, 2414).
V3  a mate score returned at ply p satisfies |score| <= MateValue - p.
    Call HOLDS. mated_in(ply) = -MateValue + ply exactly (210); a parent's negation of a
    child mate gives mate_in(ply+1) = MateValue - ply - 1 < MateValue - ply. score_to_tt
    (179-183) subtracts the absolute ply at store and score_from_tt re-adds the reader's
    ply, so a stored mate read at another ply keeps the absolute convention; the
    MateInMaxPly re-validation (191-196) drops anything that would cross the band.
    Equality (|score| = MateValue - p) is allowed and occurs at mated_in(ply) itself.
V4  early returns that CAN return a mate score, per site:
    - razoring 1683-1687: returns qsearch(alpha-1, alpha) when < alpha. qsearch can return
      a tt mate (1451-1456) or stand-pat eval taken from tt (1468-1472). CAN (rare: needs
      razor < alpha with a mate score).
    - reverse futility 1688-1692: returns eval. Guarded eval < MateInMaxPly (1690) on the
      plus side; the condition eval - margin >= beta with beta > -MateInMaxPly (guard 1680)
      rules out a negative mate. CANNOT.
    - null move 1716-1743: mate clamped to beta at 1718 before either return (1725, 1741);
      beta non-mate per 1680. CANNOT.
    - ProbCut 1777: returns value from the child search, value >= probcut_beta; a child
      can find mate at the reduced depth. CAN.
    - multi-cut 1949: returns singular_beta = tt_score - margin*depth with
      !is_mate_score(tt_score) guarded at 1930. CANNOT.
    - hash cutoff search 1637-1644 and qsearch 1451-1456: returns tt_score, mate allowed
      by score_from_tt. CAN. qsearch stand-pat cutoff 1475-1482: returns best_score = eval
      possibly replaced by tt_score at 1468-1472. CAN.
    Expect the qsearch hash cutoff and stand-pat sites to be the nonzero counts.
V5  hash stores: LOWER only with score >= beta, UPPER only with score <= alpha-at-entry,
    EXACT only where meant; stored depth in its field.
    Call HOLDS at all four sites. qsearch stand-pat store (1477) sits inside
    `best_score >= beta`. qsearch final (1541-1544) and search final (2093-2097) compute
    bound from best_score >= beta; for UPPER, best_score <= alpha-at-entry because any
    score > alpha sets best_move and raises alpha (1524-1534, 2044-2057), and UPPER is
    only chosen when best_move is none (non-PV: window 1, best_score > alpha implies
    >= beta implies break/Lower). EXACT only at pv_node with a best move, score strictly
    inside. ProbCut store (1772-1776) LOWER with value >= probcut_beta > beta.
    depth: search final passes depth >= 1 (IIR 1784 keeps >= 1... IIR only reduces when
    depth >= IirDepth >= 1 so depth >= 3 before --), ProbCut depth-3 >= 2 (ProbcutDepth
    floor 1 in the table but guard 1748 requires depth >= ProbcutDepth >= 5 default;
    parameter floor is 1, so depth-3 >= -2 is possible only if a user sets ProbcutDepth
    1..2 and depth < 3 - ProbCut guard `depth >= tune::ProbcutDepth` with depth >= 1:
    ProbcutDepth 1, depth 1 -> store depth -2 clamped to 0 at 555. Default settings: no.
    The clamp at 553-556 keeps the field in [0,255] regardless). Suspicions list.
V6  singular search (excluded_move set 1937, cleared 1941, search at 1938):
    - no hash store under this node's key: the inner search reads excluded at 1579; its
      final store is guarded `excluded.is_none()` (2093), the tt cutoff is guarded (1637),
      and the whole pruning block incl. ProbCut store is guarded (1680). HOLDS.
    - the picker never hands out the excluded move: FALSE at picker level - the tt_move of
      the singular search IS the excluded move and EvasionTT/MainTT/QsTT stages return it
      (604-608); the exclusion happens in the move loop `if (move == excluded) continue;`
      (1817). Effectively HOLDS at make_move; expect nonzero picker handouts, zero makes.
    - fields written in ss during the inner search that the outer reads afterwards:
      pv/pv_length (zeroed 1566, rewritten by inner; outer rewrites pv[0] and copies
      (ss+1)->pv at 2048-2050 and sets pv_length = (ss+1)->pv_length+1 - full overwrite of
      what it reads), killers (inner update_quiet_stats 1377-1379; outer picker copied them
      at construction 592, outer never reads ss->killers later), current_move/moved_piece/
      continuation (inner 1967-1969; outer rewrites 1967-1969 after), double_extensions
      (restored 1940), tt_pv (restored 1939), move_count (inner 1567/1825; outer continues
      its own local move_count - ss->move_count is rewritten at 1825), static_eval: KEPT by
      the inner entry at 1650 for the non-in-check case and the outer pruning already
      happened; for in-check it is ValueNone anyway. static_eval must survive the singular
      search unchanged when !in_check - counted (breach = changed).
V7  hash moves tested before made. Picker construction tests is_pseudo_legal (584); the
    loops test is_legal (1491, 1752, 1823). A pseudo-legal but illegal (pinned) hash move
    is possible. Expect nonzero "failed is_legal" counts; breach = reaches make_move,
    expect 0 (the continue is unconditional).
V8  in-check static_eval marker (ValueNone set at 1461 qsearch, 1649 search). Every
    arithmetic read is guarded: improving 1666-1668 (!= ValueNone checks on (ss-2)/(ss-4)),
    null-move guard 1693 (inside !in_check block 1680), ProbCut SEE 1753 (same block),
    futility 1872 (`!in_check &&` short-circuits first, 1869), capture futility 1898
    (`!in_check &&`), extinction-tight 1923 (may_extinguish includes !in_check, 1805),
    HindsightDepth parent eval 1615 (guarded != ValueNone; option default off),
    LmrSignedCorrection 2003-2005 (explicit != ValueNone checks; default off),
    update_correction 2106 (guarded !in_check 2102). qsearch reads futility_base only in
    the not-in-check branch (1483). Call HOLDS, expect 0 marker reads in arithmetic.
V9  depth: new_depth = depth - 1 + extension (1960), extension in {-2,-1,0,1,2}
    (1944-1958), so new_depth <= depth + 1; the double extension (extension 2) gives
    exactly depth + 1 and needs inherited_double_extensions <= 6 (1944), accumulated at
    1959, so a path carries at most 7 doubles. LmrDeeperShallower (default off) can add
    +-1 more at 2020 AFTER the reduced search - with it on, new_depth <= depth + 2.
    HindsightDepth (default off) changes depth itself +-1 at 1628. ply cap: ply >= MaxPly
    returns at 1570/1425, so ply <= 128; seldepth records the max. Call HOLDS; record
    max new_depth - depth, max double_extensions, max ply - root depth.
V10 ply vs stack/PV sizes. stack_ has MaxPly+8 entries (search.hpp 481), ss base is
    stack_[4] (2345), ply is set i-4 (2346), so ss-k reads for k <= 4 stay inside.
    (ss+1) writes happen at ply+1 <= 128 (guard 1570 fires at ply == 128 before any
    child), index ply+4 <= 132 < 136. pv arrays are MaxPly+1 (search.hpp 394);
    ss->pv_length = (ss+1)->pv_length + 1 and by induction pv_length at ply p <= 129 - p,
    so writes stay inside; copy_n reads (ss+1)->pv_length entries, same bound one ply
    deeper. Root PV replays legally: pv[0] passed is_legal at 1823 and children were made;
    the line is copied from child stacks that held legal moves. Call HOLDS. The root-PV
    replay is counted per finished iteration in the driver.
V11 history/correction bounds. apply_history (246-249): entry + clamped -
    entry*|clamped|/HistoryMax with clamped in [-HistoryMax, HistoryMax] keeps |entry|
    <= HistoryMax = 16384 (gravity formula; integer truncation rounds toward 0, the safe
    side). All history tables (main 1386/1390/2082, threat 1353, continuation 1365,
    capture 1402/1409, fail-low bonuses 2029/2082-2088) funnel through it. Correction
    tables clamp explicitly to +-CorrectionLimit = 8192 (1233-1235). Call HOLDS; count
    per table and record the extreme absolute value seen. Expect main history to come
    closest to its bound.
V12 node kinds. pv_node = beta - alpha > 1 (1551, 1416). PV calls pass cut_node false:
    root 2414, PV re-search 2034; null-window calls pass true or !cut_node (2014, 2024),
    null move !cut_node (1714), ProbCut !cut_node (1767), singular cut_node passthrough
    with a null window (1937-1938), verification null window false (1734). A PV node is
    never a cut node: by induction from the root (false): PV children get false (2034),
    non-PV children have window 1 so pv_node false regardless of their cut_node. Call
    HOLDS; breach = pv_node && cut_node at entry.
V13 make/unmake key equality. Four sites: qsearch loop (make 1513, unmake 1521), null
    (1709/1715), ProbCut (1760/1769), search loop (1973/2039). board.make_move/unmake_move
    are the same pair the perft known answer exercises (4,865,609 nodes exact). Call
    HOLDS at all four; count per site.
V14 the result. bestmove is legal: it is result.pv.front() (2457-2459) from moves that
    passed is_legal at 1823, or a root_candidates fallback (2264, 2302-2308, 2321-2324,
    2640) and root_candidates are filtered legal moves (2203-2210). The last info line of
    a finished iteration prints the score the aspiration loop accepted (strictly inside
    the final window, else the loop would not have exited) with the PV that produced it
    (2543). No bound is ever printed: emit (2229-2248) formats only "cp"/"mate", never
    lowerbound/upperbound; a finished iteration's score is exact by construction. The
    aborted-iteration emit (2450) prints result.score, the last FINISHED score. Call
    HOLDS; counted per iteration: best_move in the legal root list, pv[0] == best_move,
    PV replays legally, finished score strictly inside the final window.

Extra invariants the code promises:
V15 stored TT score field: score_to_tt output stays inside [-32767, 32767] so the clamp
    at 553 never changes a value (mate band worst case +-32128 fits). Breach = clamp
    would have altered the value. Call HOLDS.
V16 assert 1986 live in release: every root move is found in root_effort_moves_ (find at
    1984-1985); the use at 2040-2041 is guarded, so a miss is silent in release. Count
    made = root moves, breach = find returned end. Call HOLDS (root moves come from the
    same legal list copied at 2376-2378, and root_restricted_ filtering is identical in
    the picker skip 1818-1822... except: the picker skip uses root_moves_ (the UCI
    searchmoves), the effort array holds root_candidates (legal INTERSECT searchmoves);
    a pseudo-legal move that is in root_moves_ but not root_candidates is skipped at 1823
    is_legal anyway. HOLDS).
V17 assert 2376 live: root_effort_count_ <= root_effort_moves_.size(). root_candidates
    <= legal moves <= 256-ish, array sized in the header. Call HOLDS, count once per
    search.
V18 asserts 1515/1976 live: board.key_after(move) (the early prefetch key) equals
    board.key() after make_move. Counted at both prefetch sites (1503-1516 qsearch,
    1962-1977 search): made = early_key true, breach = mismatch. Call HOLDS (the same
    incremental key feeds the real key update; perft exercises it).
    The store-path clamps V5 cites are 471-475 (store_body, the FORGE_SPD_TT_NOTLS=1
    branch that the default build compiles; the #else twin at 553-556 is not compiled).

THE ONE I EXPECT TO BE BREACHED MOST OFTEN
None of the strict invariants. The nonzero counts will be V4 (mate scores returned by
the qsearch hash cutoff and stand-pat cutoff - possible by design, and these positions
are tactical) and V7 (hash moves rejected by is_legal - the two-level test exists for
exactly that case). If one strict invariant has the smallest margin it is V3 at the
score_from_tt boundary, where equality is allowed by construction; my call is HOLDS.
Prediction for the tables: 0 breaches in V1-V3, V5-V17; V11 main-history extreme within
[12000, 16384]; V4 and V7 counts > 0 and reported as counts, not breaches.
