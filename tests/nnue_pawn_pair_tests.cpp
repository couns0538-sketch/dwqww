// Tests for the pawn-pair inputs of v2 networks (O7; UCI NNUEPawnPairs; definition in forge/nnue_v2.hpp):
//   1. pawn-pair features == an independent brute-force reference (all pawn pairs, explicit frame transform) on random
//      positions for both perspectives with and without the mirror flip; explicit features of one position;
//   2. colour and mirror symmetry of pawn-pair-net accumulators; the pawn-pair columns really enter them;
//   3. loader: feature_set bit 1 (and bits 0 + 1) files load, unknown bits and wrong sizes are rejected;
//   4. selection and the fail-loud rule for NNUEPawnPairs (and NNUEThreats with a net that has both blocks);
//   5. zero-pawn-pair lock replicas: accumulators and evaluations bit-identical to the compiled-in net, identical
//      search node counts;
//   6. incremental == full refresh, bit-exact, over 102,000 random make/unmake plies driven through the real
//      Worker::static_evaluate (pawn pairs with 1 bucket; pawn pairs with 8 mirrored buckets; threats + pawn pairs
//      with 4 unmirrored buckets);
//   7. UCI (when the engine executable is given): option advertised, unusable requests exit 2, a pawn-pair net is active.
// usage: forge_nnue_pawn_pair_tests [<forge executable>] [plies per walk net (default 34000)]
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

#include "nnue_weights.inc"   // the compiled-in (lock) network, for the zero-pawn-pair replicas

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
    bool threats = false;
    bool pawn_pairs = true;
    std::uint32_t feature_set_override = 0xFFFFFFFFU;
    std::array<std::uint8_t, 64> king_map{};
    std::vector<std::int16_t> w1, wt, wp, b1, w2, b2;
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
    const std::uint32_t feature_set = n.feature_set_override != 0xFFFFFFFFU ? n.feature_set_override
                                                                            : (n.threats ? 1U : 0U) | (n.pawn_pairs ? 2U : 0U);
    put32(s, 2); put32(s, 160); put32(s, feature_set); put32(s, 768); put32(s, nnue::HiddenSize);
    put32(s, static_cast<std::uint32_t>(n.king_buckets)); put32(s, 1); put32(s, (n.residual ? 1U : 0U) | (n.mirror ? 2U : 0U));
    putf(s, 4096.0F); putf(s, 4096.0F); putf(s, 2.25F);
    for (const std::uint8_t b : n.king_map) s.push_back(static_cast<char>(b));
    s.append(33, '\0');
    s.append(160 - s.size(), '\0');
    put16s(s, n.w1);
    if (n.threats) put16s(s, n.wt);
    if (n.pawn_pairs) put16s(s, n.wp);
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

Spec random_net(int buckets, bool mirror, bool threats, bool pawn_pairs, std::uint64_t seed) {
    Spec n;
    Rng rng{seed};
    n.king_buckets = buckets;
    n.mirror = mirror;
    n.threats = threats;
    n.pawn_pairs = pawn_pairs;
    n.king_map = symmetric_map(buckets);
    const std::size_t hidden = nnue::HiddenSize;
    auto value = [&rng](int range) { return static_cast<std::int16_t>(rng.below(2 * range + 1) - range); };
    n.w1.resize(static_cast<std::size_t>(buckets) * 768 * hidden);
    for (auto& v : n.w1) v = value(220);
    if (threats) {
        n.wt.resize(static_cast<std::size_t>(v2::ThreatFeatures) * hidden);
        for (auto& v : n.wt) v = value(120);
    }
    if (pawn_pairs) {
        n.wp.resize(static_cast<std::size_t>(v2::PawnPairFeatures) * hidden);
        for (auto& v : n.wp) v = value(200);
    }
    n.b1.resize(hidden);
    for (auto& v : n.b1) v = value(1200);
    n.w2.resize(2 * hidden);
    for (auto& v : n.w2) v = value(900);
    n.b2 = {value(500)};
    return n;
}

// Lock weights in v2 form (C4's replicas r1 / rm8) plus a pawn-pair block of zeros.
Spec zero_pawn_replica(const std::string& kind) {
    Spec n;
    const std::size_t hidden = nnue::HiddenSize;
    std::vector<bool> flipped;
    if (kind == "r1") {
        n.king_buckets = 1;
        flipped = {false};
    } else {
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
    n.wp.assign(static_cast<std::size_t>(v2::PawnPairFeatures) * hidden, 0);
    n.b1.assign(NnueB1, NnueB1 + hidden);
    n.w2.assign(NnueW2, NnueW2 + 2 * hidden);
    n.b2 = {NnueB2};
    n.residual = true;
    n.threats = false;
    n.pawn_pairs = true;
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
    "4k3/pp3ppp/2p5/3p4/3P4/2P5/PP3PPP/4K3 w - - 0 1",
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

// ---------------------------------------------------------------- 1. features vs brute force
std::vector<int> brute_pairs(const Board& b, Color perspective, int flip) {
    struct P { int r; int colour; };
    std::vector<P> pawns;
    for (int s = 0; s < 64; ++s) {
        const Piece piece = b.piece_at(s);
        if (piece != WP && piece != BP) continue;
        const int r = (perspective == White ? s : (7 - (s >> 3)) * 8 + (s & 7));
        pawns.push_back({flip != 0 ? (r & 56) | (7 - (r & 7)) : r, color_of(piece) == perspective ? 0 : 1});
    }
    std::vector<int> features;
    for (std::size_t i = 0; i < pawns.size(); ++i) {
        for (std::size_t j = 0; j < pawns.size(); ++j) {
            if (i == j) continue;
            const P& a = pawns[i];
            const P& o = pawns[j];
            const int dr = (o.r >> 3) - (a.r >> 3);
            const int df = (o.r & 7) - (a.r & 7);
            // a is the anchor: o on a higher rank, or on the same rank one file to the right.
            int offset = -1;
            if (dr == 0 && df == 1) offset = 0;
            else if (dr == 1 && df >= -1 && df <= 1) offset = 2 + df;
            else if (dr == 2 && df >= -1 && df <= 1) offset = 5 + df;
            if (offset < 0) continue;
            features.push_back(((a.colour * 2 + o.colour) * 7 + offset) * 64 + a.r);
        }
    }
    std::sort(features.begin(), features.end());
    return features;
}

std::vector<int> engine_pairs(const Board& b, Color perspective, int flip) {
    v2::PawnPairList list;
    v2::pawn_pair_features(v2::pieces_of(b), perspective, flip, list);
    std::vector<int> features(list.features.begin(), list.features.begin() + list.count);
    std::sort(features.begin(), features.end());
    return features;
}

void test_pairs() {
    const std::vector<Board> boards = random_positions(3000, 201);
    int mismatches = 0;
    long pairs = 0;
    int most = 0;
    for (const Board& b : boards) {
        for (const Color p : {White, Black}) {
            for (const int flip : {0, 7}) {
                const std::vector<int> mine = engine_pairs(b, p, flip);
                if (mine != brute_pairs(b, p, flip)) ++mismatches;
                pairs += static_cast<long>(mine.size());
                most = std::max(most, static_cast<int>(mine.size()));
            }
        }
    }
    report(mismatches == 0 && pairs > 0, "pawn-pair features == brute-force reference on 3000 random positions x 2 perspectives x 2 flips (" +
                                             std::to_string(pairs) + " pairs, at most " + std::to_string(most) + " in one frame)");
    // White pawns d4 e4, black pawns d5 e5, White perspective: 6 pairs.
    const Board b = position("4k3/8/8/3pp3/3PP3/8/8/4K3 w - - 0 1");
    std::vector<int> expect = {27, 603, 667, 540, 604, 1379};
    std::sort(expect.begin(), expect.end());
    report(engine_pairs(b, White, 0) == expect,
           "explicit: d4-e4 (own phalanx), d4-d5 / e4-e5 (rams), d4-e5 / e4-d5 (levers), d5-e5 (their phalanx) = 27 603 667 540 604 1379");
    const Board far = position("4k3/8/8/p6p/8/8/P6P/4K3 w - - 0 1");
    report(engine_pairs(far, White, 0).empty(), "explicit: pawns on non-adjacent files or three ranks apart form no pair");
}

// ---------------------------------------------------------------- 2. symmetry
void test_symmetry(const std::string& dir) {
    const std::vector<Board> boards = random_positions(400, 211);
    check(load_spec(dir + "sym.fnn2", random_net(8, true, false, true, 213)), "load mirrored 8-bucket pawn-pair net");
    const v2::Net& net = *v2::loaded();
    int colour_bad = 0;
    int mirror_bad = 0;
    for (const Board& b : boards) {
        const nnue::Accumulator a = reference(net, b);
        const nnue::Accumulator c = reference(net, position(transformed_fen(b, false, true)));
        if (std::memcmp(a.values[White].data(), c.values[Black].data(), sizeof(float) * nnue::HiddenSize) != 0 ||
            std::memcmp(a.values[Black].data(), c.values[White].data(), sizeof(float) * nnue::HiddenSize) != 0) ++colour_bad;
        if (!same_values(a, reference(net, position(transformed_fen(b, true, false))))) ++mirror_bad;
    }
    report(colour_bad == 0, "colour symmetry: 400 colour-flipped positions give the swapped accumulators (pawn-pair net)");
    report(mirror_bad == 0, "mirror symmetry: 400 file-mirrored positions give identical accumulators (mirrored pawn-pair net)");
    Spec with = random_net(1, false, false, true, 217);
    Spec without = with;
    std::fill(without.wp.begin(), without.wp.end(), 0);
    check(load_spec(dir + "sym.fnn2", with), "load pawn-pair net");
    std::vector<nnue::Accumulator> accs;
    for (int i = 0; i < 60; ++i) accs.push_back(reference(*v2::loaded(), boards[static_cast<std::size_t>(i)]));
    check(load_spec(dir + "sym.fnn2", without), "load the same net with zero pawn-pair columns");
    int changed = 0;
    int with_pairs = 0;
    int changed_without = 0;
    for (int i = 0; i < 60; ++i) {
        const Board& b = boards[static_cast<std::size_t>(i)];
        const bool has_pairs = !engine_pairs(b, White, 0).empty();
        const bool differs = !same_values(accs[static_cast<std::size_t>(i)], reference(*v2::loaded(), b));
        with_pairs += has_pairs ? 1 : 0;
        changed += differs && has_pairs ? 1 : 0;
        changed_without += differs && !has_pairs ? 1 : 0;
    }
    report(changed == with_pairs && changed_without == 0 && with_pairs >= 20,
           "control: zeroing the pawn-pair columns changes exactly the accumulators of positions with pawn pairs (" +
               std::to_string(changed) + "/" + std::to_string(with_pairs) + " of 60)");
}

// ---------------------------------------------------------------- 3. loader
void test_loader(const std::string& dir) {
    const Spec good = random_net(1, false, false, true, 221);
    const std::string bytes = serialise(good);
    write_file(dir + "loader.fnn2", bytes);
    std::string error;
    report(v2::load(dir + "loader.fnn2", &error) && v2::loaded()->pawn_pairs && !v2::loaded()->threats && v2::describe(*v2::loaded()).pawn_pairs,
           "a feature_set 2 file loads with its pawn-pair block");
    report(bytes.size() == v2::file_bytes(1, 1, v2::FeatureSetPawnPairs) &&
               v2::file_bytes(1, 1, v2::FeatureSetPawnPairs) - v2::file_bytes(1, 1) == 2U * v2::PawnPairFeatures * nnue::HiddenSize,
           "file_bytes: the pawn-pair block adds 2 * 1792 * hidden bytes");
    bool block_ok = true;
    for (std::size_t i = 0; i < good.wp.size(); i += 331) block_ok = block_ok && v2::loaded()->wp.data()[i] == static_cast<float>(good.wp[i]) / 4096.0F;
    report(block_ok, "the pawn-pair block is read in file order (sampled values == int16 / 4096)");
    const Spec both = random_net(1, false, true, true, 223);
    write_file(dir + "both.fnn2", serialise(both));
    bool both_ok = v2::load(dir + "both.fnn2", &error) && v2::loaded()->threats && v2::loaded()->pawn_pairs;
    for (std::size_t i = 0; both_ok && i < both.wp.size(); i += 331) both_ok = v2::loaded()->wp.data()[i] == static_cast<float>(both.wp[i]) / 4096.0F;
    for (std::size_t i = 0; both_ok && i < both.wt.size(); i += 997) both_ok = v2::loaded()->wt.data()[i] == static_cast<float>(both.wt[i]) / 4096.0F;
    report(both_ok, "a feature_set 3 file (threat and pawn-pair blocks) loads both blocks in order");
    auto rejected = [&](const Spec& spec, const std::string& label, const std::string& phrase) {
        write_file(dir + "bad.fnn2", serialise(spec));
        std::string message;
        const bool loaded = v2::load(dir + "bad.fnn2", &message);
        report(!loaded && contains(message, phrase) && v2::loaded() == nullptr, "rejects " + label + " (" + message + ")");
    };
    Spec unknown = good;
    unknown.feature_set_override = 6;
    rejected(unknown, "feature_set 6 (unknown bit 2)", "unsupported feature set 6");
    Spec no_block = good;
    no_block.feature_set_override = 2;
    no_block.pawn_pairs = false;
    rejected(no_block, "a feature_set 2 header without the pawn-pair block", "does not match");
}

// ---------------------------------------------------------------- 4. rules
std::string problem_after(int king_buckets, int threats, int pawns, const std::string& file) {
    options::nnue_king_buckets = king_buckets;
    options::nnue_threats = threats;
    options::nnue_pawn_pairs = pawns;
    (void)options::apply_nnue_v2(nullptr);
    return options::nnue_v2_problem(file, "");
}

void test_rules(const std::string& dir) {
    v2::unload();
    std::string p = problem_after(0, 0, 0, "");
    report(p.empty() && !options::nnue_v2, "defaults: no request, no problem");
    p = problem_after(0, 0, 1, "");
    report(contains(p, "NNUEPawnPairs is 1 but no v2 net is loaded") && !options::nnue_v2, "NNUEPawnPairs without NNUEFile: " + p);
    const std::string pp = dir + "pp.fnn2";
    check(load_spec(pp, random_net(1, false, false, true, 231)), "load a one-bucket pawn-pair net");
    p = problem_after(0, 0, 1, pp);
    report(p.empty() && options::nnue_v2 && v2::active()->pawn_pairs, "NNUEPawnPairs 1 with a one-bucket pawn-pair net: active");
    p = problem_after(0, 0, 0, pp);
    report(contains(p, "has pawn-pair inputs") && contains(p, "set NNUEPawnPairs 1") && !options::nnue_v2, "pawn-pair net without the option: " + p);
    p = problem_after(0, 1, 1, pp);
    report(contains(p, "has no threat inputs") && !options::nnue_v2, "NNUEThreats 1 + NNUEPawnPairs 1 with a pawn-pair-only net: " + p);
    const std::string plain = dir + "plain.fnn2";
    check(load_spec(plain, random_net(1, false, false, false, 232)), "load a one-bucket net without extra inputs");
    p = problem_after(0, 0, 1, plain);
    report(contains(p, "has no pawn-pair inputs") && !options::nnue_v2, "NNUEPawnPairs 1 with a net without pawn pairs: " + p);
    const std::string both = dir + "both.fnn2";
    check(load_spec(both, random_net(1, false, true, true, 233)), "load a one-bucket net with both blocks");
    p = problem_after(0, 1, 1, both);
    report(p.empty() && options::nnue_v2 && v2::active()->threats && v2::active()->pawn_pairs, "both options with the two-block net: active");
    p = problem_after(0, 1, 0, both);
    report(contains(p, "set NNUEPawnPairs 1") && !options::nnue_v2, "two-block net with NNUEThreats only: " + p);
    p = problem_after(0, 0, 1, both);
    report(contains(p, "set NNUEThreats 1") && !options::nnue_v2, "two-block net with NNUEPawnPairs only: " + p);
    const std::string pp4 = dir + "pp4.fnn2";
    check(load_spec(pp4, random_net(4, true, false, true, 234)), "load a mirrored 4-bucket pawn-pair net");
    p = problem_after(0, 0, 1, pp4);
    report(contains(p, "set NNUEKingBuckets 4 as well") && !options::nnue_v2, "NNUEPawnPairs alone with a 4-bucket net: " + p);
    p = problem_after(4, 0, 1, pp4);
    report(p.empty() && options::nnue_v2, "NNUEPawnPairs 1 + NNUEKingBuckets 4: active");
    nnue::enabled = false;
    p = problem_after(4, 0, 1, pp4);
    report(p.empty() && !options::nnue_v2, "UseNNUE false wins (not an error)");
    nnue::enabled = true;
    v2::unload();
    p = problem_after(0, 0, 0, "");
    report(p.empty() && !options::nnue_v2, "request cleared: no problem");
}

// ---------------------------------------------------------------- 5. zero-pawn-pair lock replicas
std::uint64_t search_nodes(const Board& b, int depth, std::string* best) {
    Searcher searcher(16, 1);
    SearchLimits limits;
    limits.depth = depth;
    const SearchInfo info = searcher.search(b, limits, false, Searcher::TTAccess::Exclusive);
    if (best != nullptr) *best = Board::move_to_uci(info.best_move);
    return info.nodes;
}

void test_zero_pawn_replicas(const std::string& dir) {
    const std::vector<Board> boards = random_positions(300, 241);
    std::vector<std::pair<std::uint64_t, std::string>> lock_search;
    for (int i = 0; i < 4; ++i) {
        std::string best;
        const std::uint64_t nodes = search_nodes(position(start_fens[static_cast<std::size_t>(i * 2 + 1)]), 8, &best);
        lock_search.emplace_back(nodes, best);
    }
    for (const std::string kind : {"r1", "rm8"}) {
        const Spec n = zero_pawn_replica(kind);
        check(load_spec(dir + "replica.fnn2", n), "load zero-pawn-pair replica " + kind);
        options::nnue_king_buckets = n.king_buckets;
        options::nnue_threats = 0;
        options::nnue_pawn_pairs = 1;
        check(options::apply_nnue_v2(nullptr) && v2::active()->pawn_pairs, "select zero-pawn-pair replica " + kind);
        const v2::Net& net = *v2::active();
        int bad = 0;
        for (const Board& b : boards) {
            nnue::Accumulator lock;
            nnue::refresh(b, lock);
            const nnue::Accumulator mine = reference(net, b);
            if (!same_values(lock, mine) || nnue::evaluate(b, lock) != v2::evaluate(net, b, mine)) ++bad;
        }
        report(bad == 0, "zero-pawn-pair replica " + kind + ": 300 positions, accumulators and evals bit-identical to the compiled-in net");
        bool same = true;
        for (int i = 0; i < 4; ++i) {
            std::string best;
            const std::uint64_t nodes = search_nodes(position(start_fens[static_cast<std::size_t>(i * 2 + 1)]), 8, &best);
            same = same && nodes == lock_search[static_cast<std::size_t>(i)].first && best == lock_search[static_cast<std::size_t>(i)].second;
        }
        report(same, "zero-pawn-pair replica " + kind + ": depth-8 searches of 4 positions have the compiled-in net's node counts and best moves");
        options::nnue_king_buckets = 0;
        options::nnue_pawn_pairs = 0;
        (void)options::apply_nnue_v2(nullptr);
    }
}

// ---------------------------------------------------------------- 6. incremental == refresh
struct WalkStats {
    long plies = 0, nulls = 0, evals = 0, verified = 0, key_changes = 0, restarts = 0, max_chain = 0, pawn_moves = 0;
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
                    // Prefer pawn moves now and then, so that pawn pairs change often.
                    step.move = moves[static_cast<std::size_t>(rng.below(static_cast<int>(moves.size())))];
                    if (rng.chance(40)) {
                        for (const Move& m : moves) {
                            if (piece_type(board.piece_at(m.from)) == Pawn) { step.move = m; break; }
                        }
                    }
                    const Piece moved = board.piece_at(step.move.from);
                    if (piece_type(moved) == Pawn || board.captured_piece(step.move) == WP || board.captured_piece(step.move) == BP) ++st.pawn_moves;
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
    struct Case { const char* name; int buckets; bool mirror; bool threats; };
    const std::vector<Case> cases = {
        {"1 bucket, pawn-pair inputs", 1, false, false},
        {"8 mirrored buckets, pawn-pair inputs", 8, true, false},
        {"4 unmirrored buckets, threat + pawn-pair inputs", 4, false, true},
    };
    long total = 0;
    std::uint64_t seed = 251;
    for (const Case& c : cases) {
        check(load_spec(dir + "walk.fnn2", random_net(c.buckets, c.mirror, c.threats, true, seed)), std::string("load ") + c.name);
        options::nnue_king_buckets = c.buckets;
        options::nnue_threats = c.threats ? 1 : 0;
        options::nnue_pawn_pairs = 1;
        check(options::apply_nnue_v2(nullptr), std::string("select ") + c.name);
        WalkStats st;
        int bad = 0;
        walk(*worker, *v2::active(), seed * 7919U, plies_per_net, st, bad);
        total += st.plies;
        std::cout << "WALK " << c.name << ": plies " << st.plies << " (null " << st.nulls << ", pawn moves / pawn captures "
                  << st.pawn_moves << ") evaluations " << st.evals << " computed accumulators verified " << st.verified
                  << " king-key changes " << st.key_changes << " longest replay " << st.max_chain << " restarts " << st.restarts
                  << " mismatches " << bad << '\n';
        report(bad == 0 && st.max_chain >= 3 && st.pawn_moves * 5 > st.plies && (c.buckets == 1 || st.key_changes * 50 > st.plies),
               std::string("incremental == full refresh, bit-exact, ") + c.name + ": " + std::to_string(st.plies) + " plies");
        ++seed;
    }
    std::cout << "WALK total plies " << total << '\n';
    options::nnue_king_buckets = 0;
    options::nnue_threats = 0;
    options::nnue_pawn_pairs = 0;
    (void)options::apply_nnue_v2(nullptr);
}

// ---------------------------------------------------------------- 7. UCI
struct Run {
    std::string out;
    int status = -1;
};
std::string quote(const std::string& text) { return "\"" + text + "\""; }
Run run_engine(const std::string& engine, const std::string& name, const std::string& script) {
    const std::string in = "nnue_pawn_uci_" + name + ".in";
    const std::string out = "nnue_pawn_uci_" + name + ".out";
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
    const std::string pawn = dir + "uci_pawn.fnn2";
    const std::string plain = dir + "uci_plain.fnn2";
    write_file(pawn, serialise(random_net(1, false, false, true, 261)));
    write_file(plain, serialise(random_net(1, false, false, false, 261)));
    {
        const Run r = run_engine(engine, "defaults", Head + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && contains(r.out, "option name NNUEPawnPairs type spin default 0 min 0 max 1") && has_line(r.out, "readyok") &&
                   has_line(r.out, "bestmove") && !contains(r.out, "NNUE v2"),
               "UCI defaults: NNUEPawnPairs advertised (spin 0-1, default 0), nothing NNUE v2 printed, exit 0");
    }
    expect_failure(engine, "pawns_without_file", set("NNUEPawnPairs", "1"), "isready", "no v2 net is loaded");
    expect_failure(engine, "pawns_with_plain_net", set("NNUEFile", plain) + set("NNUEPawnPairs", "1"), "go depth 1", "has no pawn-pair inputs");
    expect_failure(engine, "pawn_net_without_option", set("NNUEFile", pawn) + set("NNUEKingBuckets", "1"), "bench 2", "set NNUEPawnPairs 1");
    {
        const std::string active = "info string NNUE v2: active: " + pawn + " king buckets 1 output buckets 1 hidden " +
                                   std::to_string(nnue::HiddenSize) + " unmirrored residual pawn-pair inputs";
        const Run r = run_engine(engine, "pawns_active", Head + set("NNUEPawnPairs", "1") + set("NNUEFile", pawn) +
                                                            "isready\ngo depth 5\nbench 3\nquit\n");
        report(r.status == 0 && count(r.out, active) == 2 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") &&
                   contains(r.out, "bench depth 3 nodes") && count(r.out, "ERROR") == 1,
               "UCI NNUEPawnPairs 1 + pawn-pair net: \"" + active + " ...\" (activation + isready), readyok, bestmove, bench, exit 0");
    }
    {
        const Run r = run_engine(engine, "pawns_invalid", Head + set("NNUEPawnPairs", "2") + "isready\nquit\n");
        report(r.status == 0 && contains(r.out, "info string invalid value for option NNUEPawnPairs") && has_line(r.out, "readyok"),
               "UCI NNUEPawnPairs 2: invalid value reported, the option stays 0");
    }
}

} // namespace

int main(int argc, char** argv) {
    const std::string engine = argc > 1 ? argv[1] : "";
    const long plies = argc > 2 ? std::stol(argv[2]) : 34000;
    const std::string dir = "nnue_pawn_pair_test_";
    test_pairs();
    test_symmetry(dir);
    test_loader(dir);
    test_rules(dir);
    test_zero_pawn_replicas(dir);
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
