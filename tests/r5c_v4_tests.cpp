// R5C M3: NNUE v4 (FNN4) loader and forward pass (opus_r5/r5c/FNN4_FORMAT.md).
//
//   forge_r5c_v4_tests <scratch dir> [positions per net, default 3000]
//
// Nets are built here from random weights and serialised by this test's own writer (layout of FNN4_FORMAT.md),
// so the engine's parser, its scalar forward and its AVX2 kernel are each compared with an independent reference:
//   - the parser accepts every valid image (several shapes, mirror and residual flags) and refuses every broken one
//     (each header field, the exact size, the checksum, both overflow bounds, b_out, the reserved bytes);
//   - load() checks the size before reading weights, and a failed load keeps the net that was loaded before;
//   - on random positions (random games from the start position) the scalar forward equals this test's int64
//     reference written from the format text, and the AVX2 kernel equals the scalar one, including a net that
//     reaches the accumulator bound exactly (32 pieces, every column at max|w1|).
#include "forge/board.hpp"
#include "forge/nnue_v4.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <vector>

namespace {

namespace v4 = forge::nnue_v4;
using forge::Board;

int checks = 0;
int failures = 0;

void check(bool condition, const std::string& message) {
    ++checks;
    if (!condition) {
        ++failures;
        std::cout << "FAIL " << message << '\n';
    }
}

// A net in the file's own terms (the test's model, independent of forge::nnue_v4::Net).
struct Spec {
    int hidden = 64, kb = 1, ob = 1, l2 = 16;
    std::uint32_t flags = 0;
    std::int32_t eval_scale = 400;
    std::uint32_t version = 1, header_bytes = 256, inputs = 768, qa = 255, s_shift = 6, qw = 1024, qo = 256;
    std::vector<std::uint8_t> king_map = std::vector<std::uint8_t>(64, 0);
    std::vector<std::uint8_t> output_map = std::vector<std::uint8_t>(33, 0);
    std::vector<std::int16_t> w1, b1, l2w, l2o;
    std::vector<std::int32_t> l2b;
    std::vector<std::int64_t> b_out;
};

template <typename T>
void put(std::vector<unsigned char>& out, T value) {
    unsigned char raw[sizeof(T)];
    std::memcpy(raw, &value, sizeof(T));
    out.insert(out.end(), raw, raw + sizeof(T));
}

std::uint64_t fnv(const unsigned char* p, std::size_t n) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (std::size_t i = 0; i < n; ++i) h = (h ^ p[i]) * 0x100000001b3ULL;
    return h;
}

std::vector<unsigned char> serialise(const Spec& s) {
    std::vector<unsigned char> out;
    const char magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '4'};
    out.insert(out.end(), magic, magic + 8);
    put(out, s.version);
    put(out, s.header_bytes);
    put(out, s.inputs);
    put<std::uint32_t>(out, static_cast<std::uint32_t>(s.hidden));
    put<std::uint32_t>(out, static_cast<std::uint32_t>(s.kb));
    put<std::uint32_t>(out, static_cast<std::uint32_t>(s.ob));
    put<std::uint32_t>(out, static_cast<std::uint32_t>(s.l2));
    put(out, s.flags);
    put(out, s.eval_scale);
    put(out, s.qa);
    put(out, s.s_shift);
    put(out, s.qw);
    put(out, s.qo);
    out.insert(out.end(), s.king_map.begin(), s.king_map.end());
    out.insert(out.end(), s.output_map.begin(), s.output_map.end());
    out.resize(256, 0);
    for (const auto v : s.w1) put(out, v);
    for (const auto v : s.b1) put(out, v);
    for (const auto v : s.l2w) put(out, v);
    for (const auto v : s.l2b) put(out, v);
    for (const auto v : s.l2o) put(out, v);
    for (const auto v : s.b_out) put(out, v);
    put(out, fnv(out.data(), out.size()));
    return out;
}

void reseal(std::vector<unsigned char>& bytes) {  // recompute the checksum after an edit
    const std::uint64_t h = fnv(bytes.data(), bytes.size() - 8);
    std::memcpy(bytes.data() + bytes.size() - 8, &h, 8);
}

// Random net inside both loader bounds: |w1| <= wmax, |b1| <= bmax, l2w rows scaled to the int32 bound.
Spec random_spec(std::mt19937_64& rng, int hidden, int kb, int ob, int l2, std::uint32_t flags, int wmax, int bmax) {
    Spec s;
    s.hidden = hidden;
    s.kb = kb;
    s.ob = ob;
    s.l2 = l2;
    s.flags = flags;
    s.eval_scale = static_cast<std::int32_t>(std::uniform_int_distribution<int>(1, 10000)(rng));
    for (auto& m : s.king_map) m = static_cast<std::uint8_t>(std::uniform_int_distribution<int>(0, kb - 1)(rng));
    for (auto& m : s.output_map) m = static_cast<std::uint8_t>(std::uniform_int_distribution<int>(0, ob - 1)(rng));
    std::uniform_int_distribution<int> w(-wmax, wmax), b(-bmax, bmax);
    s.w1.resize(static_cast<std::size_t>(kb) * 768 * static_cast<std::size_t>(hidden));
    for (auto& v : s.w1) v = static_cast<std::int16_t>(w(rng));
    s.b1.resize(static_cast<std::size_t>(hidden));
    for (auto& v : s.b1) v = static_cast<std::int16_t>(b(rng));
    // l2w: |weight| <= cap with 1016 * 2H * cap + |l2b| <= 2^31 - 1.
    const int cap = std::min(32767, static_cast<int>((std::int64_t{2147483647} - 2000000) / (1016 * 2 * hidden)));
    std::uniform_int_distribution<int> lw(-cap, cap);
    s.l2w.resize(static_cast<std::size_t>(l2) * 2 * static_cast<std::size_t>(hidden));
    for (auto& v : s.l2w) v = static_cast<std::int16_t>(lw(rng));
    s.l2b.resize(static_cast<std::size_t>(l2));
    for (auto& v : s.l2b) v = std::uniform_int_distribution<std::int32_t>(-2000000, 2000000)(rng);
    s.l2o.resize(static_cast<std::size_t>(ob) * static_cast<std::size_t>(l2));
    for (auto& v : s.l2o) v = static_cast<std::int16_t>(std::uniform_int_distribution<int>(-32768, 32767)(rng));
    s.b_out.resize(static_cast<std::size_t>(ob));
    for (auto& v : s.b_out) v = std::uniform_int_distribution<std::int64_t>(-(std::int64_t{1} << 40), std::int64_t{1} << 40)(rng);
    return s;
}

// Reference forward from the format text, in int64 (no shortcut shared with the engine).
int reference(const Spec& s, const Board& board) {
    const bool mirror = (s.flags & 2U) != 0;
    const forge::Color us = board.side_to_move();
    std::vector<std::int64_t> sc[2];
    for (int side = 0; side < 2; ++side) {
        const forge::Color p = side == 0 ? us : (us == forge::White ? forge::Black : forge::White);
        const int ksq = board.king_square(p);
        const int kr = p == forge::White ? ksq : (ksq ^ 56);
        const int flip = (mirror && (kr % 8) >= 4) ? 7 : 0;
        const int bucket = s.king_map[static_cast<std::size_t>(kr)];
        std::vector<std::int64_t> a(static_cast<std::size_t>(s.hidden));
        for (int h = 0; h < s.hidden; ++h) a[static_cast<std::size_t>(h)] = s.b1[static_cast<std::size_t>(h)];
        for (int sq = 0; sq < 64; ++sq) {
            const forge::Piece pc = board.piece_at(sq);
            if (pc == forge::Empty) continue;
            const int own = forge::color_of(pc) == p ? 0 : 1;
            const int f = bucket * 768 + (own * 6 + forge::piece_type(pc) - 1) * 64 + ((p == forge::White ? sq : (sq ^ 56)) ^ flip);
            for (int h = 0; h < s.hidden; ++h)
                a[static_cast<std::size_t>(h)] += s.w1[static_cast<std::size_t>(f) * static_cast<std::size_t>(s.hidden) + static_cast<std::size_t>(h)];
        }
        sc[side].resize(static_cast<std::size_t>(s.hidden));
        for (int h = 0; h < s.hidden; ++h) {
            const std::int64_t c = std::clamp<std::int64_t>(a[static_cast<std::size_t>(h)], 0, 255);
            sc[side][static_cast<std::size_t>(h)] = (c * c) >> 6;
        }
    }
    int pieces = 0;
    for (int sq = 0; sq < 64; ++sq) pieces += board.piece_at(sq) != forge::Empty ? 1 : 0;
    const int ob = s.output_map[static_cast<std::size_t>(std::min(pieces, 32))];
    constexpr std::int64_t One = 255LL * 255 * 1024 / 64;
    std::int64_t out = s.b_out[static_cast<std::size_t>(ob)];
    for (int j = 0; j < s.l2; ++j) {
        std::int64_t z = s.l2b[static_cast<std::size_t>(j)];
        for (int i = 0; i < s.hidden; ++i) {
            z += sc[0][static_cast<std::size_t>(i)] * s.l2w[static_cast<std::size_t>(j * 2 * s.hidden + i)];
            z += sc[1][static_cast<std::size_t>(i)] * s.l2w[static_cast<std::size_t>(j * 2 * s.hidden + s.hidden + i)];
        }
        out += std::clamp<std::int64_t>(z, 0, One) * s.l2o[static_cast<std::size_t>(ob * s.l2 + j)];
    }
    const std::int64_t cp = out * s.eval_scale / (One * 256);
    return static_cast<int>(std::clamp<std::int64_t>(cp, -30000, 30000));
}

std::vector<Board> random_positions(std::mt19937_64& rng, int count) {
    std::vector<Board> positions;
    Board board;
    (void)board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    positions.push_back(board);
    while (static_cast<int>(positions.size()) < count) {
        const auto moves = board.legal_moves();
        if (moves.size() == 0 || board.halfmove_clock() >= 100) {
            (void)board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
            continue;
        }
        const auto pick = std::uniform_int_distribution<std::size_t>(0, moves.size() - 1)(rng);
        forge::Undo undo;
        (void)board.make_move(moves[pick], undo);
        positions.push_back(board);
    }
    return positions;
}

void forward_checks(const std::string& label, const Spec& spec, const std::vector<Board>& positions) {
    v4::Net net;
    std::string error;
    const bool ok = v4::parse(serialise(spec), net, error);
    check(ok, label + ": parse (" + error + ")");
    if (!ok) return;
    int ref_mismatch = 0, kernel_mismatch = 0, nonzero = 0;
    std::string first;
    for (const Board& board : positions) {
        const int scalar = v4::evaluate_with(net, board, v4::Kernel::Scalar);
        const int ref = reference(spec, board);
        nonzero += scalar != 0 ? 1 : 0;
        if (scalar != ref && ref_mismatch++ == 0)
            first = board.fen() + " scalar " + std::to_string(scalar) + " reference " + std::to_string(ref);
        if (v4::kernel_available(v4::Kernel::Avx2)) {
            const int avx2 = v4::evaluate_with(net, board, v4::Kernel::Avx2);
            if (avx2 != scalar && kernel_mismatch++ == 0)
                first += " | " + board.fen() + " avx2 " + std::to_string(avx2) + " scalar " + std::to_string(scalar);
        }
    }
    check(ref_mismatch == 0 && kernel_mismatch == 0,
          label + ": " + std::to_string(ref_mismatch) + " reference and " + std::to_string(kernel_mismatch) +
              " AVX2 mismatches in " + std::to_string(positions.size()) + " positions " + first);
    check(nonzero > static_cast<int>(positions.size()) / 2, label + ": the net is not trivially zero (" +
                                                             std::to_string(nonzero) + " non-zero)");
    std::cout << "PASS-INFO " << label << ": " << positions.size() << " positions, scalar == reference"
              << (v4::kernel_available(v4::Kernel::Avx2) ? " == avx2" : " (no AVX2 in this build)") << '\n';
}

void reject(const std::string& what, const Spec& base, const std::function<void(std::vector<unsigned char>&)>& edit,
            bool reseal_after = true) {
    std::vector<unsigned char> bytes = serialise(base);
    edit(bytes);
    if (reseal_after && bytes.size() >= 264) reseal(bytes);
    v4::Net net;
    std::string error;
    const bool ok = v4::parse(bytes, net, error);
    check(!ok && !error.empty(), "refuses " + what + (ok ? " (accepted)" : " (" + error + ")"));
}

void set_u32(std::vector<unsigned char>& b, std::size_t at, std::uint32_t v) { std::memcpy(b.data() + at, &v, 4); }

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_r5c_v4_tests <scratch dir> [positions per net]\n";
        return 2;
    }
    const std::filesystem::path dir(argv[1]);
    std::filesystem::create_directories(dir);
    const int per_net = argc >= 3 ? std::max(10, std::atoi(argv[2])) : 3000;
    std::mt19937_64 rng(20261029);

    check(v4::file_size_for(512, 8, 8, 16) == 6325896, "file size formula: KB 8, H 512, L2 16, OB 8 = 6,325,896 bytes");
    check(v4::file_size_for(32, 1, 1, 16) == 0 && v4::file_size_for(64, 33, 1, 16) == 0, "file size 0 for bad shapes");
    check(v4::One == 1040400 && v4::SMax == 1016, "ONE 1,040,400 and SMax 1016");

    const std::vector<Board> positions = random_positions(rng, per_net);

    // Forward: several shapes and both flags.
    struct Shape { int hidden, kb, ob, l2; std::uint32_t flags; };
    const Shape shapes[] = {{64, 1, 1, 16, 0}, {128, 4, 8, 16, 2}, {64, 32, 16, 1, 1}, {192, 8, 8, 64, 3}, {512, 8, 8, 16, 2}};
    for (const Shape& sh : shapes) {
        const Spec spec = random_spec(rng, sh.hidden, sh.kb, sh.ob, sh.l2, sh.flags, 900, 1000);
        forward_checks("H" + std::to_string(sh.hidden) + " KB" + std::to_string(sh.kb) + " OB" + std::to_string(sh.ob) +
                           " L2 " + std::to_string(sh.l2) + " flags " + std::to_string(sh.flags),
                       spec, sh.hidden == 512 ? std::vector<Board>(positions.begin(), positions.begin() + per_net / 10)
                                              : positions);
    }
    // Accumulator bound reached exactly: every w1 entry +1000 and b1 767 (767 + 32 * 1000 = 32767), start position.
    {
        Spec spec = random_spec(rng, 64, 1, 1, 16, 0, 1, 1);
        std::fill(spec.w1.begin(), spec.w1.end(), static_cast<std::int16_t>(1000));
        std::fill(spec.b1.begin(), spec.b1.end(), static_cast<std::int16_t>(767));
        v4::Net net;
        std::string error;
        check(v4::parse(serialise(spec), net, error), "accumulator bound exactly 32767 is accepted (" + error + ")");
        forward_checks("accumulator at the bound", spec, std::vector<Board>(positions.begin(), positions.begin() + 50));
        spec.b1[3] = 768;
        reject("max|b1| + 32 * max|w1| = 32768", spec, [](std::vector<unsigned char>&) {});
    }
    // Refusals (one broken field each; the checksum is recomputed unless the checksum itself is the test).
    const Spec good = random_spec(rng, 64, 2, 2, 16, 0, 900, 1000);
    {
        v4::Net net;
        std::string error;
        check(v4::parse(serialise(good), net, error), "the reference image parses (" + error + ")");
    }
    reject("a wrong magic", good, [](auto& b) { b[7] = '3'; });
    reject("version 2", good, [](auto& b) { set_u32(b, 8, 2); });
    reject("header_bytes 192", good, [](auto& b) { set_u32(b, 12, 192); });
    reject("inputs 769", good, [](auto& b) { set_u32(b, 16, 769); });
    reject("hidden 96 (not a multiple of 64)", good, [](auto& b) { set_u32(b, 20, 96); });
    reject("king_buckets 0", good, [](auto& b) { set_u32(b, 24, 0); });
    reject("output_buckets 17", good, [](auto& b) { set_u32(b, 28, 17); });
    reject("l2 65", good, [](auto& b) { set_u32(b, 32, 65); });
    reject("an unknown flag bit", good, [](auto& b) { set_u32(b, 36, 4); });
    reject("eval_scale 0", good, [](auto& b) { set_u32(b, 40, 0); });
    reject("qa 256", good, [](auto& b) { set_u32(b, 44, 256); });
    reject("s_shift 7", good, [](auto& b) { set_u32(b, 48, 7); });
    reject("qw 512", good, [](auto& b) { set_u32(b, 52, 512); });
    reject("qo 128", good, [](auto& b) { set_u32(b, 56, 128); });
    reject("a king_map value >= KB", good, [](auto& b) { b[60 + 17] = 2; });
    reject("an output_map value >= OB", good, [](auto& b) { b[124 + 32] = 2; });
    reject("a non-zero reserved byte", good, [](auto& b) { b[200] = 1; });
    reject("one byte too many", good, [](auto& b) { b.insert(b.end() - 8, 0); });
    reject("one byte too few", good, [](auto& b) { b.erase(b.begin() + 300); });
    reject("a flipped checksum bit", good, [](auto& b) { b[b.size() - 1] ^= 1; }, false);
    reject("a flipped weight bit (checksum kept)", good, [](auto& b) { b[400] ^= 1; }, false);
    reject("a file shorter than the header", good, [](auto& b) { b.resize(100); }, false);
    {
        Spec bad = good;
        bad.b_out[1] = (std::int64_t{1} << 40) + 1;
        reject("b_out beyond 2^40", bad, [](auto&) {});
        Spec bad2 = good;  // layer-2 bound: |l2b| + 1016 * sum|w| > 2^31 - 1
        std::fill(bad2.l2w.begin(), bad2.l2w.begin() + 2 * bad2.hidden, static_cast<std::int16_t>(16600));
        reject("a layer-2 row beyond the int32 bound", bad2, [](auto&) {});
    }
    // load(): file round trip; a failed load keeps the previous net.
    {
        const auto good_path = (dir / "good.fnn4").string();
        const auto bad_path = (dir / "bad.fnn4").string();
        const auto missing = (dir / "missing.fnn4").string();
        const std::vector<unsigned char> image = serialise(good);
        std::ofstream(good_path, std::ios::binary).write(reinterpret_cast<const char*>(image.data()), static_cast<std::streamsize>(image.size()));
        std::vector<unsigned char> truncated(image.begin(), image.end() - 1000);
        std::ofstream(bad_path, std::ios::binary).write(reinterpret_cast<const char*>(truncated.data()), static_cast<std::streamsize>(truncated.size()));
        v4::unload();
        std::string error;
        check(v4::load(good_path, error) && v4::loaded() != nullptr, "load() of a valid file (" + error + ")");
        const std::uint64_t sum = v4::loaded() != nullptr ? v4::loaded()->checksum : 0;
        error.clear();
        check(!v4::load(bad_path, error) && error.find("file size") != std::string::npos,
              "load() refuses a truncated file by its size (" + error + ")");
        check(v4::loaded() != nullptr && v4::loaded()->checksum == sum, "a failed load keeps the loaded net");
        error.clear();
        check(!v4::load(missing, error) && !error.empty(), "load() of a missing file fails (" + error + ")");
        v4::requested = true;
        v4::refresh_active();
        const bool active_with_net = v4::active;
        v4::unload();
        check(v4::loaded() == nullptr && !v4::active, "unload() leaves no net and v4 inactive");
        v4::requested = false;
        v4::refresh_active();
        check(active_with_net, "requested + loaded + UseNNUE makes v4 active");
    }
    std::cout << "r5c v4: " << checks << " checks, " << failures << " failures\n";
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " forge_r5c_v4_tests\n";
    return failures == 0 ? 0 : 1;
}
