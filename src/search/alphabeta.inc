// Search module: main alpha-beta search (pruning, extensions, LMR).
// Compiled as part of src/search.cpp, which includes this file once per search instance:
//   - FORGE_SEARCH_FN names the function defined here, which is also the function
//     its child nodes are searched with; FORGE_LMP_THRESHOLD names the late-move
//     pruning threshold it calls (each instance calls its own copy, see
//     src/search/corr_margins.inc and src/search/corr_ext.inc);
//   - FORGE_SEARCH_CORR_MARGINS = 1 adds the correction-size margins of UCI
//     CorrMargins (forge/corr_margins.hpp) at reverse futility pruning, null-move
//     pruning, quiet futility pruning and late-move reductions;
//   - FORGE_SEARCH_CORR_EXT = 1 adds the correction-history extensions of UCI
//     CorrExt (forge/corr_ext.hpp): the singular-extension decision and the
//     per-path extension budget.
// The instances (src/search.cpp): Worker::search (both 0, the AL1 s198 search),
// search_corr_margins, search_corr_ext and search_cm_ce (both 1, R3 stack). The
// root (iterative.inc) picks the instance once per iteration, so with both
// options 0 no node tests an option, and the first instance's source is the
// AL1 s198 function.
#if !defined(FORGE_SEARCH_FN) || !defined(FORGE_SEARCH_CORR_MARGINS) || !defined(FORGE_SEARCH_CORR_EXT) || \
    !defined(FORGE_LMP_THRESHOLD)
#error "define FORGE_SEARCH_FN, FORGE_SEARCH_CORR_MARGINS, FORGE_SEARCH_CORR_EXT and FORGE_LMP_THRESHOLD before including search/alphabeta.inc"
#endif

namespace forge {

int Worker::FORGE_SEARCH_FN(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
    const bool pv_node = beta - alpha > 1;
    const bool root_node = ss->ply == 0;
    const int ply = ss->ply;

    if (depth <= 0) return qsearch(board, ss, alpha, beta);
    // The frame is reused across siblings and same-ply verification searches.
    // Keep this call's inherited path budget independent of those mutations.
    const int inherited_double_extensions = (ss - 1)->double_extensions;
    ss->double_extensions = inherited_double_extensions;
    if (((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
    if (aborted_) return 0;
    ++local_nodes_;
    seldepth_ = std::max(seldepth_, ply);
    ss->pv_length = 0;
    ss->move_count = 0;

    if (!root_node) {
        if (is_draw(board, ply)) return 0;
        if (ply >= MaxPly) return board.in_check() ? 0 : static_evaluate(board, ss);
        // Mate distance pruning.
        alpha = std::max(alpha, mated_in(ply));
        beta = std::min(beta, mate_in(ply + 1));
        if (alpha >= beta) return alpha;
    }

    const bool in_check = board.in_check();
    ss->in_check = in_check;
    const Move excluded = ss->excluded_move;
    (ss + 1)->excluded_move = Move::none();
    (ss + 1)->cutoff_count = 0;
    // Children share killers with their siblings; grandchildren start afresh.
    (ss + 2)->killers = {};

    // Transposition table probe.
    const TTProbe tt_probe = shared_.tt.probe(board.key());
    const bool tt_hit = tt_probe.hit;
    const TTEntry& tte = tt_probe.entry;
    const Move tt_move = tt_hit ? tte.move : Move::none();
    const int tt_score = tt_hit && tte.score_usable(board.halfmove_clock())
                             ? score_from_tt(tte.score, ply) : ValueNone;
    const int tt_depth = tt_hit ? tte.depth : -1;
    const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;
    const bool tt_capture = !tt_move.is_none() && tt_move.is_capture();
    ss->tt_pv = pv_node || (tt_hit && tte.pv());

    if (!pv_node && excluded.is_none() && tt_hit && tt_score != ValueNone && tt_depth >= depth &&
        board.halfmove_clock() < 90 &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;
    }

    // Tablebase probe (UCI SyzygyPath; cold path, tablebase.inc).
    if (syzygy::search_cardinality.load(std::memory_order_relaxed) != 0) [[unlikely]] {
        const int tb_score = probe_tablebase(board, ss, depth, alpha, beta, tt_probe);
        if (tb_score != ValueNone) return tb_score;
    }

    // Static evaluation.
    int eval;
    if (in_check) {
        eval = ss->static_eval = ss->raw_eval = ValueNone;
    } else if (!excluded.is_none()) {
        eval = ss->static_eval;
    } else {
        if (tt_hit && tte.eval != ValueNone) ss->raw_eval = tte.eval;
        else ss->raw_eval = static_evaluate(board, ss);
        eval = ss->static_eval = corrected_eval(board, ss->raw_eval);
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
    }
#if FORGE_SEARCH_CORR_MARGINS || FORGE_SEARCH_CORR_EXT
    // CorrMargins / CorrExt: size of the correction-history adjustment at this node (0 in check;
    // corr_margins::correction_size and corr_ext::correction_size are the same function).
#if FORGE_SEARCH_CORR_MARGINS
    const int correction = corr_margins::correction_size(in_check, ss->static_eval, ss->raw_eval);
#else
    const int correction = corr_ext::correction_size(in_check, ss->static_eval, ss->raw_eval);
#endif
#endif

    bool improving = false;
    if (!in_check) {
        if ((ss - 2)->static_eval != ValueNone) improving = ss->static_eval > (ss - 2)->static_eval;
        else if ((ss - 4)->static_eval != ValueNone) improving = ss->static_eval > (ss - 4)->static_eval;
        else improving = true;
    }

    if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta)) {
        // Razoring: hopeless positions fall back to quiescence.
        if (depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {
            const int razor = qsearch(board, ss, alpha - 1, alpha);
            if (aborted_) return 0;
            if (razor < alpha) return razor;
        }
        // Reverse futility pruning.
#if FORGE_SEARCH_CORR_MARGINS
        if (depth <= tune::RfpDepth && eval - corr_margins::rfp_margin(depth, improving, correction) >= beta &&
            eval < MateInMaxPly) {
            return eval;
        }
#else
        if (depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta &&
            eval < MateInMaxPly) {
            return eval;
        }
#endif
        // Null move pruning.
#if FORGE_SEARCH_CORR_MARGINS
        if (depth >= tune::NullMoveMinDepth && eval >= beta &&
            ss->static_eval >= corr_margins::null_move_threshold(beta, depth, correction) &&
#else
        if (depth >= tune::NullMoveMinDepth && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
#endif
            ss->null_move_allowed && !(ss - 1)->current_move.is_none() &&
            board.has_non_pawn_material(board.side_to_move()) &&
            !(tt_hit && tt_bound == BoundUpper && tt_score < beta)) {
            ++null_tries_;
            const int reduction = tune::NullMoveBase + depth / tune::NullMoveDepthDivisor +
                                  std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);
            ss->current_move = Move::none();
            ss->moved_piece = Empty;
            ss->continuation = &(*histories_.continuation_history)[Empty][0];
            (ss + 1)->ply = ply + 1;
            record_null_move(ss);
            NullUndo undo;
            board.make_null_move(undo);
            int null_score = -FORGE_SEARCH_FN(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
            board.unmake_null_move(undo);
            if (aborted_) return 0;
            if (null_score >= beta) {
                if (is_mate_score(null_score)) null_score = beta;
                if (depth < 14) {
                    ++null_cutoffs_;
                    return null_score;
                }
                // Verification search at high depth guards against zugzwang.
                ss->null_move_allowed = false;
                const int verification = FORGE_SEARCH_FN(board, ss, depth - reduction, beta - 1, beta, false);
                ss->double_extensions = inherited_double_extensions;
                ss->null_move_allowed = true;
                if (aborted_) return 0;
                if (verification >= beta) {
                    ++null_cutoffs_;
                    return null_score;
                }
            }
        }
        // ProbCut: a good capture that beats beta by a margin at reduced depth.
        const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;
        if (depth >= tune::ProbcutDepth && !is_mate_score(beta) &&
            !(tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score < probcut_beta)) {
            MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
            Move move;
            while (!(move = picker.next(false)).is_none()) {
                if (move == excluded || !board.is_legal(move)) continue;
                if (!board.see_ge(move, probcut_beta - ss->static_eval)) continue;
                ss->current_move = move;
                ss->moved_piece = board.moved_piece(move);
                ss->continuation = &(*histories_.continuation_history)[static_cast<std::size_t>(ss->moved_piece)][move.to];
                (ss + 1)->ply = ply + 1;
                record_move(ss, board, move);
                Undo undo;
                (void)board.make_move(move, undo);
                int value = -qsearch(board, ss + 1, -probcut_beta, -probcut_beta + 1);
                if (value >= probcut_beta && !aborted_) {
                    value = -FORGE_SEARCH_FN(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);
                }
                board.unmake_move(move, undo);
                if (aborted_) return 0;
                if (value >= probcut_beta) {
                    shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ply), ss->raw_eval, move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());
                    return value;
                }
            }
        }
    }

    // Internal iterative reduction: no hash move suggests a less important node.
    if (!in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;

    MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Main);
    std::array<Move, 128> quiets_tried{};
    std::array<Move, 64> captures_tried{};
    int quiet_count = 0;
    int capture_count = 0;
    int best_score = -Infinite;
    Move best_move = Move::none();
    int move_count = 0;
    bool skip_quiets = false;
    const bool has_material = board.has_non_pawn_material(board.side_to_move());

    Move move;
    while (!(move = picker.next(skip_quiets)).is_none()) {
        if (move == excluded) continue;
        if (root_node && root_restricted_ &&
            std::none_of(root_moves_.begin(), root_moves_.end(), [&](const Move& m) { return m == move; })) {
            continue;
        }
        if (!board.is_legal(move)) continue;
        ++move_count;
        ss->move_count = move_count;
        const bool capture = move.is_capture();
        const bool quiet = !capture && !move.is_promotion();
        const bool gives_check = board.gives_check(move);
        const Piece moved = board.moved_piece(move);
        const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);

        // Shallow-depth pruning of unpromising moves.
        if (!root_node && best_score > -MateInMaxPly && has_material) {
            if (quiet && !skip_quiets && move_count >= FORGE_LMP_THRESHOLD(depth, improving)) skip_quiets = true;
            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));
            if (quiet && !gives_check) {
#if FORGE_SEARCH_CORR_MARGINS
                if (!in_check && lmr_depth <= tune::FutilityDepth &&
                    ss->static_eval + corr_margins::futility_margin(lmr_depth, correction) <= alpha) {
#else
                if (!in_check && lmr_depth <= tune::FutilityDepth &&
                    ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {
#endif
                    skip_quiets = true;
                    continue;
                }
                if (lmr_depth <= tune::HistoryPruneDepth && history < -tune::HistoryPruneMultiplier * depth) continue;
                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;
            } else {
                // Futility pruning for captures: even winning the piece cannot
                // bring the position back to alpha.
                if (tune::CaptureFutilityBase > 0 && capture && !in_check && !gives_check &&
                    lmr_depth <= tune::CaptureFutilityDepth &&
                    ss->static_eval + tune::CaptureFutilityBase + tune::CaptureFutilityMultiplier * lmr_depth +
                            capture_value(board, move) + history / 8 <= alpha) {
                    continue;
                }
                const int see_threshold = -tune::SeeNoisyMultiplier * depth;
                if (!(picker.last_move_see_nonnegative() && see_threshold <= 0) &&
                    !board.see_ge(move, see_threshold)) continue;
            }
        }

        // Extensions.
        int extension = 0;
        if (!root_node && depth >= tune::SingularDepth && move == tt_move && excluded.is_none() && tt_bound != BoundUpper &&
            tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {
            const int singular_beta = tt_score - tune::SingularMargin * depth;
            const int singular_depth = (depth - 1) / 2;
            const bool saved_tt_pv = ss->tt_pv;
            ss->excluded_move = move;
            const int singular_score = FORGE_SEARCH_FN(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);
            ss->tt_pv = saved_tt_pv;
            ss->double_extensions = inherited_double_extensions;
            ss->excluded_move = Move::none();
            if (aborted_) return 0;
            if (singular_score < singular_beta) {
#if FORGE_SEARCH_CORR_EXT
                // CorrExt: double margin shrinking with |correction|, triple extension, per-path budget.
                extension = corr_ext::singular_extension(pv_node, singular_score, singular_beta, correction,
                                                         inherited_double_extensions);
#else
                extension = 1;
                if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {
                    extension = 2;
                }
#endif
            } else if (singular_beta >= beta) {
                return singular_beta;
            } else if (tt_score >= beta) {
                extension = -2;
            } else if (cut_node) {
                extension = -1;
            }
        } else if (gives_check && depth >= tune::CheckExtensionDepth && !root_node &&
                   (picker.last_move_see_nonnegative() || board.see_ge(move, 0))) {
            extension = 1;
        }
#if FORGE_SEARCH_CORR_EXT
        // CorrExt: the path pays extension - 1 plies for a double or triple extension.
        ss->double_extensions = corr_ext::path_extra_after(inherited_double_extensions, extension);
#else
        ss->double_extensions = inherited_double_extensions + (extension == 2);
#endif
        const int new_depth = depth - 1 + extension;

        ss->current_move = move;
        ss->moved_piece = moved;
        ss->continuation = &(*histories_.continuation_history)[static_cast<std::size_t>(moved)][move.to];
        (ss + 1)->ply = ply + 1;
        record_move(ss, board, move);
        Undo undo;
        (void)board.make_move(move, undo);
        shared_.tt.prefetch(board.key());
        const std::uint64_t nodes_before = local_nodes_;
        std::size_t root_effort_index = 0;
        if (root_node) {
            const auto root_effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);
            root_effort_index = static_cast<std::size_t>(std::find(root_effort_moves_.begin(), root_effort_end, move) - root_effort_moves_.begin());
            assert(root_effort_index < root_effort_count_);
        }

        int score = -Infinite;
        bool full_depth_needed = !pv_node || move_count > 1;
        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && (quiet || !ss->tt_pv || move_count > 4)) {
            int r = reduction(quiet, depth, move_count);
            if (ss->tt_pv) r -= 1;
            if (!improving) r += 1;
            if (cut_node) r += 2;
            if (tt_capture && quiet) r += 1;
            if (gives_check) r -= 1;
            if (in_check) r -= 1;
            if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
#if FORGE_SEARCH_CORR_MARGINS
            r = corr_margins::lmr_reduction(r, correction);
#endif
            const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);
            score = -FORGE_SEARCH_FN(board, ss + 1, reduced_depth, -alpha - 1, -alpha, true);
            full_depth_needed = score > alpha && reduced_depth < new_depth;
            if (full_depth_needed) {
                score = -FORGE_SEARCH_FN(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
                full_depth_needed = false;
            }
            if (!aborted_ && quiet && score > alpha) {
                // A late quiet move that beat expectations deserves a history boost.
                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
            }
        }
        if (full_depth_needed && !aborted_) {
            score = -FORGE_SEARCH_FN(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
        }
        if (pv_node && !aborted_ && (move_count == 1 || score > alpha)) {
            score = -FORGE_SEARCH_FN(board, ss + 1, new_depth, -beta, -alpha, false);
        }
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (root_node && root_effort_index < root_effort_count_)
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;

        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (score >= beta) {
                    ++ss->cutoff_count;
                    break;
                }
                alpha = score;
            }
        }
        if (quiet && quiet_count < static_cast<int>(quiets_tried.size())) quiets_tried[static_cast<std::size_t>(quiet_count++)] = move;
        else if (!quiet && capture_count < static_cast<int>(captures_tried.size())) captures_tried[static_cast<std::size_t>(capture_count++)] = move;
    }

    if (move_count == 0) {
        if (!excluded.is_none()) return alpha;
        if (root_node && root_restricted_) return 0;
        return in_check ? mated_in(ply) : 0;
    }

    if (best_score >= beta) {
        if (!best_move.is_capture() && !best_move.is_promotion()) {
            update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);
        }
        update_capture_stats(board, best_move, depth, captures_tried.data(), capture_count);
    } else if (!best_move.is_none() && (!best_move.is_capture() && !best_move.is_promotion())) {
        // Even without a cutoff, a new PV move earned its place.
        apply_history((*histories_.main_history)[static_cast<std::size_t>(board.side_to_move())][best_move.from][best_move.to],
                      history_bonus(depth) / 4);
    } else if (tune::FailLowContinuationBonus > 0 && best_move.is_none() && !(ss - 1)->current_move.is_none() &&
               (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_capture() && ply > 0) {
        // Every move failed low: the parent's quiet move refuted this line.
        update_continuation(ss - 1, (ss - 1)->moved_piece, (ss - 1)->current_move.to,
                            history_bonus(depth) * tune::FailLowContinuationBonus / 100);
    }

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (excluded.is_none() && !(root_node && root_restricted_)) {
        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
    }
    // Teach the static evaluation about this pawn structure when the search
    // result is a usable bound in the direction of the difference.
    if (!in_check && excluded.is_none() && !is_mate_score(best_score) &&
        (best_move.is_none() || !best_move.is_capture()) &&
        !(bound == BoundLower && best_score <= ss->static_eval) &&
        !(bound == BoundUpper && best_score >= ss->static_eval)) {
        update_correction(board, depth, best_score, ss->static_eval);
    }
    return best_score;
}

} // namespace forge
