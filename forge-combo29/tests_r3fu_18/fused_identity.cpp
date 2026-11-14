// Identity test for the lazy accumulator, including the AVX-512 fused
// update-and-output pass when that kernel is compiled in.
//
// Prints refresh_net_mismatch and refresh_total_mismatch.
// Exits non-zero if either count is non-zero, or if a required position
// class was never evaluated through Worker::static_evaluate.
//
// replay [count]
// depth8 <base> <new> [count]
// evalcmp <base> <new> [count]

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

struct Cover {
    std::uint64_t refresh_net_mismatch = 0;
    std::uint64_t refresh_total_mismatch = 0;
    std::uint64_t fused2 = 0;
    std::uint64_t fused3 = 0;
    std::uint64_t promo = 0;
    std::uint64_t castle = 0;
    std::uint64_t ep = 0;
    std::uint64_t nulls = 0;
    std::uint64_t static_evals = 0;
};

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

void note_shape(Cover& cover, const forge::Move& move, const forge::nnue::DirtyPieces& dirty) {
    if (move.is_promotion()) ++cover.promo;
    if (move.is_castle()) ++cover.castle;
    if ((move.flags & forge::EnPassant) != 0U) ++cover.ep;
    const bool quiet_pair = dirty.count == 2 && !dirty.changes[0].add && dirty.changes[1].add;
    const bool capture_triple = dirty.count == 3 && !dirty.changes[0].add && !dirty.changes[1].add && dirty.changes[2].add;
    if (quiet_pair) ++cover.fused2;
    if (capture_triple) ++cover.fused3;
}

int compare_scored(const forge::Board& board, int total, const forge::nnue::Accumulator& used, bool stored, Cover& cover) {
    ++cover.static_evals;
    const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
    if (total != parts.total) ++cover.refresh_total_mismatch;
    if (!stored) return 0;
    if (forge::nnue::evaluate(board, used) != parts.nnue) ++cover.refresh_net_mismatch;
    return 0;
}

int play_specials(forge::Worker& worker, std::array<forge::SearchStack, forge::MaxPly + 8>& frames, Cover& cover) {
    const std::array<std::string_view, 6> fens = {
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3",
        "8/P7/8/8/8/8/7k/K7 w - - 0 1",
        "1b6/P7/8/8/8/8/7k/K7 w - - 0 1",
        "k7/7K/8/8/8/8/p7/8 b - - 0 1",
    };
    for (const std::string_view fen : fens) {
        forge::Board board;
        if (!board.set_fen(fen)) return fail(std::string("fen rejected: ") + std::string(fen));
        reset_frames(frames);
        forge::SearchStack* root = &frames[4];
        const int root_total = forge::SearcherTestProbe::static_evaluate(worker, board, root);
        compare_scored(board, root_total, root->accumulator, root->accumulator.valid, cover);
        if (!root->accumulator.valid) return fail("root accumulator was not stored");
        const forge::nnue::Accumulator root_features = root->accumulator;
        const forge::MoveList moves = board.legal_moves();
        if (moves.empty()) return fail(std::string("no moves: ") + std::string(fen));
        for (std::size_t i = 0; i < moves.size(); ++i) {
            const forge::Move move = moves[i];
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
            note_shape(cover, move, dirty);
            forge::SearcherTestProbe::record_move(worker, root, board, move);
            forge::Undo undo;
            if (!board.make_move(move, undo)) return fail("make_move failed");
            forge::SearchStack* child = root + 1;
            const int total = forge::SearcherTestProbe::static_evaluate(worker, board, child);
            forge::nnue::Accumulator shadow;
            forge::nnue::update(root_features, shadow, dirty);
            if (!child->accumulator.valid || !same_features(child->accumulator, shadow)) {
                return fail("fused accumulator diverged at " + std::string(fen) + " " + forge::Board::move_to_uci(move));
            }
            compare_scored(board, total, child->accumulator, true, cover);
            board.unmake_move(move, undo);
        }
        if (!board.in_check()) {
            forge::SearcherTestProbe::record_null_move(worker, root);
            forge::NullUndo undo;
            board.make_null_move(undo);
            forge::SearchStack* child = root + 1;
            const int total = forge::SearcherTestProbe::static_evaluate(worker, board, child);
            if (child->accumulator.valid) return fail("null move stored a new accumulator");
            compare_scored(board, total, root->accumulator, true, cover);
            board.unmake_null_move(undo);
            ++cover.nulls;
        }
    }
    return 0;
}

int replay(std::uint64_t target) {
    forge::SharedSearchState shared(16);
    forge::Worker worker(shared, 0);
    std::array<forge::SearchStack, forge::MaxPly + 8> frames{};
    for (int i = 0; i < forge::MaxPly + 8; ++i) frames[static_cast<std::size_t>(i)].ply = i - 4;
    Cover cover;
    if (const int specials = play_specials(worker, frames, cover); specials != 0) return specials;

    SplitMix rng(kSeed);
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return fail("startpos rejected");
    reset_frames(frames);
    forge::SearchStack* ss = &frames[4];
    const int root_total = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
    compare_scored(board, root_total, ss->accumulator, true, cover);
    std::vector<forge::nnue::Accumulator> shadow;
    shadow.push_back(ss->accumulator);

    std::uint64_t played = 0;
    int ply = 0;
    while (played < target) {
        if (ply > 0 && (played % 11U) == 7U && !board.in_check()) {
            forge::SearcherTestProbe::record_null_move(worker, ss);
            forge::NullUndo undo;
            board.make_null_move(undo);
            forge::SearchStack* child = ss + 1;
            const int total = forge::SearcherTestProbe::static_evaluate(worker, board, child);
            if (child->accumulator.valid) return fail("null frame stored features");
            compare_scored(board, total, shadow.back(), true, cover);
            board.unmake_null_move(undo);
            ++cover.nulls;
        }
        const forge::MoveList moves = board.legal_moves();
        if (moves.empty() || board.halfmove_clock() >= 80 || ply >= 32) {
            if (ply > 0 && !ss->accumulator.valid) {
                const int total = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
                compare_scored(board, total, ss->accumulator, ss->accumulator.valid, cover);
                if (ss->accumulator.valid && !same_features(ss->accumulator, shadow.back())) {
                    return fail("end-of-game accumulator diverged");
                }
            }
            if (!board.set_fen(forge::Board::StandardStartFen)) return fail("restart rejected");
            reset_frames(frames);
            ss = &frames[4];
            ply = 0;
            const int again = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
            compare_scored(board, again, ss->accumulator, true, cover);
            shadow.clear();
            shadow.push_back(ss->accumulator);
            continue;
        }
        const forge::Move move = moves[static_cast<std::size_t>(rng.next() % moves.size())];
        const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
        const bool will_score = (ply + 1) % 7 != 3 && (ply + 1) % 7 != 4;
        if (will_score) note_shape(cover, move, dirty);
        forge::SearcherTestProbe::record_move(worker, ss, board, move);
        forge::Undo undo;
        if (!board.make_move(move, undo)) return fail("make_move failed");
        forge::nnue::Accumulator next;
        forge::nnue::update(shadow.back(), next, dirty);
        shadow.push_back(next);
        ss += 1;
        ++ply;
        if (will_score) {
            const int total = forge::SearcherTestProbe::static_evaluate(worker, board, ss);
            if (!ss->accumulator.valid || !same_features(ss->accumulator, shadow.back())) {
                return fail("accumulator bits diverged after " + std::to_string(played) + " at " + board.fen());
            }
            compare_scored(board, total, ss->accumulator, true, cover);
        }
        ++played;
    }
    std::cout << "refresh_net_mismatch " << cover.refresh_net_mismatch << '\n';
    std::cout << "refresh_total_mismatch " << cover.refresh_total_mismatch << '\n';
    std::cout << "coverage static_evals " << cover.static_evals << " fused2 " << cover.fused2 << " fused3 " << cover.fused3
              << " promo " << cover.promo << " castle " << cover.castle << " ep " << cover.ep << " null " << cover.nulls
              << '\n';
    if (cover.fused2 == 0 || cover.fused3 == 0 || cover.promo == 0 || cover.castle == 0 || cover.ep == 0 || cover.nulls == 0 ||
        cover.static_evals == 0) {
        std::cerr << "FAIL missing coverage of fused static_evaluate, null, promotion, castling, or en passant\n";
        return 1;
    }
    if (cover.refresh_net_mismatch != 0 || cover.refresh_total_mismatch != 0) return 1;
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

int evalcmp(const char* base_path, const char* new_path, std::uint64_t count) {
    const std::vector<std::string> fens = sample_fens(count);
    if (fens.size() != count) return fail("could not build eval sample");
    Engine base;
    Engine fresh;
    if (!start_engine(base, base_path)) return fail(std::string("could not start base ") + base_path);
    if (!start_engine(fresh, new_path)) return fail(std::string("could not start new ") + new_path);
    for (std::uint64_t i = 0; i < fens.size(); ++i) {
        auto line_of = [](Engine& engine, const std::string& fen) {
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
        };
        const std::string left = line_of(base, fens[i]);
        const std::string right = line_of(fresh, fens[i]);
        if (left.empty() || left != right) {
            std::cerr << "FAIL eval fen " << fens[i] << "\n base " << left << "\n new " << right << "\n";
            return 1;
        }
    }
    std::cout << "uci_eval positions " << fens.size() << " identical\n";
    return 0;
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
    result.ok = !result.score.empty() && static_cast<bool>(nodes_in) && !result.best.empty();
    return result;
}

int depth8(const char* base_path, const char* new_path, std::uint64_t count) {
    const std::vector<std::string> fens = sample_fens(count);
    if (fens.size() != count) return fail("could not build depth8 sample");
    Engine base;
    Engine fresh;
    if (!start_engine(base, base_path)) return fail(std::string("could not start base ") + base_path);
    if (!start_engine(fresh, new_path)) return fail(std::string("could not start new ") + new_path);
    for (std::uint64_t i = 0; i < fens.size(); ++i) {
        const GoResult left = search_depth8(base, fens[i]);
        const GoResult right = search_depth8(fresh, fens[i]);
        if (!left.ok || !right.ok || left.best != right.best || left.score != right.score || left.nodes != right.nodes) {
            std::cerr << "FAIL depth8 fen " << fens[i] << "\n";
            return 1;
        }
        if ((i + 1) % 500U == 0U) std::cout << "depth8 " << (i + 1) << " / " << fens.size() << '\n';
    }
    std::cout << "depth8 positions " << fens.size() << " identical\n";
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    const std::string_view mode = argc >= 2 ? argv[1] : "replay";
    if (mode == "replay") {
        std::uint64_t count = 1000000;
        if (argc >= 3) count = std::strtoull(argv[2], nullptr, 10);
        return replay(count);
    }
    if (mode == "depth8") {
        if (argc < 4) return fail("usage: fused_identity depth8 <base> <new> [count]");
        const std::uint64_t count = argc >= 5 ? std::strtoull(argv[4], nullptr, 10) : 10000;
        return depth8(argv[2], argv[3], count);
    }
    if (mode == "evalcmp") {
        if (argc < 4) return fail("usage: fused_identity evalcmp <base> <new> [count]");
        const std::uint64_t count = argc >= 5 ? std::strtoull(argv[4], nullptr, 10) : 1000000;
        return evalcmp(argv[2], argv[3], count);
    }
    return fail("usage: fused_identity replay [count] | depth8 <base> <new> [count] | evalcmp <base> <new> [count]");
}
