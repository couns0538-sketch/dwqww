// R5C M1: the N3 options (SyzygyPath + IntendedThreefold + HardDeadline) together, and their interactions with
// the other draw logic. HardDeadline lives in the UCI layer and is tested by tools/r5c_n3_uci.py; this file
// covers the search side:
//  1. IntendedThreefold x CuckooRep matrix (both off, each alone, both on): exact mate scores (cold and warm
//     transposition table), a threefold claim found by the losing side, no draw score for a winning side that
//     only has repetition chances, deterministic node counts.
//  2. Syzygy with real 3-4-5 tables (optional second argument; skipped without it): probes at the root and inside
//     the search, Syzygy50MoveRule both ways on blessed losses, DTZ root filtering under a tight 50-move counter
//     (the chosen move is legal and keeps the win / the draw), all with the matrix options on.
//  3. SyzygyPath robustness: missing and wrong folders answer every search, a path change between searches gives
//     the same result as a fresh load, and the empty path gives the same nodes as a process that never loaded.
// usage: forge_r5c_n3_tests <syzygy_reference.tsv> [syzygy_dir]
#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"
#include "forge/syzygy.hpp"

#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace {

using forge::Board;
using forge::Move;

int failures = 0;
int checks = 0;

void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) {
        ++failures;
        std::cout << "FAIL " << what << '\n';
    }
}

std::string uci(Move move) { return Board::move_to_uci(move); }

Board board_from(const std::string& fen, const std::vector<std::string>& moves = {}) {
    Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "FAIL bad FEN " << fen << ": " << error << '\n';
        std::exit(1);
    }
    for (const std::string& text : moves) {
        const auto move = board.parse_uci(text);
        if (!move) {
            std::cout << "FAIL bad move " << text << " in " << fen << '\n';
            std::exit(1);
        }
        forge::Undo undo;
        (void)board.make_move(*move, undo);
    }
    return board;
}

// The score the engine reports: with a tablebase root the UCI output shows display_score() (iterative.inc).
int reported(const forge::SearchInfo& info) {
    return forge::syzygy::root_display.load() != 0 ? forge::syzygy::display_score(info.score) : info.score;
}

forge::SearchInfo run(forge::Searcher& searcher, const Board& board, int depth) {
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits);
}

struct Combo {
    bool intended;
    bool cuckoo;
    [[nodiscard]] std::string name() const {
        return std::string("IntendedThreefold=") + (intended ? "on" : "off") + " CuckooRep=" + (cuckoo ? "on" : "off");
    }
};
constexpr Combo Combos[] = {{false, false}, {true, false}, {false, true}, {true, true}};

void set_combo(const Combo& c) {
    forge::options::intended_threefold = c.intended;
    forge::options::cuckoo_rep = c.cuckoo;
}

// ---------------------------------------------------------------------------------------------------------------
void draw_matrix() {
    std::cout << "== 1. IntendedThreefold x CuckooRep\n";
    struct MateCase {
        const char* fen;
        int depth;
    };
    // Mate in 1 (back rank), mate in 2 (Kc7 Ka7 Ra1#), mate in 3 (Kd5-c5 only), searched to depth 20: no game
    // history, so neither option may change the exact mate score. (Depth matters: with CuckooRep on, the
    // engine reports the KR mate in 3 from depth 14, with it off from depth 10 - the draw bounds of the rook
    // shuffles change the move order; once found, the distance is the same. Seen with `go depth 24`.)
    const MateCase mates[] = {{"6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", 20},
                              {"k7/8/2K5/8/8/8/8/7R w - - 0 1", 20},
                              {"4R3/8/8/k2K4/8/8/8/8 w - - 0 1", 20}};
    for (const MateCase& m : mates) {
        int reference = 0;
        for (const Combo& c : Combos) {
            set_combo(c);
            forge::Searcher searcher(16, 1);
            const Board board = board_from(m.fen);
            const forge::SearchInfo cold = run(searcher, board, m.depth);
            const forge::SearchInfo warm = run(searcher, board, m.depth);  // same TT, second search
            if (!c.intended && !c.cuckoo) {
                reference = cold.score;
                check(forge::is_mate_score(cold.score) && cold.score > 0,
                      std::string("OFF finds the mate: ") + m.fen + " score " + std::to_string(cold.score));
            }
            check(cold.score == reference, c.name() + ": mate score " + std::to_string(cold.score) + " == OFF " +
                                               std::to_string(reference) + " (" + m.fen + ")");
            check(warm.score == reference, c.name() + ": warm-TT mate score " + std::to_string(warm.score) +
                                               " == OFF " + std::to_string(reference) + " (" + m.fen + ")");
        }
        std::cout << "  mate " << m.fen << " score " << reference << " in all four combinations\n";
    }

    // White is a rook and two pawns up; Kg1/Kh8 shuffling put the root position on the board twice.
    const char* rook_up = "7k/8/8/8/8/8/6PP/R5K1 w - - 0 1";
    // Losing side to move with a threefold claim available: after 1.Kf1 Kg8 2.Kg1 Kh8 3.Kf1 Kg8 4.Kg1 Black's Kh8
    // makes the third occurrence of the start position, the only draw in a lost endgame.
    const std::vector<std::string> claim = {"g1f1", "h8g8", "f1g1", "g8h8", "g1f1", "h8g8", "f1g1"};
    // Winning side to move with repetition chances only: 1.Kf1 Kg8 2.Kg1 Kh8 (the root occurs for the second time).
    const std::vector<std::string> winning = {"g1f1", "h8g8", "f1g1", "g8h8"};
    for (const Combo& c : Combos) {
        set_combo(c);
        {
            forge::Searcher searcher(16, 1);
            const forge::SearchInfo a = run(searcher, board_from(rook_up, claim), 10);
            searcher.clear();
            const forge::SearchInfo b = run(searcher, board_from(rook_up, claim), 10);
            check(a.score == 0 && uci(a.best_move) == "g8h8",
                  c.name() + ": losing side claims the threefold (g8h8, score 0), got " + uci(a.best_move) + " " +
                      std::to_string(a.score));
            check(a.nodes == b.nodes && a.score == b.score, c.name() + ": claim search deterministic (" +
                                                                std::to_string(a.nodes) + " / " + std::to_string(b.nodes) + " nodes)");
            std::cout << "  " << c.name() << " claim: " << uci(a.best_move) << " " << a.score << " (" << a.nodes << " nodes)\n";
        }
        {
            forge::Searcher searcher(16, 1);
            const forge::SearchInfo a = run(searcher, board_from(rook_up, winning), 10);
            const forge::SearchInfo warm = run(searcher, board_from(rook_up, winning), 10);
            check(a.score > 300 && !forge::is_mate_score(-a.score),
                  c.name() + ": winning side with repetition chances is not scored as a draw: " + std::to_string(a.score));
            check(warm.score > 300, c.name() + ": ... and not on a warm TT either: " + std::to_string(warm.score));
            std::cout << "  " << c.name() << " winning: " << uci(a.best_move) << " " << a.score << " (warm " << warm.score << ")\n";
        }
    }
    set_combo({false, false});
}

// ---------------------------------------------------------------------------------------------------------------
struct RefRow {
    std::string fen;
    int wdl = 0;
    int dtz = 0;
    std::map<std::string, int> root;  // uci -> dtz counted from the root, from the side to move
};

std::vector<RefRow> read_reference(const std::string& path) {
    std::vector<RefRow> rows;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        std::vector<std::string> fields;
        std::stringstream split(line);
        std::string field;
        while (std::getline(split, field, '\t')) fields.push_back(field);
        if (fields.size() < 4) continue;
        RefRow row;
        row.fen = fields[0];
        row.wdl = std::stoi(fields[1]);
        row.dtz = std::stoi(fields[2]);
        std::stringstream moves(fields[3]);
        std::string item;
        while (moves >> item) {
            const auto colon = item.find(':');
            if (colon != std::string::npos) row.root[item.substr(0, colon)] = std::stoi(item.substr(colon + 1));
        }
        rows.push_back(row);
    }
    return rows;
}

std::string with_counter(const std::string& fen, int halfmove) {
    std::stringstream in(fen);
    std::string placement, side, castling, ep, half, full;
    in >> placement >> side >> castling >> ep >> half >> full;
    return placement + " " + side + " " + castling + " " + ep + " " + std::to_string(halfmove) + " " + full;
}

bool has_castling(const std::string& fen) {
    std::stringstream in(fen);
    std::string placement, side, castling;
    in >> placement >> side >> castling;
    return castling != "-";
}

void syzygy_with_tables(const std::vector<RefRow>& rows, const std::string& dir) {
    std::cout << "== 2. Syzygy 3-4-5 with the draw options on\n";
    forge::options::intended_threefold = true;
    forge::options::cuckoo_rep = true;
    const forge::syzygy::LoadSummary s = forge::syzygy::load(dir);
    std::cout << "  load: " << s.wdl_tables << " WDL, " << s.dtz_tables << " DTZ, max " << s.max_pieces << " pieces, "
              << s.rejected << " rejected\n";
    check(s.wdl_tables == 145 && s.dtz_tables == 145 && s.max_pieces == 5 && s.rejected == 0,
          "the 3-4-5 folder loads 145 WDL + 145 DTZ tables, 5 pieces, nothing rejected");
    forge::Searcher searcher(16, 1);

    // Root probe: KQR vs K is a tablebase win; the reported score is in the TB win range or a mate score.
    {
        const forge::SearchInfo info = run(searcher, board_from("8/8/8/8/2k5/8/1Q6/K6R w - - 0 1"), 8);
        check(reported(info) >= forge::syzygy::TbWinInMaxPly,
              "root TB win reported: " + std::to_string(reported(info)) + " (search score " + std::to_string(info.score) + ")");
        std::cout << "  KQRvK root: " << uci(info.best_move) << " reported " << reported(info) << " (search " << info.score << ")\n";
    }
    // In-search probes: a 6-piece root reaches 5-piece positions after captures.
    {
        searcher.clear();
        const std::uint64_t before = forge::syzygy::probe_hits.load();
        const forge::SearchInfo info = run(searcher, board_from("8/5kp1/8/8/2q5/8/1Q6/K6R w - - 0 1"), 9);
        const std::uint64_t hits = forge::syzygy::probe_hits.load() - before;
        check(hits > 0, "in-search WDL probes from a 6-piece root: " + std::to_string(hits) + " hits");
        std::cout << "  6-piece root: " << uci(info.best_move) << " " << info.score << ", " << hits << " in-search TB hits\n";
    }

    // Syzygy50MoveRule both ways on the blessed losses of the reference (loser to move, decided after move 50).
    int blessed = 0;
    for (const RefRow& row : rows) {
        if (row.wdl != -1) continue;
        ++blessed;
        for (const bool rule50 : {true, false}) {
            forge::options::syzygy_50_move_rule = rule50;
            searcher.clear();
            const forge::SearchInfo info = run(searcher, board_from(row.fen), 6);
            const int shown = reported(info);
            if (rule50) {
                check(shown > -forge::syzygy::TbWinInMaxPly && shown <= 0,
                      "Syzygy50MoveRule=true: blessed loss is reported in the draw range: " + std::to_string(shown) + " " + row.fen);
            } else {
                check(shown <= -forge::syzygy::TbWinInMaxPly,
                      "Syzygy50MoveRule=false: blessed loss is reported as a TB loss: " + std::to_string(shown) + " " + row.fen);
            }
            check(row.root.count(uci(info.best_move)) == 1, "blessed loss: legal bestmove " + uci(info.best_move));
            std::cout << "  blessed loss rule50=" << rule50 << ": " << uci(info.best_move) << " reported " << shown
                      << " (search " << info.score << ")  " << row.fen << '\n';
        }
    }
    check(blessed >= 3, "reference has blessed losses: " + std::to_string(blessed));
    forge::options::syzygy_50_move_rule = true;

    // DTZ root filtering: every 3rd reference row without castling rights, depth 4. The chosen move must be a
    // legal root move; in a win it must keep the win; in a draw it must not lose. Wins are searched twice more
    // with the 50-move counter set one ply short of the limit for the fastest win: with Syzygy50MoveRule=true the
    // move must still win in time (dtz + counter <= 100, +1 for DTZ rounding); with false any win is fine.
    int searched = 0, tight = 0;
    for (std::size_t i = 0; i < rows.size(); i += 3) {
        const RefRow& row = rows[i];
        if (has_castling(row.fen) || row.root.empty() || row.wdl == -1) continue;
        searcher.clear();
        const forge::SearchInfo info = run(searcher, board_from(row.fen), 4);
        ++searched;
        const auto it = row.root.find(uci(info.best_move));
        check(it != row.root.end(), "DTZ root filter: legal bestmove " + uci(info.best_move) + " in " + row.fen);
        if (it == row.root.end()) continue;
        if (row.wdl == 2) check(it->second > 0, "win kept: " + it->first + " dtz " + std::to_string(it->second) + " " + row.fen);
        if (row.wdl == 0) check(it->second == 0, "draw kept: " + it->first + " dtz " + std::to_string(it->second) + " " + row.fen);
        if (row.wdl == 2 && row.dtz > 0 && row.dtz <= 99) {
            const int counter = 100 - row.dtz - 1;
            for (const bool rule50 : {true, false}) {
                forge::options::syzygy_50_move_rule = rule50;
                searcher.clear();
                const forge::SearchInfo t = run(searcher, board_from(with_counter(row.fen, counter)), 4);
                const auto jt = row.root.find(uci(t.best_move));
                check(jt != row.root.end() && jt->second > 0,
                      "tight counter " + std::to_string(counter) + " rule50=" + std::to_string(rule50) + ": winning move " +
                          uci(t.best_move) + " " + row.fen);
                if (rule50 && jt != row.root.end())
                    check(jt->second + counter <= 101, "tight counter: the win comes before the 50-move rule: dtz " +
                                                           std::to_string(jt->second) + " + " + std::to_string(counter) + " " + row.fen);
            }
            forge::options::syzygy_50_move_rule = true;
            ++tight;
        }
    }
    std::cout << "  DTZ root filter: " << searched << " reference rows, " << tight << " with a tight 50-move counter (x2)\n";
    check(searched >= 300 && tight >= 100, "enough reference rows searched");
    forge::options::intended_threefold = false;
    forge::options::cuckoo_rep = false;
}

// ---------------------------------------------------------------------------------------------------------------
void path_changes(const std::string& dir, const forge::SearchInfo& off_before) {
    std::cout << "== 3. SyzygyPath robustness\n";
    const char* kqk = "8/8/8/8/2k5/8/1Q6/K6R w - - 0 1";
    forge::Searcher searcher(16, 1);
    for (const char* wrong : {"Z:/r5c/no/such/folder", "tests", ";;"}) {
        const forge::syzygy::LoadSummary s = forge::syzygy::load(wrong);
        check(s.wdl_tables == 0 && forge::syzygy::max_pieces() == 0 && !forge::syzygy::tb_scores,
              std::string("wrong path loads nothing: ") + wrong);
        searcher.clear();
        const forge::SearchInfo info = run(searcher, board_from(kqk), 8);
        check(!info.best_move.is_none() && info.score > 300, std::string("search answers without tables: ") + wrong +
                                                                  " " + uci(info.best_move) + " " + std::to_string(info.score));
    }
    if (!dir.empty()) {
        (void)forge::syzygy::load(dir);
        searcher.clear();
        const forge::SearchInfo first = run(searcher, board_from(kqk), 8);
        (void)forge::syzygy::load("Z:/r5c/no/such/folder");
        searcher.clear();
        const forge::SearchInfo none = run(searcher, board_from(kqk), 8);
        (void)forge::syzygy::load(dir);
        searcher.clear();
        const forge::SearchInfo again = run(searcher, board_from(kqk), 8);
        check(first.score == again.score && first.nodes == again.nodes && first.best_move == again.best_move,
              "reload after a wrong path gives the first result again: " + std::to_string(first.score) + "/" +
                  std::to_string(first.nodes) + " vs " + std::to_string(again.score) + "/" + std::to_string(again.nodes));
        check(none.score < forge::syzygy::TbWinInMaxPly || forge::is_mate_score(none.score),
              "without tables no TB-range score: " + std::to_string(none.score));
        std::cout << "  reload: " << first.score << "/" << first.nodes << " == " << again.score << "/" << again.nodes
                  << " (no tables in between: " << none.score << ")\n";
    }
    (void)forge::syzygy::load("");
    check(!forge::syzygy::tb_scores && forge::syzygy::max_pieces() == 0, "empty path unloads everything");
    forge::Searcher fresh(16, 1);
    const forge::SearchInfo off_after = run(fresh, Board(), 10);
    check(off_after.nodes == off_before.nodes && off_after.score == off_before.score &&
              off_after.best_move == off_before.best_move,
          "empty path = never loaded: startpos d10 " + std::to_string(off_after.nodes) + " nodes vs " +
              std::to_string(off_before.nodes));
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "usage: forge_r5c_n3_tests <syzygy_reference.tsv> [syzygy_dir]\n";
        return 2;
    }
    const std::string dir = argc > 2 ? argv[2] : "";
    // Startpos depth 10 before anything is loaded: the OFF reference of section 3.
    forge::SearchInfo off_before;
    {
        forge::Searcher searcher(16, 1);
        off_before = run(searcher, Board(), 10);
    }
    draw_matrix();
    const std::vector<RefRow> rows = read_reference(argv[1]);
    check(rows.size() > 1000, "reference rows read: " + std::to_string(rows.size()));
    if (dir.empty()) std::cout << "SKIP section 2 and the reload part of 3: no Syzygy folder given\n";
    else syzygy_with_tables(rows, dir);
    path_changes(dir, off_before);
    std::cout << checks << " checks, " << failures << " failures\n";
    if (failures == 0) std::cout << "PASS\n";
    return failures == 0 ? 0 : 1;
}
