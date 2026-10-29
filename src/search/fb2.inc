// Search module: FB2-J3 options on the R3 stack (forge/fb2.hpp; BUNDLES.md).
// Compiled as part of src/search.cpp (included exactly once, last, so the default search functions keep their
// placement). Every hook in alphabeta.inc / qsearch.inc reads the worker's per-search snapshot fb2_, never
// fb2::requested.

namespace forge {

namespace fb2 {

Options requested{};

namespace {
// LmrTableV2 model (idea: a logistic model of "the reduced search raised alpha", fitted by FB2-J3 on 1,268,077
// LMR decisions of `bench 16`; coefficients from fable_fb2/j3/logs/lmr_fit_bench16.json on fable-fb2-j3).
// Reduction = the lock's log-log base + scale * (mean log-odds - log-odds of this decision), rounded, >= 0:
// decisions the model expects to fail low are reduced more, those it expects to raise alpha less. The fitted
// history slope replaces the lock's clamp(history / divisor, -2, 2) term.
struct LmrV2Model {
    double intercept, ln_depth, ln_moves, ln_product, history, improving, cut_node, tt_pv;
    double mean_logodds;
    double scale;
};
constexpr LmrV2Model LmrV2Quiet{-1.738394, -0.645324, -1.551285, 0.213368, 0.482482, 0.889737, 1.517481, 0.185308,
                                -3.978049, 0.547076};
constexpr LmrV2Model LmrV2Noisy{-0.307650, -1.360382, -3.300709, 0.884022, 0.680828, 1.174135, 1.817594, -0.182583,
                                -5.206993, 0.399677};
} // namespace

int lmr_v2_reduction(bool quiet, int depth, int moves, int history, bool improving, bool cut_node, bool tt_pv) {
    const LmrV2Model& m = quiet ? LmrV2Quiet : LmrV2Noisy;
    const double ld = std::log(static_cast<double>(std::max(depth, 1)));
    const double lm = std::log(static_cast<double>(std::max(moves, 1)));
    const double h = static_cast<double>(std::clamp(history, -HistoryMax, HistoryMax)) / HistoryMax;
    const double logodds = m.intercept + m.ln_depth * ld + m.ln_moves * lm + m.ln_product * ld * lm + m.history * h +
                           m.improving * (improving ? 1.0 : 0.0) + m.cut_node * (cut_node ? 1.0 : 0.0) +
                           m.tt_pv * (tt_pv ? 1.0 : 0.0);
    const double base = quiet ? tune::LmrQuietBase / 100.0 + ld * lm / (tune::LmrQuietDivisor / 100.0)
                              : tune::LmrNoisyBase / 100.0 + ld * lm / (tune::LmrNoisyDivisor / 100.0);
    const double r = base + m.scale * (m.mean_logodds - logodds);
    return static_cast<int>(std::lround(std::max(0.0, r)));
}

void apply_bundle(Bundle bundle) {
    const BundleSettings s = bundle_settings(bundle);
    // CorrHistPlus is written before CorrHistV2 is read by any search, and the pair is exclusive by construction.
    options::corr_hist_plus = static_cast<std::uint8_t>(s.corr_hist_plus);
    search_options::hist_rework = s.hist_rework;
    options::cuckoo_rep = s.cuckoo_rep;
    const bool smp_v2 = requested.smp_v2; // BundlePreset still owns only its original six options.
    requested = s.fb2;
    requested.smp_v2 = smp_v2;
}

// SmpV2: same helper diversification as Forge FB2-J5, with a corrected selector.
int smp_depth_skew(int id) { return id > 0 && (id & 1) != 0 ? 1 : 0; }
int smp_aspiration_multiplier(int id) { return id > 0 && (id & 1) == 0 ? 1 + ((id >> 1) % 3) : 1; }

[[gnu::cold]] SearchInfo smp_select_result(const SearchInfo& main, const std::vector<SearchInfo>& helpers) {
    if (main.restricted_root_empty) return main;
    const auto valid_score = [](int score) { return score >= -MateValue && score <= MateValue; };
    const auto proven = [&](int score) {
        return valid_score(score) && (is_mate_score(score) ||
               (syzygy::tb_scores && score >= syzygy::TbWinInMaxPly));
    };
    const SearchInfo* best = &main;
    for (const auto& helper : helpers) {
        if (helper.best_move.is_none() || helper.pv.empty() || helper.pv.front() != helper.best_move ||
            helper.restricted_root_empty || helper.depth <= best->depth || !valid_score(helper.score)) continue;
        // Depth alone cannot erase a proven score, even after one helper has been selected.
        if (proven(best->score) && (!proven(helper.score) || helper.score < best->score)) continue;
        best = &helper;
    }
    SearchInfo result = *best;
    result.nodes = main.nodes;
    result.elapsed_ms = main.elapsed_ms;
    return result;
}

} // namespace fb2

// CorrHistV2 (idea: continuation correction history, FB2-J3): the AL1 s198 pawn / material correction, HistRework's
// joint term when that option is on (bundle B4), plus the continuation corrections of the last two moves.
// Only called while CorrHistPlus is 0 (fb2::effective), so corrected_eval's CorrHistPlus branch is never bypassed.
int Worker::corrected_eval_v2(const Board& board, int raw_eval, const SearchStack* ss) const {
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    std::int32_t correction = (*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)];
    if (tune::MaterialCorrectionWeight > 0) {
        correction += (*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)] * tune::MaterialCorrectionWeight / 100;
    }
    if (const int level = search_options::hist_rework; level != 0) {
        correction += (*joint_correction_)[side][hist_rework::joint_key(board) & (CorrectionSize - 1U)] *
                      hist_rework::joint_weight(level) / 100;
    }
    // Null moves and the root carry no continuation key.
    if (ss->ply >= 1 && (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_none()) {
        correction += (*continuation_correction_)[0][static_cast<std::size_t>((ss - 1)->moved_piece)][(ss - 1)->current_move.to];
    }
    if (ss->ply >= 2 && (ss - 2)->moved_piece != Empty && !(ss - 2)->current_move.is_none()) {
        correction += (*continuation_correction_)[1][static_cast<std::size_t>((ss - 2)->moved_piece)][(ss - 2)->current_move.to];
    }
    return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);
}

void Worker::update_correction_v2(const Board& board, const SearchStack* ss, int depth, int best_score, int static_eval) {
    // The lock's update (with HistRework's joint table when on), then the two continuation entries, same step.
    update_correction(board, depth, best_score, static_eval);
    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
    const int weight = std::min(depth + 1, 16);
    auto apply = [&](std::int32_t& entry) {
        entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);
    };
    if (ss->ply >= 1 && (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_none()) {
        apply((*continuation_correction_)[0][static_cast<std::size_t>((ss - 1)->moved_piece)][(ss - 1)->current_move.to]);
    }
    if (ss->ply >= 2 && (ss - 2)->moved_piece != Empty && !(ss - 2)->current_move.is_none()) {
        apply((*continuation_correction_)[1][static_cast<std::size_t>((ss - 2)->moved_piece)][(ss - 2)->current_move.to]);
    }
}

} // namespace forge
