// Search module: root setup and the iterative-deepening driver with
// aspiration windows (one Worker; thread 0 also does time management/output).
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

// Cold: called only with HardDeadline on, once per iteration (keeps the hot
// search functions' placement unchanged).
[[gnu::cold]] void Worker::publish_best_move(const SearchInfo& result) {
    if (!is_main()) return;
    const std::uint64_t pair = static_cast<std::uint64_t>(pack_move(result.ponder_move)) << 32U | pack_move(result.best_move);
    options::published_moves.store(pair, std::memory_order_relaxed);
}

SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {
#ifdef FORGE_PROF
    prof::Scope profile_scope(shared_.profile_active ? &profile_bank_ : nullptr);
#endif

#ifdef FORGE_S13_TT_CHILD_PREFETCH
    s13_tt_child_prefetch_ = limits.s13_tt_child_prefetch;
#endif
    const auto origin = limits.start_time != std::chrono::steady_clock::time_point{}
        ? limits.start_time : limits.request_start;
    start_ = origin == std::chrono::steady_clock::time_point{}
        ? std::chrono::steady_clock::now() : origin;
#if FORGE_NNUE_LAZY_ACC
    lazy_acc_stats_ = {};
#endif
    local_nodes_ = 0;
    nodes_.store(0, std::memory_order_relaxed);
    all_workers_ = &all;
    seldepth_ = 0;
    aborted_ = false;
    pondering_ = limits.ponder;
    null_tries_ = 0;
    null_cutoffs_ = 0;
    root_moves_ = limits.search_moves;
    root_restricted_ = limits.search_moves_specified;
    root_history_index_ = board.history_size() - 1;
    node_limit_ = limits.nodes;
    node_limit_specified_ = is_main() && (limits.nodes_specified || limits.nodes != 0);

    // Time allocation.
    timeman::allocate(limits, soft_limit_ms_, hard_limit_ms_, time_managed_);
    SearchInfo result;
    const MoveList legal = board.legal_moves();
    MoveList root_candidates;
    for (const Move move : legal) {
        if (!root_restricted_ ||
            std::any_of(root_moves_.begin(), root_moves_.end(), [&](const Move& m) { return m == move; })) {
            root_candidates.push_back(move);
        }
    }
    result.restricted_root_empty = root_restricted_ && !legal.empty() && root_candidates.empty();
    if (result.restricted_root_empty && emit_info) {
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        if (!shared_.output_closed.load(std::memory_order_relaxed)) {
            std::cout << "info string searchmoves restriction has no legal root moves" << std::endl;
        }
    }

    const int mate_moves = std::clamp(limits.mate_moves, 0, 32);
    const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
    const int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);
    // UCI SmpHelpersPastDepth (R3-6): a helper deepens past a `go depth` limit until the main thread
    // stops it, instead of idling once it has completed the limit; `result` keeps the limit iteration.
    const int last_depth = options::smp_helpers_past_depth && !is_main() && mate_moves == 0 ? 64 : max_depth;

    auto emit = [&](int depth, int score, const std::vector<Move>& pv) {
        if (!emit_info) return;
        const std::int64_t elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count();
        const std::uint64_t nodes = total_nodes();
        const std::uint64_t nps = elapsed > 0 ? nodes * 1000U / static_cast<std::uint64_t>(elapsed) : 0;
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        if (shared_.output_closed.load(std::memory_order_relaxed)) return;  // HardDeadline answered this go
        std::cout << "info depth " << depth << " seldepth " << std::max(seldepth_, depth) << " score " << format_score(score)
                  << " nodes " << nodes << " nps " << nps << " hashfull " << shared_.tt.hashfull() << " time " << elapsed << " pv";
        for (const Move move : pv) std::cout << ' ' << Board::move_to_uci(move);
        std::cout << std::endl;
    };

    // Terminal or adjudicated roots: report without searching.
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) {
        int score = 0;
        if (legal.empty() && board.in_check()) score = -MateValue;
        for (int depth = 1; depth <= max_depth; ++depth) {
            result.depth = depth;
            result.score = score;
            emit(depth, score, {});
            if (should_stop()) break;
        }
        if (!root_candidates.empty()) result.best_move = root_candidates.front();
        result.nodes = total_nodes();
        nodes_.store(local_nodes_, std::memory_order_relaxed);
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        return result;
    }

    // An explicit zero node budget is an immediate bounded answer.
    if (limits.nodes_specified && limits.nodes == 0) {
        result.best_move = root_candidates.front();
        result.depth = 0;
        return result;
    }

    // Dispatch and root setup may already have consumed the entire budget.
    // Check helpers too before they switch to the main worker's stop signal.
    if (hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_) {
        result.best_move = root_candidates.front();
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        return result;
    }
    if (!is_main()) {
        // Helpers run until the main thread stops them.
        soft_limit_ms_ = hard_limit_ms_ = 0;
        time_managed_ = false;
    }

    for (SearchStack& ss : stack_) {
        ss.pv_length = 0;
        ss.current_move = Move::none();
        ss.excluded_move = Move::none();
        ss.moved_piece = Empty;
        ss.static_eval = ValueNone;
        ss.continuation = &(*histories_.continuation_history)[Empty][0];
        ss.double_extensions = 0;
        ss.null_move_allowed = true;
        ss.killers = {};
    }
    SearchStack* ss = &stack_[4];
    for (int i = 0; i < MaxPly + 4; ++i) stack_[static_cast<std::size_t>(i)].ply = i - 4;
    for (SearchStack& entry : stack_) {
        entry.accumulator.valid = false;
        entry.runtime_psqt.valid = false;
#if FORGE_NNUE_LAZY_ACC
        entry.accumulator_owner = nullptr;
#endif
    }
    if (nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
#if FORGE_NNUE_LAZY_ACC
        ++lazy_acc_stats_.refreshes;
#endif
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    }
    // A v2 network computes the root accumulator itself (static_evaluate_v2).
    if (options::nnue_v2) [[unlikely]] ss->accumulator.valid = false;

    Move previous_best = Move::none();
    int stable_iterations = 0;
    int score = 0;
    int previous_score = ValueNone;
    root_effort_count_ = root_candidates.size();
    assert(root_effort_count_ <= root_effort_moves_.size());
    std::copy(root_candidates.begin(), root_candidates.end(), root_effort_moves_.begin());
    root_move_nodes_.fill(0);
    for (int depth = 1; depth <= last_depth; ++depth) {
        root_depth_ = depth;
        int delta = tune::AspirationDelta;
        int alpha = -Infinite;
        int beta = Infinite;
        if (depth >= 4) {
            alpha = std::max(score - delta, -Infinite);
            beta = std::min(score + delta, Infinite);
        }
        int iteration_score = score;
        while (true) {
            ss->ply = 0;
            // UCI CorrMargins / CorrExt / CuckooRep pick the search instance (src/search.cpp, head of
            // alphabeta.inc); with all three off it is the AL1 s198 search.
            switch ((options::corr_margins != 0 ? 1 : 0) | (options::corr_ext != 0 ? 2 : 0) | (options::cuckoo_rep ? 4 : 0)) {
                case 0: iteration_score = search(board, ss, depth, alpha, beta, false); break;
                case 1: iteration_score = search_corr_margins(board, ss, depth, alpha, beta, false); break;
                case 2: iteration_score = search_corr_ext(board, ss, depth, alpha, beta, false); break;
                case 3: iteration_score = search_cm_ce(board, ss, depth, alpha, beta, false); break;
                case 4: iteration_score = search_cuckoo(board, ss, depth, alpha, beta, false); break;
                case 5: iteration_score = search_cm_cu(board, ss, depth, alpha, beta, false); break;
                case 6: iteration_score = search_ce_cu(board, ss, depth, alpha, beta, false); break;
                default: iteration_score = search_cm_ce_cu(board, ss, depth, alpha, beta, false); break;
            }
            if (aborted_) break;
            if (iteration_score <= alpha) {
                beta = (alpha + beta) / 2;
                alpha = std::max(iteration_score - delta, -Infinite);
            } else if (iteration_score >= beta) {
                beta = std::min(iteration_score + delta, Infinite);
            } else {
                break;
            }
            delta += delta / 2 + 4;
        }
        if (aborted_) {
            // A partially searched iteration that already raised alpha at the
            // root has found a move at least as good as the previous best
            // (within the depth limit: SmpHelpersPastDepth iterations past it do not count).
            if (depth <= max_depth && ss->pv_length > 0 && !(result.pv.size() > 0 && result.pv[0] == ss->pv[0])) {
                result.best_move = ss->pv[0];
                result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                if (options::hard_deadline_ms > 0) publish_best_move(result);
                // Publish the revised line so GUIs see a PV consistent with the move.
                // A tablebase root (UCI SyzygyPath) reports the tablebase result.
                emit(depth, syzygy::root_display.load(std::memory_order_relaxed) != 0 ? syzygy::display_score(result.score)
                                                                                     : result.score, result.pv);
            }
            break;
        }
        score = iteration_score;
        // SmpHelpersPastDepth: past the limit only the aspiration window follows the score.
        if (depth > max_depth) continue;
        result.score = score;
        result.depth = depth;
        result.seldepth = std::max(seldepth_, depth);
        result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
        if (!result.pv.empty()) result.best_move = result.pv.front();
        result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
        result.nodes = total_nodes();
        if (options::hard_deadline_ms > 0) publish_best_move(result);
        emit(depth, syzygy::root_display.load(std::memory_order_relaxed) != 0 ? syzygy::display_score(score) : score,
             result.pv);

        if (result.best_move == previous_best) ++stable_iterations;
        else stable_iterations = 0;
        previous_best = result.best_move;
        const int iteration_previous_score = previous_score;
        previous_score = score;

        if (mate_moves > 0 && is_mate_score(score) && MateValue - std::abs(score) <= mate_depth) break;
        if (should_stop()) break;
        if (time_managed_ && !(pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0)) {
            double factor = timeman::stability_factor(stable_iterations, depth);
            if (local_nodes_ > 0 && depth >= 6) {
                const auto effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);
                const auto best_effort = std::find(root_effort_moves_.begin(), effort_end, result.best_move);
                if (best_effort != effort_end) {
                    const auto index = static_cast<std::size_t>(best_effort - root_effort_moves_.begin());
                    const double effort = static_cast<double>(root_move_nodes_[index]) / static_cast<double>(local_nodes_);
                    factor *= timeman::effort_scale(effort);
                }
            }
            if (timeman::eval_fell(iteration_previous_score, score)) {
                factor *= timeman::falling_eval_scale(iteration_previous_score, score);
            }
            factor = timeman::factor_floor(factor);
            if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) break;
        }
    }

    nodes_.store(local_nodes_, std::memory_order_relaxed);
    result.nodes = total_nodes();
    result.seldepth = std::max(result.seldepth, seldepth_);
    result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count());
    if (result.best_move.is_none()) result.best_move = root_candidates.front();
    return result;
}

} // namespace forge
