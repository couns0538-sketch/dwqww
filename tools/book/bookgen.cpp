// Opening-book tooling for Forge.
//
//   forge_bookgen openings --count N [--min-ply A] [--max-ply B] [--depth D]
//                 [--margin CP] [--seed S] --out start.epd
//       Walks from the start position choosing random moves among those a
//       shallow search rates within CP of the best, producing diverse but sane
//       starting positions (FEN move counters preserve the ply count).
//
//   forge_bookgen expand [--widths 3,3,3,3,2,2] [--max-ply 16] [--nodes N]
//                 [--alt-nodes M] [--margin CP] [--threads T] --out book_data.inc
//       Engine-generated book: from the start position, keeps the best
//       `width` moves at each ply (ranked by searches of M nodes, within CP of
//       the best) and continues each line with the best move of an N-node
//       search until max-ply.
//
//   forge_bookgen build [--max-ply P] [--min-games G] [--min-score PCT]
//                 [--verify NODES] [--margin CP] --out book_data.inc <games.pgn ...>
//       Tallies move statistics from UCI-notation PGNs (fastchess output with
//       [FEN] tags), keeps well-supported moves and optionally verifies each
//       with the engine, then writes the embedded book include.
#include "forge/board.hpp"
#include "forge/book.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <sstream>
#include <atomic>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

namespace {

struct MoveStats {
    int games = 0;
    double points = 0.0; // for the side that played the move
};

struct Game {
    std::string result;
    std::string fen;
    std::vector<std::string> moves;
    std::vector<bool> from_book; // moves supplied by the match runner's opening book
};

bool read_game(std::istream& input, Game& game) {
    game = Game{};
    std::string line;
    bool have_moves = false;
    std::string movetext;
    while (std::getline(input, line)) {
        if (line.empty()) {
            if (have_moves) break;
            continue;
        }
        if (line[0] == '[') {
            if (have_moves) break;
            if (line.rfind("[Result ", 0) == 0 || line.rfind("[FEN ", 0) == 0) {
                const auto first = line.find('"');
                const auto last = line.rfind('"');
                if (first != std::string::npos && last != std::string::npos && last > first) {
                    const std::string value = line.substr(first + 1, last - first - 1);
                    if (line[1] == 'R') game.result = value;
                    else game.fen = value;
                }
            }
            continue;
        }
        have_moves = true;
        movetext += line + ' ';
    }
    if (!have_moves) return false;
    std::size_t i = 0;
    while (i < movetext.size()) {
        const char c = movetext[i];
        if (c == ' ') { ++i; continue; }
        if (c == '{') {
            const auto end = movetext.find('}', i);
            if (end == std::string::npos) break;
            if (!game.from_book.empty() && movetext.compare(i + 1, 4, "book") == 0) game.from_book.back() = true;
            i = end + 1;
            continue;
        }
        std::size_t end = movetext.find(' ', i);
        if (end == std::string::npos) end = movetext.size();
        std::string token = movetext.substr(i, end - i);
        i = end;
        if (token == "1-0" || token == "0-1" || token == "1/2-1/2" || token == "*") break;
        if (!token.empty() && std::isdigit(static_cast<unsigned char>(token[0]))) {
            const auto dot = token.find('.');
            if (dot == std::string::npos) continue;
            token = token.substr(token.find_last_of('.') + 1);
            if (token.empty()) continue;
        }
        game.moves.push_back(token);
        game.from_book.push_back(false);
    }
    return true;
}

int game_ply(const forge::Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == forge::Black ? 1 : 0);
}

int run_openings(int argc, char** argv) {
    int count = 2000;
    int min_ply = 2;
    int max_ply = 8;
    int depth = 6;
    int margin = 50;
    int final_margin = 80;
    std::uint64_t seed = 20261013;
    std::string out_path = "start.epd";
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        auto next = [&]() -> std::string { return i + 1 < argc ? argv[++i] : ""; };
        if (arg == "--count") count = std::stoi(next());
        else if (arg == "--min-ply") min_ply = std::stoi(next());
        else if (arg == "--max-ply") max_ply = std::stoi(next());
        else if (arg == "--depth") depth = std::stoi(next());
        else if (arg == "--margin") margin = std::stoi(next());
        else if (arg == "--final-margin") final_margin = std::stoi(next());
        else if (arg == "--seed") seed = std::stoull(next());
        else if (arg == "--out") out_path = next();
    }
    std::mt19937_64 rng(seed);
    forge::Searcher searcher(16);
    std::set<std::string> unique;
    std::ofstream out(out_path);
    int produced = 0;
    int attempts = 0;
    while (produced < count && attempts < count * 20) {
        ++attempts;
        forge::Board board;
        const int target_ply = min_ply + static_cast<int>(rng() % static_cast<std::uint64_t>(max_ply - min_ply + 1));
        bool ok = true;
        for (int ply = 0; ply < target_ply; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) { ok = false; break; }
            // Score every move with a shallow search from the opponent's view.
            std::vector<std::pair<int, forge::Move>> scored;
            for (const forge::Move move : legal) {
                forge::Board child = board;
                forge::Undo undo;
                (void)child.make_move(move, undo);
                forge::SearchLimits limits;
                limits.depth = depth;
                searcher.clear_hash();
                const forge::SearchInfo info = searcher.search(child, limits);
                scored.emplace_back(-info.score, move);
            }
            std::sort(scored.begin(), scored.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
            std::vector<forge::Move> candidates;
            for (const auto& [score, move] : scored) {
                if (score >= scored.front().first - margin) candidates.push_back(move);
            }
            const forge::Move chosen = candidates[rng() % candidates.size()];
            forge::Undo undo;
            (void)board.make_move(chosen, undo);
        }
        if (!ok) continue;
        // Final sanity check with a deeper search.
        forge::SearchLimits limits;
        limits.nodes = 100000;
        limits.nodes_specified = true;
        searcher.clear_hash();
        const forge::SearchInfo info = searcher.search(board, limits);
        if (std::abs(info.score) > final_margin) continue;
        const std::string fen = board.fen();
        if (!unique.insert(fen).second) continue;
        out << fen << '\n';
        ++produced;
        if (produced % 100 == 0) std::cerr << "generated " << produced << " openings (" << attempts << " attempts)\n";
    }
    std::cerr << "wrote " << produced << " openings to " << out_path << '\n';
    return 0;
}

void write_entries(const std::string& out_path, std::vector<forge::book::Entry> entries);

int run_build(int argc, char** argv) {
    int max_ply = 30;
    int min_games = 4;
    double min_score = 0.45;
    std::uint64_t verify_nodes = 0;
    int margin = 25;
    std::string out_path = "book_data.inc";
    std::vector<std::string> inputs;
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        auto next = [&]() -> std::string { return i + 1 < argc ? argv[++i] : ""; };
        if (arg == "--max-ply") max_ply = std::stoi(next());
        else if (arg == "--min-games") min_games = std::stoi(next());
        else if (arg == "--min-score") min_score = std::stod(next()) / 100.0;
        else if (arg == "--verify") verify_nodes = std::stoull(next());
        else if (arg == "--margin") margin = std::stoi(next());
        else if (arg == "--out") out_path = next();
        else inputs.push_back(arg);
    }
    if (inputs.empty()) {
        std::cerr << "no input PGN files\n";
        return 2;
    }

    // key -> (encoded move -> stats); also remember one FEN per key for verification.
    std::unordered_map<std::uint64_t, std::map<std::uint16_t, MoveStats>> table;
    std::unordered_map<std::uint64_t, std::string> fens;
    std::uint64_t games = 0;
    for (const std::string& path : inputs) {
        std::ifstream in(path);
        if (!in) {
            std::cerr << "cannot open " << path << '\n';
            return 1;
        }
        Game game;
        while (read_game(in, game)) {
            double white_points;
            if (game.result == "1-0") white_points = 1.0;
            else if (game.result == "0-1") white_points = 0.0;
            else if (game.result == "1/2-1/2") white_points = 0.5;
            else continue;
            forge::Board board;
            if (!game.fen.empty() && !board.set_fen(game.fen)) continue;
            ++games;
            for (std::size_t m = 0; m < game.moves.size(); ++m) {
                if (game_ply(board) >= max_ply) break;
                const auto move = board.parse_uci(game.moves[m]);
                if (!move.has_value()) break;
                // Only the engine's own choices are tallied; opening-book moves
                // supplied by the match runner are replayed but not counted.
                if (!game.from_book[m]) {
                    const std::uint64_t key = forge::book::polyglot_key(board);
                    MoveStats& stats = table[key][forge::book::encode_move(board, *move)];
                    ++stats.games;
                    stats.points += board.side_to_move() == forge::White ? white_points : 1.0 - white_points;
                    if (fens.find(key) == fens.end()) fens[key] = board.fen();
                }
                forge::Undo undo;
                (void)board.make_move(*move, undo);
            }
        }
    }
    std::cerr << "read " << games << " games, " << table.size() << " positions\n";
    {
        std::map<int, int> histogram;
        for (const auto& [key, moves] : table) {
            int total = 0;
            for (const auto& [move, stats] : moves) total += stats.games;
            ++histogram[std::min(total, 10)];
        }
        for (const auto& [count, positions] : histogram) std::cerr << "  positions with " << count << (count == 10 ? "+" : "") << " games: " << positions << '\n';
    }

    struct Candidate {
        std::uint64_t key;
        std::uint16_t move;
        int games;
        double score;
        std::string fen;
    };
    std::vector<Candidate> candidates;
    for (const auto& [key, moves] : table) {
        int position_games = 0;
        for (const auto& [move, stats] : moves) position_games += stats.games;
        for (const auto& [move, stats] : moves) {
            if (stats.games < min_games) continue;
            const double score = stats.points / stats.games;
            if (score < min_score) continue;
            candidates.push_back(Candidate{key, move, stats.games, score, fens[key]});
        }
        (void)position_games;
    }
    std::cerr << candidates.size() << " candidate moves\n";

    std::vector<forge::book::Entry> entries;
    if (verify_nodes > 0) {
        forge::Searcher searcher(64);
        std::unordered_map<std::uint64_t, int> best_scores;
        std::size_t kept = 0;
        std::size_t checked = 0;
        for (const Candidate& candidate : candidates) {
            forge::Board board;
            if (!board.set_fen(candidate.fen)) continue;
            auto best_it = best_scores.find(candidate.key);
            if (best_it == best_scores.end()) {
                forge::SearchLimits limits;
                limits.nodes = verify_nodes;
                limits.nodes_specified = true;
                searcher.clear_hash();
                best_it = best_scores.emplace(candidate.key, searcher.search(board, limits).score).first;
            }
            const forge::Move move = forge::book::decode_move(board, candidate.move);
            if (move.is_none()) continue;
            forge::SearchLimits limits;
            limits.nodes = verify_nodes;
            limits.nodes_specified = true;
            limits.search_moves_specified = true;
            limits.search_moves.push_back(move);
            searcher.clear_hash();
            const int score = searcher.search(board, limits).score;
            ++checked;
            if (score < best_it->second - margin) continue;
            const double weight = std::min(65535.0, 10.0 * candidate.games * candidate.score * (1.0 + 0.002 * std::max(0, score)));
            entries.push_back(forge::book::Entry{candidate.key, candidate.move, static_cast<std::uint16_t>(std::max(1.0, weight)), 0});
            ++kept;
            if (checked % 200 == 0) std::cerr << "verified " << checked << " / " << candidates.size() << ", kept " << kept << '\n';
        }
        std::cerr << "kept " << kept << " of " << checked << " verified moves\n";
    } else {
        for (const Candidate& candidate : candidates) {
            const double weight = std::min(65535.0, 10.0 * candidate.games * candidate.score);
            entries.push_back(forge::book::Entry{candidate.key, candidate.move, static_cast<std::uint16_t>(std::max(1.0, weight)), 0});
        }
    }
    write_entries(out_path, entries);
    return 0;
}

void write_entries(const std::string& out_path, std::vector<forge::book::Entry> entries) {
    std::sort(entries.begin(), entries.end(), [](const forge::book::Entry& a, const forge::book::Entry& b) {
        return a.key != b.key ? a.key < b.key : a.weight > b.weight;
    });
    std::ofstream out(out_path);
    out << "// Generated by forge_bookgen: " << entries.size() << " Polyglot-compatible entries.\n";
    out << "static constexpr std::size_t BookEntryCount = " << entries.size() << ";\n";
    out << "static const std::uint64_t BookKeys[" << std::max<std::size_t>(1, entries.size()) << "] = {";
    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (i % 4 == 0) out << "\n   ";
        out << " 0x" << std::hex << entries[i].key << std::dec << "ULL,";
    }
    out << "\n};\nstatic const std::uint16_t BookMoves[" << std::max<std::size_t>(1, entries.size()) << "] = {";
    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (i % 16 == 0) out << "\n   ";
        out << ' ' << entries[i].move << ',';
    }
    out << "\n};\nstatic const std::uint16_t BookWeights[" << std::max<std::size_t>(1, entries.size()) << "] = {";
    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (i % 16 == 0) out << "\n   ";
        out << ' ' << entries[i].weight << ',';
    }
    out << "\n};\n";
    std::cerr << "wrote " << entries.size() << " entries to " << out_path << '\n';
}

int run_expand(int argc, char** argv) {
    std::vector<int> widths{3, 3, 3, 3, 2, 2};
    int max_ply = 16;
    std::uint64_t nodes = 1500000;
    std::uint64_t alt_nodes = 300000;
    int margin = 20;
    int threads = static_cast<int>(std::max(1U, std::thread::hardware_concurrency()));
    std::string out_path = "book_data.inc";
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        auto next = [&]() -> std::string { return i + 1 < argc ? argv[++i] : ""; };
        if (arg == "--widths") {
            widths.clear();
            std::istringstream list(next());
            std::string item;
            while (std::getline(list, item, ',')) widths.push_back(std::stoi(item));
        } else if (arg == "--max-ply") max_ply = std::stoi(next());
        else if (arg == "--nodes") nodes = std::stoull(next());
        else if (arg == "--alt-nodes") alt_nodes = std::stoull(next());
        else if (arg == "--margin") margin = std::stoi(next());
        else if (arg == "--threads") threads = std::stoi(next());
        else if (arg == "--out") out_path = next();
    }

    std::vector<forge::book::Entry> entries;
    std::mutex entries_mutex;
    std::vector<std::string> frontier{std::string(forge::Board::StandardStartFen)};
    std::set<std::string> seen;
    for (int ply = 0; ply < max_ply && !frontier.empty(); ++ply) {
        const int width = ply < static_cast<int>(widths.size()) ? std::max(1, widths[static_cast<std::size_t>(ply)]) : 1;
        std::vector<std::string> next_frontier;
        std::mutex next_mutex;
        std::atomic<std::size_t> cursor{0};
        std::vector<std::thread> workers;
        for (int t = 0; t < threads; ++t) {
            workers.emplace_back([&]() {
                forge::Searcher searcher(64);
                while (true) {
                    const std::size_t index = cursor.fetch_add(1);
                    if (index >= frontier.size()) break;
                    forge::Board board;
                    if (!board.set_fen(frontier[index])) continue;
                    std::vector<std::pair<int, forge::Move>> ranked;
                    if (width > 1) {
                        for (const forge::Move move : board.legal_moves()) {
                            forge::SearchLimits limits;
                            limits.nodes = alt_nodes;
                            limits.nodes_specified = true;
                            limits.search_moves_specified = true;
                            limits.search_moves.push_back(move);
                            searcher.clear_hash();
                            ranked.emplace_back(searcher.search(board, limits).score, move);
                        }
                    } else {
                        forge::SearchLimits limits;
                        limits.nodes = nodes;
                        limits.nodes_specified = true;
                        searcher.clear_hash();
                        const forge::SearchInfo info = searcher.search(board, limits);
                        if (info.best_move.is_none()) continue;
                        ranked.emplace_back(info.score, info.best_move);
                    }
                    if (ranked.empty()) continue;
                    std::stable_sort(ranked.begin(), ranked.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
                    const int best = ranked.front().first;
                    // Do not continue clearly lost or won lines.
                    if (std::abs(best) > 150) continue;
                    int kept = 0;
                    for (const auto& [score, move] : ranked) {
                        if (kept >= width || score < best - margin) break;
                        const std::uint16_t weight = static_cast<std::uint16_t>(std::max(1, 100 - 15 * kept - (best - score)));
                        {
                            const std::lock_guard<std::mutex> lock(entries_mutex);
                            entries.push_back(forge::book::Entry{forge::book::polyglot_key(board), forge::book::encode_move(board, move), weight, 0});
                        }
                        forge::Board child = board;
                        forge::Undo undo;
                        (void)child.make_move(move, undo);
                        {
                            const std::lock_guard<std::mutex> lock(next_mutex);
                            next_frontier.push_back(child.fen());
                        }
                        ++kept;
                    }
                }
            });
        }
        for (auto& worker : workers) worker.join();
        // Transpositions: expand each position once.
        std::vector<std::string> unique;
        for (const std::string& fen : next_frontier) {
            if (seen.insert(fen).second) unique.push_back(fen);
        }
        frontier = std::move(unique);
        std::cerr << "ply " << ply + 1 << ": " << frontier.size() << " positions, " << entries.size() << " entries\n";
        write_entries(out_path, entries);
    }
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_bookgen openings|build [options]\n";
        return 2;
    }
    const std::string mode = argv[1];
    if (mode == "openings") return run_openings(argc, argv);
    if (mode == "build") return run_build(argc, argv);
    if (mode == "expand") return run_expand(argc, argv);
    std::cerr << "unknown mode " << mode << '\n';
    return 2;
}
