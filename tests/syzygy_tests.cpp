// Syzygy tablebase tests (job C1).
//
//   forge_syzygy_tests <lichess.tsv> <reference.tsv> [tablebase_dir]
//   forge_syzygy_tests gen <material> <count> <seed> [ep]     (fixture positions)
//
// Without a tablebase folder (third argument, or FORGE_SYZYGY_PATH) only the
// checks that need no table files run; the others are reported as SKIPPED.
// Checks:
//  - robustness: empty/missing/junk/truncated/corrupt/partial folders load
//    without crashing, invalid files are rejected, probes fail cleanly;
//  - every loaded file's sections account for its size;
//  - known answers from the public tablebase.lichess.ovh API
//    (tests/syzygy_fixtures.tsv): WDL, DTZ, 50-move counter categories,
//    castling rights (not probed), en passant, and the DTZ of every root move.
//    The API knows some distances exactly where the files store moves
//    (rounded, see probe_dtz): a rounded value may be one ply short of it;
//  - exact answers of an independent reference prober on the same files
//    (tests/syzygy_reference.tsv): WDL, DTZ and root move DTZ, all equal;
//  - search glue: tables loaded and unloaded again leaves the search exactly
//    as before, root filtering, in-search probes, SyzygyProbeDepth and
//    Syzygy50MoveRule.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"
#include "forge/syzygy.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using forge::Board;
using forge::Move;
using forge::Undo;

namespace {

int g_checks = 0;
int g_failures = 0;

void check(bool ok, const std::string& what) {
    ++g_checks;
    if (!ok) {
        ++g_failures;
        if (g_failures <= 60) std::cout << "FAIL: " << what << "\n";
    }
}

Board board_of(const std::string& fen) {
    Board b;
    if (!b.set_fen(fen)) {
        std::cout << "FAIL: bad FEN " << fen << "\n";
        ++g_failures;
    }
    return b;
}

std::string separator() {
#if defined(_WIN32)
    return ";";
#else
    return ":";
#endif
}

std::string path_string(const fs::path& p) {
    const std::u8string u = p.u8string();
    return std::string(reinterpret_cast<const char*>(u.data()), u.size());
}

void write_file(const fs::path& p, const std::vector<char>& bytes) {
    std::ofstream out(p, std::ios::binary);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
}

std::vector<char> read_file(const fs::path& p) {
    std::ifstream in(p, std::ios::binary);
    return std::vector<char>((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

int category_wdl(const std::string& c, bool& definite) {
    definite = true;
    if (c == "win") return 2;
    if (c == "cursed-win") return 1;
    if (c == "draw") return 0;
    if (c == "blessed-loss") return -1;
    if (c == "loss") return -2;
    definite = false;
    return 0;
}

int zeroing_dtz(int wdl) { return wdl == 2 ? 1 : wdl == 1 ? 101 : wdl == -1 ? -101 : wdl == -2 ? -1 : 0; }

// ---------------------------------------------------------------------------
// Random legal positions of a material ("KRPvKR"), colours swapped at random;
// with `ep` a legal en-passant capture is available.
bool random_position(const std::string& material, std::mt19937_64& rng, bool swap, bool ep, std::string& fen_out) {
    const std::size_t v = material.find('v');
    if (v == std::string::npos) return false;
    std::string sides[2] = {material.substr(0, v), material.substr(v + 1)};
    if (swap) std::swap(sides[0], sides[1]);
    for (int attempt = 0; attempt < 100000; ++attempt) {
        char squares[64] = {};
        const int stm = static_cast<int>(rng() % 2);
        const int mover = 1 - stm;
        int ep_square = -1;
        int origin = -1;
        if (ep) {
            if (sides[mover].find('P') == std::string::npos || sides[stm].find('P') == std::string::npos) return false;
            const int file = static_cast<int>(rng() % 8);
            const int rank = mover == 0 ? 3 : 4;
            const int sq = rank * 8 + file;
            const int adjacent = file == 0 ? 1 : file == 7 ? 6 : (rng() % 2 ? file - 1 : file + 1);
            squares[sq] = mover == 0 ? 'P' : 'p';
            squares[rank * 8 + adjacent] = mover == 0 ? 'p' : 'P';
            ep_square = mover == 0 ? sq - 8 : sq + 8;
            origin = mover == 0 ? ep_square - 8 : ep_square + 8;
        }
        bool ok = true;
        for (int side = 0; side < 2 && ok; ++side) {
            bool skipped_pawn = false;
            for (const char piece : sides[side]) {
                if (ep && piece == 'P' && !skipped_pawn) {
                    skipped_pawn = true;  // already placed
                    continue;
                }
                const char c = side == 0 ? piece : static_cast<char>(piece - 'A' + 'a');
                int sq = 0;
                int tries = 0;
                do {
                    sq = static_cast<int>(rng() % 64);
                    if (++tries > 1000) {
                        ok = false;
                        break;
                    }
                } while (squares[sq] != 0 || (piece == 'P' && (sq < 8 || sq >= 56)) || sq == ep_square || sq == origin);
                squares[sq] = c;
            }
        }
        if (!ok) continue;
        std::string fen;
        for (int rank = 7; rank >= 0; --rank) {
            int empty = 0;
            for (int file = 0; file < 8; ++file) {
                const char c = squares[rank * 8 + file];
                if (c == 0) {
                    ++empty;
                    continue;
                }
                if (empty != 0) fen += static_cast<char>('0' + empty);
                empty = 0;
                fen += c;
            }
            if (empty != 0) fen += static_cast<char>('0' + empty);
            if (rank != 0) fen += '/';
        }
        fen += stm == 0 ? " w - " : " b - ";
        if (ep_square >= 0) {
            fen += static_cast<char>('a' + ep_square % 8);
            fen += static_cast<char>('1' + ep_square / 8);
        } else {
            fen += '-';
        }
        fen += " 0 1";
        Board b;
        if (!b.set_fen(fen)) continue;
        if (ep) {
            bool legal_ep = false;
            for (const Move m : b.legal_moves()) legal_ep = legal_ep || (m.flags & forge::EnPassant) != 0;
            if (!legal_ep) continue;
        }
        fen_out = fen;
        return true;
    }
    return false;
}

// ---------------------------------------------------------------------------
std::uint64_t search_nodes(const std::string& fen, int depth, int* score = nullptr, Move* best = nullptr) {
    forge::Searcher searcher(16);
    forge::SearchLimits limits;
    limits.depth = depth;
    const forge::SearchInfo info = searcher.search(board_of(fen), limits, false, forge::Searcher::TTAccess::Exclusive);
    if (score != nullptr) *score = info.score;
    if (best != nullptr) *best = info.best_move;
    return info.nodes;
}

const std::vector<std::string> kSearchFens = {
    "4k3/8/8/8/8/8/8/4K2Q w - - 0 1",
    "8/8/3k4/8/2KP4/8/8/8 w - - 0 1",
    "8/4k3/8/8/2K5/8/1P4R1/r7 w - - 0 1",
    "4k3/8/8/8/3r4/8/3Q4/3RK2n w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
};

// ---------------------------------------------------------------------------
// Transposition-table encoding of scores (score_to_tt / score_from_tt in
// src/search/scores.inc, through the test hook). Mate scores always carry their
// distance; tablebase-range scores only while tables are loaded, otherwise
// they are stored unchanged exactly as in AL1 s198.
void tt_score_encoding(bool tables_loaded) {
    using forge::syzygy::TbWin;
    using forge::syzygy::TbWinInMaxPly;
    using forge::syzygy::tt_score_round_trip;
    const std::string mode = tables_loaded ? " (tables loaded)" : " (no tables)";
    check((forge::syzygy::max_pieces() > 0) == tables_loaded && forge::syzygy::tb_scores == tables_loaded,
          "TT encoding test runs in the intended mode" + mode);
    // Mate scores, ordinary scores: as in the lock in both modes.
    check(tt_score_round_trip(forge::MateValue - 5, 3, 7) == forge::MateValue - 9, "mate score keeps its distance" + mode);
    check(tt_score_round_trip(-forge::MateValue + 5, 3, 7) == -forge::MateValue + 9, "mated score keeps its distance" + mode);
    for (const int score : {0, 1, -1, 250, -250, 30000, -30000, TbWinInMaxPly - 1, -(TbWinInMaxPly - 1)}) {
        check(tt_score_round_trip(score, 3, 7) == score, "ordinary score unchanged: " + std::to_string(score) + mode);
    }
    for (const int store_ply : {0, 1, 4, 9}) {
        for (const int read_ply : {0, 2, 5, 9}) {
            for (const int found : {store_ply, store_ply + 3, store_ply + 20}) {
                const int win = TbWin - found;  // a TB win found at ply `found`, seen at ply store_ply
                const int expected_win = tables_loaded ? win - (read_ply - store_ply) : win;
                const int expected_loss = tables_loaded ? -win + (read_ply - store_ply) : -win;
                const std::string at = " found " + std::to_string(found) + " stored at ply " + std::to_string(store_ply) +
                                       " read at ply " + std::to_string(read_ply) + mode;
                check(tt_score_round_trip(win, store_ply, read_ply) == expected_win, "TB win distance" + at);
                check(tt_score_round_trip(-win, store_ply, read_ply) == expected_loss, "TB loss distance" + at);
                check(std::abs(tt_score_round_trip(win, store_ply, read_ply)) < forge::MateInMaxPly,
                      "TB win stays below the mate scores" + at);
            }
        }
    }
}

void robustness(const fs::path& tb_dir, bool have_tables) {
    std::cout << "== robustness\n";
    {
        const auto s = forge::syzygy::load("");
        check(s.wdl_tables == 0 && s.max_pieces == 0 && forge::syzygy::max_pieces() == 0, "empty path loads nothing");
        Board b = board_of("4k3/8/8/8/8/8/8/4K2Q w - - 0 1");
        int v = 0;
        check(!forge::syzygy::probe_wdl(b, v) && !forge::syzygy::probe_dtz(b, v), "no tables: probes fail");
        std::vector<forge::syzygy::RootRank> ranks;
        bool used = false;
        check(!forge::syzygy::rank_root_moves(b, true, ranks, used), "no tables: no root ranking");
        check(b.fen() == "4k3/8/8/8/8/8/8/4K2Q w - - 0 1", "board unchanged");
    }
    check(forge::syzygy::load("<empty>").wdl_tables == 0, "<empty> loads nothing");
    check(forge::syzygy::load("this/folder/does/not/exist").wdl_tables == 0, "missing folder loads nothing");
    check(forge::syzygy::load(separator() + separator()).wdl_tables == 0, "separators only");

    std::mt19937_64 rng(20261026);
    const fs::path root = fs::temp_directory_path() / ("forge_syzygy_test_" + std::to_string(rng() % 1000000000ULL));
    std::error_code ec;
    fs::create_directories(root / "empty", ec);
    fs::create_directories(root / "junk", ec);
    fs::create_directories(root / "partial", ec);
    fs::create_directories(root / "corrupt", ec);
    check(forge::syzygy::load(path_string(root / "empty")).wdl_tables == 0, "empty folder loads nothing");

    // Junk files with table names.
    write_file(root / "junk" / "KQvK.rtbw", {});
    write_file(root / "junk" / "KRvK.rtbw", std::vector<char>(1000, '\x5a'));
    write_file(root / "junk" / "KPvK.rtbw", {'\x71', '\xe8', '\x23', '\x5d'});
    write_file(root / "junk" / "KBNvK.rtbw", {'\x71', '\xe8', '\x23', '\x5d', '\x41', '\x00'});
    write_file(root / "junk" / "notatable.rtbw", std::vector<char>(100, '\x00'));
    write_file(root / "junk" / "KvK.rtbw", std::vector<char>(100, '\x00'));
    write_file(root / "junk" / "KQQQQQQvK.rtbw", std::vector<char>(100, '\x00'));
    {
        const auto s = forge::syzygy::load(path_string(root / "junk"));
        check(s.wdl_tables == 0 && s.rejected == 4, "junk folder: 4 table-named files rejected, rejected=" + std::to_string(s.rejected));
        Board b = board_of("4k3/8/8/8/8/8/8/4K2Q w - - 0 1");
        int v = 0;
        check(!forge::syzygy::probe_wdl(b, v), "junk: probe fails");
    }
    if (!have_tables) {
        std::cout << "SKIPPED: truncated/corrupt/partial table checks (no tablebase folder)\n";
        fs::remove_all(root, ec);
        return;
    }
    // Truncated copies of a real table: every truncation inside the data is rejected.
    const std::vector<char> kqvk = read_file(tb_dir / "KQvK.rtbw");
    const std::vector<char> krvk = read_file(tb_dir / "KRvK.rtbw");
    check(kqvk.size() > 100 && krvk.size() > 100, "real KQvK/KRvK tables readable");
    int rejected_truncations = 0;
    for (const std::size_t cut : {std::size_t{5}, std::size_t{9}, std::size_t{40}, kqvk.size() / 2, kqvk.size() - 49}) {
        const fs::path dir = root / ("cut" + std::to_string(cut));
        fs::create_directories(dir, ec);
        write_file(dir / "KQvK.rtbw", std::vector<char>(kqvk.begin(), kqvk.begin() + static_cast<std::ptrdiff_t>(cut)));
        const auto s = forge::syzygy::load(path_string(dir));
        rejected_truncations += s.rejected == 1 && s.wdl_tables == 0 ? 1 : 0;
    }
    check(rejected_truncations == 5, "truncated tables rejected: " + std::to_string(rejected_truncations) + "/5");
    // Corrupt data blocks: probes may return wrong values but never crash.
    std::vector<char> corrupt = krvk;
    for (std::size_t i = 300; i < corrupt.size(); i += 7) corrupt[i] = static_cast<char>(rng());
    write_file(root / "corrupt" / "KRvK.rtbw", corrupt);
    write_file(root / "corrupt" / "KRvK.rtbz", read_file(tb_dir / "KRvK.rtbz"));
    {
        (void)forge::syzygy::load(path_string(root / "corrupt"));
        int answered = 0;
        for (int i = 0; i < 2000; ++i) {
            std::string fen;
            if (!random_position("KRvK", rng, rng() % 2 == 1, false, fen)) continue;
            Board b = board_of(fen);
            int v = 0;
            answered += forge::syzygy::probe_wdl(b, v) ? 1 : 0;
            (void)forge::syzygy::probe_dtz(b, v);
        }
        check(true, "corrupt table probed 2000x without crash (answered " + std::to_string(answered) + ")");
    }
    // Partial folder: WDL only, and the needed 3-piece tables missing.
    for (const char* name : {"KQvK.rtbw", "KRvK.rtbw", "KQvKR.rtbw"}) write_file(root / "partial" / name, read_file(tb_dir / name));
    {
        const auto s = forge::syzygy::load(path_string(root / "partial"));
        check(s.wdl_tables == 3 && s.dtz_tables == 0 && s.max_pieces == 4, "partial folder: 3 WDL, 0 DTZ");
        Board b = board_of("4k3/8/8/8/8/8/8/4K2Q w - - 0 1");
        int v = 0;
        check(forge::syzygy::probe_wdl(b, v) && v == 2, "partial: KQvK WDL win");
        check(!forge::syzygy::probe_dtz(b, v), "partial: no DTZ");
        std::vector<forge::syzygy::RootRank> ranks;
        bool used = true;
        check(forge::syzygy::rank_root_moves(b, true, ranks, used) && !used && !ranks.empty(), "partial: root ranked by WDL");
        // KQvKR where the rook can capture the queen: needs KRvK (present) -> ok;
        // where the king can capture the rook: needs KQvK (present) -> ok.
        Board c = board_of("8/8/8/8/8/2k5/8/K2Q3r b - - 0 1");
        check(forge::syzygy::probe_wdl(c, v), "partial: capture into a present table");
        // KQvKR where the queen can be captured by the king: KvKR missing -> KRvK flipped, present.
        // A capture into a missing table (KQvKB needs KQvK and KBvK... KBvK absent).
        Board d = board_of("8/8/8/8/8/2k5/8/K1Bq4 w - - 0 1");  // KBvKQ: no table at all
        check(!forge::syzygy::probe_wdl(d, v), "partial: missing table fails");
    }
    // Two folders with a separator, one missing: tables from the existing one.
    {
        const std::string paths = "no/such/dir" + separator() + path_string(root / "partial");
        check(forge::syzygy::load(paths).wdl_tables == 3, "multi-folder path with a missing folder");
    }
    (void)forge::syzygy::load("");
    fs::remove_all(root, ec);
}

// ---------------------------------------------------------------------------
struct FixtureRow {
    std::string fen, category, dtz, precise, moves, note;
};

std::vector<FixtureRow> read_fixture(const std::string& path) {
    std::vector<FixtureRow> rows;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        if (!line.empty() && line.back() == '\r') line.pop_back();
        std::vector<std::string> f;
        std::stringstream ss(line);
        std::string field;
        while (std::getline(ss, field, '\t')) f.push_back(field);
        if (f.size() < 6) {
            std::cout << "FAIL: bad fixture line: " << line << "\n";
            ++g_failures;
            continue;
        }
        rows.push_back(FixtureRow{f[0], f[1], f[2], f[3], f[4], f[5]});
    }
    return rows;
}

void known_answers(const std::vector<FixtureRow>& rows, const std::string& label) {
    std::cout << "== known answers (" << label << ")\n";
    int wdl_checked = 0, dtz_checked = 0, counter_checked = 0, castling_checked = 0, move_checked = 0, ep_rows = 0;
    int dtz_rounded = 0, counter_undecided = 0, move_rounded_count = 0;
    for (const FixtureRow& row : rows) {
        Board b = board_of(row.fen);
        const std::string before = b.fen();
        const bool castling = b.castling_rights() != 0;
        int wdl = 0;
        int dtz = 0;
        bool rounded = false;
        const bool wdl_ok = forge::syzygy::probe_wdl(b, wdl);
        const bool dtz_ok = forge::syzygy::probe_dtz(b, dtz, rounded);
        check(b.fen() == before, "board restored after probes: " + row.fen);
        {
            std::stringstream fs_fields(row.fen);
            std::string placement, side, castle, ep;
            fs_fields >> placement >> side >> castle >> ep;
            if (ep != "-") ++ep_rows;
        }
        if (castling) {
            check(!wdl_ok && !dtz_ok, "castling rights are not probed: " + row.fen);
            std::vector<forge::syzygy::RootRank> ranks;
            bool used = false;
            check(!forge::syzygy::rank_root_moves(b, true, ranks, used), "castling root not ranked: " + row.fen);
            ++castling_checked;
            continue;
        }
        bool definite = false;
        const int expected = category_wdl(row.category, definite);
        if (b.halfmove_clock() == 0) {
            check(definite && wdl_ok && wdl == expected,
                  "WDL " + row.fen + " expected " + row.category + " got " + (wdl_ok ? std::to_string(wdl) : "FAIL"));
            ++wdl_checked;
        } else if (definite) {
            int counted = 0;
            const bool ok = forge::syzygy::probe_wdl_with_counter(b, counted);
            if (!ok && dtz_ok && rounded) {
                ++counter_undecided;  // rounded distance exactly at the 50-move boundary
            } else {
                check(ok && counted == expected, "WDL with counter " + row.fen + " expected " + row.category + " got " +
                                                     (ok ? std::to_string(counted) : "FAIL"));
                ++counter_checked;
            }
        }
        if (row.dtz != "-") {
            const int want = std::stoi(row.dtz);
            const bool exact = dtz_ok && dtz == want;
            const bool within_rounding = dtz_ok && rounded && want == dtz + (dtz > 0) - (dtz < 0);
            check(exact || within_rounding, "DTZ " + row.fen + " expected " + row.dtz + " got " +
                                                (dtz_ok ? std::to_string(dtz) + (rounded ? " (rounded)" : "") : "FAIL"));
            ++dtz_checked;
            if (!exact && within_rounding) ++dtz_rounded;
        }
        if (row.moves == "-" || b.halfmove_clock() != 0) continue;
        std::vector<forge::syzygy::RootRank> ranks;
        bool used = false;
        const bool ranked = forge::syzygy::rank_root_moves(b, true, ranks, used);
        check(ranked && used, "root ranked with DTZ: " + row.fen);
        if (!ranked) continue;
        std::map<std::string, int> value;
        std::map<std::string, bool> value_rounded;
        for (const auto& r : ranks) {
            value[Board::move_to_uci(r.move)] = r.value;
            value_rounded[Board::move_to_uci(r.move)] = r.rounded;
        }
        std::stringstream ms(row.moves);
        std::string token;
        int api_moves = 0;
        while (ms >> token) {
            // uci,zeroing,checkmate,category,dtz
            std::vector<std::string> p;
            std::stringstream ts(token);
            std::string part;
            while (std::getline(ts, part, ',')) p.push_back(part);
            if (p.size() != 5) continue;
            ++api_moves;
            const auto it = value.find(p[0]);
            check(it != value.end(), "root move present: " + p[0] + " in " + row.fen);
            if (it == value.end()) continue;
            int want = 0;
            if (p[1] == "1") {
                bool d = false;
                const int child = category_wdl(p[3], d);
                if (!d) continue;
                want = zeroing_dtz(-child);
            } else if (p[2] == "1") {
                want = 1;
            } else {
                if (p[4] == "-") continue;
                const int child = std::stoi(p[4]);
                want = -child;
                want += (want > 0) - (want < 0);
            }
            const bool move_rounded = value_rounded[p[0]];
            const bool move_exact = it->second == want;
            check(move_exact || (move_rounded && want == it->second + (it->second > 0) - (it->second < 0)),
                  "root move " + p[0] + " of " + row.fen + " expected " + std::to_string(want) + " got " +
                      std::to_string(it->second) + (move_rounded ? " (rounded)" : ""));
            ++move_checked;
            if (!move_exact) ++move_rounded_count;
        }
        check(api_moves == static_cast<int>(ranks.size()), "root move count " + row.fen);
    }
    std::cout << "rows " << rows.size() << " wdl " << wdl_checked << " dtz " << dtz_checked << " (one ply short, rounded: "
              << dtz_rounded << ") counter " << counter_checked << " (undecided by rounding: " << counter_undecided
              << ") castling " << castling_checked << " ep-rows " << ep_rows << " root-moves " << move_checked
              << " (rounded: " << move_rounded_count << ")\n";
    check(rows.size() >= 200, "fixture has at least 200 positions");
}

// Exact answers of the reference prober: fen, wdl, dtz, root moves "uci:dtz", note.
void reference_answers(const std::string& path) {
    std::cout << "== reference prober answers\n";
    std::ifstream in(path);
    std::string line;
    int rows = 0, moves = 0, skipped = 0;
    std::error_code ec;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        if (line.back() == '\r') line.pop_back();
        std::vector<std::string> f;
        std::stringstream ss(line);
        std::string field;
        while (std::getline(ss, field, '\t')) f.push_back(field);
        if (f.size() < 5) {
            check(false, "bad reference line: " + line);
            continue;
        }
        if (f[4].find("needs:") != std::string::npos) {
            bool all = true;
            std::stringstream ns(f[4].substr(f[4].find("needs:") + 6));
            std::string table;
            while (ns >> table) all = all && forge::syzygy::has_table(table);
            if (!all) {
                ++skipped;
                continue;
            }
        }
        ++rows;
        Board b = board_of(f[0]);
        int wdl = 0;
        int dtz = 0;
        check(forge::syzygy::probe_wdl(b, wdl) && std::to_string(wdl) == f[1], "reference WDL " + f[0] + " expected " + f[1]);
        check(forge::syzygy::probe_dtz(b, dtz) && std::to_string(dtz) == f[2],
              "reference DTZ " + f[0] + " expected " + f[2] + " got " + std::to_string(dtz));
        if (f[3] == "-") continue;
        std::vector<forge::syzygy::RootRank> ranks;
        bool used = false;
        check(forge::syzygy::rank_root_moves(b, true, ranks, used) && used, "reference root ranked: " + f[0]);
        std::map<std::string, int> value;
        for (const auto& r : ranks) value[Board::move_to_uci(r.move)] = r.value;
        std::stringstream ms(f[3]);
        std::string token;
        int count = 0;
        while (ms >> token) {
            const std::size_t colon = token.find(':');
            const std::string uci = token.substr(0, colon);
            const auto it = value.find(uci);
            check(it != value.end() && std::to_string(it->second) == token.substr(colon + 1),
                  "reference root move " + token + " of " + f[0] + " got " + (it != value.end() ? std::to_string(it->second) : "none"));
            ++count;
        }
        check(count == static_cast<int>(ranks.size()), "reference root move count " + f[0]);
        moves += count;
    }
    std::cout << "rows " << rows << " root-moves " << moves << " skipped " << skipped << " (tables not present)\n";
    check(rows + skipped >= 1000, "reference fixture has at least 1000 positions");
}

// ---------------------------------------------------------------------------
void search_glue(const std::string& tb_dir) {
    std::cout << "== search glue\n";
    (void)forge::syzygy::load("");
    std::vector<std::uint64_t> off;
    for (const std::string& fen : kSearchFens) off.push_back(search_nodes(fen, 9));
    (void)forge::syzygy::load(tb_dir);
    const int largest = forge::syzygy::max_pieces();
    check(largest >= 4, "tables loaded");
    std::vector<std::uint64_t> on;
    for (const std::string& fen : kSearchFens) on.push_back(search_nodes(fen, 9));
    check(on != off, "tables change the search on endgame positions");
    (void)forge::syzygy::load("");
    std::vector<std::uint64_t> off_again;
    for (const std::string& fen : kSearchFens) off_again.push_back(search_nodes(fen, 9));
    check(off == off_again, "unloading restores the exact OFF search");

    (void)forge::syzygy::load(tb_dir);
    forge::options::syzygy_probe_depth = 1;
    forge::options::syzygy_50_move_rule = true;
    // Root filtering: the best move of a won KQvK keeps the win (TB check).
    {
        Move best;
        int score = 0;
        (void)search_nodes("4k3/8/8/8/8/8/8/4K2Q w - - 0 1", 8, &score, &best);
        Board b = board_of("4k3/8/8/8/8/8/8/4K2Q w - - 0 1");
        Undo undo;
        (void)b.make_move(best, undo);
        int wdl = 0;
        check(forge::syzygy::probe_wdl(b, wdl) && wdl == -2, "KQvK: search keeps the win");
        check(forge::syzygy::display_score(score) == forge::syzygy::TbWin - 1, "KQvK: reported score is a TB win");
    }
    // Probes in the search only right after a capture or pawn move: from a root
    // with castling rights (not ranked, so probing stays on) at depth 2 every
    // probed node (ply 1) follows a king or rook move: no probe at all.
    {
        forge::syzygy::probe_hits.store(0);
        (void)search_nodes("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1", 2);
        check(forge::syzygy::probe_hits.load() == 0,
              "no probe with a non-zero 50-move counter, hits " + std::to_string(forge::syzygy::probe_hits.load()));
    }
    // In-search probe: from a root with one piece more than the tables, the
    // capture into a won tablebase ending is found and scored as a TB win.
    {
        const std::string fen = largest >= 5 ? "4k3/8/8/8/3r4/8/3Q4/3RK2n w - - 0 1" : "4k3/8/8/8/3r4/8/3Q4/4K2n w - - 0 1";
        if (forge::syzygy::has_table(largest >= 5 ? "KQRvKN" : "KQvKN")) {
            int score = 0;
            Move best;
            forge::syzygy::probe_hits.store(0);
            (void)search_nodes(fen, 4, &score, &best);
            check(Board::move_to_uci(best) == "d2d4" && score == forge::syzygy::TbWin - 1,
                  "root above the tables: capture into a TB win, score " + std::to_string(score));
            check(forge::syzygy::probe_hits.load() > 0, "probes counted in the search");
            // SyzygyProbeDepth 10: positions with the maximum piece count are probed only at depth >= 10.
            forge::options::syzygy_probe_depth = 10;
            (void)search_nodes(fen, 4, &score, &best);
            check(score < forge::syzygy::TbWin - forge::MaxPly, "SyzygyProbeDepth 10 skips the probe at depth 4");
            forge::options::syzygy_probe_depth = 1;
        }
    }
    // The other sign: the only legal move (Kxg2) leaves a won ending to the
    // opponent, who is probed at ply 1 as the side to move: -(TbWin - 1).
    {
        const std::string fen = largest >= 5 ? "rr2k3/8/8/8/8/8/6q1/1B5K w - - 0 1" : "rr2k3/8/8/8/8/8/6q1/7K w - - 0 1";
        if (forge::syzygy::has_table(largest >= 5 ? "KRRvKB" : "KRRvK")) {
            int score = 0;
            Move best;
            (void)search_nodes(fen, 3, &score, &best);
            check(Board::move_to_uci(best) == "h1g2" && score == -(forge::syzygy::TbWin - 1),
                  "forced capture into a lost ending scores a TB loss, score " + std::to_string(score));
        }
    }
    // Syzygy50MoveRule: a cursed win is a draw-ish +2 with the rule, a TB win without it.
    if (forge::syzygy::has_table("KNNvKP")) {
        forge::SearchLimits limits;
        limits.depth = 1;
        forge::syzygy::prepare_root(board_of("K7/N7/k7/8/3p4/8/N7/8 w - - 0 1"), limits);
        check(limits.search_moves_specified && !limits.search_moves.empty(), "cursed win root restricted");
        check(forge::syzygy::display_score(0) == forge::syzygy::TbCursed, "50-move rule on: cursed win shows +2");
        forge::options::syzygy_50_move_rule = false;
        forge::SearchLimits limits2;
        forge::syzygy::prepare_root(board_of("K7/N7/k7/8/3p4/8/N7/8 w - - 0 1"), limits2);
        check(forge::syzygy::display_score(0) == forge::syzygy::TbWin - 1, "50-move rule off: cursed win shows a win");
        forge::options::syzygy_50_move_rule = true;
    } else {
        std::cout << "SKIPPED: Syzygy50MoveRule cursed-win checks (KNNvKP not present)\n";
    }
    {
        check(forge::syzygy::display_score(forge::MateValue - 5) == forge::MateValue - 5, "mate scores are kept");
        // searchmoves that exclude every best move are kept as given.
        forge::SearchLimits limits3;
        Board b = board_of("4k3/8/8/8/8/8/8/4K2Q w - - 0 1");
        limits3.search_moves_specified = true;
        limits3.search_moves = {*b.parse_uci("e1e2")};
        forge::syzygy::prepare_root(b, limits3);
        check(limits3.search_moves.size() == 1, "searchmoves kept");
        // Castling rights: no root filtering.
        forge::SearchLimits limits4;
        forge::syzygy::prepare_root(board_of("4k3/8/8/8/8/8/8/4K2R w K - 0 1"), limits4);
        check(!limits4.search_moves_specified && forge::syzygy::display_score(7) == 7, "castling root not filtered");
        check(forge::syzygy::search_cardinality.load() == largest, "castling root: probing in search stays on");
    }
    (void)forge::syzygy::load("");
    check(forge::syzygy::search_cardinality.load() == 0 && forge::syzygy::display_score(7) == 7, "unload resets the search state");
}

} // namespace

int main(int argc, char** argv) {
    if (argc >= 3 && std::string(argv[1]) == "probe") {
        // forge_syzygy_tests probe <tablebase_dir> < fens: fen, wdl, dtz, rounded (fixture tooling)
        (void)forge::syzygy::load(argv[2]);
        std::string line;
        while (std::getline(std::cin, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            Board b;
            if (line.empty() || !b.set_fen(line)) continue;
            int wdl = 0;
            int dtz = 0;
            bool rounded = false;
            const bool ok = forge::syzygy::probe_wdl(b, wdl) && forge::syzygy::probe_dtz(b, dtz, rounded);
            std::cout << line << '\t' << (ok ? std::to_string(wdl) + '\t' + std::to_string(dtz) + '\t' + (rounded ? "1" : "0") : "-\t-\t-")
                      << '\n';
        }
        return 0;
    }
    if (argc >= 5 && std::string(argv[1]) == "gen") {
        std::mt19937_64 rng(std::stoull(argv[4]));
        const bool ep = argc > 5 && std::string(argv[5]) == "ep";
        const int count = std::stoi(argv[3]);
        for (int i = 0; i < count; ++i) {
            std::string fen;
            if (random_position(argv[2], rng, rng() % 2 == 1, ep, fen)) std::cout << fen << "\n";
        }
        return 0;
    }
    if (argc < 3) {
        std::cerr << "usage: forge_syzygy_tests <lichess.tsv> <reference.tsv> [tablebase_dir]\n";
        return 2;
    }
    const std::string fixture = argv[1];
    const std::string reference = argv[2];
    std::string tb = argc >= 4 ? argv[3] : "";
    if (tb.empty()) {
        const char* env = std::getenv("FORGE_SYZYGY_PATH");
        if (env != nullptr) tb = env;
    }
    std::error_code ec;
    const fs::path tb_dir = fs::path(std::u8string(reinterpret_cast<const char8_t*>(tb.data()), tb.size()));
    const bool have_tables = !tb.empty() && fs::exists(tb_dir / "KQvK.rtbw", ec);
    tt_score_encoding(false);
    robustness(tb_dir, have_tables);
    if (!have_tables) {
        std::cout << "SKIPPED: known-answer and search checks need a tablebase folder (argument or FORGE_SYZYGY_PATH)\n";
    } else {
        const auto s = forge::syzygy::load(tb);
        std::cout << "loaded " << s.wdl_tables << " WDL, " << s.dtz_tables << " DTZ, rejected " << s.rejected << ", max "
                  << s.max_pieces << " pieces\n";
        check(s.rejected == 0, "no table rejected");
        tt_score_encoding(true);
        std::uint64_t total = 0;
        for (const auto& t : forge::syzygy::loaded_tables()) {
            check(t.tail == 16 || t.tail == 48, "file layout of " + t.name + " ends at the checksum, tail " + std::to_string(t.tail));
            total += t.file_size;
        }
        const std::vector<FixtureRow> rows = read_fixture(fixture);
        // Rows whose tables are not in the folder (e.g. a CI subset) are skipped.
        std::vector<FixtureRow> usable;
        for (const FixtureRow& row : rows) {
            if (row.note.find("needs:") != std::string::npos) {
                bool all = true;
                std::stringstream ns(row.note.substr(row.note.find("needs:") + 6));
                std::string table;
                while (ns >> table) all = all && fs::exists(tb_dir / (table + ".rtbw"), ec) && fs::exists(tb_dir / (table + ".rtbz"), ec);
                if (!all) continue;
            }
            usable.push_back(row);
        }
        if (usable.size() != rows.size()) std::cout << "SKIPPED: " << rows.size() - usable.size() << " fixture rows (tables not present)\n";
        known_answers(usable, "mapped files");
        reference_answers(reference);
        if (total < (256ULL << 20)) {
            forge::syzygy::set_heap_loading(true);
            (void)forge::syzygy::load(tb);
            known_answers(usable, "heap copies");
            reference_answers(reference);
            forge::syzygy::set_heap_loading(false);
        } else {
            std::cout << "SKIPPED: heap-copy pass (folder larger than 256 MB)\n";
        }
        if (forge::syzygy::load(tb).max_pieces >= 4) search_glue(tb);
        else std::cout << "SKIPPED: search glue checks (need the 3-4 piece tables)\n";
    }
    (void)forge::syzygy::load("");
    std::cout << "syzygy tests: " << g_checks << " checks, " << g_failures << " failures\n";
    return g_failures == 0 ? 0 : 1;
}
