// NNUE v3 tests (job FB1). usage: forge_nnue_v3_tests <scratch dir>
// M1: file format round trip, loader rejections (loud failure, nothing loaded),
//     feature set, output buckets, scalar reference arithmetic on a hand-made net.
#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <string_view>
#include <vector>

namespace {

int checks = 0;
int failures = 0;

void check(bool condition, const std::string& what) {
    ++checks;
    if (!condition) {
        ++failures;
        std::cout << "FAIL: " << what << '\n';
    }
}

void put_u32(std::vector<std::uint8_t>& out, std::uint32_t v) {
    for (int i = 0; i < 4; ++i) out.push_back(static_cast<std::uint8_t>((v >> (8 * i)) & 0xFFU));
}

void put_i16(std::vector<std::uint8_t>& out, std::int16_t v) {
    const auto u = static_cast<std::uint16_t>(v);
    out.push_back(static_cast<std::uint8_t>(u & 0xFFU));
    out.push_back(static_cast<std::uint8_t>((u >> 8U) & 0xFFU));
}

struct NetSpec {
    int hidden = 32;
    int king_buckets = 1;
    int output_buckets = 1;
    bool mirror = false;
    bool residual = false;
    std::int32_t eval_scale = 400;
    std::array<std::uint8_t, 64> king_map{};
    std::array<std::uint8_t, 33> output_map{};
    std::vector<std::int16_t> w1;   // [KB][768][H]
    std::vector<std::int16_t> b1;   // [H]
    std::vector<std::int16_t> w2;   // [OB][2H]
    std::vector<std::int32_t> b2;   // [OB]
};

std::vector<std::uint8_t> serialize(const NetSpec& n) {
    std::vector<std::uint8_t> out;
    const char magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '3'};
    out.insert(out.end(), magic, magic + 8);
    put_u32(out, 3);
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::v3::HeaderBytes));
    put_u32(out, 768);
    put_u32(out, static_cast<std::uint32_t>(n.hidden));
    put_u32(out, static_cast<std::uint32_t>(n.king_buckets));
    put_u32(out, static_cast<std::uint32_t>(n.output_buckets));
    put_u32(out, (n.residual ? forge::nnue::v3::FlagResidual : 0U) | (n.mirror ? forge::nnue::v3::FlagMirror : 0U));
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::v3::QA));
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::v3::QB));
    put_u32(out, static_cast<std::uint32_t>(n.eval_scale));
    out.insert(out.end(), n.king_map.begin(), n.king_map.end());
    out.insert(out.end(), n.output_map.begin(), n.output_map.end());
    while (out.size() < static_cast<std::size_t>(forge::nnue::v3::HeaderBytes)) out.push_back(0);
    for (const std::int16_t v : n.w1) put_i16(out, v);
    for (const std::int16_t v : n.b1) put_i16(out, v);
    for (const std::int16_t v : n.w2) put_i16(out, v);
    for (const std::int32_t v : n.b2) put_u32(out, static_cast<std::uint32_t>(v));
    const std::uint64_t hash = forge::nnue::v3::fnv1a64(out.data(), out.size());
    for (int i = 0; i < 8; ++i) out.push_back(static_cast<std::uint8_t>((hash >> (8 * i)) & 0xFFU));
    return out;
}

void write_file(const std::string& path, const std::vector<std::uint8_t>& bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

NetSpec make_spec(int hidden, int king_buckets, int output_buckets, bool mirror, std::uint32_t seed) {
    NetSpec n;
    n.hidden = hidden;
    n.king_buckets = king_buckets;
    n.output_buckets = output_buckets;
    n.mirror = mirror;
    for (int sq = 0; sq < 64; ++sq) {
        // rank bands: a simple map that uses every bucket
        n.king_map[static_cast<std::size_t>(sq)] = static_cast<std::uint8_t>((sq >> 3) * king_buckets / 8);
    }
    for (int p = 0; p <= 32; ++p) {
        n.output_map[static_cast<std::size_t>(p)] = static_cast<std::uint8_t>(std::min(output_buckets - 1, std::max(p - 2, 0) * output_buckets / 32));
    }
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> dw1(-40, 40);
    std::uniform_int_distribution<int> db1(-200, 200);
    std::uniform_int_distribution<int> dw2(-127, 127);
    std::uniform_int_distribution<int> db2(-5000, 5000);
    const std::size_t h = static_cast<std::size_t>(hidden);
    n.w1.resize(static_cast<std::size_t>(king_buckets) * 768 * h);
    for (auto& v : n.w1) v = static_cast<std::int16_t>(dw1(rng));
    n.b1.resize(h);
    for (auto& v : n.b1) v = static_cast<std::int16_t>(db1(rng));
    n.w2.resize(static_cast<std::size_t>(output_buckets) * 2 * h);
    for (auto& v : n.w2) v = static_cast<std::int16_t>(dw2(rng));
    n.b2.resize(static_cast<std::size_t>(output_buckets));
    for (auto& v : n.b2) v = db2(rng);
    return n;
}

bool expect_reject(const std::string& path, const std::string& reason_part, const std::string& what) {
    std::string error;
    const bool ok = forge::nnue::v3::load(path, &error);
    check(!ok, what + ": load must fail");
    check(forge::nnue::v3::loaded() == nullptr, what + ": nothing stays loaded after a failed load");
    check(error.find(reason_part) != std::string::npos, what + ": error names the reason ('" + reason_part + "' in '" + error + "')");
    return !ok;
}

// Independent reference: evaluate a position with plain integer arithmetic over the spec.
int reference_cp(const NetSpec& n, const forge::Board& board) {
    const int H = n.hidden;
    std::array<std::vector<std::int64_t>, 2> acc;
    std::array<int, 2> flips{};
    std::array<int, 2> buckets{};
    for (const forge::Color p : {forge::White, forge::Black}) {
        const int ksq = board.king_square(p);
        const int kr = p == forge::White ? ksq : ksq ^ 56;
        const int flip = (n.mirror && (kr & 7) >= 4) ? 7 : 0;
        const int bucket = n.king_map[static_cast<std::size_t>(kr)];
        flips[static_cast<std::size_t>(p)] = flip;
        buckets[static_cast<std::size_t>(p)] = bucket;
        auto& a = acc[static_cast<std::size_t>(p)];
        a.assign(static_cast<std::size_t>(H), 0);
        for (int h = 0; h < H; ++h) a[static_cast<std::size_t>(h)] = n.b1[static_cast<std::size_t>(h)];
        for (int sq = 0; sq < 64; ++sq) {
            const forge::Piece pc = board.piece_at(sq);
            if (pc == forge::Empty) continue;
            const int rel = forge::color_of(pc) == p ? 0 : 1;
            const int type = forge::piece_type(pc) - 1;
            const int r = (p == forge::White ? sq : sq ^ 56) ^ flip;
            const int idx = bucket * 768 + (rel * 6 + type) * 64 + r;
            for (int h = 0; h < H; ++h) a[static_cast<std::size_t>(h)] += n.w1[static_cast<std::size_t>(idx) * static_cast<std::size_t>(H) + static_cast<std::size_t>(h)];
        }
    }
    const forge::Color us = board.side_to_move();
    const int pieces = std::min(forge::popcount(board.occupied()), 32);
    const int ob = n.output_map[static_cast<std::size_t>(pieces)];
    std::int64_t sum = 0;
    for (int h = 0; h < H; ++h) {
        const std::int64_t a = std::clamp<std::int64_t>(acc[static_cast<std::size_t>(us)][static_cast<std::size_t>(h)], 0, 255);
        const std::int64_t b = std::clamp<std::int64_t>(acc[static_cast<std::size_t>(forge::opposite(us))][static_cast<std::size_t>(h)], 0, 255);
        sum += a * a * n.w2[static_cast<std::size_t>(ob) * 2 * static_cast<std::size_t>(H) + static_cast<std::size_t>(h)];
        sum += b * b * n.w2[static_cast<std::size_t>(ob) * 2 * static_cast<std::size_t>(H) + static_cast<std::size_t>(H + h)];
    }
    const std::int64_t out = sum / 255 + n.b2[static_cast<std::size_t>(ob)];
    const std::int64_t cp = out * n.eval_scale / (255 * 64);
    return static_cast<int>(std::clamp<std::int64_t>(cp, -30000, 30000));
}

const std::string_view kFens[] = {
    forge::Board::StandardStartFen,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "8/8/8/8/8/8/8/K6k w - - 0 1",
    "7K/8/8/8/8/8/8/k7 b - - 0 1",
    "4k3/8/8/8/8/8/8/4K2R w K - 0 1",
    "r3k3/8/8/8/8/8/8/4K3 b q - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
};

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_nnue_v3_tests <scratch dir>\n";
        return 2;
    }
    const std::filesystem::path dir = argv[1];
    std::filesystem::create_directories(dir);
    const auto file = [&](const char* name) { return (dir / name).string(); };

    // ---- 1. round trip + describe ----
    {
        const NetSpec spec = make_spec(64, 4, 8, true, 7);
        write_file(file("ok.fnn3"), serialize(spec));
        std::string error;
        check(forge::nnue::v3::load(file("ok.fnn3"), &error), "valid file loads: " + error);
        const forge::nnue::v3::Net* net = forge::nnue::v3::loaded();
        check(net != nullptr, "loaded() after a successful load");
        if (net != nullptr) {
            check(net->hidden == 64 && net->king_buckets == 4 && net->output_buckets == 8 && net->mirror && !net->residual, "header fields");
            check(net->eval_scale == 400, "eval_scale");
            check(std::equal(net->king_map.begin(), net->king_map.end(), spec.king_map.begin()), "king map");
            check(std::equal(net->output_map.begin(), net->output_map.end(), spec.output_map.begin()), "output map");
            check(net->w1.size() == spec.w1.size() && std::equal(spec.w1.begin(), spec.w1.end(), net->w1.data()), "w1 integers");
            check(std::equal(spec.b1.begin(), spec.b1.end(), net->b1.data()), "b1 integers");
            check(std::equal(spec.w2.begin(), spec.w2.end(), net->w2.data()), "w2 integers");
            check(net->b2 == spec.b2, "b2 integers");
            check(forge::nnue::v3::file_size_for(64, 4, 8) == serialize(spec).size(), "file_size_for");
            check(forge::nnue::v3::describe(*net).find("hidden 64") != std::string::npos, "describe mentions hidden");
        }
        forge::nnue::v3::unload();
        check(forge::nnue::v3::loaded() == nullptr, "unload");
    }

    // ---- 2. loud rejections ----
    {
        const NetSpec spec = make_spec(32, 2, 2, false, 3);
        const std::vector<std::uint8_t> good = serialize(spec);
        auto corrupt = [&](const char* name, auto&& mutate) {
            std::vector<std::uint8_t> bytes = good;
            mutate(bytes);
            write_file(file(name), bytes);
            return file(name);
        };
        expect_reject(file("missing.fnn3"), "cannot open", "missing file");
        expect_reject(corrupt("magic.fnn3", [](auto& b) { b[0] = 'X'; }), "bad magic", "bad magic");
        expect_reject(corrupt("version.fnn3", [](auto& b) { b[8] = 2; }), "version", "wrong version");
        expect_reject(corrupt("short.fnn3", [](auto& b) { b.pop_back(); }), "file size", "truncated file");
        expect_reject(corrupt("long.fnn3", [](auto& b) { b.push_back(0); }), "file size", "extra bytes");
        expect_reject(corrupt("checksum.fnn3", [](auto& b) { b[forge::nnue::v3::HeaderBytes + 10] ^= 1; }), "checksum", "flipped weight bit");
        expect_reject(corrupt("hidden.fnn3", [](auto& b) { b[20] = 48; }), "hidden", "hidden not a multiple of 32 (size check or hidden check)");
        expect_reject(corrupt("qa.fnn3", [](auto& b) { b[36] = 127; }), "quantisation", "wrong qa");
        expect_reject(corrupt("reserved.fnn3", [](auto& b) { b[150] = 1; }), "reserved", "reserved byte set");
        expect_reject(corrupt("flags.fnn3", [](auto& b) { b[32] = 4; }), "flag", "unknown flag");
        {
            NetSpec bad = spec;
            bad.king_map[5] = 2;   // 2 king buckets: entries must be 0 or 1 (re-serialised, so the checksum is valid)
            write_file(file("kmap.fnn3"), serialize(bad));
            expect_reject(file("kmap.fnn3"), "king_bucket_map", "king map entry out of range");
        }
        {
            NetSpec bad = spec;
            bad.output_map[5] = 2;
            write_file(file("omap.fnn3"), serialize(bad));
            expect_reject(file("omap.fnn3"), "output_bucket_map", "output map entry out of range");
        }
        expect_reject(corrupt("hdrbit.fnn3", [](auto& b) { b[48 + 5] ^= 1; }), "checksum", "flipped header bit");
        {
            NetSpec bad = spec;
            bad.w2[3] = 128;
            write_file(file("w2.fnn3"), serialize(bad));
            expect_reject(file("w2.fnn3"), "|w2|", "w2 out of range");
        }
        {
            NetSpec bad = spec;
            bad.w1[100] = 1024;   // 32 * 1024 > 32767
            write_file(file("w1.fnn3"), serialize(bad));
            expect_reject(file("w1.fnn3"), "accumulator range", "accumulator range");
        }
        check(forge::nnue::v3::requested == false, "NNUEArch defaults to off");
        forge::nnue::v3::requested = true;
        check(!forge::nnue::v3::problem().empty(), "problem() reported when requested without a net");
        check(!forge::nnue::v3::active(), "not active without a net");
        forge::nnue::v3::requested = false;
        check(forge::nnue::v3::problem().empty(), "no problem when not requested");
    }

    // ---- 3. feature set ----
    {
        const NetSpec spec = make_spec(32, 8, 1, true, 5);
        write_file(file("feat.fnn3"), serialize(spec));
        std::string error;
        check(forge::nnue::v3::load(file("feat.fnn3"), &error), "feature net loads: " + error);
        const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();
        // white king on e1 -> kr = 4, file 4 -> flip; black king on e8 -> kr = 4 too
        const auto kw = forge::nnue::v3::king_key(net, forge::White, 4);
        const auto kb = forge::nnue::v3::king_key(net, forge::Black, 60);
        check(kw.flip == 7 && kb.flip == 7, "e-file kings are mirrored");
        check(kw.bucket == spec.king_map[4] && kb.bucket == spec.king_map[4], "bucket from the perspective frame");
        const auto kd = forge::nnue::v3::king_key(net, forge::White, 3);
        check(kd.flip == 0, "d-file king not mirrored");
        // With bucket 0 and no flip, feature_index equals the compiled-in feature index.
        forge::nnue::v3::KingKey zero;
        for (int sq = 0; sq < 64; sq += 7) {
            check(forge::nnue::v3::feature_index(zero, forge::White, forge::BQ, sq) == forge::nnue::feature_index(forge::White, forge::BQ, sq), "bucket 0 == lock feature (white)");
            check(forge::nnue::v3::feature_index(zero, forge::Black, forge::WP, sq) == forge::nnue::feature_index(forge::Black, forge::WP, sq), "bucket 0 == lock feature (black)");
        }
        forge::nnue::v3::KingKey k3;
        k3.bucket = 3;
        k3.flip = 7;
        check(forge::nnue::v3::feature_index(k3, forge::White, forge::WK, 4) == 3 * 768 + 5 * 64 + 3, "mirrored own king e1 -> d1 in bucket 3");
        forge::Board board;
        check(board.set_fen("8/8/8/8/8/8/8/K6k w - - 0 1"), "fen");
        check(forge::nnue::v3::output_bucket(net, board) == 0, "2 pieces -> bucket 0 with one output bucket");
        forge::nnue::v3::unload();
    }

    // ---- 4. scalar reference arithmetic vs an independent integer implementation ----
    {
        int positions = 0;
        for (const int ob : {1, 8}) {
            for (const bool mirror : {false, true}) {
                const NetSpec spec = make_spec(96, 4, ob, mirror, 11U + static_cast<unsigned>(ob) + (mirror ? 100U : 0U));
                write_file(file("ref.fnn3"), serialize(spec));
                std::string error;
                check(forge::nnue::v3::load(file("ref.fnn3"), &error), "ref net loads: " + error);
                const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();
                for (const std::string_view fen : kFens) {
                    forge::Board board;
                    check(board.set_fen(fen), "fen " + std::string(fen));
                    const int engine = forge::nnue::v3::evaluate_reference(net, board);
                    const int reference = reference_cp(spec, board);
                    check(engine == reference, "scalar eval == independent integer reference on " + std::string(fen) +
                                                   " (" + std::to_string(engine) + " vs " + std::to_string(reference) + ")");
                    ++positions;
                }
                forge::nnue::v3::unload();
            }
        }
        std::cout << "scalar reference positions compared: " << positions << '\n';
    }

    // ---- 5. the lock net replica idea: one bucket, w2 identical heads -> output independent of the bucket ----
    {
        NetSpec spec = make_spec(32, 1, 8, false, 21);
        for (int b = 1; b < 8; ++b) {
            std::copy_n(spec.w2.begin(), 64, spec.w2.begin() + b * 64);
            spec.b2[static_cast<std::size_t>(b)] = spec.b2[0];
        }
        write_file(file("heads.fnn3"), serialize(spec));
        std::string error;
        check(forge::nnue::v3::load(file("heads.fnn3"), &error), "heads net loads: " + error);
        NetSpec one = spec;
        one.output_buckets = 1;
        one.w2.resize(64);
        one.b2.resize(1);
        one.output_map.fill(0);
        for (const std::string_view fen : kFens) {
            forge::Board board;
            (void)board.set_fen(fen);
            check(forge::nnue::v3::evaluate_reference(*forge::nnue::v3::loaded(), board) == reference_cp(one, board), "identical heads == one head");
        }
        forge::nnue::v3::unload();
    }

    std::cout << "nnue_v3_tests: " << checks << " checks, " << failures << " failures\n";
    return failures == 0 ? 0 : 1;
}
