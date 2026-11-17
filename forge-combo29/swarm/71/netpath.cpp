// swarm/71 net-path correctness driver.
//
// Drives the v3 incremental path exactly as the search does (same WorkerState, same
// make_valid/replay_ply/apply_changes calls, same DirtyPieces the search builds from
// moves), and after every position compares the incrementally-maintained accumulator
// against a fresh refresh from pieces. It also exercises colour-mirror symmetry, bare
// kings, and the loader's reject-vs-accept behaviour on damaged files.
//
// Subcommands:
//   inc <net> <fens>     incremental-vs-refresh over real move sequences
//   mirror <net> <fens>  evaluate pos and its colour-mirror, count asymmetric pairs
//   bare <net>           lone-king positions, no crash + score sanity
//   loadprobe <net>      loader behaviour on the pristine file (baseline for damage tests)
//
// Exit status: 0 all checks pass, 3 checks failed, 2 usage, 1 cannot load.
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

namespace {

using namespace forge;
using namespace forge::nnue::v3;
using forge::nnue::DirtyPieces;

struct Frame {
    Board board;
    DirtyPieces dirty;
};

// Same shape as Worker::record_move: the search records the entered move/piece/capture/side
// before make_move and derives the change list with nnue::dirty_from_move.
void record(Frame& child, const Board& board, const Move& move) {
    child.dirty = nnue::dirty_from_move(move, board.piece_at(move.from), board.captured_piece(move), board.side_to_move());
}

std::vector<std::string> read_lines(const std::string& path) {
    std::vector<std::string> out;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ' || line.back() == '\t')) line.pop_back();
        if (!line.empty()) out.push_back(line);
    }
    return out;
}

bool same_accumulator(const Accumulator& a, const Accumulator& b, int hidden, long long* max_delta) {
    for (int p = 0; p < 2; ++p) {
        const auto pi = static_cast<std::size_t>(p);
        if (!(a.keys[pi] == b.keys[pi])) return false;
        if (a.king_sq[pi] != b.king_sq[pi]) return false;
        bool equal = true;
        for (int h = 0; h < hidden; ++h) {
            const auto hi = static_cast<std::size_t>(h);
            const int d = std::abs(static_cast<int>(a.values[pi][hi]) - static_cast<int>(b.values[pi][hi]));
            if (d != 0) {
                if (max_delta != nullptr) *max_delta = std::max<long long>(*max_delta, d);
                equal = false;
            }
        }
        if (!equal) return false;
    }
    return true;
}

struct IncResult {
    long long compared = 0;        // positions whose accumulator was compared
    long long acc_mismatched = 0;  // accumulator disagreed with a fresh refresh
    long long eval_compared = 0;   // positions whose incremental eval was compared
    long long eval_mismatched = 0; // incremental eval disagreed with the reference eval
    long long fens_refused = 0;    // root FENs the engine refused
    long long moves_refused = 0;   // moves in a sequence the engine would not play
    long long sequences = 0;
    long long max_abs_delta = 0;
    long long replays = 0;         // make_valid calls that had to replay (not a root refresh)
    long long king_key_changes = 0; // perspective-plies where the king key changed (rebuild-from-pieces)
    int stride = 1;                // evaluate every `stride` plies, so gaps exist
    std::string first_mismatch;
    bool verbose = false;
};

int cmd_inc(const Net& net, const std::string& fens_path, int stride, bool verbose, int inject) {
    const std::vector<std::string> lines = read_lines(fens_path);
    IncResult result;
    result.stride = stride;
    result.verbose = verbose;
    WorkerState state;
    prepare(net, state, 512);

    // One sequence per input line. Format: "<fen>" or "<fen> | <move> <move> ..."
    for (const std::string& line : lines) {
        const std::size_t bar = line.find('|');
        std::string fen = bar == std::string::npos ? line : line.substr(0, bar);
        while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\t')) fen.pop_back();
        std::vector<std::string> moves;
        if (bar != std::string::npos) {
            const std::string rest = line.substr(bar + 1);
            std::size_t i = 0;
            while (i < rest.size()) {
                while (i < rest.size() && std::isspace(static_cast<unsigned char>(rest[i])) != 0) ++i;
                const std::size_t start = i;
                while (i < rest.size() && std::isspace(static_cast<unsigned char>(rest[i])) == 0) ++i;
                if (i > start) moves.push_back(rest.substr(start, i - start));
            }
        }
        Frame root;
        if (!root.board.set_fen(fen)) {
            ++result.fens_refused;
            continue;
        }
        ++result.sequences;

        // Rebuild the whole sequence, keeping one frame per ply, exactly as the search does
        // when it descends and then evaluates at some ply.
        std::vector<Frame> frames;
        frames.push_back(root);
        for (const std::string& text : moves) {
            Frame& parent = frames.back();
            const auto move = parent.board.parse_uci(text);
            if (!move.has_value() || !parent.board.is_legal(*move)) {
                ++result.moves_refused;
                break;
            }
            Frame child;
            record(child, parent.board, *move);
            child.board = parent.board;
            Undo undo;
            if (!child.board.make_move(*move, undo)) {
                ++result.moves_refused;
                break;
            }
            frames.push_back(child);
        }

        const int top = static_cast<int>(frames.size()) - 1;
        // The search descends to a leaf and evaluates there, so it does NOT mark every
        // intermediate ply valid: it walks back from the deepest valid ancestor and replays.
        // Emitting a gap (a ply whose stack entry was never made valid) is what exercises
        // replay_ply's "king key changed -> rebuild the piece bitboards by undoing the later
        // plies" branch. `gaps` is a stride; 1 marks every ply (no gap), 3 marks one ply in
        // three, which is a gap pattern a real search produces constantly.
        const int stride = result.stride;
        std::vector<int> evaluated;
        for (int k = 0; k <= top; k += stride) evaluated.push_back(k);
        if (evaluated.back() != top) evaluated.push_back(top);

        for (const int k : evaluated) {
            const int index = k + 4;
            const Frame& frame = frames[static_cast<std::size_t>(k)];
            // The search's dirty_of takes a STACK index (ply + 4) and returns the change
            // list that led to that stack entry, which belongs to frame (index - 4).
            auto dirty_of = [&frames](int j) -> const DirtyPieces& {
                return frames[static_cast<std::size_t>(j - 4)].dirty;
            };
            if (k == 0) {
                state.invalidate();
                refresh_cached(net, state.cache, frame.board, state.stack[static_cast<std::size_t>(index)]);
            } else {
                // Count the king-key transitions, because those are the plies where
                // replay_ply abandons the incremental update and rebuilds from pieces.
                for (const Color p : {White, Black}) {
                    const auto pi = static_cast<std::size_t>(p);
                    if (king_key(net, p, frame.board.king_square(p)) !=
                        state.stack[static_cast<std::size_t>(index - 1)].keys[pi]) {
                        ++result.king_key_changes;
                    }
                }
                state.stack[static_cast<std::size_t>(index)].valid = false;
                make_valid(net, state, index, frame.board, dirty_of);
                ++result.replays;
            }
            Accumulator reference;
            refresh(net, frame.board, reference);
            if (inject == 1) {
                // Fault injection: corrupt the incremental result by one unit in one hidden
                // slot, so the comparison must report a mismatch. Proves the check can fail.
                state.stack[static_cast<std::size_t>(index)].values[0][0] =
                    static_cast<std::int16_t>(state.stack[static_cast<std::size_t>(index)].values[0][0] + 1);
            }
            ++result.compared;
            long long delta = 0;
            if (!same_accumulator(state.stack[static_cast<std::size_t>(index)], reference, net.hidden, &delta)) {
                ++result.acc_mismatched;
                result.max_abs_delta = std::max<long long>(result.max_abs_delta, delta);
                if (result.first_mismatch.empty() || result.verbose) {
                    const Accumulator& got = state.stack[static_cast<std::size_t>(index)];
                    std::printf("ACC_MISMATCH ply %d delta %lld keys got %d/%d %d/%d want %d/%d %d/%d ksq got %d %d want %d %d fen %s\n",
                                k, delta, got.keys[0].bucket, got.keys[0].flip, got.keys[1].bucket, got.keys[1].flip,
                                reference.keys[0].bucket, reference.keys[0].flip, reference.keys[1].bucket,
                                reference.keys[1].flip, static_cast<int>(got.king_sq[0]), static_cast<int>(got.king_sq[1]),
                                static_cast<int>(reference.king_sq[0]), static_cast<int>(reference.king_sq[1]),
                                frame.board.fen().c_str());
                }
                if (result.first_mismatch.empty()) {
                    result.first_mismatch = "accumulator at ply " + std::to_string(k) + " of sequence from " + fen;
                }
            }
            // The value the search would return must agree as well.
            ++result.eval_compared;
            const int incremental = evaluate(net, frame.board, state.stack[static_cast<std::size_t>(index)]);
            const int fresh = evaluate_reference(net, frame.board);
            if (incremental != fresh) {
                ++result.eval_mismatched;
                if (result.first_mismatch.empty()) {
                    result.first_mismatch = "eval " + std::to_string(incremental) + " vs " + std::to_string(fresh) +
                                            " at ply " + std::to_string(k) + " of sequence from " + fen;
                }
            }
        }
    }

    std::printf("INC sequences %lld compared %lld acc_mismatched %lld eval_compared %lld eval_mismatched %lld "
                "fens_refused %lld moves_refused %lld replays %lld king_key_changes %lld stride %d max_abs_delta %lld\n",
                result.sequences, result.compared, result.acc_mismatched, result.eval_compared, result.eval_mismatched,
                result.fens_refused, result.moves_refused, result.replays, result.king_key_changes, result.stride,
                result.max_abs_delta);
    if (!result.first_mismatch.empty()) std::printf("INC first_mismatch %s\n", result.first_mismatch.c_str());
    return (result.acc_mismatched == 0 && result.eval_mismatched == 0) ? 0 : 3;
}

// Colour mirror: flip ranks, swap colours, swap side to move, mirror castling rights and ep square.
std::string mirror_fen(const std::string& fen) {
    const std::size_t space = fen.find(' ');
    const std::string placement = fen.substr(0, space);
    const std::string rest = space == std::string::npos ? std::string() : fen.substr(space + 1);

    std::vector<std::string> ranks;
    std::size_t start = 0;
    while (true) {
        const std::size_t slash = placement.find('/', start);
        ranks.push_back(placement.substr(start, slash == std::string::npos ? std::string::npos : slash - start));
        if (slash == std::string::npos) break;
        start = slash + 1;
    }
    std::string out;
    for (int r = static_cast<int>(ranks.size()) - 1; r >= 0; --r) {
        std::string row;
        for (const char c : ranks[static_cast<std::size_t>(r)]) {
            if (c >= 'a' && c <= 'z') row.push_back(static_cast<char>(c - 'a' + 'A'));
            else if (c >= 'A' && c <= 'Z') row.push_back(static_cast<char>(c - 'A' + 'a'));
            else row.push_back(c);
        }
        if (!out.empty()) out.push_back('/');
        out += row;
    }
    if (rest.empty()) return out;

    std::vector<std::string> fields;
    std::size_t i = 0;
    while (i < rest.size()) {
        while (i < rest.size() && rest[i] == ' ') ++i;
        const std::size_t s = i;
        while (i < rest.size() && rest[i] != ' ') ++i;
        if (i > s) fields.push_back(rest.substr(s, i - s));
    }
    if (fields.size() < 4) return out;
    out += ' ';
    out += (fields[0] == "w") ? "b" : "w";
    out += ' ';
    std::string castling;
    for (const char c : fields[1]) {
        if (c == 'K') castling.push_back('k');
        else if (c == 'Q') castling.push_back('q');
        else if (c == 'k') castling.push_back('K');
        else if (c == 'q') castling.push_back('Q');
        else castling.push_back(c);
    }
    if (castling.empty()) castling = "-";
    out += castling;
    out += ' ';
    if (fields[2] != "-") {
        const int file = fields[2][0] - 'a';
        const int rank = fields[2][1] - '1';
        out.push_back(static_cast<char>('a' + file));
        out.push_back(static_cast<char>('1' + (7 - rank)));
    } else {
        out += '-';
    }
    for (std::size_t f = 3; f < fields.size(); ++f) {
        out += ' ';
        out += fields[f];
    }
    return out;
}

int cmd_mirror(const Net& net, const std::string& fens_path) {
    const std::vector<std::string> lines = read_lines(fens_path);
    long long compared = 0;
    long long asymmetric = 0;
    long long refused = 0;
    long long max_delta = 0;
    std::string first;
    for (const std::string& raw : lines) {
        // Accept either a bare FEN or a "<fen> | <moves>" sequence line.
        std::string fen = raw;
        const std::size_t bar = fen.find('|');
        if (bar != std::string::npos) fen = fen.substr(0, bar);
        while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\t')) fen.pop_back();
        Board a;
        if (!a.set_fen(fen)) {
            ++refused;
            continue;
        }
        const std::string mirrored = mirror_fen(fen);
        Board b;
        if (!b.set_fen(mirrored)) {
            ++refused;
            continue;
        }
        const int va = evaluate_reference(net, a);
        const int vb = evaluate_reference(net, b);
        ++compared;
        if (va != vb) {
            ++asymmetric;
            max_delta = std::max<long long>(max_delta, std::abs(va - vb));
            if (first.empty()) {
                first = fen + " -> " + mirrored + " : " + std::to_string(va) + " vs " + std::to_string(vb);
            }
        }
    }
    std::printf("MIRROR compared %lld asymmetric %lld refused %lld max_abs_delta %lld\n", compared, asymmetric, refused,
                max_delta);
    if (!first.empty()) std::printf("MIRROR first %s\n", first.c_str());
    return asymmetric == 0 ? 0 : 3;
}

int cmd_bare(const Net& net) {
    const std::vector<std::string> fens{
        "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/4K3 b - - 0 1",
        "8/8/8/8/8/8/8/K6k w - - 0 1",
        "k7/8/8/8/8/8/8/7K b - - 0 1",
        "4k3/8/8/8/8/8/8/3qK3 w - - 0 1",
        "4k3/8/8/8/8/8/8/3QK3 b - - 0 1",
    };
    int refused = 0;
    int wild = 0;
    for (const std::string& fen : fens) {
        Board board;
        if (!board.set_fen(fen)) {
            ++refused;
            std::printf("BARE refused %s\n", fen.c_str());
            continue;
        }
        const int value = evaluate_reference(net, board);
        const bool wild_score = std::abs(value) > 2000;
        if (wild_score) ++wild;
        std::printf("BARE %-42s eval %6d wild %d\n", fen.c_str(), value, wild_score ? 1 : 0);
    }
    std::printf("BARE compared %zu refused %d wild %d\n", fens.size(), refused, wild);
    return (refused == 0 && wild == 0) ? 0 : 3;
}

int cmd_loadprobe(const std::string& path) {
    std::string error;
    if (!load(path, &error)) {
        std::printf("LOADPROBE refused %s\n", error.c_str());
        return 1;
    }
    const Net& net = *loaded();
    Board board;
    board.set_fen(board.StandardStartFen);
    const int value = evaluate_reference(net, board);
    std::printf("LOADPROBE accepted %s startpos_eval %d\n", describe(net).c_str(), value);
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr,
                     "usage: netpath <inc|mirror|bare|loadprobe> <net> [fens] [stride] [verbose] [inject]\n"
                     "  inc: stride N evaluates every Nth ply (default 1); inject 1 corrupts the incremental\n"
                     "       accumulator to prove the check can fail\n");
        return 2;
    }
    const std::string command = argv[1];
    if (command == "loadprobe") return cmd_loadprobe(argv[2]);
    std::string error;
    if (!load(argv[2], &error)) {
        std::fprintf(stderr, "cannot load %s: %s\n", argv[2], error.c_str());
        return 1;
    }
    const Net& net = *loaded();
    if (command == "inc") {
        if (argc < 4) return 2;
        const int stride = argc > 4 ? std::max(1, std::atoi(argv[4])) : 1;
        const bool verbose = argc > 5 && std::atoi(argv[5]) != 0;
        const int inject = argc > 6 ? std::atoi(argv[6]) : 0;
        return cmd_inc(net, argv[3], stride, verbose, inject);
    }
    if (command == "mirror") {
        if (argc < 4) return 2;
        return cmd_mirror(net, argv[3]);
    }
    if (command == "bare") return cmd_bare(net);
    std::fprintf(stderr, "unknown command %s\n", command.c_str());
    return 2;
}
