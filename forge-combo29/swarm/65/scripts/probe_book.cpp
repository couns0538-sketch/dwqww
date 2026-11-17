// Book probe: walks the embedded book from a root FEN and dumps every reachable
// book position with its candidate moves and weights, in a machine-readable form.
//
// Build (from forge-combo29/):
//   g++ -std=c++20 -O2 -Iinclude -DFORGE_NNUE_HIDDEN=256 \
//       -DFORGE_NNUE_WEIGHTS=\"$PWD/src/nnue_weights.inc\" \
//       swarm/65/scripts/probe_book.cpp src/board.cpp src/bitboard.cpp src/book.cpp \
//       src/eval.cpp src/eval_params.cpp src/nnue.cpp -o /tmp/probe_book -lpthread
//
// Usage: probe_book <max_plies> [root_fen]

#include "forge/board.hpp"
#include "forge/book.hpp"

#include <cstdio>
#include <cstdlib>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace {

struct Node {
    std::string fen;
    std::uint64_t key = 0;
    int ply = 0;
    std::vector<forge::book::Book::Candidate> cands;
};

std::set<std::uint64_t> visited;
std::vector<Node> nodes;
std::set<std::uint64_t> undecodable_keys;
std::map<std::uint64_t, int> undecodable_count;

void walk(forge::Board& board, const forge::book::Book& book, int ply, int max_ply) {
    const std::uint64_t key = forge::book::polyglot_key(board);
    if (!visited.insert(key).second) return;

    Node node;
    node.fen = board.fen();
    node.key = key;
    node.ply = ply;
    node.cands = book.candidates(board);

    // Count encoded moves that decode to none for this position: an entry whose
    // key matches but whose 16-bit move is illegal here.
    for (const forge::book::Entry& entry : book.entries()) {
        if (entry.key != key) continue;
        if (forge::book::decode_move(board, entry.move).is_none()) {
            ++undecodable_count[key];
            undecodable_keys.insert(key);
        }
    }

    std::vector<forge::Move> moves;
    for (const auto& c : node.cands) moves.push_back(c.move);
    nodes.push_back(node);

    if (ply >= max_ply) return;
    for (const forge::Move& move : moves) {
        forge::Board child = board;
        forge::Undo undo;
        if (!child.make_move(move, undo)) continue;
        walk(child, book, ply + 1, max_ply);
    }
}

} // namespace

int main(int argc, char** argv) {
    const int max_ply = argc > 1 ? std::atoi(argv[1]) : 20;
    const std::string root_fen = argc > 2 ? argv[2] : std::string(forge::Board::StandardStartFen);

    forge::Board board;
    std::string error;
    if (!board.set_fen(root_fen, &error)) {
        std::fprintf(stderr, "invalid root FEN: %s\n", error.c_str());
        return 2;
    }

    forge::book::Book book;
    book.load_embedded();

    std::printf("# embedded_available %d entries %zu max_ply %d\n",
                forge::book::embedded_available() ? 1 : 0, book.size(), max_ply);
    std::printf("# root %s\n", root_fen.c_str());

    walk(board, book, 0, max_ply);

    int cand_total = 0;
    for (const Node& n : nodes) cand_total += static_cast<int>(n.cands.size());
    int undecodable_total = 0;
    for (const auto& kv : undecodable_count) undecodable_total += kv.second;
    std::printf("# positions %zu candidate_moves %d undecodable_keys %zu undecodable_entries %d\n",
                nodes.size(), cand_total, undecodable_keys.size(), undecodable_total);

    std::printf("FEN\tKEY\tPLY\tMOVES\n");
    for (const Node& n : nodes) {
        std::string moves;
        for (const auto& c : n.cands) {
            if (!moves.empty()) moves += ',';
            moves += forge::Board::move_to_uci(c.move);
            moves += ':';
            moves += std::to_string(c.weight);
        }
        std::printf("%s\t%016llx\t%d\t%s\n", n.fen.c_str(),
                    static_cast<unsigned long long>(n.key), n.ply, moves.c_str());
    }
    return 0;
}
