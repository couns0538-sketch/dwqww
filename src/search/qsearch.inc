// Search module: quiescence search.
// Compiled as part of src/search.cpp, which includes this file twice (see the
// head of alphabeta.inc): as Worker::qsearch, the AL1 s198 function, and as
// Worker::qsearch_cuckoo_body for UCI CuckooRep. FORGE_QSEARCH_FN names the
// function defined here, FORGE_QSEARCH_CALL the function called for children.
#if !defined(FORGE_QSEARCH_FN) || !defined(FORGE_QSEARCH_CALL)
#error "define FORGE_QSEARCH_FN and FORGE_QSEARCH_CALL before including search/qsearch.inc"
#endif

namespace forge {

int Worker::FORGE_QSEARCH_FN(Board& board, SearchStack* ss, int alpha, int beta) {
    const bool pv_node = beta - alpha > 1;
    const int ply = ss->ply;
    if (((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
    if (aborted_) return 0;
    ++local_nodes_;
#ifdef FORGE_PROF
    prof::count(prof::Counter::Nodes);
    prof::count(prof::Counter::QsNodes);
#endif

    seldepth_ = std::max(seldepth_, ply);
    ss->pv_length = 0;

    if (is_draw(board, ply)) return 0;
    if (ply >= MaxPly) return board.in_check() ? 0 : static_evaluate(board, ss);

    // UCI IntendedThreefold: the side to move may claim a draw before its next
    // move (FIDE 9.2.1), so the draw score is a floor here. The value then depends
    // on the game history: no TT score is used or stored at this node.
    const bool claim = options::intended_threefold && board.can_claim_threefold_by_next_move();
    if (claim) {
        if (beta <= 0) return 0;
        alpha = std::max(alpha, 0);
    }

    const bool in_check = board.in_check();
    ss->in_check = in_check;

    const TTProbe tt_probe = FORGE_TT_PROBE(board.key());
    const bool tt_hit = tt_probe.hit;
    const TTEntry& tte = tt_probe.entry;
    const Move tt_move = tt_hit ? tte.move : Move::none();
    const int tt_score = !claim && tt_hit && tte.score_usable(board.halfmove_clock())
                             ? score_from_tt(tte.score, ply) : ValueNone;
    const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;
    const bool tt_pv = pv_node || (tt_hit && tte.pv());
    if (!pv_node && tt_hit && tt_score != ValueNone &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;
    }

    int best_score;
    int futility_base;
    if (in_check) {
        ss->static_eval = ValueNone;
        best_score = futility_base = -Infinite;
    } else {
        int eval;
        if (tt_hit && tte.eval != ValueNone) ss->raw_eval = tte.eval;
        else ss->raw_eval = static_evaluate(board, ss);
        eval = ss->static_eval = fb2_.corr_hist_v2 ? corrected_eval_v2(board, ss->raw_eval, ss) : corrected_eval(board, ss->raw_eval);
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
        best_score = eval;
        if (best_score >= beta) {
            if (!tt_hit && !claim) FORGE_TT_STORE(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
            return best_score;
        }
        if (best_score > alpha) alpha = best_score;
        futility_base = ss->static_eval + tune::QsFutilityMargin;
    }
    if (claim && best_score < 0) best_score = 0;

    // HistRework: check evasions score quiet moves with quiet_history, which reads this node's maps.
    if (in_check && search_options::hist_rework != 0) [[unlikely]]
        threat_maps_[static_cast<std::size_t>(ply)] = hist_rework::lesser_threats(board);
    MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
    Move best_move = Move::none();
    int move_count = 0;
    Move move;
    while (!(move = picker.next(false)).is_none()) {
        if (!board.is_legal(move)) continue;
        ++move_count;
        if (!in_check && best_score > -MateInMaxPly) {
            const bool gives_check = board.gives_check(move);
#ifdef FORGE_PROF
            prof::count(prof::Counter::QsFutilityChecks);
#endif
            // Futility: even winning the captured piece cannot raise alpha.
            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
#ifdef FORGE_PROF
                prof::count(prof::Counter::QsFutilityPrunes);
#endif
                best_score = std::max(best_score, futility_base + capture_value(board, move));
                continue;
            }
#ifdef FORGE_PROF
            prof::count(prof::Counter::QsSeeChecks);
#endif
#ifdef FORGE_PROF
            if (!board.see_ge(move, -tune::QsSeeMargin)) {
                prof::count(prof::Counter::QsSeePrunes);
                continue;
            }
#else
            if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
#endif
        }
        ss->current_move = move;
        ss->moved_piece = board.moved_piece(move);
        ss->continuation = &(*histories_.continuation_history)[static_cast<std::size_t>(ss->moved_piece)][move.to];
        (ss + 1)->ply = ply + 1;
        record_move(ss, board, move);
        Undo undo;
        (void)board.make_move(move, undo);
        shared_.tt.prefetch(board.key());
        if (options::r7_eval_prefetch) evaluator_.prefetch_pawn_entry(board.pawn_key());  // R7 J3 R7EvalPrefetch
        const int score = -FORGE_QSEARCH_CALL(board, ss + 1, -beta, -alpha);
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (score >= beta) break;
                alpha = score;
            }
        }
    }
    if (in_check && move_count == 0) return mated_in(ply);

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (!claim) {
        FORGE_TT_STORE(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
    } else if (!tt_hit || tte.score == ValueNone) {
        // Claim node: keep the move and the static evaluation, never the
        // history-dependent score. The raw score ValueNone (not score_to_tt) makes
        // every probe read tt_score == ValueNone; each use of tt_score or of the
        // bound requires tt_score != ValueNone or tests tt_score < beta, which
        // ValueNone (> Infinite) never passes. Entries with a score are not replaced.
        FORGE_TT_STORE(tt_probe, board.key(), ValueNone, in_check ? ValueNone : ss->raw_eval, best_move, 0, BoundUpper, tt_pv,
                         static_cast<std::uint16_t>(board.halfmove_clock()));
    }
    return best_score;
}

} // namespace forge
