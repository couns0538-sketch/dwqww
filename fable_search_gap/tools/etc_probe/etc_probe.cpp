// etc_probe.cpp - ANALYSIS HARNESS, NOT ENGINE CODE.
//
// Question it answers: in an alpha-beta search of the kind Forge runs, how often does the transposition
// table already hold a child entry that proves a cutoff at a node the search is about to expand
// ("enhanced transposition cutoff", Plaat, Schaeffer, Pijls, de Bruin 1996), and how much of the tree
// sits under such nodes?
//
// What it is: a small, original fixed-depth search (PVS, TT, null move, reverse futility, late-move
// reductions and pruning, check extension, quiescence) written for this measurement. It links the
// UNMODIFIED lock sources bitboard.cpp, board.cpp, eval.cpp, eval_params.cpp for move generation, keys,
// SEE, repetition and the hand-crafted evaluation. It does NOT contain or link Forge's search.cpp, so
// every number it prints describes this replica, not the lock. No engine file is edited.
//
// Modes per position (fresh tables each time):
//   OFF     plain search
//   PROBE   same tree as OFF; at each eligible node it looks up every child in the TT and only COUNTS
//           (a) whether a child entry would cut, (b) whether that child is the hash move (then the plain
//           search finds the cutoff with one extra node anyway) and (c) how many nodes the plain search
//           then spends below that node. Node counts must equal OFF: that is the built-in control.
//   ETC     the cutoff is taken.
// Eligibility rules swept: "cutN" (expected cut nodes, depth >= N, N = 4, 6, 8, 10), "all3" (every
// non-PV node, depth >= 3) and "nohmN" (expected cut nodes at depth >= N whose own table entry gives no
// move to try first, N = 4, 6, 8).
//
// usage: etc_probe POSITIONS.epd OUT.tsv [hash_mb=16] [node_cap=60000000]
#include "forge/board.hpp"
#include "forge/eval.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using namespace forge;

namespace {

constexpr int Inf = 32001;
constexpr int Mate = 32000;
constexpr int MateBound = Mate - 256;
constexpr int NoEval = 32002;
constexpr int MaxPly = 120;

enum Bound : std::uint8_t { BNone = 0, BUpper = 1, BLower = 2, BExact = 3 };

struct Entry {
    std::uint32_t key32 = 0;
    Move move{};
    std::int16_t score = 0;
    std::int16_t eval = 0;
    std::uint8_t depth = 0;
    std::uint8_t bound = BNone;
    std::uint16_t pad = 0;
};
static_assert(sizeof(Entry) == 16);

// Four 16-byte entries per 64-byte cluster and "lowest depth goes first", like the lock's table.
struct Table {
    std::vector<Entry> entries;
    std::size_t clusters = 0;
    void resize(std::size_t mb) {
        clusters = mb * 1024 * 1024 / 64;
        entries.assign(clusters * 4, Entry{});
    }
    void clear() { std::fill(entries.begin(), entries.end(), Entry{}); }
    [[nodiscard]] Entry* cluster(std::uint64_t key) {
        __extension__ using u128 = unsigned __int128;
        return &entries[4 * static_cast<std::size_t>((static_cast<u128>(key) * clusters) >> 64U)];
    }
    [[nodiscard]] const Entry* find(std::uint64_t key) {
        Entry* c = cluster(key);
        const auto k = static_cast<std::uint32_t>(key);
        for (int i = 0; i < 4; ++i) {
            if (c[i].bound != BNone && c[i].key32 == k) return &c[i];
        }
        return nullptr;
    }
    void store(std::uint64_t key, int score, int eval, Move move, int depth, Bound bound) {
        Entry* c = cluster(key);
        const auto k = static_cast<std::uint32_t>(key);
        Entry* slot = nullptr;
        for (int i = 0; i < 4; ++i) {
            if (c[i].bound != BNone && c[i].key32 == k) { slot = &c[i]; break; }
        }
        const bool same = slot != nullptr;
        if (!same) {
            slot = &c[0];
            for (int i = 0; i < 4; ++i) {
                if (c[i].bound == BNone) { slot = &c[i]; break; }
                if (c[i].depth < slot->depth) slot = &c[i];
            }
        }
        if (!move.is_none() || !same) slot->move = move;
        if (bound == BExact || !same || depth + 4 > slot->depth) {
            slot->key32 = k;
            slot->score = static_cast<std::int16_t>(std::clamp(score, -32767, 32767));
            slot->eval = static_cast<std::int16_t>(std::clamp(eval, -32767, 32767));
            slot->depth = static_cast<std::uint8_t>(std::clamp(depth, 0, 255));
            slot->bound = bound;
        }
    }
};

[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= MateBound) return score + ply;
    if (score <= -MateBound) return score - ply;
    return score;
}
[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score >= MateBound) return score - ply;
    if (score <= -MateBound) return score + ply;
    return score;
}

enum Mode { Off = 0, Probe = 1, Etc = 2 };

struct Stats {
    std::uint64_t nodes = 0;
    std::uint64_t eligible = 0;      // nodes where the child lookups ran
    std::uint64_t lookups = 0;       // child TT lookups
    std::uint64_t hits = 0;          // eligible nodes with a cutting child entry
    std::uint64_t hits_hash_move = 0;// ... where that child is the node's hash move
    std::uint64_t top_hits = 0;      // PROBE only: hits not nested below another hit
    std::uint64_t savable = 0;       // PROBE only: nodes the plain search spent below top hits
    std::uint64_t top_hits_fail_high = 0; // PROBE only: top hits where the plain search also returned >= beta
};

class Search {
public:
    Table tt;
    Stats st;
    Mode mode = Off;
    int etc_min_depth = 4;
    bool etc_cut_only = true;
    bool etc_no_hash_move_only = false;   // only nodes whose own TT entry gives no move to try first
    bool etc_store = true;                // write a lower bound for the node when the cutoff is taken
    bool etc_fail_hard = false;           // return beta instead of the child's bound
    int history_offset = -32;             // placebo knob: -31 perturbs move ordering without a design change
    std::uint64_t node_cap = 0;
    bool aborted = false;

    void new_position() {
        tt.clear();
        st = Stats{};
        aborted = false;
        in_hit_subtree_ = false;
        for (auto& k : killers_) k = {Move::none(), Move::none()};
        for (auto& a : history_) for (auto& b : a) b.fill(0);
        evaluator_.clear();
        static_eval_.fill(NoEval);
        null_ok_.fill(true);
    }

    Search() {
        for (int d = 1; d < 64; ++d) {
            for (int m = 1; m < 64; ++m) {
                lmr_[static_cast<std::size_t>(d)][static_cast<std::size_t>(m)] =
                    static_cast<int>(std::max(0.0, 0.85 + std::log(static_cast<double>(d)) * std::log(static_cast<double>(m)) / 2.20));
            }
        }
    }

    int iterate(Board& board, int max_depth, Move& best_out) {
        root_index_ = board.history_size() - 1;
        int score = 0;
        for (int depth = 1; depth <= max_depth && !aborted; ++depth) {
            int delta = 18;
            int alpha = -Inf;
            int beta = Inf;
            if (depth >= 4) { alpha = std::max(score - delta, -Inf); beta = std::min(score + delta, Inf); }
            while (true) {
                root_best_ = Move::none();
                const int s = search(board, depth, alpha, beta, 0, false);
                if (aborted) break;
                if (s <= alpha) { beta = (alpha + beta) / 2; alpha = std::max(s - delta, -Inf); }
                else if (s >= beta) { beta = std::min(s + delta, Inf); }
                else { score = s; if (!root_best_.is_none()) best_out = root_best_; break; }
                delta += delta / 2 + 4;
            }
        }
        return score;
    }

private:
    Evaluator evaluator_;
    std::array<std::array<Move, 2>, MaxPly + 8> killers_{};
    std::array<std::array<std::array<int, 64>, 64>, 2> history_{};
    std::array<std::array<int, 64>, 64> lmr_{};
    std::array<int, MaxPly + 8> static_eval_{};
    std::array<bool, MaxPly + 8> null_ok_{};
    std::size_t root_index_ = 0;
    Move root_best_{};
    bool in_hit_subtree_ = false;

    [[nodiscard]] bool is_draw(const Board& board) const {
        return board.halfmove_clock() >= 100 || board.is_repetition(root_index_) || board.is_insufficient_material();
    }

    // Would the child position repeat an earlier position of this path or game? Then its TT score says
    // nothing about this path (the plain search scores it as a draw before it ever probes the table).
    [[nodiscard]] static bool repeats_on_path(const Board& board, std::uint64_t child_key) {
        const auto& h = board.key_history();
        const std::ptrdiff_t size = static_cast<std::ptrdiff_t>(h.size());
        const std::ptrdiff_t limit = size - 1 - std::min<std::ptrdiff_t>(board.halfmove_clock(), size - 1);
        for (std::ptrdiff_t i = size - 4; i >= limit; i -= 2) {
            if (h[static_cast<std::size_t>(i)] == child_key) return true;
        }
        return false;
    }

    [[nodiscard]] static int capture_value(const Board& board, Move move) {
        int value = SeePieceValue[static_cast<std::size_t>(piece_type(board.captured_piece(move)))];
        if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
        return value;
    }

    int qsearch(Board& board, int alpha, int beta, int ply) {
        ++st.nodes;
        if (node_cap != 0 && st.nodes >= node_cap) aborted = true;
        if (aborted) return 0;
        if (is_draw(board)) return 0;
        const bool pv = beta - alpha > 1;
        const bool in_check = board.in_check();
        if (ply >= MaxPly) return in_check ? 0 : evaluator_.evaluate(board);
        const std::uint64_t key = board.key();
        const Entry* e = tt.find(key);
        const Move tt_move = e != nullptr ? e->move : Move::none();
        const int tt_score = e != nullptr ? score_from_tt(e->score, ply) : NoEval;
        const Bound tt_bound = e != nullptr ? static_cast<Bound>(e->bound) : BNone;
        const bool had_entry = e != nullptr;
        if (!pv && had_entry &&
            (tt_bound == BExact || (tt_bound == BLower && tt_score >= beta) || (tt_bound == BUpper && tt_score <= alpha))) {
            return tt_score;
        }
        int best;
        int futility_base = -Inf;
        int raw_eval = NoEval;
        if (in_check) {
            best = -Inf;
        } else {
            raw_eval = (had_entry && e->eval != NoEval) ? e->eval : evaluator_.evaluate(board);
            int eval = raw_eval;
            if (had_entry && ((tt_bound == BLower && tt_score > eval) || (tt_bound == BUpper && tt_score < eval) || tt_bound == BExact)) {
                eval = tt_score;
            }
            best = eval;
            if (best >= beta) {
                if (!had_entry) tt.store(key, score_to_tt(best, ply), raw_eval, Move::none(), 0, BLower);
                return best;
            }
            if (best > alpha) alpha = best;
            futility_base = raw_eval + 160;
        }
        MoveList list;
        board.generate_pseudo_legal(list, !in_check);
        std::array<std::pair<int, Move>, 256> scored;
        std::size_t n = 0;
        for (const Move m : list) {
            int s = (m.is_capture() || m.is_promotion()) ? 10 * capture_value(board, m) + 100000 : 0;
            if (m == tt_move) s = 10000000;
            scored[n++] = {s, m};
        }
        std::sort(scored.begin(), scored.begin() + static_cast<std::ptrdiff_t>(n),
                  [](const auto& a, const auto& b) { return a.first > b.first; });
        Move best_move = Move::none();
        int move_count = 0;
        for (std::size_t i = 0; i < n; ++i) {
            const Move m = scored[i].second;
            if (!board.is_legal(m)) continue;
            ++move_count;
            if (!in_check && best > -MateBound) {
                if (!board.gives_check(m) && !m.is_promotion() && futility_base + capture_value(board, m) <= alpha) {
                    best = std::max(best, futility_base + capture_value(board, m));
                    continue;
                }
                if (!board.see_ge(m, -40)) continue;
            }
            Undo undo;
            (void)board.make_move(m, undo);
            const int s = -qsearch(board, -beta, -alpha, ply + 1);
            board.unmake_move(m, undo);
            if (aborted) return 0;
            if (s > best) {
                best = s;
                if (s > alpha) {
                    best_move = m;
                    if (s >= beta) break;
                    alpha = s;
                }
            }
        }
        if (in_check && move_count == 0) return -Mate + ply;
        const Bound bound = best >= beta ? BLower : (pv && !best_move.is_none() ? BExact : BUpper);
        tt.store(key, score_to_tt(best, ply), in_check ? NoEval : raw_eval, best_move, 0, bound);
        return best;
    }

    int search(Board& board, int depth, int alpha, int beta, int ply, bool cut_node) {
        if (depth <= 0) return qsearch(board, alpha, beta, ply);
        const bool pv = beta - alpha > 1;
        const bool root = ply == 0;
        ++st.nodes;
        if (node_cap != 0 && st.nodes >= node_cap) aborted = true;
        if (aborted) return 0;
        if (!root) {
            if (is_draw(board)) return 0;
            if (ply >= MaxPly) return board.in_check() ? 0 : evaluator_.evaluate(board);
            alpha = std::max(alpha, -Mate + ply);
            beta = std::min(beta, Mate - ply - 1);
            if (alpha >= beta) return alpha;
        }
        const std::uint64_t key = board.key();
        const Entry* e = tt.find(key);
        Entry copy{};
        const bool had_entry = e != nullptr;
        if (had_entry) copy = *e;
        const Move tt_move = had_entry ? copy.move : Move::none();
        const int tt_score = had_entry ? score_from_tt(copy.score, ply) : NoEval;
        const int tt_depth = had_entry ? copy.depth : -1;
        const Bound tt_bound = had_entry ? static_cast<Bound>(copy.bound) : BNone;
        if (!pv && had_entry && tt_depth >= depth && board.halfmove_clock() < 90 &&
            (tt_bound == BExact || (tt_bound == BLower && tt_score >= beta) || (tt_bound == BUpper && tt_score <= alpha))) {
            return tt_score;
        }

        // ---- child lookups (the mechanism under measurement) ----
        bool hit = false;
        if (mode != Off && !pv && depth >= etc_min_depth && (!etc_cut_only || cut_node) &&
            (!etc_no_hash_move_only || tt_move.is_none()) &&
            std::abs(beta) < MateBound && board.halfmove_clock() < 90) {
            ++st.eligible;
            MoveList list;
            board.generate_pseudo_legal(list, false);
            Move hit_move = Move::none();
            int hit_score = 0;
            for (const Move m : list) {
                if (!board.is_legal(m)) continue;
                std::uint64_t child_key = 0;
                if (!board.key_after(m, child_key)) continue;   // en-passant cases: key not cheap, skip
                ++st.lookups;
                const Entry* ce = tt.find(child_key);
                if (ce == nullptr) continue;
                if (ce->bound != BUpper && ce->bound != BExact) continue;
                const int s = -score_from_tt(ce->score, ply + 1);
                if (s < beta || std::abs(s) >= MateBound) continue;
                // The plain search extends safe checks by one ply: ask for the depth it would use.
                const int need = depth - 1 + ((depth >= 2 && board.gives_check(m) && board.see_ge(m, 0)) ? 1 : 0);
                if (static_cast<int>(ce->depth) < need) continue;
                if (repeats_on_path(board, child_key)) continue;
                hit = true;
                hit_move = m;
                hit_score = s;
                break;
            }
            if (hit) {
                ++st.hits;
                if (hit_move == tt_move) ++st.hits_hash_move;
                if (mode == Etc) {
                    const int value = etc_fail_hard ? beta : hit_score;
                    if (etc_store) tt.store(key, score_to_tt(value, ply), NoEval, hit_move, depth, BLower);
                    return value;
                }
            }
        }
        const bool top_hit = hit && !in_hit_subtree_;
        const std::uint64_t nodes_at_entry = st.nodes;
        if (top_hit) in_hit_subtree_ = true;
        const int result = body(board, depth, alpha, beta, ply, cut_node, had_entry, copy);
        if (top_hit) {
            in_hit_subtree_ = false;
            if (!aborted) {
                ++st.top_hits;
                st.savable += st.nodes - nodes_at_entry;
                if (result >= beta) ++st.top_hits_fail_high;
            }
        }
        return result;
    }

    int body(Board& board, int depth, int alpha, int beta, int ply, bool cut_node, bool had_entry, const Entry& entry) {
        const bool pv = beta - alpha > 1;
        const bool root = ply == 0;
        const std::uint64_t key = board.key();
        const bool in_check = board.in_check();
        const Move tt_move = had_entry ? entry.move : Move::none();
        const int tt_score = had_entry ? score_from_tt(entry.score, ply) : NoEval;
        const Bound tt_bound = had_entry ? static_cast<Bound>(entry.bound) : BNone;
        const Color us = board.side_to_move();
        const auto p = static_cast<std::size_t>(ply);

        int raw_eval = NoEval;
        int eval = NoEval;
        if (!in_check) {
            raw_eval = (had_entry && entry.eval != NoEval) ? entry.eval : evaluator_.evaluate(board);
            eval = raw_eval;
            if (had_entry && ((tt_bound == BLower && tt_score > eval) || (tt_bound == BUpper && tt_score < eval) || tt_bound == BExact)) {
                eval = tt_score;
            }
        }
        static_eval_[p] = raw_eval;
        bool improving = false;
        if (!in_check) improving = (ply >= 2 && static_eval_[p - 2] != NoEval) ? raw_eval > static_eval_[p - 2] : true;

        if (!pv && !in_check && std::abs(beta) < MateBound) {
            if (depth <= 8 && eval - (72 * depth - 40 * (improving ? 1 : 0)) >= beta && eval < MateBound) return eval;
            if (depth >= 3 && eval >= beta && raw_eval >= beta - 24 * depth + 180 && null_ok_[p] && !root &&
                board.has_non_pawn_material(us) && !(had_entry && tt_bound == BUpper && tt_score < beta)) {
                const int r = 3 + depth / 3 + std::min((eval - beta) / 200, 3);
                NullUndo undo;
                board.make_null_move(undo);
                null_ok_[p + 1] = false;
                const int s = -search(board, depth - r, -beta, -beta + 1, ply + 1, !cut_node);
                null_ok_[p + 1] = true;
                board.unmake_null_move(undo);
                if (aborted) return 0;
                if (s >= beta) return std::abs(s) >= MateBound ? beta : s;
            }
        }
        if (!in_check && depth >= 4 && tt_move.is_none() && (pv || cut_node)) --depth;

        MoveList list;
        board.generate_pseudo_legal(list, false);
        std::array<std::pair<int, Move>, 256> scored;
        std::size_t n = 0;
        for (const Move m : list) {
            int s;
            if (m == tt_move) s = 100000000;
            else if (m.is_capture() || m.is_promotion()) {
                s = (board.see_ge(m, 0) ? 10000000 : -10000000) + 10 * capture_value(board, m);
            } else if (m == killers_[p][0]) s = 9000000;
            else if (m == killers_[p][1]) s = 8000000;
            else s = history_[static_cast<std::size_t>(us)][m.from][m.to];
            scored[n++] = {s, m};
        }
        std::sort(scored.begin(), scored.begin() + static_cast<std::ptrdiff_t>(n),
                  [](const auto& a, const auto& b) { return a.first > b.first; });

        const bool has_material = board.has_non_pawn_material(us);
        std::array<Move, 128> quiets_tried;
        int quiet_count = 0;
        int best = -Inf;
        Move best_move = Move::none();
        int move_count = 0;
        bool skip_quiets = false;
        for (std::size_t i = 0; i < n; ++i) {
            const Move m = scored[i].second;
            const bool quiet = !m.is_capture() && !m.is_promotion();
            if (quiet && skip_quiets) continue;
            if (!board.is_legal(m)) continue;
            ++move_count;
            const bool gives_check = board.gives_check(m);
            const int h = quiet ? history_[static_cast<std::size_t>(us)][m.from][m.to] : 0;
            if (!root && best > -MateBound && has_material) {
                const int lmr_depth = std::max(0, depth - lmr_[static_cast<std::size_t>(std::min(depth, 63))][static_cast<std::size_t>(std::min(move_count, 63))]);
                if (quiet) {
                    const int lmp = improving ? 4 + depth * depth : (4 + depth * depth) / 2;
                    if (move_count >= lmp) skip_quiets = true;
                    if (!gives_check) {
                        if (!in_check && lmr_depth <= 7 && raw_eval + 100 + 110 * lmr_depth <= alpha) { skip_quiets = true; continue; }
                        if (lmr_depth <= 3 && h < -2048 * depth) continue;
                        if (!board.see_ge(m, -24 * lmr_depth * lmr_depth)) continue;
                    }
                } else if (!board.see_ge(m, -150 * depth)) {
                    continue;
                }
            }
            const int extension = (gives_check && depth >= 2 && !root && board.see_ge(m, 0)) ? 1 : 0;
            const int new_depth = depth - 1 + extension;
            Undo undo;
            (void)board.make_move(m, undo);
            int s = -Inf;
            bool full = !pv || move_count > 1;
            if (depth >= 2 && move_count > 1 + (root ? 1 : 0) && (quiet || move_count > 4)) {
                int r = lmr_[static_cast<std::size_t>(std::min(depth, 63))][static_cast<std::size_t>(std::min(move_count, 63))];
                if (!quiet) r /= 2;
                if (!improving) r += 1;
                if (cut_node) r += 2;
                if (gives_check) r -= 1;
                if (in_check) r -= 1;
                if (quiet) r -= std::clamp(h / 6000, -2, 2);
                const int reduced = std::clamp(new_depth - r, 1, new_depth);
                s = -search(board, reduced, -alpha - 1, -alpha, ply + 1, true);
                full = s > alpha && reduced < new_depth;
            }
            if (full && !aborted) s = -search(board, new_depth, -alpha - 1, -alpha, ply + 1, !cut_node);
            if (pv && !aborted && (move_count == 1 || s > alpha)) s = -search(board, new_depth, -beta, -alpha, ply + 1, false);
            board.unmake_move(m, undo);
            if (aborted) return 0;
            if (s > best) {
                best = s;
                if (s > alpha) {
                    best_move = m;
                    if (root) root_best_ = m;
                    if (s >= beta) break;
                    alpha = s;
                }
            }
            if (quiet && quiet_count < 128) quiets_tried[static_cast<std::size_t>(quiet_count++)] = m;
        }
        if (move_count == 0) return in_check ? -Mate + ply : 0;
        if (best >= beta && !best_move.is_capture() && !best_move.is_promotion()) {
            const int bonus = std::min(2048, 20 * depth * depth + 48 * depth + history_offset);
            auto apply = [](int& v, int b) { v += b - v * std::abs(b) / 16384; };
            if (!(killers_[p][0] == best_move)) { killers_[p][1] = killers_[p][0]; killers_[p][0] = best_move; }
            apply(history_[static_cast<std::size_t>(us)][best_move.from][best_move.to], bonus);
            for (int i = 0; i < quiet_count; ++i) {
                const Move q = quiets_tried[static_cast<std::size_t>(i)];
                if (q == best_move) continue;
                apply(history_[static_cast<std::size_t>(us)][q.from][q.to], -bonus);
            }
        }
        const Bound bound = best >= beta ? BLower : (pv && !best_move.is_none() ? BExact : BUpper);
        tt.store(key, score_to_tt(best, ply), in_check ? NoEval : raw_eval, best_move, depth, bound);
        return best;
    }
};

struct Position {
    std::string fen;
    int depth = 12;
    std::string label;
};

std::vector<Position> load(const std::string& path) {
    std::vector<Position> out;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        Position p;
        const auto a = line.find(';');
        p.fen = line.substr(0, a);
        while (!p.fen.empty() && p.fen.back() == ' ') p.fen.pop_back();
        if (a != std::string::npos) {
            const auto b = line.find(';', a + 1);
            const std::string d = line.substr(a + 1, b == std::string::npos ? std::string::npos : b - a - 1);
            const auto eq = d.find('=');
            if (eq != std::string::npos) p.depth = std::atoi(d.c_str() + eq + 1);
            if (b != std::string::npos) p.label = line.substr(b + 1);
            while (!p.label.empty() && p.label.front() == ' ') p.label.erase(p.label.begin());
        }
        out.push_back(p);
    }
    return out;
}

} // namespace

// --gen: widen a position list without outside data. From every input position the plain search
// (fixed depth, mode OFF) plays its own best move `step` plies at a time and the position reached is
// written out, `count` times. These are single continuation lines, not games between engines.
int generate(const char* in_path, const char* out_path, int step, int count, int play_depth) {
    const std::vector<Position> positions = load(in_path);
    std::FILE* out = std::fopen(out_path, "w");
    if (out == nullptr) return 3;
    auto searcher = std::make_unique<Search>();
    searcher->tt.resize(16);
    searcher->node_cap = 20000000ULL;
    int written = 0;
    for (const Position& pos : positions) {
        Board board;
        if (!board.set_fen(pos.fen)) continue;
        std::fprintf(out, "%s ; depth=%d ; %s\n", pos.fen.c_str(), pos.depth, pos.label.c_str());
        ++written;
        bool alive = true;
        for (int k = 1; k <= count && alive; ++k) {
            for (int i = 0; i < step && alive; ++i) {
                searcher->new_position();
                searcher->mode = Off;
                Move best = Move::none();
                (void)searcher->iterate(board, play_depth, best);
                if (best.is_none() || searcher->aborted || board.halfmove_clock() >= 100 ||
                    board.is_repetition() || board.is_insufficient_material()) { alive = false; break; }
                Undo undo;
                (void)board.make_move(best, undo);
            }
            if (!alive || board.legal_moves().empty()) break;
            std::fprintf(out, "%s ; depth=%d ; %s_p%d\n", board.fen().c_str(), std::max(8, pos.depth - 2), pos.label.c_str(), k * step);
            ++written;
        }
    }
    std::fclose(out);
    std::printf("wrote %d positions to %s\n", written, out_path);
    return 0;
}

int main(int argc, char** argv) {
    if (argc >= 7 && std::string(argv[1]) == "--gen") {
        return generate(argv[2], argv[3], std::atoi(argv[4]), std::atoi(argv[5]), std::atoi(argv[6]));
    }
    if (argc < 3) {
        std::puts("usage: etc_probe POSITIONS.epd OUT.tsv [hash_mb=16] [node_cap=60000000] [run,run,...] [history_offset=-32]\n"
                  "       etc_probe --gen IN.epd OUT.epd STEP COUNT PLAY_DEPTH");
        return 2;
    }
    const std::size_t hash_mb = argc > 3 ? static_cast<std::size_t>(std::atoi(argv[3])) : 16;
    const std::uint64_t cap = argc > 4 ? std::strtoull(argv[4], nullptr, 10) : 60000000ULL;
    const std::string only = argc > 5 ? std::string(",") + argv[5] + "," : std::string();
    // Optional sixth argument: the history-bonus offset used by every run except the placebo (default -32).
    // Any other value turns each run into a slightly perturbed copy of itself. Used for the pawn-ending grid:
    // does a result survive changes that are not a mechanism?
    const int base_offset = argc > 6 ? std::atoi(argv[6]) : -32;
    const std::vector<Position> positions = load(argv[1]);
    std::FILE* out = std::fopen(argv[2], "w");
    if (out == nullptr) return 3;
    std::fprintf(out, "label\tdepth\trun\tnodes\tms\tscore\tbest\teligible\tlookups\thits\thits_hash_move\ttop_hits\tsavable_nodes\ttop_hits_fail_high\taborted\tus\n");

    // Rule names: cutN = expected cut nodes at depth >= N; allN = every non-PV node at depth >= N;
    // nohmN = expected cut nodes at depth >= N that have no hash move.
    // Variants of the cutoff: _ns = no table store at the node, _fh = return beta (fail-hard) and store beta.
    // off_p = placebo: the plain search with one history constant changed by 1, to show how much node counts
    // and best moves move under a change that is not a mechanism at all.
    struct Run {
        const char* name; Mode mode; int min_depth; bool cut_only; bool no_hash_move;
        bool store = true; bool fail_hard = false; bool placebo = false;
    };
    const std::array<Run, 21> runs{{
        {"off", Off, 0, false, false},
        {"off_b", Off, 0, false, false},      // identical repeat: A/A timing noise and determinism check
        {"off_p", Off, 0, false, false, true, false, true},
        {"etc_cut6_ns", Etc, 6, true, false, false, false, false},
        {"etc_cut6_fh", Etc, 6, true, false, true, true, false},
        {"etc_cut8_ns", Etc, 8, true, false, false, false, false},
        {"etc_cut8_fh", Etc, 8, true, false, true, true, false},
        {"probe_cut4", Probe, 4, true, false},
        {"probe_cut6", Probe, 6, true, false},
        {"probe_cut8", Probe, 8, true, false},
        {"probe_cut10", Probe, 10, true, false},
        {"probe_all3", Probe, 3, false, false},
        {"probe_nohm4", Probe, 4, true, true},
        {"probe_nohm6", Probe, 6, true, true},
        {"probe_nohm8", Probe, 8, true, true},
        {"etc_cut4", Etc, 4, true, false},
        {"etc_cut6", Etc, 6, true, false},
        {"etc_cut8", Etc, 8, true, false},
        {"etc_all3", Etc, 3, false, false},
        {"etc_nohm4", Etc, 4, true, true},
        {"etc_nohm6", Etc, 6, true, true},
    }};
    auto searcher = std::make_unique<Search>();
    searcher->tt.resize(hash_mb);
    searcher->node_cap = cap;
    int index = 0;
    for (const Position& pos : positions) {
        ++index;
        for (const Run& run : runs) {
            if (!only.empty() && only.find(std::string(",") + run.name + ",") == std::string::npos) continue;
            Board board;
            std::string error;
            if (!board.set_fen(pos.fen, &error)) {
                std::printf("skip %d (%s): bad FEN: %s\n", index, pos.label.c_str(), error.c_str());
                break;
            }
            searcher->new_position();
            searcher->mode = run.mode;
            searcher->etc_min_depth = run.min_depth;
            searcher->etc_cut_only = run.cut_only;
            searcher->etc_no_hash_move_only = run.no_hash_move;
            searcher->etc_store = run.store;
            searcher->etc_fail_hard = run.fail_hard;
            searcher->history_offset = run.placebo ? -31 : base_offset;
            Move best = Move::none();
            const auto t0 = std::chrono::steady_clock::now();
            const int score = searcher->iterate(board, pos.depth, best);
            const auto us = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - t0).count();
            const auto ms = us / 1000;
            const Stats& s = searcher->st;
            const std::string bm = best.is_none() ? "none" : Board::move_to_uci(best);
            std::fprintf(out, "%s\t%d\t%s\t%llu\t%lld\t%d\t%s\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%d\t%lld\n",
                         pos.label.c_str(), pos.depth, run.name, static_cast<unsigned long long>(s.nodes),
                         static_cast<long long>(ms), score, bm.c_str(), static_cast<unsigned long long>(s.eligible),
                         static_cast<unsigned long long>(s.lookups), static_cast<unsigned long long>(s.hits),
                         static_cast<unsigned long long>(s.hits_hash_move), static_cast<unsigned long long>(s.top_hits),
                         static_cast<unsigned long long>(s.savable), static_cast<unsigned long long>(s.top_hits_fail_high),
                         searcher->aborted ? 1 : 0, static_cast<long long>(us));
            std::fflush(out);
            std::printf("%2d %-22s d%-2d %-10s nodes %10llu  %6lld ms  score %6d %s  hits %llu/%llu\n", index, pos.label.c_str(),
                        pos.depth, run.name, static_cast<unsigned long long>(s.nodes), static_cast<long long>(ms), score,
                        bm.c_str(), static_cast<unsigned long long>(s.hits), static_cast<unsigned long long>(s.eligible));
            std::fflush(stdout);
        }
    }
    std::fclose(out);
    return 0;
}
