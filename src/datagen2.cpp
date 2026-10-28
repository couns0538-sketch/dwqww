// Self-play data generation v2 (job FB2-J2). See include/forge/datagen2.hpp for the file format.
#include "forge/datagen2.hpp"

#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <unordered_set>

namespace forge::datagen2 {

namespace {

class Rng {
public:
    explicit Rng(std::uint64_t seed) : state_(seed) {}
    std::uint64_t next() {
        std::uint64_t z = (state_ += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31U);
    }
    std::uint64_t below(std::uint64_t n) { return n <= 1 ? 0 : next() % n; }
    double uniform() { return static_cast<double>(next() >> 11U) * (1.0 / 9007199254740992.0); }

private:
    std::uint64_t state_;
};

std::uint64_t fnv1a64(const char* data, std::size_t size, std::uint64_t h = 14695981039346656037ULL) {
    for (std::size_t i = 0; i < size; ++i) {
        h ^= static_cast<unsigned char>(data[i]);
        h *= 1099511628211ULL;
    }
    return h;
}

void put_u16(std::string& out, std::uint32_t v) {
    out.push_back(static_cast<char>(v & 0xFFU));
    out.push_back(static_cast<char>((v >> 8U) & 0xFFU));
}

void put_i16(std::string& out, int v) { put_u16(out, static_cast<std::uint32_t>(static_cast<std::uint16_t>(static_cast<std::int16_t>(v)))); }

void put_u32(std::string& out, std::uint32_t v) {
    for (int i = 0; i < 4; ++i) out.push_back(static_cast<char>((v >> (8 * i)) & 0xFFU));
}

void put_u64(std::string& out, std::uint64_t v) {
    for (int i = 0; i < 8; ++i) out.push_back(static_cast<char>((v >> (8 * i)) & 0xFFU));
}

struct Reader {
    const std::string& s;
    std::size_t pos = 0;
    bool ok = true;
    std::uint32_t u8() { if (pos + 1 > s.size()) { ok = false; return 0; } return static_cast<unsigned char>(s[pos++]); }
    std::uint32_t u16() { const auto lo = u8(); const auto hi = u8(); return lo | (hi << 8U); }
    std::uint32_t u32() { std::uint32_t v = 0; for (int i = 0; i < 4; ++i) v |= u8() << (8 * i); return v; }
    std::uint64_t u64() { std::uint64_t v = 0; for (int i = 0; i < 8; ++i) v |= static_cast<std::uint64_t>(u8()) << (8 * i); return v; }
    std::string bytes(std::size_t n) { if (pos + n > s.size()) { ok = false; return {}; } std::string r = s.substr(pos, n); pos += n; return r; }
};

int game_ply(const Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == Black ? 1 : 0);
}

// Terminal rules in a fixed order: checkmate, stalemate, insufficient material, repetition, 50 moves, max ply.
bool terminal(const Board& board, int max_ply, int& white_result_x2, Termination& why) {
    const bool any_legal = board.has_legal_move();
    if (!any_legal && board.in_check()) { white_result_x2 = board.side_to_move() == White ? 0 : 2; why = Termination::Checkmate; return true; }
    if (!any_legal) { white_result_x2 = 1; why = Termination::Stalemate; return true; }
    if (board.is_insufficient_material()) { white_result_x2 = 1; why = Termination::Insufficient; return true; }
    if (board.is_repetition()) { white_result_x2 = 1; why = Termination::Repetition; return true; }
    if (board.halfmove_clock() >= 100) { white_result_x2 = 1; why = Termination::FiftyMoves; return true; }
    if (game_ply(board) >= max_ply) { white_result_x2 = 1; why = Termination::MaxPly; return true; }
    return false;
}

SearchLimits main_limits(const Config& config) {
    SearchLimits limits;
    if (config.depth > 0) {
        limits.depth = config.depth;
    } else {
        limits.nodes = config.nodes;
        limits.nodes_specified = true;
    }
    return limits;
}

std::string json_escape(const std::string& s) {
    std::string out;
    for (const char c : s) {
        if (c == '"' || c == '\\') { out.push_back('\\'); out.push_back(c); }
        else if (c == '\n') out += "\\n";
        else out.push_back(c);
    }
    return out;
}

} // namespace

const char* termination_name(Termination t) {
    switch (t) {
        case Termination::Checkmate: return "checkmate";
        case Termination::Stalemate: return "stalemate";
        case Termination::Insufficient: return "insufficient";
        case Termination::Repetition: return "repetition";
        case Termination::FiftyMoves: return "fifty";
        case Termination::MaxPly: return "max_ply";
        case Termination::AdjudicatedWin: return "adj_win";
        case Termination::AdjudicatedDraw: return "adj_draw";
    }
    return "unknown";
}

std::uint64_t game_seed(std::uint64_t run_seed, std::uint64_t index) {
    Rng mix(run_seed ^ (index * 0xD1B54A32D192ED03ULL) ^ 0x7F4A7C15F39CC060ULL);
    return mix.next();
}

std::uint16_t encode_move(const Move& move) {
    const unsigned promo = move.is_promotion() ? static_cast<unsigned>(move.promotion) : 0U;
    return static_cast<std::uint16_t>(move.from | (move.to << 6U) | (promo << 12U));
}

Move decode_move(const Board& board, std::uint16_t code) {
    const int from = code & 63;
    const int to = (code >> 6U) & 63;
    const unsigned promo = (code >> 12U) & 7U;
    for (const Move& move : board.legal_moves()) {
        const unsigned mp = move.is_promotion() ? static_cast<unsigned>(move.promotion) : 0U;
        if (move.from == from && move.to == to && mp == promo) return move;
    }
    return Move{};
}

std::array<std::uint8_t, 32> pack_board(const Board& board) {
    std::array<std::uint8_t, 32> packed{};
    for (int square = 0; square < 64; ++square) {
        const auto code = static_cast<unsigned>(board.piece_at(square));
        auto& byte = packed[static_cast<std::size_t>(square >> 1)];
        byte = static_cast<std::uint8_t>(byte | ((square & 1) != 0 ? code << 4U : code));
    }
    return packed;
}

// ---------------------------------------------------------------------------------------------
// Serialisation

void append_game(std::string& out, const Game& game) {
    put_u16(out, static_cast<std::uint32_t>(game.start_fen.size()));
    out += game.start_fen;
    out.push_back(static_cast<char>(game.white_result_x2));
    out.push_back(static_cast<char>(static_cast<std::uint8_t>(game.termination)));
    put_u16(out, game.opening_plies);
    put_u16(out, static_cast<std::uint32_t>(game.plies.size()));
    for (const Ply& ply : game.plies) {
        put_u16(out, encode_move(ply.move));
        put_i16(out, ply.score);
        out.push_back(static_cast<char>(ply.flags));
    }
}

namespace {

bool read_game(Reader& r, Game& game, std::string* error) {
    const auto fen_len = r.u16();
    game.start_fen = r.bytes(fen_len);
    game.white_result_x2 = static_cast<std::uint8_t>(r.u8());
    game.termination = static_cast<Termination>(r.u8());
    game.opening_plies = static_cast<std::uint16_t>(r.u16());
    const auto plies = r.u16();
    if (!r.ok) { if (error) *error = "truncated game header"; return false; }
    if (game.white_result_x2 > 2 || static_cast<unsigned>(game.termination) > 7 || game.opening_plies > plies) {
        if (error) *error = "bad game header fields";
        return false;
    }
    game.plies.resize(plies);
    for (auto& ply : game.plies) {
        const auto code = r.u16();
        ply.move.from = static_cast<std::uint8_t>(code & 63U);
        ply.move.to = static_cast<std::uint8_t>((code >> 6U) & 63U);
        ply.move.promotion = static_cast<std::uint8_t>((code >> 12U) & 7U);
        ply.move.flags = ply.move.promotion != 0 ? static_cast<std::uint8_t>(Promotion) : 0;
        ply.score = static_cast<std::int16_t>(static_cast<std::uint16_t>(r.u16()));
        ply.flags = static_cast<std::uint8_t>(r.u8());
    }
    if (!r.ok) { if (error) *error = "truncated game body"; return false; }
    return true;
}

} // namespace

std::string file_bytes(const std::vector<Game>& games, std::uint64_t seed) {
    std::string out = "FGB1";
    put_u32(out, 1);
    std::uint64_t plies = 0, records = 0;
    for (const Game& g : games) {
        plies += g.plies.size();
        for (const Ply& p : g.plies) records += (p.flags & RecordKept) != 0 ? 1 : 0;
    }
    put_u64(out, games.size());
    put_u64(out, plies);
    put_u64(out, records);
    put_u64(out, seed);
    put_u64(out, 0);
    for (const Game& g : games) append_game(out, g);
    put_u64(out, fnv1a64(out.data(), out.size()));
    return out;
}

bool read_games(const std::string& bytes, std::vector<Game>& games, std::uint64_t& seed, std::string* error) {
    if (bytes.size() < 56 || bytes.compare(0, 4, "FGB1") != 0) { if (error) *error = "not an FGB1 file"; return false; }
    const std::uint64_t stored = [&] { Reader t{bytes, bytes.size() - 8}; return t.u64(); }();
    if (fnv1a64(bytes.data(), bytes.size() - 8) != stored) { if (error) *error = "checksum mismatch"; return false; }
    Reader r{bytes, 4};
    const auto version = r.u32();
    const auto n_games = r.u64();
    const auto n_plies = r.u64();
    const auto n_records = r.u64();
    seed = r.u64();
    (void)r.u64();
    if (version != 1) { if (error) *error = "unsupported version"; return false; }
    games.clear();
    std::uint64_t plies = 0, records = 0;
    for (std::uint64_t i = 0; i < n_games; ++i) {
        Game g;
        if (!read_game(r, g, error)) return false;
        plies += g.plies.size();
        for (const Ply& p : g.plies) records += (p.flags & RecordKept) != 0 ? 1 : 0;
        games.push_back(std::move(g));
    }
    if (r.pos != bytes.size() - 8) { if (error) *error = "trailing bytes"; return false; }
    if (plies != n_plies || records != n_records) { if (error) *error = "header counts differ from the games"; return false; }
    return true;
}

bool records_of(const Game& game, std::string& pos_rows, std::string& score_bytes, std::string& meta_bytes,
                std::string& hce_bytes, std::string* text_lines, std::uint64_t& count, std::string* error) {
    Board board;
    if (!board.set_fen(game.start_fen)) { if (error) *error = "bad start FEN: " + game.start_fen; return false; }
    for (std::size_t i = 0; i < game.plies.size(); ++i) {
        const Ply& ply = game.plies[i];
        if ((ply.flags & RecordKept) != 0) {
            const auto packed = pack_board(board);
            pos_rows.append(reinterpret_cast<const char*>(packed.data()), packed.size());
            put_i16(score_bytes, ply.score);
            meta_bytes.push_back(static_cast<char>((board.side_to_move() == Black ? 1U : 0U) | (static_cast<unsigned>(game.white_result_x2) << 1U)));
            put_i16(hce_bytes, std::clamp(Evaluator::evaluate_uncached(board), -32767, 32767));
            if (text_lines) {
                *text_lines += board.fen() + " | " + std::to_string(ply.score) + " | "
                    + (game.white_result_x2 == 2 ? "1.0" : (game.white_result_x2 == 1 ? "0.5" : "0.0")) + "\n";
            }
            ++count;
        }
        const Move move = decode_move(board, encode_move(ply.move));
        Undo undo;
        if (move.is_none() || !board.make_move(move, undo)) {
            if (error) *error = "illegal move at ply " + std::to_string(i) + " of game starting " + game.start_fen;
            return false;
        }
    }
    return true;
}

std::string fpos_bytes(const std::string& rows, const std::string& scores, const std::string& metas, std::uint64_t count) {
    std::string out = "FPOS";
    put_u32(out, 1);
    put_u64(out, count);
    out += rows;
    out += scores;
    out += metas;
    return out;
}

std::string fhce_bytes(const std::string& hces, std::uint64_t count) {
    std::string out = "FHCE";
    put_u32(out, 1);
    put_u64(out, count);
    out += hces;
    return out;
}

// ---------------------------------------------------------------------------------------------
// Play

namespace {

struct Opening {
    Board board;
    std::vector<Move> moves;
    int redraws = 0;
};

// Softmax-sampled move: one shallow search per legal move; p(move) ~ exp(score / temperature).
Move sample_move(Searcher& searcher, Board& board, const Config& config, Rng& rng, std::uint64_t& nodes) {
    const MoveList moves = board.legal_moves();
    std::vector<double> scores;
    scores.reserve(moves.size());
    SearchLimits limits;
    limits.depth = std::max(1, config.temp_depth);
    for (const Move& move : moves) {
        Undo undo;
        if (!board.make_move(move, undo)) { scores.push_back(-1e9); continue; }
        int wr = 1;
        Termination why = Termination::MaxPly;
        if (terminal(board, config.max_ply, wr, why)) {
            // mate for us = +inf, draws = 0
            scores.push_back(why == Termination::Checkmate ? 1e6 : 0.0);
        } else {
            const SearchInfo info = searcher.search(board, limits, false, Searcher::TTAccess::Exclusive);
            nodes += info.nodes;
            scores.push_back(-static_cast<double>(info.score));
        }
        board.unmake_move(move, undo);
    }
    const double best = *std::max_element(scores.begin(), scores.end());
    const double t = std::max(1.0, config.temperature);
    std::vector<double> weights(scores.size());
    double total = 0.0;
    for (std::size_t i = 0; i < scores.size(); ++i) {
        weights[i] = std::exp(std::max(-700.0, (scores[i] - best) / t));
        total += weights[i];
    }
    double u = rng.uniform() * total;
    for (std::size_t i = 0; i < weights.size(); ++i) {
        u -= weights[i];
        if (u <= 0.0) return moves[i];
    }
    return moves[moves.size() - 1];
}

bool build_opening(Searcher& searcher, const Config& config, const std::string& start_fen, Rng& rng, Opening& opening,
                   Stats& stats, std::string* error) {
    for (int attempt = 0; attempt < std::max(1, config.opening_attempts); ++attempt) {
        opening.moves.clear();
        if (!opening.board.set_fen(start_fen)) { if (error) *error = "bad start FEN: " + start_fen; return false; }
        int plies = config.random_plies;
        if (config.random_plies_jitter > 0) {
            plies = config.random_plies - config.random_plies_jitter
                + static_cast<int>(rng.below(static_cast<std::uint64_t>(2 * config.random_plies_jitter + 1)));
            plies = std::max(0, plies);
        }
        bool dead = false;
        int wr; Termination why;
        for (int ply = 0; ply < plies; ++ply) {
            if (terminal(opening.board, config.max_ply, wr, why)) { dead = true; break; }
            const MoveList moves = opening.board.legal_moves();
            const Move move = moves[static_cast<std::size_t>(rng.below(moves.size()))];
            Undo undo;
            if (!opening.board.make_move(move, undo)) { if (error) *error = "random opening move rejected"; return false; }
            opening.moves.push_back(move);
        }
        for (int ply = 0; !dead && ply < config.temp_plies; ++ply) {
            if (terminal(opening.board, config.max_ply, wr, why)) { dead = true; break; }
            const Move move = sample_move(searcher, opening.board, config, rng, stats.nodes);
            Undo undo;
            if (!opening.board.make_move(move, undo)) { if (error) *error = "sampled opening move rejected"; return false; }
            opening.moves.push_back(move);
        }
        if (dead || terminal(opening.board, config.max_ply, wr, why)) { ++opening.redraws; continue; }
        if (config.opening_eval_cap > 0) {
            const SearchInfo info = searcher.search(opening.board, main_limits(config), false, Searcher::TTAccess::Exclusive);
            stats.nodes += info.nodes;
            if (std::abs(info.score) > config.opening_eval_cap || is_mate_score(info.score)) { ++opening.redraws; continue; }
        }
        return true;
    }
    return false;   // every attempt was lopsided or dead: the caller skips this game index
}

} // namespace

bool play_game(Searcher& searcher, const Config& config, const std::string& start_fen, std::uint64_t seed, Game& game,
               Stats& stats, std::string* error) {
    Rng rng(seed);
    searcher.clear();   // as "ucinewgame": empty table, histories, evaluation caches
    Opening opening;
    if (!build_opening(searcher, config, start_fen, rng, opening, stats, error)) {
        stats.opening_redraws += static_cast<std::uint64_t>(opening.redraws);
        return false;
    }
    stats.opening_redraws += static_cast<std::uint64_t>(opening.redraws);
    game = Game{};
    game.start_fen = start_fen;
    game.opening_plies = static_cast<std::uint16_t>(opening.moves.size());
    for (const Move& move : opening.moves) game.plies.push_back(Ply{move, ScoreNone, 0});
    Board board = opening.board;
    const SearchLimits limits = main_limits(config);

    auto finish = [&](int white_result_x2, Termination why) {
        game.white_result_x2 = static_cast<std::uint8_t>(white_result_x2);
        game.termination = why;
    };
    int wr; Termination why;
    if (terminal(board, config.max_ply, wr, why)) { finish(wr, why); return true; }
    int winner = -1, win_streak = 0, draw_streak = 0;
    while (true) {
        const SearchInfo info = searcher.search(board, limits, false, Searcher::TTAccess::Exclusive);
        stats.nodes += info.nodes;
        ++stats.searched;
        const Move move = info.best_move;
        const Move legal_move = decode_move(board, encode_move(move));
        if (move.is_none() || legal_move.is_none()) {
            if (error) *error = "search returned no legal best move in " + board.fen();
            return false;
        }
        const int score = info.score;
        const Color side = board.side_to_move();
        const bool mate = is_mate_score(score);
        std::uint8_t flags = 0;
        if (board.in_check()) { flags |= RecordInCheck; ++stats.in_check; }
        bool noisy = false;
        const int look = std::max(1, config.pv_capture_plies);
        for (int i = 0; i < look && i < static_cast<int>(info.pv.size()); ++i) {
            if (info.pv[static_cast<std::size_t>(i)].is_capture() || info.pv[static_cast<std::size_t>(i)].is_promotion()) noisy = true;
        }
        if (info.pv.empty() && (move.is_capture() || move.is_promotion())) noisy = true;
        if (noisy) { flags |= RecordNoisyPv; ++stats.noisy_pv; }
        if (mate) { flags |= RecordMateScore; ++stats.mate; }
        if (std::abs(score) > config.max_score) { flags |= RecordScoreCap; ++stats.score_cap; }
        if (game_ply(board) < config.min_ply) { flags |= RecordEarly; ++stats.early; }
        if (board.gives_check(legal_move)) { flags |= RecordGivesCheck; ++stats.gives_check; }
        bool kept = !noisy && !mate && (flags & RecordScoreCap) == 0 && (flags & RecordEarly) == 0
                    && !(config.filter_in_check && (flags & RecordInCheck) != 0)
                    && !(config.filter_gives_check && (flags & RecordGivesCheck) != 0);
        if (kept && config.skip_prob > 0.0 && rng.uniform() < config.skip_prob) { flags |= RecordSubsampled; ++stats.subsampled; kept = false; }
        if (kept) { flags |= RecordKept; ++stats.records; }
        game.plies.push_back(Ply{legal_move, static_cast<std::int16_t>(std::clamp(score, -32000, 32000)), flags});

        // adjudication bookkeeping (White's view; the same side must stay ahead on consecutive plies)
        const int white_view = side == White ? score : -score;
        int ahead = -1;
        if (white_view >= config.win_cp) ahead = White;
        else if (white_view <= -config.win_cp) ahead = Black;
        win_streak = ahead >= 0 ? (ahead == winner ? win_streak + 1 : 1) : 0;
        winner = ahead;
        draw_streak = !mate && std::abs(score) <= config.draw_cp ? draw_streak + 1 : 0;

        Undo undo;
        if (!board.make_move(legal_move, undo)) { if (error) *error = "best move rejected by make_move"; return false; }
        if (terminal(board, config.max_ply, wr, why)) { finish(wr, why); return true; }
        if (config.win_plies > 0 && win_streak >= config.win_plies) { finish(winner == White ? 2 : 0, Termination::AdjudicatedWin); return true; }
        if (config.draw_plies > 0 && draw_streak >= config.draw_plies && game_ply(board) >= config.draw_min_ply) {
            finish(1, Termination::AdjudicatedDraw);
            return true;
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Command line

bool parse_args(const std::vector<std::string>& args, Config& config, std::string* error) {
    auto need = [&](std::size_t i, const char* name) {
        if (i + 1 >= args.size()) { if (error) *error = std::string("missing value for ") + name; return false; }
        return true;
    };
    for (std::size_t i = 0; i < args.size(); ++i) {
        const std::string& a = args[i];
        auto num = [&](auto& field) {
            if (!need(i, a.c_str())) return false;
            std::istringstream in(args[++i]);
            in >> field;
            if (in.fail()) { if (error) *error = "bad number for " + a; return false; }
            return true;
        };
        if (a == "--out") { if (!need(i, "--out")) return false; config.out = args[++i]; }
        else if (a == "--games") { if (!num(config.games)) return false; }
        else if (a == "--records" || a == "--positions") { if (!num(config.records)) return false; }
        else if (a == "--max-minutes") { if (!num(config.max_minutes)) return false; }
        else if (a == "--nodes") { if (!num(config.nodes)) return false; }
        else if (a == "--depth") { if (!num(config.depth)) return false; }
        else if (a == "--hash") { if (!num(config.hash_mb)) return false; }
        else if (a == "--seed") { if (!num(config.seed)) return false; }
        else if (a == "--book") { if (!need(i, "--book")) return false; config.book = args[++i]; }
        else if (a == "--random-plies") { if (!num(config.random_plies)) return false; }
        else if (a == "--random-plies-jitter") { if (!num(config.random_plies_jitter)) return false; }
        else if (a == "--temp-plies") { if (!num(config.temp_plies)) return false; }
        else if (a == "--temperature") { if (!num(config.temperature)) return false; }
        else if (a == "--temp-depth") { if (!num(config.temp_depth)) return false; }
        else if (a == "--opening-eval-cap") { if (!num(config.opening_eval_cap)) return false; }
        else if (a == "--opening-attempts") { if (!num(config.opening_attempts)) return false; }
        else if (a == "--max-ply") { if (!num(config.max_ply)) return false; }
        else if (a == "--win-cp") { if (!num(config.win_cp)) return false; }
        else if (a == "--win-plies") { if (!num(config.win_plies)) return false; }
        else if (a == "--draw-cp") { if (!num(config.draw_cp)) return false; }
        else if (a == "--draw-plies") { if (!num(config.draw_plies)) return false; }
        else if (a == "--draw-min-ply") { if (!num(config.draw_min_ply)) return false; }
        else if (a == "--max-score") { if (!num(config.max_score)) return false; }
        else if (a == "--min-ply") { if (!num(config.min_ply)) return false; }
        else if (a == "--pv-capture-plies") { if (!num(config.pv_capture_plies)) return false; }
        else if (a == "--skip-prob") { if (!num(config.skip_prob)) return false; }
        else if (a == "--keep-in-check") config.filter_in_check = false;
        else if (a == "--filter-gives-check") config.filter_gives_check = true;
        else if (a == "--pos") config.write_pos = true;
        else if (a == "--text") config.write_text = true;
        else if (a == "--quiet") config.quiet = true;
        else { if (error) *error = "unknown argument " + a; return false; }
    }
    if (config.out.empty()) { if (error) *error = "--out is required"; return false; }
    if (config.games == 0 && config.records == 0 && config.max_minutes <= 0.0) { if (error) *error = "give --games, --records or --max-minutes"; return false; }
    if (config.random_plies < 0 || config.temp_plies < 0 || config.max_ply < 1 || config.hash_mb < 1) { if (error) *error = "bad limits"; return false; }
    return true;
}

namespace {

bool write_file(const std::string& path, const std::string& bytes, std::string* error) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) { if (error) *error = "cannot write " + path; return false; }
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    out.flush();
    if (!out) { if (error) *error = "write failed: " + path; return false; }
    return true;
}

std::vector<std::string> read_book(const std::string& path, std::string* error) {
    std::vector<std::string> fens;
    std::ifstream in(path);
    if (!in) { if (error) *error = "cannot read book " + path; return fens; }
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream fields(line);
        std::string f1, f2, f3, f4, f5, f6;
        if (!(fields >> f1 >> f2 >> f3 >> f4)) continue;
        if (!(fields >> f5)) f5 = "0";
        if (!(fields >> f6)) f6 = "1";
        if (f5.find_first_not_of("0123456789") != std::string::npos) { f5 = "0"; f6 = "1"; }
        Board board;
        const std::string fen = f1 + " " + f2 + " " + f3 + " " + f4 + " " + f5 + " " + f6;
        if (board.set_fen(fen)) fens.push_back(board.fen());
    }
    if (fens.empty() && error) *error = "no valid positions in book " + path;
    return fens;
}

} // namespace

int run_generate(const Config& config, Stats* stats_out) {
    const auto t0 = std::chrono::steady_clock::now();
    std::string error;
    std::vector<std::string> book;
    if (!config.book.empty()) {
        book = read_book(config.book, &error);
        if (book.empty()) { std::cout << "info string ERROR datagen: " << error << std::endl; return 1; }
    }
    const std::string startpos = [] { Board b; (void)b.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"); return b.fen(); }();
    Searcher searcher(static_cast<std::size_t>(config.hash_mb), 1);
    Stats stats;
    std::unordered_set<std::uint64_t> starts, after_opening;
    // incremental output: header placeholder, games appended as they finish, trailer at the end
    std::string header = "FGB1";
    put_u32(header, 1);
    for (int i = 0; i < 5; ++i) put_u64(header, 0);
    std::FILE* fgb = std::fopen((config.out + ".fgb").c_str(), "wb");
    if (!fgb) { std::cout << "info string ERROR datagen: cannot write " << config.out << ".fgb" << std::endl; return 1; }
    std::fwrite(header.data(), 1, header.size(), fgb);
    std::string pos_rows, score_bytes, meta_bytes, hce_bytes, text_lines;
    std::uint64_t written_plies = 0, written_records = 0, game_index = 0, record_count = 0;
    std::vector<Game> batch;   // games are hashed into the trailer through the same bytes that were written
    std::uint64_t running = fnv1a64(header.data(), header.size());
    std::uint64_t next_report = 0;
    while (true) {
        if (config.games > 0 && stats.games >= config.games) break;
        if (config.records > 0 && stats.records >= config.records) break;
        const double minutes = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count() / 60.0;
        if (config.max_minutes > 0.0 && minutes >= config.max_minutes) break;
        const std::uint64_t seed = game_seed(config.seed, game_index);
        Rng pick(seed ^ 0xA5A5A5A5A5A5A5A5ULL);
        const std::string& start = book.empty() ? startpos : book[static_cast<std::size_t>(pick.below(book.size()))];
        ++game_index;
        Game game;
        if (!play_game(searcher, config, start, seed, game, stats, &error)) {
            if (!error.empty()) { std::cout << "info string ERROR datagen: " << error << std::endl; std::fclose(fgb); return 1; }
            continue;   // no acceptable opening for this index
        }
        ++stats.games;
        stats.plies += game.plies.size();
        ++stats.results[game.white_result_x2];
        ++stats.terminations[static_cast<std::size_t>(game.termination)];
        {
            Board b; (void)b.set_fen(game.start_fen);
            starts.insert(b.key());
            for (std::size_t i = 0; i < game.opening_plies; ++i) { Undo u; (void)b.make_move(decode_move(b, encode_move(game.plies[i].move)), u); }
            after_opening.insert(b.key());
        }
        std::string bytes;
        append_game(bytes, game);
        std::fwrite(bytes.data(), 1, bytes.size(), fgb);
        running = fnv1a64(bytes.data(), bytes.size(), running);
        written_plies += game.plies.size();
        for (const Ply& p : game.plies) written_records += (p.flags & RecordKept) != 0 ? 1 : 0;
        if (config.write_pos || config.write_text) {
            if (!records_of(game, pos_rows, score_bytes, meta_bytes, hce_bytes, config.write_text ? &text_lines : nullptr, record_count, &error)) {
                std::cout << "info string ERROR datagen: " << error << std::endl; std::fclose(fgb); return 1;
            }
        }
        if (!config.quiet && stats.games >= next_report) {
            std::cout << "info string datagen games " << stats.games << " records " << stats.records << " plies " << stats.plies
                      << " nodes " << stats.nodes << " minutes " << minutes << std::endl;
            next_report = stats.games + 50;
        }
    }
    stats.seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    stats.distinct_starts = starts.size();
    stats.distinct_after_opening = after_opening.size();
    // trailer and the real header
    std::string trailer;
    put_u64(trailer, running);
    std::fwrite(trailer.data(), 1, trailer.size(), fgb);
    header.clear();
    header = "FGB1";
    put_u32(header, 1);
    put_u64(header, stats.games);
    put_u64(header, written_plies);
    put_u64(header, written_records);
    put_u64(header, config.seed);
    put_u64(header, 0);
    std::fseek(fgb, 0, SEEK_SET);
    std::fwrite(header.data(), 1, header.size(), fgb);
    std::fclose(fgb);
    // The checksum covered the placeholder header: recompute over the final bytes (small files) or patch it.
    {
        std::ifstream in(config.out + ".fgb", std::ios::binary);
        std::string all((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        in.close();
        const std::uint64_t sum = fnv1a64(all.data(), all.size() - 8);
        std::string fixed;
        put_u64(fixed, sum);
        std::FILE* f = std::fopen((config.out + ".fgb").c_str(), "r+b");
        if (f) { std::fseek(f, -8, SEEK_END); std::fwrite(fixed.data(), 1, 8, f); std::fclose(f); }
    }
    if (config.write_pos) {
        if (!write_file(config.out + ".pos", fpos_bytes(pos_rows, score_bytes, meta_bytes, record_count), &error)
            || !write_file(config.out + ".hce", fhce_bytes(hce_bytes, record_count), &error)) {
            std::cout << "info string ERROR datagen: " << error << std::endl; return 1;
        }
    }
    if (config.write_text && !write_file(config.out + ".txt", text_lines, &error)) { std::cout << "info string ERROR datagen: " << error << std::endl; return 1; }
    std::ostringstream js;
    js << "{\"out\": \"" << json_escape(config.out) << "\", \"seed\": " << config.seed << ", \"nodes\": " << config.nodes << ", \"depth\": " << config.depth
       << ", \"hash_mb\": " << config.hash_mb << ", \"book\": \"" << json_escape(config.book) << "\", \"random_plies\": " << config.random_plies
       << ", \"random_plies_jitter\": " << config.random_plies_jitter << ", \"temp_plies\": " << config.temp_plies << ", \"temperature\": " << config.temperature
       << ", \"temp_depth\": " << config.temp_depth << ", \"opening_eval_cap\": " << config.opening_eval_cap << ", \"max_ply\": " << config.max_ply
       << ", \"win_cp\": " << config.win_cp << ", \"win_plies\": " << config.win_plies << ", \"draw_cp\": " << config.draw_cp << ", \"draw_plies\": " << config.draw_plies
       << ", \"draw_min_ply\": " << config.draw_min_ply << ", \"max_score\": " << config.max_score << ", \"min_ply\": " << config.min_ply
       << ", \"pv_capture_plies\": " << config.pv_capture_plies << ", \"skip_prob\": " << config.skip_prob << ", \"filter_in_check\": " << (config.filter_in_check ? "true" : "false")
       << ", \"filter_gives_check\": " << (config.filter_gives_check ? "true" : "false")
       << ", \"games\": " << stats.games << ", \"plies\": " << stats.plies << ", \"searched\": " << stats.searched << ", \"records\": " << stats.records
       << ", \"opening_redraws\": " << stats.opening_redraws << ", \"distinct_starts\": " << stats.distinct_starts
       << ", \"distinct_after_opening\": " << stats.distinct_after_opening << ", \"filtered\": {\"in_check\": " << stats.in_check << ", \"noisy_pv\": " << stats.noisy_pv
       << ", \"mate\": " << stats.mate << ", \"score_cap\": " << stats.score_cap << ", \"early\": " << stats.early << ", \"subsampled\": " << stats.subsampled
       << ", \"gives_check\": " << stats.gives_check << "}, \"results_black_draw_white\": [" << stats.results[0] << ", " << stats.results[1] << ", " << stats.results[2]
       << "], \"terminations\": {";
    for (int i = 0; i < 8; ++i) js << (i ? ", " : "") << "\"" << termination_name(static_cast<Termination>(i)) << "\": " << stats.terminations[i];
    js << "}, \"nodes_total\": " << stats.nodes << ", \"seconds\": " << stats.seconds << ", \"fgb_bytes_per_ply\": 5, \"fpos_bytes_per_record\": 37}";
    const std::string summary = js.str();
    if (!write_file(config.out + ".info.json", summary + "\n", &error)) { std::cout << "info string ERROR datagen: " << error << std::endl; return 1; }
    std::cout << "info string datagen done " << summary << std::endl;
    if (stats_out) *stats_out = stats;
    return 0;
}

int run_convert(const std::string& in_path, const std::string& out_prefix, bool text, std::string* error) {
    std::ifstream in(in_path, std::ios::binary);
    if (!in) { if (error) *error = "cannot read " + in_path; return 1; }
    const std::string bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    std::vector<Game> games;
    std::uint64_t seed = 0;
    if (!read_games(bytes, games, seed, error)) return 1;
    std::string pos_rows, score_bytes, meta_bytes, hce_bytes, text_lines;
    std::uint64_t count = 0;
    for (const Game& game : games) {
        if (!records_of(game, pos_rows, score_bytes, meta_bytes, hce_bytes, text ? &text_lines : nullptr, count, error)) return 1;
    }
    if (!write_file(out_prefix + ".pos", fpos_bytes(pos_rows, score_bytes, meta_bytes, count), error)) return 1;
    if (!write_file(out_prefix + ".hce", fhce_bytes(hce_bytes, count), error)) return 1;
    if (text && !write_file(out_prefix + ".txt", text_lines, error)) return 1;
    std::cout << "info string datagen convert games " << games.size() << " records " << count << " seed " << seed << " -> " << out_prefix << ".pos/.hce" << std::endl;
    return 0;
}

} // namespace forge::datagen2
