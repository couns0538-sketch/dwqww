// Tests for the threat inputs of v2 networks (O6; UCI NNUEThreats; definition in forge/nnue_v2.hpp):
//   1. threat pairs == an independent brute-force reference (ray walking, no attack tables) on random positions,
//      including the two redundant pair kinds that are left out (king-king, attacks on the own king);
//   2. feature indices: explicit values, colour symmetry and mirror symmetry of threat-net accumulators;
//   3. loader: feature_set bit 0 files load (sizes, threat block), unknown feature bits and wrong sizes are rejected;
//   4. selection and the fail-loud rule for NNUEThreats (header bit and option must agree);
//   5. zero-threat lock replicas (lock weights + a threat block of zeros): accumulators and evaluations
//      bit-identical to the compiled-in net, and identical search node counts (the threat machinery changes nothing
//      when its columns are zero);
//   6. incremental == full refresh, bit-exact, over 102,000 random make/unmake plies driven through the real
//      Worker::static_evaluate with threat nets (1 bucket; 8 mirrored buckets; 4 unmirrored buckets);
//   7. UCI (when the engine executable is given): option advertised, unusable requests exit 2, a threat net is active.
// usage: forge_nnue_threat_tests [<forge executable>] [plies per walk net (default 34000)]
#include "forge/nnue_v2.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#if !defined(_WIN32)
#include <sys/wait.h>
#endif

#include "nnue_weights.inc"   // the compiled-in (lock) network, for the zero-threat replicas

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static int eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void move(Worker& w, SearchStack* ss, const Board& b, Move m) { w.record_move(ss, b, m); (ss + 1)->ply = ss->ply + 1; }
    static void null(Worker& w, SearchStack* ss) { w.record_null_move(ss); (ss + 1)->ply = ss->ply + 1; }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;
namespace v2 = forge::nnue::v2;

namespace {

int checks = 0;
int failures = 0;
void report(bool okay, const std::string& label) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << label << '\n';
}
void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) {
        ++failures;
        std::cout << "FAIL " << label << '\n';
    }
}

struct Rng {
    std::uint64_t s;
    std::uint64_t next() {
        s ^= s >> 12U; s ^= s << 25U; s ^= s >> 27U;
        return s * 2685821657736338717ULL;
    }
    int below(int n) { return static_cast<int>(next() % static_cast<std::uint64_t>(n)); }
    bool chance(int percent) { return below(100) < percent; }
};

std::vector<std::string> temporary_files;
void write_file(const std::string& path, const std::string& bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    if (std::find(temporary_files.begin(), temporary_files.end(), path) == temporary_files.end()) temporary_files.push_back(path);
}
std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream text;
    text << in.rdbuf();
    return text.str();
}
bool contains(const std::string& text, const std::string& what) { return text.find(what) != std::string::npos; }

// ---------------------------------------------------------------- v2 files (independent writer)
struct Spec {
    int king_buckets = 1;
    bool mirror = false;
    bool residual = true;
    bool threats = true;
    std::uint32_t feature_set_override = 0xFFFFFFFFU;   // write this feature_set instead (loader tests)
    std::array<std::uint8_t, 64> king_map{};
    std::vector<std::int16_t> w1, wt, b1, w2, b2;
};

std::uint64_t fnv(const std::string& data) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (const unsigned char c : data) { h ^= c; h *= 0x100000001b3ULL; }
    return h;
}
void put32(std::string& s, std::uint32_t v) { for (int i = 0; i < 4; ++i) s.push_back(static_cast<char>((v >> (8 * i)) & 0xFFU)); }
void putf(std::string& s, float f) { std::uint32_t v = 0; std::memcpy(&v, &f, 4); put32(s, v); }
void put16s(std::string& s, const std::vector<std::int16_t>& a) {
    for (const std::int16_t v : a) {
        const auto u = static_cast<std::uint16_t>(v);
        s.push_back(static_cast<char>(u & 0xFFU));
        s.push_back(static_cast<char>(u >> 8U));
    }
}

std::string serialise(const Spec& n) {
    std::string s = "FORGENN2";
    const std::uint32_t feature_set = n.feature_set_override != 0xFFFFFFFFU ? n.feature_set_override : (n.threats ? 1U : 0U);
    put32(s, 2); put32(s, 160); put32(s, feature_set); put32(s, 768); put32(s, nnue::HiddenSize);
    put32(s, static_cast<std::uint32_t>(n.king_buckets)); put32(s, 1); put32(s, (n.residual ? 1U : 0U) | (n.mirror ? 2U : 0U));
    putf(s, 4096.0F); putf(s, 4096.0F); putf(s, 2.25F);
    for (const std::uint8_t b : n.king_map) s.push_back(static_cast<char>(b));
    s.append(33, '\0');
    s.append(160 - s.size(), '\0');
    put16s(s, n.w1);
    if (n.threats) put16s(s, n.wt);
    put16s(s, n.b1);
    put16s(s, n.w2);
    put16s(s, n.b2);
    const std::uint64_t h = fnv(s);
    for (int i = 0; i < 8; ++i) s.push_back(static_cast<char>((h >> (8 * i)) & 0xFFU));
    return s;
}

int half_index(int square) { const int f = square & 7; return (square >> 3) * 4 + (f < 4 ? f : 7 - f); }
std::array<std::uint8_t, 64> symmetric_map(int buckets) {
    const char* rows4[8] = {"0011", "0011", "2222", "2222", "3333", "3333", "3333", "3333"};
    const char* rows8[8] = {"0123", "4455", "6666", "7777", "7777", "7777", "7777", "7777"};
    std::array<std::uint8_t, 64> m{};
    for (int s = 0; s < 64; ++s) {
        const int h = half_index(s);
        m[static_cast<std::size_t>(s)] = buckets == 1 ? 0 : static_cast<std::uint8_t>((buckets == 8 ? rows8 : rows4)[h / 4][h % 4] - '0');
    }
    return m;
}

Spec random_net(int buckets, bool mirror, bool threats, std::uint64_t seed) {
    Spec n;
    Rng rng{seed};
    n.king_buckets = buckets;
    n.mirror = mirror;
    n.threats = threats;
    n.king_map = symmetric_map(buckets);
    const std::size_t hidden = nnue::HiddenSize;
    auto value = [&rng](int range) { return static_cast<std::int16_t>(rng.below(2 * range + 1) - range); };
    n.w1.resize(static_cast<std::size_t>(buckets) * 768 * hidden);
    for (auto& v : n.w1) v = value(220);
    if (threats) {
        n.wt.resize(static_cast<std::size_t>(v2::ThreatFeatures) * hidden);
        for (auto& v : n.wt) v = value(120);
    }
    n.b1.resize(hidden);
    for (auto& v : n.b1) v = value(1200);
    n.w2.resize(2 * hidden);
    for (auto& v : n.w2) v = value(900);
    n.b2 = {value(500)};
    return n;
}

// Lock weights in v2 form (C4's replicas r1 / rm8) plus a threat block of zeros.
Spec zero_threat_replica(const std::string& kind) {
    Spec n;
    const std::size_t hidden = nnue::HiddenSize;
    std::vector<bool> flipped;
    if (kind == "r1") {
        n.king_buckets = 1;
        flipped = {false};
    } else {   // rm8: files e-h use their own buckets holding file-flipped weights (king-key changes happen)
        const char* rows4[8] = {"0011", "0011", "2222", "2222", "3333", "3333", "3333", "3333"};
        n.king_buckets = 8;
        n.mirror = true;
        for (int s = 0; s < 64; ++s) {
            const int h = half_index(s);
            n.king_map[static_cast<std::size_t>(s)] = static_cast<std::uint8_t>((rows4[h / 4][h % 4] - '0') + ((s & 7) >= 4 ? 4 : 0));
        }
        for (int b = 0; b < 8; ++b) flipped.push_back(b >= 4);
    }
    for (int b = 0; b < n.king_buckets; ++b) {
        for (std::size_t f = 0; f < 768; ++f) {
            const std::size_t src = flipped[static_cast<std::size_t>(b)] ? ((f & ~63U) | ((f & 63U) ^ 7U)) : f;
            n.w1.insert(n.w1.end(), NnueW1 + src * hidden, NnueW1 + (src + 1) * hidden);
        }
    }
    n.wt.assign(static_cast<std::size_t>(v2::ThreatFeatures) * hidden, 0);
    n.b1.assign(NnueB1, NnueB1 + hidden);
    n.w2.assign(NnueW2, NnueW2 + 2 * hidden);
    n.b2 = {NnueB2};
    n.residual = true;
    n.threats = true;
    return n;
}

bool load_spec(const std::string& path, const Spec& n) {
    write_file(path, serialise(n));
    std::string error;
    const bool ok = v2::load(path, &error);
    if (!ok) std::cout << "load error: " << error << '\n';
    return ok;
}

// ---------------------------------------------------------------- positions
Board position(const std::string& fen) {
    Board b;
    std::string error;
    if (!b.set_fen(fen, &error)) throw std::runtime_error(fen + ": " + error);
    return b;
}

const std::vector<std::string> start_fens = {
    std::string(Board::StandardStartFen),
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "8/8/4k3/8/2K5/8/3P4/8 w - - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "8/P7/8/8/8/8/p7/K6k w - - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
};

std::vector<Board> random_positions(int count, std::uint64_t seed) {
    std::vector<Board> out;
    Rng rng{seed};
    while (static_cast<int>(out.size()) < count) {
        Board b = position(start_fens[static_cast<std::size_t>(rng.below(static_cast<int>(start_fens.size())))]);
        const int plies = rng.below(80);
        for (int p = 0; p < plies; ++p) {
            const MoveList moves = b.legal_moves();
            if (moves.empty()) break;
            Undo undo;
            (void)b.make_move(moves[static_cast<std::size_t>(rng.below(static_cast<int>(moves.size())))], undo);
        }
        if (!b.legal_moves().empty()) out.push_back(b);
    }
    return out;
}

std::string transformed_fen(const Board& b, bool mirror_files, bool swap_colours) {
    std::ostringstream fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const int sq = swap_colours ? (7 - rank) * 8 + file : rank * 8 + (mirror_files ? 7 - file : file);
            const Piece p = b.piece_at(sq);
            if (p == Empty) { ++empty; continue; }
            if (empty) { fen << empty; empty = 0; }
            fen << (swap_colours ? " pnbrqkPNBRQK" : " PNBRQKpnbrqk")[static_cast<int>(p)];
        }
        if (empty) fen << empty;
        if (rank) fen << '/';
    }
    const bool white = b.side_to_move() == White;
    fen << ((white != swap_colours) ? " w - - 0 1" : " b - - 0 1");
    return fen.str();
}

nnue::Accumulator reference(const v2::Net& net, const Board& b) {
    nnue::Accumulator acc;
    v2::refresh(net, b, White, acc.values[White].data());
    v2::refresh(net, b, Black, acc.values[Black].data());
    acc.valid = true;
    return acc;
}
bool same_values(const nnue::Accumulator& a, const nnue::Accumulator& b) {
    return std::memcmp(a.values.data(), b.values.data(), sizeof(a.values)) == 0;
}

// ---------------------------------------------------------------- 1. threat pairs vs brute force
bool attacks_brute(int code, int s, int v, const std::array<int, 64>& board) {
    const int df = (v & 7) - (s & 7);
    const int dr = (v >> 3) - (s >> 3);
    const int type = (code - 1) % 6 + 1;
    const bool white = code <= 6;
    if (type == Pawn) return std::abs(df) == 1 && dr == (white ? 1 : -1);
    if (type == Knight) return (std::abs(df) == 1 && std::abs(dr) == 2) || (std::abs(df) == 2 && std::abs(dr) == 1);
    if (type == King) return std::max(std::abs(df), std::abs(dr)) == 1;
    const bool straight = (df == 0) != (dr == 0);
    const bool diagonal = df != 0 && std::abs(df) == std::abs(dr);
    if (!((type == Rook && straight) || (type == Bishop && diagonal) || (type == Queen && (straight || diagonal)))) return false;
    const int sf = (df > 0) - (df < 0);
    const int sr = (dr > 0) - (dr < 0);
    for (int f = (s & 7) + sf, r = (s >> 3) + sr; f != (v & 7) || r != (v >> 3); f += sf, r += sr) {
        if (board[static_cast<std::size_t>(r * 8 + f)] != 0) return false;
    }
    return true;
}

std::vector<int> brute_keys(const Board& b, int* excluded) {
    std::array<int, 64> board{};
    for (int s = 0; s < 64; ++s) board[static_cast<std::size_t>(s)] = static_cast<int>(b.piece_at(s));
    std::vector<int> keys;
    for (int s = 0; s < 64; ++s) {
        const int a = board[static_cast<std::size_t>(s)];
        if (a == 0) continue;
        for (int v = 0; v < 64; ++v) {
            const int c = board[static_cast<std::size_t>(v)];
            if (v == s || c == 0 || !attacks_brute(a, s, v, board)) continue;
            const bool victim_king = c == WK || c == BK;
            if (victim_king && ((a == WK || a == BK) || ((a <= 6) == (c <= 6)))) {
                ++*excluded;
                continue;
            }
            keys.push_back(((a - 1) * 12 + (c - 1)) * 64 + v);
        }
    }
    std::sort(keys.begin(), keys.end());
    return keys;
}

void test_pairs() {
    const std::vector<Board> boards = random_positions(3000, 101);
    int mismatches = 0;
    int excluded = 0;
    long pairs = 0;
    int most = 0;
    for (const Board& b : boards) {
        v2::ThreatList list;
        v2::threat_keys(v2::pieces_of(b), list);
        std::vector<int> mine(list.keys.begin(), list.keys.begin() + list.count);
        std::sort(mine.begin(), mine.end());
        if (mine != brute_keys(b, &excluded)) ++mismatches;
        pairs += list.count;
        most = std::max(most, list.count);
    }
    report(mismatches == 0 && excluded > 0, "threat pairs == brute-force reference on 3000 random positions (" + std::to_string(pairs) +
                                                " pairs, at most " + std::to_string(most) + " in one position, " +
                                                std::to_string(excluded) + " redundant king pairs left out)");
    // Explicit positions.
    auto keys_of = [](const std::string& fen) {
        v2::ThreatList list;
        v2::threat_keys(v2::pieces_of(position(fen)), list);
        return std::vector<int>(list.keys.begin(), list.keys.begin() + list.count);
    };
    auto key = [](int a, int b, int v) { return ((a - 1) * 12 + (b - 1)) * 64 + v; };
    {
        // White Ke1, Re2; Black Ke8, pawn e7: Re2 attacks e7 (its ray stops there: no x-ray to e8), Ke1 defends
        // Re2, Ke8 defends e7; Re2 seeing its own king on e1 is left out.
        std::vector<int> k = keys_of("4k3/4p3/8/8/8/8/4R3/4K3 w - - 0 1");
        std::sort(k.begin(), k.end());
        std::vector<int> expect = {key(WR, BP, 52), key(WK, WR, 12), key(BK, BP, 52)};
        std::sort(expect.begin(), expect.end());
        report(k == expect, "explicit: Re2 attacks e7 (ray stops), Ke1 defends Re2, Ke8 defends e7; Re2 -> own king left out");
    }
    {
        std::vector<int> k = keys_of("4k3/8/8/8/8/8/8/R3K2R w - - 0 1");
        report(k.empty(), "explicit: rooks that only see their own king give no pair");
    }
    {
        std::vector<int> k = keys_of("4k3/8/8/8/8/8/8/4R1K1 b - - 0 1");
        report(k.size() == 1 && k[0] == key(WR, BK, 60), "explicit: a check (Re1 attacks the black king on e8) is a pair");
    }
    {
        std::vector<int> k = keys_of("8/8/8/2n1n3/3P4/8/8/K6k w - - 0 1");
        std::sort(k.begin(), k.end());
        std::vector<int> expect = {key(WP, BN, 34), key(WP, BN, 36)};
        report(k == expect, "explicit: pawn d4 attacks both knights (c5, e5); the knights do not attack d4");
    }
    {
        std::vector<int> k = keys_of("8/8/8/8/8/2N1N3/8/K2r3k w - - 0 1");
        report(std::count(k.begin(), k.end(), key(WN, BR, 3)) == 2,
               "explicit: two knights attacking the rook on d1 give the same feature twice (pair count)");
    }
}

// ---------------------------------------------------------------- 2. feature indices and symmetry
void test_features(const std::string& dir) {
    const v2::KingKey none{0, 0};
    const v2::KingKey flipped{0, 7};
    auto key = [](int a, int b, int v) { return ((a - 1) * 12 + (b - 1)) * 64 + v; };
    report(v2::threat_feature(White, none, key(WN, BQ, 35)) == ((1 * 12 + 10) * 64 + 35),
           "feature: white knight attacks black queen on d5, White perspective = (1 * 12 + 10) * 64 + 35");
    report(v2::threat_feature(Black, none, key(WN, BQ, 35)) == ((7 * 12 + 4) * 64 + (35 ^ 56)),
           "feature: the same pair seen by Black = their knight (7) attacks own queen (4) on d5 ^ 56");
    report(v2::threat_feature(White, flipped, key(WP, BP, 36)) == ((0 * 12 + 6) * 64 + (36 ^ 7)),
           "feature: mirrored perspective flips the victim's file (e5 -> d5)");
    bool in_range = true;
    for (int pk = 0; pk < v2::ThreatFeatures; ++pk) {
        for (const Color p : {White, Black}) {
            for (const v2::KingKey k : {none, flipped}) {
                const int f = v2::threat_feature(p, k, pk);
                in_range = in_range && f >= 0 && f < v2::ThreatFeatures;
            }
        }
    }
    report(in_range, "feature: every pair key maps into [0, 9216) for both perspectives, with and without flip");
    const std::vector<Board> boards = random_positions(400, 111);
    check(load_spec(dir + "sym.fnn2", random_net(8, true, true, 113)), "load mirrored 8-bucket threat net");
    const v2::Net& net = *v2::loaded();
    int colour_bad = 0;
    int mirror_bad = 0;
    for (const Board& b : boards) {
        const nnue::Accumulator a = reference(net, b);
        const nnue::Accumulator c = reference(net, position(transformed_fen(b, false, true)));
        if (std::memcmp(a.values[White].data(), c.values[Black].data(), sizeof(float) * nnue::HiddenSize) != 0 ||
            std::memcmp(a.values[Black].data(), c.values[White].data(), sizeof(float) * nnue::HiddenSize) != 0) ++colour_bad;
        const nnue::Accumulator m = reference(net, position(transformed_fen(b, true, false)));
        if (!same_values(a, m)) ++mirror_bad;
    }
    report(colour_bad == 0, "colour symmetry: 400 colour-flipped positions give the swapped accumulators (threat net)");
    report(mirror_bad == 0, "mirror symmetry: 400 file-mirrored positions give identical accumulators (mirrored threat net)");
    check(load_spec(dir + "sym.fnn2", random_net(1, false, true, 113)), "load unmirrored threat net");
    int differ = 0;
    for (const Board& b : boards) {
        if (!same_values(reference(*v2::loaded(), b), reference(*v2::loaded(), position(transformed_fen(b, true, false))))) ++differ;
    }
    report(differ > 0, "control: without mirroring the file mirror changes the accumulators (" + std::to_string(differ) + "/400)");
    // The threat columns really enter the accumulator: zeroing them changes it.
    Spec with = random_net(1, false, true, 117);
    Spec without = with;
    std::fill(without.wt.begin(), without.wt.end(), 0);
    check(load_spec(dir + "sym.fnn2", with), "load threat net");
    std::vector<nnue::Accumulator> accs;
    for (int i = 0; i < 50; ++i) accs.push_back(reference(*v2::loaded(), boards[static_cast<std::size_t>(i)]));
    check(load_spec(dir + "sym.fnn2", without), "load the same net with zero threat columns");
    int changed = 0;
    int with_pairs = 0;
    int changed_without_pairs = 0;
    for (int i = 0; i < 50; ++i) {
        v2::ThreatList list;
        v2::threat_keys(v2::pieces_of(boards[static_cast<std::size_t>(i)]), list);
        const bool differs = !same_values(accs[static_cast<std::size_t>(i)], reference(*v2::loaded(), boards[static_cast<std::size_t>(i)]));
        with_pairs += list.count > 0 ? 1 : 0;
        changed += differs && list.count > 0 ? 1 : 0;
        changed_without_pairs += differs && list.count == 0 ? 1 : 0;
    }
    report(changed == with_pairs && changed_without_pairs == 0 && with_pairs >= 25,
           "control: zeroing the threat columns changes exactly the accumulators of the positions with threat pairs (" +
               std::to_string(changed) + "/" + std::to_string(with_pairs) + " of 50 positions have pairs)");
}

// ---------------------------------------------------------------- 3. loader
void test_loader(const std::string& dir) {
    const Spec good = random_net(1, false, true, 121);
    const std::string bytes = serialise(good);
    write_file(dir + "loader.fnn2", bytes);
    std::string error;
    report(v2::load(dir + "loader.fnn2", &error) && v2::loaded()->threats && v2::describe(*v2::loaded()).threats,
           "a feature_set 1 file loads with its threat block");
    report(bytes.size() == v2::file_bytes(1, 1, v2::FeatureSetThreats) &&
               v2::file_bytes(1, 1, v2::FeatureSetThreats) - v2::file_bytes(1, 1) == 2U * v2::ThreatFeatures * nnue::HiddenSize,
           "file_bytes: the threat block adds 2 * 9216 * hidden bytes (" + std::to_string(bytes.size()) + " bytes)");
    bool block_ok = true;
    for (std::size_t i = 0; i < good.wt.size(); i += 997) {
        block_ok = block_ok && v2::loaded()->wt.data()[i] == static_cast<float>(good.wt[i]) / 4096.0F;
    }
    report(block_ok, "the threat block is read in file order (sampled values == int16 / 4096)");
    auto rejected = [&](const Spec& spec, const std::string& label, const std::string& phrase) {
        write_file(dir + "bad.fnn2", serialise(spec));
        std::string message;
        const bool loaded = v2::load(dir + "bad.fnn2", &message);
        report(!loaded && contains(message, phrase) && v2::loaded() == nullptr, "rejects " + label + " (" + message + ")");
    };
    Spec unknown = good;
    unknown.feature_set_override = 3;
    rejected(unknown, "feature_set 3 (unknown bit 1)", "unsupported feature set 3");
    Spec no_block = good;
    no_block.feature_set_override = 1;
    no_block.threats = false;   // header says threats, no block written
    rejected(no_block, "a feature_set 1 header without the threat block", "does not match");
    Spec extra_block = good;
    extra_block.feature_set_override = 0;   // block written, header says none
    rejected(extra_block, "a threat block under a feature_set 0 header", "does not match");
}

// ---------------------------------------------------------------- 4. selection and request rule
std::string problem_after(int king_buckets, int threats, const std::string& file) {
    options::nnue_king_buckets = king_buckets;
    options::nnue_threats = threats;
    (void)options::apply_nnue_v2(nullptr);
    return options::nnue_v2_problem(file, "");
}

void test_rules(const std::string& dir) {
    const std::string t1 = dir + "t1.fnn2";
    const std::string p1 = dir + "p1.fnn2";
    const std::string t4 = dir + "t4.fnn2";
    v2::unload();
    std::string p = problem_after(0, 0, "");
    report(p.empty() && !options::nnue_v2, "defaults: no request, no problem");
    p = problem_after(0, 1, "");
    report(contains(p, "NNUEThreats is 1 but no v2 net is loaded") && !options::nnue_v2, "NNUEThreats without NNUEFile: " + p);
    check(load_spec(t1, random_net(1, false, true, 131)), "load a one-bucket threat net");
    p = problem_after(0, 1, t1);
    report(p.empty() && options::nnue_v2 && v2::active()->threats, "NNUEThreats 1 with a one-bucket threat net (NNUEKingBuckets 0): active");
    p = problem_after(1, 1, t1);
    report(p.empty() && options::nnue_v2, "NNUEThreats 1 + NNUEKingBuckets 1: active");
    p = problem_after(0, 0, t1);
    report(contains(p, "has threat inputs") && contains(p, "set NNUEThreats 1") && !options::nnue_v2, "threat net without NNUEThreats: " + p);
    p = problem_after(1, 0, t1);
    report(contains(p, "has threat inputs") && !options::nnue_v2, "threat net, NNUEKingBuckets 1, NNUEThreats 0: " + p);
    check(load_spec(p1, random_net(1, false, false, 132)), "load a one-bucket net without threat inputs");
    p = problem_after(0, 1, p1);
    report(contains(p, "has no threat inputs") && !options::nnue_v2, "NNUEThreats 1 with a net without threat inputs: " + p);
    p = problem_after(1, 0, p1);
    report(p.empty() && options::nnue_v2 && !v2::active()->threats, "C4 rule unchanged: a net without threats, NNUEKingBuckets 1: active");
    check(load_spec(t4, random_net(4, true, true, 133)), "load a mirrored 4-bucket threat net");
    p = problem_after(0, 1, t4);
    report(contains(p, "set NNUEKingBuckets 4 as well") && !options::nnue_v2, "NNUEThreats alone with a 4-bucket threat net: " + p);
    p = problem_after(4, 1, t4);
    report(p.empty() && options::nnue_v2, "NNUEThreats 1 + NNUEKingBuckets 4: active");
    p = problem_after(2, 1, t4);
    report(contains(p, "does not match") && !options::nnue_v2, "NNUEKingBuckets 2 vs the 4-bucket threat net: " + p);
    nnue::enabled = false;
    p = problem_after(4, 1, t4);
    report(p.empty() && !options::nnue_v2, "UseNNUE false wins over NNUEThreats (not an error)");
    nnue::enabled = true;
    v2::unload();
    p = problem_after(0, 0, "");
    report(p.empty() && !options::nnue_v2, "request cleared: no problem");
}

// ---------------------------------------------------------------- 5. zero-threat lock replicas
std::uint64_t search_nodes(const Board& b, int depth, std::string* best) {
    Searcher searcher(16, 1);
    SearchLimits limits;
    limits.depth = depth;
    const SearchInfo info = searcher.search(b, limits, false, Searcher::TTAccess::Exclusive);
    if (best != nullptr) *best = Board::move_to_uci(info.best_move);
    return info.nodes;
}

void test_zero_threat_replicas(const std::string& dir) {
    const std::vector<Board> boards = random_positions(300, 141);
    std::vector<std::pair<std::uint64_t, std::string>> lock_search;
    for (int i = 0; i < 4; ++i) {
        std::string best;
        const std::uint64_t nodes = search_nodes(position(start_fens[static_cast<std::size_t>(i * 2 + 1)]), 8, &best);
        lock_search.emplace_back(nodes, best);
    }
    for (const std::string kind : {"r1", "rm8"}) {
        const Spec n = zero_threat_replica(kind);
        check(load_spec(dir + "replica.fnn2", n), "load zero-threat replica " + kind);
        options::nnue_king_buckets = n.king_buckets;
        options::nnue_threats = 1;
        check(options::apply_nnue_v2(nullptr) && v2::active()->threats, "select zero-threat replica " + kind);
        const v2::Net& net = *v2::active();
        int bad = 0;
        for (const Board& b : boards) {
            nnue::Accumulator lock;
            nnue::refresh(b, lock);
            const nnue::Accumulator mine = reference(net, b);
            if (!same_values(lock, mine) || nnue::evaluate(b, lock) != v2::evaluate(net, b, mine)) ++bad;
        }
        report(bad == 0, "zero-threat replica " + kind + ": 300 positions, accumulators and evals bit-identical to the compiled-in net");
        bool same = true;
        for (int i = 0; i < 4; ++i) {
            std::string best;
            const std::uint64_t nodes = search_nodes(position(start_fens[static_cast<std::size_t>(i * 2 + 1)]), 8, &best);
            same = same && nodes == lock_search[static_cast<std::size_t>(i)].first && best == lock_search[static_cast<std::size_t>(i)].second;
        }
        report(same, "zero-threat replica " + kind + ": depth-8 searches of 4 positions have the compiled-in net's node counts and best moves");
        options::nnue_king_buckets = 0;
        options::nnue_threats = 0;
        (void)options::apply_nnue_v2(nullptr);
    }
}

// ---------------------------------------------------------------- 6. incremental == refresh, 100k plies
struct WalkStats {
    long plies = 0, nulls = 0, evals = 0, verified = 0, key_changes = 0, restarts = 0, max_chain = 0, max_pairs = 0;
};

void walk(Worker& w, const v2::Net& net, std::uint64_t seed, long target_plies, WalkStats& st, int& bad) {
    Rng rng{seed};
    constexpr int MaxDepth = 24;
    while (st.plies < target_plies) {
        Board board = position(start_fens[static_cast<std::size_t>(rng.below(static_cast<int>(start_fens.size())))]);
        ++st.restarts;
        w.clear();
        SearchLimits limits;
        limits.depth = 1;
        const std::vector<Worker*> all{&w};
        (void)w.search(board, limits, false, all);
        SearchStack* root = Probe::root(w);
        std::vector<Board> path{board};
        struct Step { bool null; Move move; Undo undo; NullUndo null_undo; };
        std::vector<Step> steps;
        int depth = 0;
        const int length = 200 + rng.below(400);
        for (int t = 0; t < length && st.plies < target_plies; ++t) {
            SearchStack* ss = root + depth;
            if (depth < MaxDepth && (depth == 0 || rng.chance(58))) {
                const MoveList moves = board.legal_moves();
                if (moves.empty()) continue;
                Step step{};
                if (!board.in_check() && rng.chance(4)) {
                    step.null = true;
                    Probe::null(w, ss);
                    board.make_null_move(step.null_undo);
                    ++st.nulls;
                } else {
                    step.move = moves[static_cast<std::size_t>(rng.below(static_cast<int>(moves.size())))];
                    const Piece moved = board.piece_at(step.move.from);
                    if (piece_type(moved) == King) {
                        const Color c = color_of(moved);
                        if (!(v2::king_key(net, c, step.move.from) == v2::king_key(net, c, step.move.to))) ++st.key_changes;
                    }
                    Probe::move(w, ss, board, step.move);
                    (void)board.make_move(step.move, step.undo);
                }
                steps.push_back(step);
                path.push_back(board);
                ++depth;
                ++st.plies;
                v2::ThreatList list;
                v2::threat_keys(v2::pieces_of(board), list);
                st.max_pairs = std::max<long>(st.max_pairs, list.count);
                if (rng.chance(45)) {
                    std::vector<bool> was_valid(static_cast<std::size_t>(depth + 1));
                    for (int j = 0; j <= depth; ++j) was_valid[static_cast<std::size_t>(j)] = (root + j)->accumulator.valid;
                    const int actual = Probe::eval(w, board, root + depth);
                    ++st.evals;
                    long chain = 0;
                    for (int j = 0; j <= depth; ++j) {
                        SearchStack* e = root + j;
                        if (!e->accumulator.valid || was_valid[static_cast<std::size_t>(j)]) continue;
                        ++chain;
                        ++st.verified;
                        if (!same_values(e->accumulator, reference(net, path[static_cast<std::size_t>(j)]))) ++bad;
                    }
                    st.max_chain = std::max(st.max_chain, chain);
                    const int expected = std::clamp(Evaluator::evaluate_uncached(board) + v2::evaluate(net, board, reference(net, board)),
                                                    -MateInMaxPly + 1, MateInMaxPly - 1);
                    if (actual != expected || !(root + depth)->accumulator.valid) ++bad;
                }
            } else if (depth > 0) {
                const Step& step = steps.back();
                if (step.null) board.unmake_null_move(step.null_undo);
                else board.unmake_move(step.move, step.undo);
                steps.pop_back();
                path.pop_back();
                --depth;
                if (rng.chance(30)) {
                    const int actual = Probe::eval(w, board, root + depth);
                    const nnue::Accumulator ref = reference(net, board);
                    const int expected = std::clamp(Evaluator::evaluate_uncached(board) + v2::evaluate(net, board, ref),
                                                    -MateInMaxPly + 1, MateInMaxPly - 1);
                    ++st.evals;
                    if (actual != expected || !same_values((root + depth)->accumulator, ref)) ++bad;
                }
            }
        }
    }
}

void test_incremental_equals_refresh(const std::string& dir, long plies_per_net) {
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    struct Case { const char* name; int buckets; bool mirror; };
    const std::vector<Case> cases = {
        {"1 bucket, threat inputs", 1, false},
        {"8 mirrored buckets, threat inputs", 8, true},
        {"4 unmirrored buckets, threat inputs", 4, false},
    };
    long total = 0;
    std::uint64_t seed = 151;
    for (const Case& c : cases) {
        Spec n = random_net(c.buckets, c.mirror, true, seed);
        if (!c.mirror) n.king_map = symmetric_map(c.buckets);
        check(load_spec(dir + "walk.fnn2", n), std::string("load ") + c.name);
        options::nnue_king_buckets = c.buckets;
        options::nnue_threats = 1;
        check(options::apply_nnue_v2(nullptr), std::string("select ") + c.name);
        WalkStats st;
        int bad = 0;
        walk(*worker, *v2::active(), seed * 7919U, plies_per_net, st, bad);
        total += st.plies;
        std::cout << "WALK " << c.name << ": plies " << st.plies << " (null " << st.nulls << ") evaluations " << st.evals
                  << " computed accumulators verified " << st.verified << " king-key changes " << st.key_changes
                  << " longest replay " << st.max_chain << " most threat pairs " << st.max_pairs << " restarts " << st.restarts
                  << " mismatches " << bad << '\n';
        report(bad == 0 && st.max_chain >= 3 && (c.buckets == 1 || st.key_changes * 50 > st.plies),
               std::string("incremental == full refresh, bit-exact, ") + c.name + ": " + std::to_string(st.plies) + " plies");
        ++seed;
    }
    std::cout << "WALK total plies " << total << '\n';
    options::nnue_king_buckets = 0;
    options::nnue_threats = 0;
    (void)options::apply_nnue_v2(nullptr);
}

// ---------------------------------------------------------------- 7. UCI
struct Run {
    std::string out;
    int status = -1;
};
std::string quote(const std::string& text) { return "\"" + text + "\""; }
Run run_engine(const std::string& engine, const std::string& name, const std::string& script) {
    const std::string in = "nnue_threat_uci_" + name + ".in";
    const std::string out = "nnue_threat_uci_" + name + ".out";
    write_file(in, script);
    temporary_files.push_back(out);
    std::string command = quote(engine) + " < " + quote(in) + " > " + quote(out);
#if defined(_WIN32)
    command = "\"" + command + "\"";
#endif
    std::fflush(nullptr);
    const int raw = std::system(command.c_str());
    Run run;
#if defined(_WIN32)
    run.status = raw;
#else
    run.status = WIFEXITED(raw) ? WEXITSTATUS(raw) : 128 + (WIFSIGNALED(raw) ? WTERMSIG(raw) : 0);
#endif
    run.out = read_file(out);
    return run;
}
int count(const std::string& text, const std::string& what) {
    int n = 0;
    for (std::size_t at = text.find(what); at != std::string::npos; at = text.find(what, at + what.size())) ++n;
    return n;
}
bool has_line(const std::string& text, const std::string& prefix) {
    std::istringstream lines(text);
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind(prefix, 0) == 0) return true;
    }
    return false;
}
std::string last_error(const std::string& text) {
    std::istringstream lines(text);
    std::string last = "(no ERROR line)";
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind("info string ERROR NNUE v2:", 0) == 0) last = line;
    }
    return last;
}
const std::string Head = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n";
std::string set(const std::string& name, const std::string& value) { return "setoption name " + name + " value " + value + "\n"; }
void expect_failure(const std::string& engine, const std::string& name, const std::string& options, const std::string& trigger,
                    const std::string& phrase) {
    const Run r = run_engine(engine, name, Head + options + trigger + "\nquit\n");
    const bool no_answer = !has_line(r.out, "readyok") && !has_line(r.out, "bestmove") && !contains(r.out, "bench depth");
    report(r.status == 2 && count(r.out, "info string ERROR NNUE v2: ") >= 2 && no_answer && contains(last_error(r.out), phrase),
           "UCI " + name + ": exit status " + std::to_string(r.status) + " at " + trigger + (no_answer ? ", no answer: " : ", ANSWERED: ") +
               last_error(r.out));
}

void test_uci(const std::string& engine, const std::string& dir) {
    const std::string threat = dir + "uci_threat.fnn2";
    const std::string plain = dir + "uci_plain.fnn2";
    write_file(threat, serialise(random_net(1, false, true, 161)));
    write_file(plain, serialise(random_net(1, false, false, 161)));
    {
        const Run r = run_engine(engine, "defaults", Head + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && contains(r.out, "option name NNUEThreats type spin default 0 min 0 max 1") && has_line(r.out, "readyok") &&
                   has_line(r.out, "bestmove") && !contains(r.out, "NNUE v2"),
               "UCI defaults: NNUEThreats advertised (spin 0-1, default 0), nothing NNUE v2 printed, exit 0");
    }
    expect_failure(engine, "threats_without_file", set("NNUEThreats", "1"), "isready", "no v2 net is loaded");
    expect_failure(engine, "threats_with_plain_net", set("NNUEFile", plain) + set("NNUEThreats", "1"), "go depth 1", "has no threat inputs");
    expect_failure(engine, "threat_net_without_option", set("NNUEFile", threat) + set("NNUEKingBuckets", "1"), "bench 2", "set NNUEThreats 1");
    {
        const std::string active = "info string NNUE v2: active: " + threat + " king buckets 1 output buckets 1 hidden " +
                                   std::to_string(nnue::HiddenSize) + " unmirrored residual threat inputs";
        const Run r = run_engine(engine, "threats_active", Head + set("NNUEThreats", "1") + set("NNUEFile", threat) +
                                                              "isready\ngo depth 5\nbench 3\nquit\n");
        report(r.status == 0 && count(r.out, active) == 2 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") &&
                   contains(r.out, "bench depth 3 nodes") && count(r.out, "ERROR") == 1,
               "UCI NNUEThreats 1 + threat net: \"" + active + " ...\" (activation + isready), readyok, bestmove, bench, exit 0 "
               "(the half-set request before NNUEFile reported once)");
    }
    {
        const Run r = run_engine(engine, "threats_invalid", Head + set("NNUEThreats", "2") + "isready\nquit\n");
        report(r.status == 0 && contains(r.out, "info string invalid value for option NNUEThreats") && has_line(r.out, "readyok"),
               "UCI NNUEThreats 2: invalid value reported, the option stays 0");
    }
}

} // namespace

int main(int argc, char** argv) {
    const std::string engine = argc > 1 ? argv[1] : "";
    const long plies = argc > 2 ? std::stol(argv[2]) : 34000;
    const std::string dir = "nnue_threat_test_";
    test_pairs();
    test_features(dir);
    test_loader(dir);
    test_rules(dir);
    test_zero_threat_replicas(dir);
    test_incremental_equals_refresh(dir, plies);
    if (!engine.empty()) {
        std::string path = engine;
#if defined(_WIN32)
        for (char& c : path) if (c == '/') c = '\\';
#endif
        test_uci(path, dir);
    } else {
        std::cout << "(no engine executable given: UCI tests skipped)\n";
    }
    v2::unload();
    for (const std::string& file : temporary_files) std::remove(file.c_str());
    std::cout << checks - failures << "/" << checks << " checks passed\n";
    return failures == 0 ? 0 : 1;
}
