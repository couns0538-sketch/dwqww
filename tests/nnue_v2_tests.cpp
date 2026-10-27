// Tests for the v2 network path (C4, forge/nnue_v2.hpp; UCI NNUEFile + NNUEKingBuckets):
//   1. king bucket map and horizontal mirroring (king_key, feature indices, mirror and colour symmetry);
//   2. the v2 file loader (valid file, every rejected corruption, failed load keeps the old net);
//   3. option selection (bucket count must match, UseNNUE false wins, unload deactivates);
//   4. exact equivalence with the compiled-in network: replicas of it (1, 4, 2/8/16 mirrored king buckets)
//      give bit-identical accumulators and evaluations, and identical search node counts;
//   5. incremental == full refresh, bit-exact, over 100k random make/unmake plies driven through the
//      real Worker::static_evaluate (lazy walk-back, king-key refreshes through the refresh cache).
// Writes temporary net files next to the working directory (removed at the end).
#include "forge/nnue_v2.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "nnue_weights.inc"   // the compiled-in (lock) network, for the replica tests

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
void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) {
        ++failures;
        std::cout << "FAIL " << label << '\n';
    }
}
void report(bool okay, const std::string& label) {
    check(okay, label);
    if (okay) std::cout << "PASS " << label << '\n';
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

// ---------------------------------------------------------------- v2 files (independent writer)
struct Spec {
    int king_buckets = 1;
    bool mirror = false;
    bool residual = true;
    std::array<std::uint8_t, 64> king_map{};
    std::vector<std::int16_t> w1, b1, w2, b2;
};

std::uint64_t fnv(const std::string& data) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (const unsigned char c : data) { h ^= c; h *= 0x100000001b3ULL; }
    return h;
}
void put32(std::string& s, std::uint32_t v) { for (int i = 0; i < 4; ++i) s.push_back(static_cast<char>((v >> (8 * i)) & 0xFFU)); }
void putf(std::string& s, float f) { std::uint32_t v = 0; std::memcpy(&v, &f, 4); put32(s, v); }

std::string serialise(const Spec& n) {
    std::string s = "FORGENN2";
    put32(s, 2); put32(s, 160); put32(s, 0); put32(s, 768); put32(s, nnue::HiddenSize);
    put32(s, static_cast<std::uint32_t>(n.king_buckets)); put32(s, 1); put32(s, (n.residual ? 1U : 0U) | (n.mirror ? 2U : 0U));
    putf(s, 4096.0F); putf(s, 4096.0F); putf(s, 2.25F);
    for (const std::uint8_t b : n.king_map) s.push_back(static_cast<char>(b));
    s.append(33, '\0');
    s.append(160 - s.size(), '\0');
    for (const auto* a : {&n.w1, &n.b1, &n.w2, &n.b2}) {
        for (const std::int16_t v : *a) {
            const auto u = static_cast<std::uint16_t>(v);
            s.push_back(static_cast<char>(u & 0xFFU));
            s.push_back(static_cast<char>(u >> 8U));
        }
    }
    const std::uint64_t h = fnv(s);
    for (int i = 0; i < 8; ++i) s.push_back(static_cast<char>((h >> (8 * i)) & 0xFFU));
    return s;
}
void write_file(const std::string& path, const std::string& bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
}
void write_spec(const std::string& path, const Spec& n) { write_file(path, serialise(n)); }

// Standard half-board layouts of tools/nnue/forge_nnue_v2.py (files a-d after mirroring, ranks 1-8).
std::array<int, 32> half_layout(int buckets) {
    std::array<int, 32> h{};
    const char* rows4[8] = {"0011", "0011", "2222", "2222", "3333", "3333", "3333", "3333"};
    const char* rows8[8] = {"0123", "4455", "6666", "7777", "7777", "7777", "7777", "7777"};
    const char* rows1[8] = {"0000", "0000", "0000", "0000", "0000", "0000", "0000", "0000"};
    const char** rows = buckets == 8 ? rows8 : buckets == 4 ? rows4 : rows1;
    for (int r = 0; r < 8; ++r) for (int f = 0; f < 4; ++f) h[static_cast<std::size_t>(r * 4 + f)] = rows[r][f] - '0';
    if (buckets == 32) for (int i = 0; i < 32; ++i) h[static_cast<std::size_t>(i)] = i;
    return h;
}
int half_index(int square) { const int f = square & 7; return (square >> 3) * 4 + (f < 4 ? f : 7 - f); }
std::array<std::uint8_t, 64> symmetric_map(int buckets) {
    std::array<std::uint8_t, 64> m{};
    const auto h = half_layout(buckets);
    for (int s = 0; s < 64; ++s) m[static_cast<std::size_t>(s)] = static_cast<std::uint8_t>(h[static_cast<std::size_t>(half_index(s))]);
    return m;
}

Spec lock_replica(const std::string& kind) {
    Spec n;
    const std::size_t hidden = nnue::HiddenSize;
    std::vector<bool> flipped;
    if (kind == "r1") { n.king_buckets = 1; flipped = {false}; }
    else if (kind == "r4") { n.king_buckets = 4; n.king_map = symmetric_map(4); flipped.assign(4, false); }
    else {   // rm2 / rm8 / rm16: files e-h use their own buckets holding file-flipped weights
        const int base = kind == "rm2" ? 1 : kind == "rm8" ? 4 : 8;
        const auto h = half_layout(base);
        n.king_buckets = 2 * base;
        n.mirror = true;
        for (int s = 0; s < 64; ++s) {
            n.king_map[static_cast<std::size_t>(s)] = static_cast<std::uint8_t>(h[static_cast<std::size_t>(half_index(s))] + ((s & 7) >= 4 ? base : 0));
        }
        for (int b = 0; b < n.king_buckets; ++b) flipped.push_back(b >= base);
    }
    for (int b = 0; b < n.king_buckets; ++b) {
        for (std::size_t f = 0; f < 768; ++f) {
            const std::size_t src = flipped[static_cast<std::size_t>(b)] ? ((f & ~63U) | ((f & 63U) ^ 7U)) : f;
            n.w1.insert(n.w1.end(), NnueW1 + src * hidden, NnueW1 + (src + 1) * hidden);
        }
    }
    n.b1.assign(NnueB1, NnueB1 + hidden);
    n.w2.assign(NnueW2, NnueW2 + 2 * hidden);
    n.b2 = {NnueB2};
    n.residual = true;
    return n;
}

Spec random_net(int buckets, bool mirror, const std::array<std::uint8_t, 64>& map, std::uint64_t seed) {
    Spec n;
    Rng rng{seed};
    n.king_buckets = buckets;
    n.mirror = mirror;
    n.king_map = map;
    const std::size_t hidden = nnue::HiddenSize;
    auto value = [&rng](int range) { return static_cast<std::int16_t>(rng.below(2 * range + 1) - range); };
    n.w1.resize(static_cast<std::size_t>(buckets) * 768 * hidden);
    for (auto& v : n.w1) v = value(220);
    n.b1.resize(hidden);
    for (auto& v : n.b1) v = value(1200);
    n.w2.resize(2 * hidden);
    for (auto& v : n.w2) v = value(900);
    n.b2 = {value(500)};
    return n;
}

bool load_spec(const std::string& path, const Spec& n) {
    write_spec(path, n);
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

// Positions along random games (for the symmetry and replica tests).
std::vector<Board> random_positions(int count, std::uint64_t seed) {
    std::vector<Board> out;
    Rng rng{seed};
    while (static_cast<int>(out.size()) < count) {
        Board b = position(start_fens[static_cast<std::size_t>(rng.below(static_cast<int>(start_fens.size())))]);
        const int plies = rng.below(60);
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

// FEN with every piece mirrored horizontally (files a<->h); no castling rights.
std::string mirror_files_fen(const Board& b) {
    std::ostringstream fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const Piece p = b.piece_at(rank * 8 + (7 - file));
            if (p == Empty) { ++empty; continue; }
            if (empty) { fen << empty; empty = 0; }
            fen << " PNBRQKpnbrqk"[static_cast<int>(p)];
        }
        if (empty) fen << empty;
        if (rank) fen << '/';
    }
    fen << (b.side_to_move() == White ? " w - - 0 1" : " b - - 0 1");
    return fen.str();
}

// FEN with colours swapped and ranks mirrored (the same position for the other side); no castling.
std::string colour_flip_fen(const Board& b) {
    std::ostringstream fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const Piece p = b.piece_at((7 - rank) * 8 + file);
            if (p == Empty) { ++empty; continue; }
            if (empty) { fen << empty; empty = 0; }
            fen << " pnbrqkPNBRQK"[static_cast<int>(p)];
        }
        if (empty) fen << empty;
        if (rank) fen << '/';
    }
    fen << (b.side_to_move() == White ? " b - - 0 1" : " w - - 0 1");
    return fen.str();
}

// Reference accumulator from scratch and the evaluation oracle.
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

// ---------------------------------------------------------------- 1. bucket map and mirroring
void test_bucket_map_and_mirroring(const std::string& dir) {
    // Asymmetric map with 32 buckets: bucket = (7 * s + 3) % 32 for every perspective-relative square.
    Spec n = random_net(32, true, {}, 11);
    for (int s = 0; s < 64; ++s) n.king_map[static_cast<std::size_t>(s)] = static_cast<std::uint8_t>((7 * s + 3) % 32);
    check(load_spec(dir + "map.fnn2", n), "load 32-bucket mirrored net");
    const v2::Net& net = *v2::loaded();
    int bad = 0;
    for (const Color p : {White, Black}) {
        for (int k = 0; k < 64; ++k) {
            const int rel = p == White ? k : k ^ 56;
            const v2::KingKey key = v2::king_key(net, p, k);
            if (key.bucket != (7 * rel + 3) % 32) ++bad;
            if (key.flip != ((rel & 7) >= 4 ? 7 : 0)) ++bad;
        }
    }
    report(bad == 0, "king_key: bucket = map[relative king square] and flip = 7 exactly on files e-h, both perspectives, 64 squares");
    n.mirror = false;
    check(load_spec(dir + "map.fnn2", n), "load 32-bucket unmirrored net");
    bad = 0;
    for (const Color p : {White, Black}) for (int k = 0; k < 64; ++k) if (v2::king_key(*v2::loaded(), p, k).flip != 0) ++bad;
    report(bad == 0, "king_key: no flip without the mirror flag");

    // Explicit feature indices.
    report(v2::feature(White, {0, 0}, WP, 8) == 8, "feature: white pawn a2, white perspective, bucket 0 = 8");
    report(v2::feature(White, {0, 0}, BK, 60) == (1 * 6 + 5) * 64 + 60, "feature: black king e8, white perspective = 764");
    report(v2::feature(Black, {0, 0}, BP, 48) == 8, "feature: black pawn a7 seen by black = own pawn on a2 = 8");
    report(v2::feature(Black, {0, 0}, WK, 4) == (1 * 6 + 5) * 64 + 60, "feature: white king e1 seen by black = 764");
    report(v2::feature(White, {3, 7}, WN, 6) == 3 * 768 + 64 + 1, "feature: bucket 3, flipped: white knight g1 -> b1 = 2369");
    report(v2::feature(Black, {5, 7}, BQ, 59) == 5 * 768 + 4 * 64 + ((59 ^ 56) ^ 7), "feature: bucket 5, flipped, black perspective: black queen d8 -> e1");
    bool v1_equal = true;
    for (const Color p : {White, Black}) {
        for (int pc = WP; pc <= BK; ++pc) {
            for (int s = 0; s < 64; ++s) {
                v1_equal = v1_equal && v2::feature(p, {0, 0}, static_cast<Piece>(pc), s) == nnue::feature_index(p, static_cast<Piece>(pc), s);
            }
        }
    }
    report(v1_equal, "feature: bucket 0 without flip equals the compiled-in feature_index for all 1536 inputs");

    // Standard layouts (tools/nnue/forge_nnue_v2.py): spot checks of the symmetric 4- and 8-bucket maps.
    const auto m4 = symmetric_map(4);
    const auto m8 = symmetric_map(8);
    report(m4[6] == 0 && m4[1] == 0 && m4[4] == 1 && m4[3] == 1 && m4[27] == 2 && m4[36] == 3 && m4[63] == 3,
           "layout 4: g1,b1 -> 0; e1,d1 -> 1; d4 -> 2; e5 -> 3; h8 -> 3");
    report(m8[0] == 0 && m8[7] == 0 && m8[6] == 1 && m8[5] == 2 && m8[4] == 3 && m8[9] == 4 && m8[12] == 5 && m8[20] == 6 && m8[63] == 7,
           "layout 8: a1,h1 -> 0; g1 -> 1; f1 -> 2; e1 -> 3; b2 -> 4; e2 -> 5; e3 -> 6; h8 -> 7");
    bool symmetric = true;
    for (int s = 0; s < 64; ++s) symmetric = symmetric && m4[static_cast<std::size_t>(s)] == m4[static_cast<std::size_t>(s ^ 7)] &&
                                                m8[static_cast<std::size_t>(s)] == m8[static_cast<std::size_t>(s ^ 7)];
    report(symmetric, "standard layouts are file-symmetric (map[s] == map[s ^ 7])");

    // Mirror symmetry: a mirrored net with a symmetric map sees a position and its file mirror identically.
    const std::vector<Board> boards = random_positions(400, 21);
    check(load_spec(dir + "mirror.fnn2", random_net(8, true, symmetric_map(8), 31)), "load mirrored 8-bucket net");
    int mismatches = 0;
    int differing_plain = 0;
    for (const Board& b : boards) {
        const Board m = position(mirror_files_fen(b));
        const nnue::Accumulator a = reference(*v2::loaded(), b);
        const nnue::Accumulator c = reference(*v2::loaded(), m);
        if (!same_values(a, c) || v2::evaluate(*v2::loaded(), b, a) != v2::evaluate(*v2::loaded(), m, c)) ++mismatches;
    }
    report(mismatches == 0, "mirror symmetry: 400 positions and their file mirrors give bit-identical accumulators and evals (mirrored net)");
    check(load_spec(dir + "plain.fnn2", random_net(8, false, symmetric_map(8), 31)), "load unmirrored 8-bucket net");
    for (const Board& b : boards) {
        const Board m = position(mirror_files_fen(b));
        if (v2::evaluate(*v2::loaded(), b, reference(*v2::loaded(), b)) != v2::evaluate(*v2::loaded(), m, reference(*v2::loaded(), m))) ++differing_plain;
    }
    report(differing_plain > 0, "control: without mirroring the file mirror changes the evaluation (" + std::to_string(differing_plain) + "/400)");

    // Colour symmetry: both perspectives share the weights, so the colour-flipped position evaluates the same.
    check(load_spec(dir + "mirror.fnn2", random_net(8, true, symmetric_map(8), 31)), "reload mirrored 8-bucket net");
    mismatches = 0;
    for (const Board& b : boards) {
        const Board f = position(colour_flip_fen(b));
        const nnue::Accumulator a = reference(*v2::loaded(), b);
        const nnue::Accumulator c = reference(*v2::loaded(), f);
        if (std::memcmp(a.values[White].data(), c.values[Black].data(), sizeof(float) * nnue::HiddenSize) != 0 ||
            v2::evaluate(*v2::loaded(), b, a) != v2::evaluate(*v2::loaded(), f, c)) ++mismatches;
    }
    report(mismatches == 0, "colour symmetry: 400 colour-flipped positions give the swapped accumulators and the same eval");
}

// ---------------------------------------------------------------- 2. loader
void test_loader(const std::string& dir) {
    const Spec good = random_net(4, true, symmetric_map(4), 41);
    const std::string bytes = serialise(good);
    const std::string path = dir + "loader.fnn2";
    write_file(path, bytes);
    std::string error;
    report(v2::load(path, &error), "valid 4-bucket mirrored file loads");
    const v2::Description d = v2::describe(*v2::loaded());
    report(d.king_buckets == 4 && d.mirror && d.residual && d.output_buckets == 1 && d.checksum == fnv(bytes.substr(0, bytes.size() - 8)),
           "describe(): buckets, mirror, residual, output buckets, FNV-1a checksum");
    const v2::Net* before = v2::loaded();
    auto rejected = [&](std::string corrupt, const std::string& label, bool fix_checksum) {
        if (fix_checksum) {
            corrupt.resize(corrupt.size() - 8);
            const std::uint64_t h = fnv(corrupt);
            for (int i = 0; i < 8; ++i) corrupt.push_back(static_cast<char>((h >> (8 * i)) & 0xFFU));
        }
        write_file(dir + "bad.fnn2", corrupt);
        std::string message;
        const bool loaded = v2::load(dir + "bad.fnn2", &message);
        report(!loaded && !message.empty() && v2::loaded() == before, "rejects " + label + " (" + message + "), keeps the loaded net");
    };
    auto patch32 = [&](std::size_t offset, std::uint32_t value) {
        std::string s = bytes;
        for (int i = 0; i < 4; ++i) s[offset + static_cast<std::size_t>(i)] = static_cast<char>((value >> (8 * i)) & 0xFFU);
        return s;
    };
    { std::string s = bytes; s[1000] = static_cast<char>(s[1000] ^ 1); rejected(s, "a flipped weight bit (checksum)", false); }
    { std::string s = bytes; s[0] = 'X'; rejected(s, "bad magic", true); }
    rejected(patch32(8, 3), "version 3", true);
    rejected(patch32(12, 128), "header size 128", true);
    rejected(patch32(16, 1), "feature set 1", true);
    rejected(patch32(20, 640), "inputs 640", true);
    rejected(patch32(24, 128), "hidden 128", true);
    rejected(patch32(28, 0), "0 king buckets", true);
    rejected(patch32(28, 33), "33 king buckets", true);
    rejected(patch32(32, 2), "2 output buckets", true);
    rejected(patch32(36, 4), "unknown flag bit", true);
    { float f = 4095.0F; std::uint32_t v = 0; std::memcpy(&v, &f, 4); rejected(patch32(40, v), "weight scale 4095", true); }
    { float f = 2.5F; std::uint32_t v = 0; std::memcpy(&v, &f, 4); rejected(patch32(48, v), "sigmoid K 2.5", true); }
    { std::string s = bytes; s[52 + 10] = 4; rejected(s, "king map entry 4 >= 4 buckets", true); }
    { std::string s = bytes; s[116 + 5] = 1; rejected(s, "output map entry 1", true); }
    { std::string s = bytes; s[150] = 1; rejected(s, "non-zero reserved byte", true); }
    { std::string s = bytes; s.erase(500, 2); rejected(s, "truncated file", true); }
    { std::string s = bytes; s.insert(500, "xy"); rejected(s, "two extra bytes", true); }
    rejected("FORGENN2", "8-byte file", false);
    std::string message;
    const bool missing = v2::load(dir + "does_not_exist.fnn2", &message);
    report(!missing && v2::loaded() == before, "missing file rejected (" + message + ")");
}

// ---------------------------------------------------------------- 3. option selection
void test_selection(const std::string& dir) {
    check(load_spec(dir + "select.fnn2", random_net(4, true, symmetric_map(4), 51)), "load 4-bucket net for selection");
    std::string message;
    bool active = false;
    options::nnue_king_buckets = 0;
    active = options::apply_nnue_v2(&message);
    report(!active && !options::nnue_v2 && v2::active() == nullptr, "NNUEKingBuckets 0: compiled-in net (" + message + ")");
    options::nnue_king_buckets = 8;
    active = options::apply_nnue_v2(&message);
    report(!active && !options::nnue_v2, "NNUEKingBuckets 8 vs a 4-bucket file: not selected (" + message + ")");
    options::nnue_king_buckets = 4;
    active = options::apply_nnue_v2(&message);
    report(active && options::nnue_v2 && v2::active() == v2::loaded(), "NNUEKingBuckets 4: selected (" + message + ")");
    nnue::enabled = false;
    active = options::apply_nnue_v2(&message);
    report(!active && !options::nnue_v2, "UseNNUE false wins (" + message + ")");
    nnue::enabled = true;
    active = options::apply_nnue_v2(&message);
    report(active, "UseNNUE true again: selected");
    v2::unload();
    active = options::apply_nnue_v2(&message);
    report(!active && v2::active() == nullptr && v2::loaded() == nullptr, "unload: compiled-in net (" + message + ")");
    options::nnue_king_buckets = 0;
    (void)options::apply_nnue_v2(nullptr);
}

// ---------------------------------------------------------------- 4. lock replicas
std::uint64_t search_nodes(const Board& b, int depth, std::string* best) {
    Searcher searcher(16, 1);
    SearchLimits limits;
    limits.depth = depth;
    const SearchInfo info = searcher.search(b, limits, false, Searcher::TTAccess::Exclusive);
    if (best != nullptr) *best = Board::move_to_uci(info.best_move);
    return info.nodes;
}

void test_lock_replicas(const std::string& dir) {
    const std::vector<Board> boards = random_positions(300, 61);
    std::vector<std::pair<std::uint64_t, std::string>> lock_search;
    for (int i = 0; i < 4; ++i) {
        std::string best;
        const std::uint64_t nodes = search_nodes(position(start_fens[static_cast<std::size_t>(i * 2 + 1)]), 8, &best);
        lock_search.emplace_back(nodes, best);
    }
    for (const std::string kind : {"r1", "r4", "rm2", "rm8", "rm16"}) {
        const Spec n = lock_replica(kind);
        check(load_spec(dir + "replica.fnn2", n), "load replica " + kind);
        options::nnue_king_buckets = n.king_buckets;
        check(options::apply_nnue_v2(nullptr), "select replica " + kind);
        const v2::Net& net = *v2::active();
        int bad = 0;
        for (const Board& b : boards) {
            nnue::Accumulator lock;
            nnue::refresh(b, lock);
            const nnue::Accumulator mine = reference(net, b);
            if (!same_values(lock, mine) || nnue::evaluate(b, lock) != v2::evaluate(net, b, mine)) ++bad;
        }
        report(bad == 0, "replica " + kind + ": 300 positions, accumulators and evals bit-identical to the compiled-in net");
        bool same_search = true;
        for (int i = 0; i < 4; ++i) {
            std::string best;
            const std::uint64_t nodes = search_nodes(position(start_fens[static_cast<std::size_t>(i * 2 + 1)]), 8, &best);
            same_search = same_search && nodes == lock_search[static_cast<std::size_t>(i)].first && best == lock_search[static_cast<std::size_t>(i)].second;
        }
        report(same_search, "replica " + kind + ": depth-8 searches of 4 positions have the compiled-in net's node counts and best moves");
        options::nnue_king_buckets = 0;
        (void)options::apply_nnue_v2(nullptr);
    }
}

// ---------------------------------------------------------------- 5. incremental == refresh, 100k plies
struct WalkStats {
    long plies = 0, nulls = 0, evals = 0, verified = 0, key_changes = 0, restarts = 0, max_chain = 0;
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
        (void)w.search(board, limits, false, all);   // sets up the stack as a real search does
        SearchStack* root = Probe::root(w);
        std::vector<Board> path{board};
        struct Step { bool null; Move move; Undo undo; NullUndo null_undo; };
        std::vector<Step> steps;
        int depth = 0;
        const int length = 200 + rng.below(400);
        for (int t = 0; t < length && st.plies < target_plies; ++t) {
            SearchStack* ss = root + depth;
            const bool can_push = depth < MaxDepth;
            if (can_push && (depth == 0 || rng.chance(58))) {
                const MoveList moves = board.legal_moves();
                if (moves.empty()) continue;
                Step step{};
                if (!board.in_check() && rng.chance(4)) {
                    step.null = true;
                    Probe::null(w, ss);
                    board.make_null_move(step.null_undo);
                    ++st.nulls;
                } else {
                    step.null = false;
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
                if (rng.chance(45)) {
                    // Evaluate; then check every accumulator this evaluation computed.
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
                    const nnue::Accumulator ref = reference(net, board);
                    const int expected = std::clamp(Evaluator::evaluate_uncached(board) + v2::evaluate(net, board, ref),
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
                if (rng.chance(30)) {   // re-evaluate an ancestor after unmake (cached accumulator reuse)
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
    struct Case { const char* name; int buckets; bool mirror; std::array<std::uint8_t, 64> map; };
    std::array<std::uint8_t, 64> every{};
    for (int s = 0; s < 64; ++s) every[static_cast<std::size_t>(s)] = static_cast<std::uint8_t>(half_index(s));
    const std::vector<Case> cases = {
        {"8 mirrored buckets (standard layout)", 8, true, symmetric_map(8)},
        {"32 mirrored buckets (one per half-board square)", 32, true, every},
        {"4 unmirrored buckets", 4, false, symmetric_map(4)},
    };
    long total = 0;
    std::uint64_t seed = 71;
    for (const Case& c : cases) {
        check(load_spec(dir + "walk.fnn2", random_net(c.buckets, c.mirror, c.map, seed)), std::string("load ") + c.name);
        options::nnue_king_buckets = c.buckets;
        check(options::apply_nnue_v2(nullptr), std::string("select ") + c.name);
        WalkStats st;
        int bad = 0;
        walk(*worker, *v2::active(), seed * 7919U, plies_per_net, st, bad);
        total += st.plies;
        std::cout << "WALK " << c.name << ": plies " << st.plies << " (null " << st.nulls << ") evaluations " << st.evals
                  << " computed accumulators verified " << st.verified << " king-key changes " << st.key_changes
                  << " longest replay " << st.max_chain << " restarts " << st.restarts << " mismatches " << bad << '\n';
        report(bad == 0 && st.key_changes > 1000 && st.max_chain >= 3,
               std::string("incremental == full refresh, bit-exact, ") + c.name + ": " + std::to_string(st.plies) + " plies");
        ++seed;
    }
    std::cout << "WALK total plies " << total << '\n';
    options::nnue_king_buckets = 0;
    (void)options::apply_nnue_v2(nullptr);
}

} // namespace

int main(int argc, char** argv) {
    // argv[1] (optional): plies per net for the walk test (default 34000, i.e. > 100k in total).
    const long plies = argc > 1 ? std::stol(argv[1]) : 34000;
    const std::string dir = "nnue_v2_test_";
    test_bucket_map_and_mirroring(dir);
    test_loader(dir);
    test_selection(dir);
    test_lock_replicas(dir);
    test_incremental_equals_refresh(dir, plies);
    v2::unload();
    for (const char* f : {"map", "mirror", "plain", "loader", "bad", "select", "replica", "walk"}) std::remove((dir + f + ".fnn2").c_str());
    std::cout << checks - failures << "/" << checks << " checks passed\n";
    return failures == 0 ? 0 : 1;
}
