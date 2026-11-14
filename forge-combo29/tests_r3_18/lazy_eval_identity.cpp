// Identity checks for the lazy network accumulator.
//
// replay: fixed-seed playouts. Every legal move's change list matches
// dirty_pieces. The accumulator built at evaluation matches applying
// nnue::update from the parent with that change list. A null move is
// checked against a copy, which is what a null move used to do.
//
// depth8 <base-engine> <new-engine> [count]:
//   Threads 1, Hash 16, OwnBook false, other options left at defaults.
//   Each position is ucinewgame, then go depth 8. Best move, score and
//   nodes are compared.
//
// evalcmp <base-engine> <new-engine> [count]:
//   Same options. `eval` text from both binaries is compared.

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#include <cstdio>
#include <cstdlib>
#include <sys/wait.h>
#include <unistd.h>

namespace forge {

struct SearcherTestProbe {
    static int static_evaluate(Worker& worker, const Board& board, SearchStack* ss) {
        return worker.static_evaluate(board, ss);
    }
    static void record_move(Worker& worker, SearchStack* ss, const Board& board, const Move& move) {
        worker.record_move(ss, board, move);
    }
    static void record_null_move(Worker& worker, SearchStack* ss) { worker.record_null_move(ss); }
};

} // namespace forge

namespace {

constexpr std::uint64_t kSeed = 0x18D15C0DEULL;

class SplitMix {
public:
    explicit SplitMix(std::uint64_t seed) : state_(seed) {}
    std::uint64_t next() {
        state_ += 0x9E3779B97F4A7C15ULL;
        std::uint64_t z = state_;
        z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31U);
    }

private:
    std::uint64_t state_;
};

bool same_dirty(const forge::nnue::DirtyPieces& left, const forge::nnue::DirtyPieces& right) {
    if (left.count != right.count) return false;
    for (int i = 0; i < left.count; ++i) {
        const forge::nnue::PieceChange& a = left.changes[static_cast<std::size_t>(i)];
        const forge::nnue::PieceChange& b = right.changes[static_cast<std::size_t>(i)];
        if (a.piece != b.piece || a.square != b.square || a.add != b.add) return false;
    }
    return true;
}

bool same_features(const forge::nnue::Accumulator& left, const forge::nnue::Accumulator& right) {
    return std::memcmp(left.values.data(), right.values.data(), sizeof(left.values)) == 0;
}

int fail(const std::string& message) {
    std::cerr << "FAIL " << message << '\n';
    return 1;
}

void reset_frames(std::array<forge::SearchStack, forge::MaxPly + 8>& frames) {
    for (forge::SearchStack& frame : frames) {
        frame.accumulator.valid = false;
        frame.runtime_psqt.valid = false;
        frame.diff_known = false;
        frame.entered_null = false;
        frame.dirty.count = 0;
    }
}

bool dirty_matches_board(const forge::Board& board, const forge::Move& move) {
    const forge::nnue::DirtyPieces from_board = forge::nnue::dirty_pieces(board, move);
    const forge::nnue::DirtyPieces from_parts = forge::nnue::dirty_from_move(
        move, board.piece_at(move.from), board.captured_piece(move), board.side_to_move());
    return same_dirty(from_board, from_parts);
}

int check_catalog() {
    const std::array<std::string_view, 6> fens = {
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3",
        "8/P7/8/8/8/8/7k/K7 w - - 0 1",
        "1b6/P7/8/8/8/8/7k/K7 w - - 0 1",
        "k7/7K/8/8/8/8/p7/8 b - - 0 1",
    };
    int moves_checked = 0;
    int ep_moves = 0;
    int castle_moves = 0;
    int promo_moves = 0;
    for (const std::string_view fen : fens) {
        forge::Board board;
        if (!board.set_fen(fen)) return fail(std::string("catalog fen rejected: ") + std::string(fen));
        const forge::MoveList moves = board.legal_moves();
        if (moves.empty()) return fail(std::string("catalog fen has no moves: ") + std::string(fen));
        forge::nnue::Accumulator before;
        forge::nnue::refresh(board, before);
        for (std::size_t i = 0; i < moves.size(); ++i) {
            const forge::Move move = moves[i];
            if (!dirty_matches_board(board, move)) {
                return fail("dirty_from_move differs at " + std::string(fen) + " move " +
                            forge::Board::move_to_uci(move));
            }
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
            forge::Undo undo;
            if (!board.make_move(move, undo)) return fail("catalog make_move failed");
            forge::nnue::Accumulator after;
            forge::nnue::update(before, after, dirty);
            forge::nnue::Accumulator fresh;
            forge::nnue::refresh(board, fresh);
            const int updated = forge::nnue::evaluate(board, after);
            const int rebuilt = forge::nnue::evaluate(board, fresh);
            board.unmake_move(move, undo);
            if (updated != rebuilt) {
                return fail("update eval != refresh at " + std::string(fen) + " move " +
                            forge::Board::move_to_uci(move) + " " + std::to_string(updated) +
                            " vs " + std::to_string(rebuilt));
            }
            ++moves_checked;
            if ((move.flags & forge::EnPassant) != 0U) ++ep_moves;
            if (move.is_castle()) ++castle_moves;
            if (move.is_promotion()) ++promo_moves;
        }
    }
    if (ep_moves == 0 || castle_moves == 0 || promo_moves == 0) {
        return fail("catalog missed a special move class ep " + std::to_string(ep_moves) + " castle " +
                    std::to_string(castle_moves) + " promo " + std::to_string(promo_moves));
    }
    std::cout << "catalog moves " << moves_checked << " ep " << ep_moves << " castle " << castle_moves
              << " promo " << promo_moves << '\n';
    return 0;
}

int replay(std::uint64_t target) {
    if (const int catalog = check_catalog(); catalog != 0) return catalog;
    forge::SharedSearchState shared(16);
    forge::Worker worker(shared, 0);
    std::array<forge::SearchStack, forge::MaxPly + 8> frames{};
    for (int i = 0; i < forge::MaxPly + 8; ++i) frames[static_cast<std::size_t>(i)].ply = i - 4;

    SplitMix rng(kSeed);
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return fail("startpos rejected");
    reset_frames(frames);
    forge::SearchStack* ss = &frames[4];
    const int root_eval = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
    const forge::EvalComponents root_parts = forge::Evaluator::static_eval_components(board);
    if (root_eval != root_parts.total || !ss->accumulator.valid) return fail("root eval mismatch");
    std::vector<forge::nnue::Accumulator> shadow;
    shadow.push_back(ss->accumulator);

    std::uint64_t played = 0;
    std::uint64_t dirty_checks = 0;
    std::uint64_t null_checks = 0;
    std::uint64_t refresh_net_mismatch = 0;
    std::uint64_t refresh_total_mismatch = 0;
    int ply = 0;
    while (played < target) {
        if (ply > 0 && (played % 11U) == 7U && !board.in_check()) {
            forge::SearcherTestProbe::record_null_move(worker, ss);
            forge::NullUndo undo;
            board.make_null_move(undo);
            forge::SearchStack* child = ss + 1;
            const int lazy_total = forge::SearcherTestProbe::static_evaluate(worker, board, child);
            forge::nnue::DirtyPieces empty;
            forge::nnue::Accumulator copied;
            forge::nnue::update(shadow.back(), copied, empty);
            if (!same_features(copied, shadow.back())) return fail("null copy changed features at ply " + std::to_string(ply));
            if (forge::nnue::evaluate(board, shadow.back()) != forge::nnue::evaluate(board, copied)) {
                return fail("null evaluate diverged at ply " + std::to_string(ply));
            }
            const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
            if (lazy_total != parts.total) ++refresh_total_mismatch;
            if (forge::nnue::evaluate(board, shadow.back()) != parts.nnue) ++refresh_net_mismatch;
            // The search reads the parent's features for a null move.
            if (child->accumulator.valid) return fail("null frame stored a new accumulator");
            board.unmake_null_move(undo);
            ++null_checks;
        }

        const forge::MoveList moves = board.legal_moves();
        if (moves.empty() || board.halfmove_clock() >= 80 || ply >= 32) {
            if (ply > 0 && !ss->accumulator.valid) {
                const int lazy_total = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
                if (!same_features(ss->accumulator, shadow.back())) return fail("end-of-game accumulator diverged");
                const int lazy_net = forge::nnue::evaluate(board, ss->accumulator);
                const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
                if (lazy_net != parts.nnue) ++refresh_net_mismatch;
                if (lazy_total != parts.total) ++refresh_total_mismatch;
            }
            if (!board.set_fen(forge::Board::StandardStartFen)) return fail("restart rejected");
            reset_frames(frames);
            ss = &frames[4];
            ply = 0;
            const int again = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
            const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
            if (again != parts.total || !ss->accumulator.valid) return fail("restart eval mismatch");
            shadow.clear();
            shadow.push_back(ss->accumulator);
            continue;
        }
        for (std::size_t i = 0; i < moves.size(); ++i) {
            if (!dirty_matches_board(board, moves[i])) {
                return fail("dirty mismatch at " + board.fen() + " " + forge::Board::move_to_uci(moves[i]));
            }
            ++dirty_checks;
        }
        const forge::Move move = moves[static_cast<std::size_t>(rng.next() % moves.size())];
        const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
        forge::SearcherTestProbe::record_move(worker, ss, board, move);
        forge::Undo undo;
        if (!board.make_move(move, undo)) return fail("make_move failed");
        forge::nnue::Accumulator next;
        forge::nnue::update(shadow.back(), next, dirty);
        shadow.push_back(next);
        ss += 1;
        ++ply;
        // Two plies out of seven are left unevaluated, the way a check or a
        // table hit skips static evaluation. The next evaluation has to
        // rebuild that gap from the last finished accumulator.
        const bool defer = (ply % 7) == 3 || (ply % 7) == 4;
        if (!defer) {
            const int lazy_total = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
            if (!same_features(ss->accumulator, shadow.back())) {
                return fail("accumulator bits diverged at " + board.fen() + " after " + std::to_string(played));
            }
            for (std::size_t built = 0; built < shadow.size(); ++built) {
                forge::SearchStack* frame = &frames[4U + built];
                if (!frame->accumulator.valid || !same_features(frame->accumulator, shadow[built])) {
                    return fail("chain accumulator diverged at " + board.fen());
                }
            }
            const int lazy_net = forge::nnue::evaluate(board, ss->accumulator);
            if (lazy_net != forge::nnue::evaluate(board, shadow.back())) return fail("network eval diverged at " + board.fen());
            const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
            if (lazy_net != parts.nnue) ++refresh_net_mismatch;
            if (lazy_total != parts.total) ++refresh_total_mismatch;
        }
        ++played;
        if ((played % 100000U) == 0U) {
            std::cout << "replay " << played << " dirty_checks " << dirty_checks << " null_checks " << null_checks
                      << " refresh_net_mismatch " << refresh_net_mismatch << " refresh_total_mismatch "
                      << refresh_total_mismatch << '\n';
        }
    }
    std::cout << "replay positions " << played << " dirty_checks " << dirty_checks << " null_checks " << null_checks
              << " refresh_net_mismatch " << refresh_net_mismatch << " refresh_total_mismatch "
              << refresh_total_mismatch << '\n';
    return 0;
}

struct Engine {
    pid_t pid = -1;
    FILE* to = nullptr;
    FILE* from = nullptr;

    ~Engine() { close(); }

    void close() {
        if (to != nullptr) {
            std::fputs("quit\n", to);
            std::fflush(to);
        }
        if (pid > 0) {
            int status = 0;
            waitpid(pid, &status, 0);
            pid = -1;
        }
        if (to != nullptr) {
            std::fclose(to);
            to = nullptr;
        }
        if (from != nullptr) {
            std::fclose(from);
            from = nullptr;
        }
    }
};

bool start_engine(Engine& engine, const char* path) {
    int to_child[2];
    int from_child[2];
    if (pipe(to_child) != 0 || pipe(from_child) != 0) return false;
    const pid_t pid = fork();
    if (pid < 0) return false;
    if (pid == 0) {
        dup2(to_child[0], STDIN_FILENO);
        dup2(from_child[1], STDOUT_FILENO);
        close(to_child[0]);
        close(to_child[1]);
        close(from_child[0]);
        close(from_child[1]);
        execl(path, path, static_cast<char*>(nullptr));
        std::_Exit(127);
    }
    close(to_child[0]);
    close(from_child[1]);
    engine.pid = pid;
    engine.to = fdopen(to_child[1], "w");
    engine.from = fdopen(from_child[0], "r");
    if (engine.to == nullptr || engine.from == nullptr) return false;
    std::fputs("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\n",
               engine.to);
    std::fflush(engine.to);
    char* line = nullptr;
    std::size_t cap = 0;
    bool ready = false;
    while (getline(&line, &cap, engine.from) != -1) {
        if (std::string_view(line).find("readyok") != std::string_view::npos) {
            ready = true;
            break;
        }
    }
    std::free(line);
    return ready;
}

struct GoResult {
    std::string best;
    std::string score;
    std::uint64_t nodes = 0;
    bool ok = false;
};

GoResult search_depth8(Engine& engine, const std::string& fen) {
    GoResult result;
    std::fputs("ucinewgame\nposition fen ", engine.to);
    std::fputs(fen.c_str(), engine.to);
    std::fputs("\ngo depth 8\n", engine.to);
    std::fflush(engine.to);
    char* line = nullptr;
    std::size_t cap = 0;
    std::string last_info;
    while (getline(&line, &cap, engine.from) != -1) {
        const std::string_view text(line);
        if (text.rfind("info ", 0) == 0 && text.find(" score ") != std::string_view::npos &&
            text.find(" nodes ") != std::string_view::npos) {
            last_info.assign(text);
        }
        if (text.rfind("bestmove ", 0) == 0) {
            std::istringstream in{std::string(text)};
            std::string cmd;
            in >> cmd >> result.best;
            break;
        }
    }
    std::free(line);
    if (result.best.empty() || last_info.empty()) return result;
    const auto score_at = last_info.find(" score ");
    const auto nodes_at = last_info.find(" nodes ");
    if (score_at == std::string::npos || nodes_at == std::string::npos) return result;
    std::istringstream score_in(last_info.substr(score_at + 7));
    std::string kind;
    std::string value;
    score_in >> kind >> value;
    result.score = kind + " " + value;
    std::istringstream nodes_in(last_info.substr(nodes_at + 7));
    nodes_in >> result.nodes;
    result.ok = !result.score.empty() && nodes_in && !result.best.empty();
    return result;
}

std::vector<std::string> sample_fens(std::uint64_t count) {
    std::vector<std::string> fens;
    fens.reserve(static_cast<std::size_t>(count));
    SplitMix rng(kSeed);
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return {};
    int ply = 0;
    while (fens.size() < count) {
        fens.push_back(board.fen());
        const forge::MoveList moves = board.legal_moves();
        if (moves.empty() || board.halfmove_clock() >= 80 || ply >= 24) {
            if (!board.set_fen(forge::Board::StandardStartFen)) return {};
            ply = 0;
            continue;
        }
        const forge::Move move = moves[static_cast<std::size_t>(rng.next() % moves.size())];
        forge::Undo undo;
        if (!board.make_move(move, undo)) return {};
        ++ply;
    }
    return fens;
}

std::string eval_line(Engine& engine, const std::string& fen) {
    std::fputs("position fen ", engine.to);
    std::fputs(fen.c_str(), engine.to);
    std::fputs("\neval\n", engine.to);
    std::fflush(engine.to);
    char* line = nullptr;
    std::size_t cap = 0;
    std::string found;
    while (getline(&line, &cap, engine.from) != -1) {
        const std::string_view text(line);
        if (text.find("info string eval ") != std::string_view::npos) {
            found.assign(text);
            while (!found.empty() && (found.back() == '\n' || found.back() == '\r')) found.pop_back();
            break;
        }
    }
    std::free(line);
    return found;
}

int evalcmp(const char* base_path, const char* new_path, std::uint64_t count) {
    const std::vector<std::string> fens = sample_fens(count);
    if (fens.size() != count) return fail("could not build eval sample");
    Engine base;
    Engine fresh;
    if (!start_engine(base, base_path)) return fail(std::string("could not start base ") + base_path);
    if (!start_engine(fresh, new_path)) return fail(std::string("could not start new ") + new_path);
    for (std::uint64_t i = 0; i < fens.size(); ++i) {
        const std::string left = eval_line(base, fens[i]);
        const std::string right = eval_line(fresh, fens[i]);
        if (left.empty() || left != right) {
            std::cerr << "FAIL eval fen " << fens[i] << "\n base " << left << "\n new " << right << "\n";
            return 1;
        }
    }
    std::cout << "uci_eval positions " << fens.size() << " identical\n";
    return 0;
}

int depth8(const char* base_path, const char* new_path, std::uint64_t count) {
    const std::vector<std::string> fens = sample_fens(count);
    Engine base;
    Engine fresh;
    if (!start_engine(base, base_path)) return fail(std::string("could not start base ") + base_path);
    if (!start_engine(fresh, new_path)) return fail(std::string("could not start new ") + new_path);
    for (std::uint64_t i = 0; i < fens.size(); ++i) {
        const GoResult left = search_depth8(base, fens[i]);
        const GoResult right = search_depth8(fresh, fens[i]);
        if (!left.ok || !right.ok) {
            return fail("missing search result at " + fens[i]);
        }
        if (left.best != right.best || left.score != right.score || left.nodes != right.nodes) {
            std::cerr << "FAIL depth8 fen " << fens[i] << "\n base " << left.best << " " << left.score << " nodes "
                      << left.nodes << "\n new " << right.best << " " << right.score << " nodes " << right.nodes
                      << "\n";
            return 1;
        }
        if ((i + 1) % 250U == 0U) std::cout << "depth8 " << (i + 1) << " / " << fens.size() << '\n';
    }
    std::cout << "depth8 positions " << fens.size() << " identical\n";
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc >= 2 && std::string_view(argv[1]) == "evalcmp") {
        if (argc < 4) {
            std::cerr << "usage: lazy_eval_identity evalcmp <base> <new> [count]\n";
            return 2;
        }
        std::uint64_t count = 2000;
        if (argc >= 5) count = std::strtoull(argv[4], nullptr, 10);
        return evalcmp(argv[2], argv[3], count);
    }
    if (argc >= 2 && std::string_view(argv[1]) == "depth8") {
        if (argc < 4) {
            std::cerr << "usage: lazy_eval_identity depth8 <base> <new> [count]\n";
            return 2;
        }
        std::uint64_t count = 10000;
        if (argc >= 5) count = std::strtoull(argv[4], nullptr, 10);
        return depth8(argv[2], argv[3], count);
    }
    std::uint64_t count = 1000000;
    if (argc >= 3 && std::string_view(argv[1]) == "replay") count = std::strtoull(argv[2], nullptr, 10);
    else if (argc >= 2 && std::string_view(argv[1]) != "replay") {
        std::cerr << "usage: lazy_eval_identity replay [count] | depth8 <base> <new> [count]\n";
        return 2;
    }
    return replay(count);
}
