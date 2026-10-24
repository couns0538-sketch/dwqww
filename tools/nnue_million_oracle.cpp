// Original deterministic actual-API oracle. Link this identical source against
// each frozen core; tools/nnue_million_oracle.py compares the original bytes.
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <cfenv>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#endif
#if defined(_WIN32)
#include <cstdio>
#include <fcntl.h>
#include <io.h>
#endif

namespace {
constexpr std::uint64_t Seed = 0x243f6a8885a308d3ULL;
constexpr std::uint32_t RecordBytes = 104U + 2U * (2U * forge::nnue::HiddenSize * 4U + 8U);
constexpr std::array<const char*, 10> Starts{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
    "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
    "4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
};
std::uint64_t random_state = Seed;
std::uint64_t random_word() {
    random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return random_state;
}
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
void emit32(std::uint32_t value) {
    char bytes[4];
    for (int i = 0; i < 4; ++i) bytes[i] = static_cast<char>((value >> (8 * i)) & 255U);
    std::cout.write(bytes, sizeof bytes);
}
void emit64(std::uint64_t value) {
    emit32(static_cast<std::uint32_t>(value));
    emit32(static_cast<std::uint32_t>(value >> 32U));
}
bool same(const forge::nnue::Accumulator& a, const forge::nnue::Accumulator& b) {
    if (a.valid != b.valid) return false;
    for (std::size_t side = 0; side < a.values.size(); ++side)
        for (std::size_t h = 0; h < a.values[side].size(); ++h)
            if (std::bit_cast<std::uint32_t>(a.values[side][h]) !=
                std::bit_cast<std::uint32_t>(b.values[side][h])) return false;
    return true;
}
struct Coverage {
    std::uint64_t records = 0, fresh = 0, updates = 0, parent = 0, inplace = 0, starts = 0;
    std::uint32_t games = 0;
    std::array<std::uint32_t, 2> moves{}, captures{}, ep{};
    std::array<std::array<std::uint32_t, 2>, 2> castles{};
    std::array<std::array<std::uint32_t, 4>, 2> quiet_promotions{}, capture_promotions{};
} coverage;

void emit_accumulator(const forge::Board& board, const forge::nnue::Accumulator& acc) {
    require(acc.valid, "invalid actual accumulator");
    for (const auto& side : acc.values)
        for (float value : side) {
            require(std::isfinite(value), "nonfinite actual accumulator");
            emit32(std::bit_cast<std::uint32_t>(value));
        }
    emit32(static_cast<std::uint32_t>(forge::nnue::evaluate(board, acc)));
    emit32(acc.valid ? 1U : 0U);
}
void snapshot(const forge::Board& board, const forge::nnue::Accumulator& incremental,
              std::uint32_t ply, std::uint32_t kind, forge::Move move) {
    forge::nnue::Accumulator fresh;
    forge::nnue::refresh(board, fresh);
    ++coverage.fresh;
    emit64(coverage.records++);
    emit64(board.key());
    emit32(coverage.games - 1U);
    emit32(ply);
    emit32(kind);
    emit32(static_cast<std::uint32_t>(move.from) |
           (static_cast<std::uint32_t>(move.to) << 8U) |
           (static_cast<std::uint32_t>(move.promotion) << 16U) |
           (static_cast<std::uint32_t>(move.flags) << 24U));
    emit32(static_cast<std::uint32_t>(board.side_to_move()));
    emit32(0U);
    for (int square = 0; square < 64; ++square)
        std::cout.put(static_cast<char>(board.piece_at(square)));
    // These are compared to the corresponding fields in the other core, not
    // asserted equal to one another: their addition histories may differ.
    emit_accumulator(board, incremental);
    emit_accumulator(board, fresh);
}
void record_move(forge::Color color, forge::Move move) {
    const auto side = static_cast<std::size_t>(color);
    ++coverage.moves[side];
    if (move.is_capture()) ++coverage.captures[side];
    if ((move.flags & forge::EnPassant) != 0U) ++coverage.ep[side];
    if (move.is_castle()) ++coverage.castles[side][(move.flags & forge::KingCastle) != 0U ? 0U : 1U];
    if (move.is_promotion()) {
        require(move.promotion >= forge::Knight && move.promotion <= forge::Queen, "invalid promotion");
        auto& counts = move.is_capture() ? coverage.capture_promotions : coverage.quiet_promotions;
        ++counts[side][static_cast<std::size_t>(move.promotion - forge::Knight)];
    }
}
forge::nnue::Accumulator transition(forge::Board& board, const forge::nnue::Accumulator& parent,
                                  forge::Move move, forge::Undo& undo) {
    const auto dirty = forge::nnue::dirty_pieces(board, move);
    const auto before = parent;
    record_move(board.side_to_move(), move);
    require(board.make_move(move, undo), "legal move rejected");
    forge::nnue::Accumulator child;
    for (auto& side : child.values) side.fill(-0x1.fffffep10F);
    forge::nnue::update(parent, child, dirty);
    ++coverage.updates;
    require(same(parent, before), "distinct update modified parent");
    ++coverage.parent;
    auto inplace = parent;
    forge::nnue::update(inplace, inplace, dirty);
    require(child.valid && same(child, inplace), "in-place and distinct updates differ");
    ++coverage.inplace;
    return child;
}
forge::nnue::Accumulator start(forge::Board& board, const char* fen) {
    require(board.set_fen(fen), "invalid fixture");
    ++coverage.games;
    ++coverage.starts;
    forge::nnue::Accumulator acc;
    forge::nnue::refresh(board, acc);
    snapshot(board, acc, 0U, 0U, forge::Move::none());
    return acc;
}
void emit_header(std::uint64_t count, std::uint64_t seed) {
    emit32(0x314f4d4eU); // NMO1
    emit32(1U);
    emit32(static_cast<std::uint32_t>(forge::nnue::HiddenSize));
    emit32(RecordBytes);
    emit64(count);
    emit64(seed);
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
    emit32(_mm_getcsr() & 0x0000ffc0U);
#else
    emit32(0xffffffffU);
#endif
    emit32(static_cast<std::uint32_t>(std::fegetround()));
    emit32(192U);
    emit32(static_cast<std::uint32_t>(Starts.size()));
    emit32(2U);
    emit32(0U); emit32(0U); emit32(0U);
}
template<std::size_t N>
void json_array(const std::array<std::uint32_t, N>& values) {
    std::cerr << '[';
    for (std::size_t i = 0; i < N; ++i) {
        if (i != 0U) std::cerr << ',';
        std::cerr << values[i];
    }
    std::cerr << ']';
}
template<std::size_t Rows, std::size_t Cols>
void json_matrix(const std::array<std::array<std::uint32_t, Cols>, Rows>& values) {
    std::cerr << '[';
    for (std::size_t i = 0; i < Rows; ++i) {
        if (i != 0U) std::cerr << ',';
        json_array(values[i]);
    }
    std::cerr << ']';
}
void emit_trailer(std::uint64_t count, std::uint64_t seed) {
    require(coverage.records == count && coverage.fresh == count &&
            coverage.updates + coverage.starts == count &&
            coverage.parent == coverage.updates && coverage.inplace == coverage.updates,
            "position/API coverage count mismatch");
    emit32(0x544f4d4eU); // NMOT
    emit32(1U);
    emit64(coverage.records); emit64(coverage.fresh); emit64(coverage.updates);
    emit64(coverage.parent); emit64(coverage.inplace); emit64(coverage.games); emit64(coverage.starts);
    for (auto n : coverage.moves) emit32(n);
    for (auto n : coverage.captures) { require(n != 0U, "missing capture color"); emit32(n); }
    for (auto n : coverage.ep) { require(n != 0U, "missing en-passant color"); emit32(n); }
    for (const auto& side : coverage.castles)
        for (auto n : side) { require(n != 0U, "missing castle side/color"); emit32(n); }
    for (const auto& side : coverage.quiet_promotions)
        for (auto n : side) { require(n != 0U, "missing quiet promotion type/color"); emit32(n); }
    for (const auto& side : coverage.capture_promotions)
        for (auto n : side) { require(n != 0U, "missing capture promotion type/color"); emit32(n); }
    for (int i = 42; i < 64; ++i) emit32(0U);
    std::cerr << "records=" << coverage.records << " refresh=" << coverage.fresh
              << " updates=" << coverage.updates << " parent_checks=" << coverage.parent
              << " inplace_checks=" << coverage.inplace << " games=" << coverage.games
              << " genuine_boards=yes special_moves=both_colors_all_promotions\n";
    std::cerr << "{\"kind\":\"nnue_million_oracle\",\"positions\":" << count
              << ",\"records\":" << coverage.records << ",\"seed\":" << seed
              << ",\"refresh\":" << coverage.fresh << ",\"updates\":" << coverage.updates
              << ",\"parent_checks\":" << coverage.parent
              << ",\"inplace_checks\":" << coverage.inplace << ",\"games\":" << coverage.games
              << ",\"starts\":" << coverage.starts << ",\"moves\":";
    json_array(coverage.moves);
    std::cerr << ",\"captures\":"; json_array(coverage.captures);
    std::cerr << ",\"en_passant\":"; json_array(coverage.ep);
    std::cerr << ",\"castles\":"; json_matrix(coverage.castles);
    std::cerr << ",\"quiet_promotions\":"; json_matrix(coverage.quiet_promotions);
    std::cerr << ",\"capture_promotions\":"; json_matrix(coverage.capture_promotions);
    std::cerr << ",\"genuine_boards\":true}\n";
}
std::uint64_t unsigned_argument(std::string_view value) {
    std::uint64_t result = 0;
    const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
    require(!value.empty() && parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size(),
            "invalid unsigned decimal argument");
    return result;
}
void wait_for_start() {
    std::string line;
    require(static_cast<bool>(std::getline(std::cin, line)), "start command required on stdin");
    if (!line.empty() && line.back() == '\r') line.pop_back();
    require(line == "start", "expected start command on stdin");
}
} // namespace

int main(int argc, char** argv) {
    try {
#if defined(_WIN32)
        require(_setmode(_fileno(stdout), _O_BINARY) != -1, "binary stdout unavailable");
#endif
        std::uint64_t count = 1000000U;
        std::uint64_t seed = Seed;
        bool wait_start = false, positions_seen = false, seed_seen = false;
        for (int i = 1; i < argc; ++i) {
            const std::string_view option(argv[i]);
            if (option == "--positions" || option == "--seed") {
                require(i + 1 < argc, "option requires an unsigned decimal argument");
                auto& seen = option == "--positions" ? positions_seen : seed_seen;
                require(!seen, "duplicate option");
                seen = true;
                auto& value = option == "--positions" ? count : seed;
                value = unsigned_argument(argv[++i]);
            } else if (option == "--wait-start") {
                require(!wait_start, "duplicate option");
                wait_start = true;
            } else {
                throw std::runtime_error("usage: nnue_million_oracle [--positions COUNT] [--seed UINT64] [--wait-start]");
            }
        }
        require(count >= 1024U && count <= std::numeric_limits<std::uint32_t>::max(),
                "position count must be in [1024, 4294967295]");
        std::ios::sync_with_stdio(false);
        if (wait_start) wait_for_start();
        random_state = seed;
        require(forge::nnue::available(), "NNUE network required");
        require(std::fegetround() == FE_TONEAREST, "round-to-nearest required");
        emit_header(count, seed);
        forge::Board board;
        // Exhaust legal first moves before any random choices, guaranteeing
        // captures, both castles, EP and all promotions for both colors.
        for (const char* fen : Starts) {
            const auto parent = start(board, fen);
            for (auto move : board.legal_moves()) {
                forge::Undo undo;
                const auto child = transition(board, parent, move, undo);
                snapshot(board, child, 1U, 1U, move);
                board.unmake_move(move, undo);
            }
        }
        require(coverage.records < count, "fixtures exceed requested count");
        while (coverage.records < count) {
            // Each independent walk is bounded to 192 legal plies, preserving
            // middlegame diversity rather than spending the corpus on lone kings.
            const auto fixture = static_cast<std::size_t>(random_word() % Starts.size());
            auto acc = start(board, Starts[fixture]);
            for (std::uint32_t ply = 1U; ply <= 192U && coverage.records < count; ++ply) {
                const auto moves = board.legal_moves();
                if (moves.empty()) break;
                const auto move = moves[static_cast<std::size_t>(random_word() % moves.size())];
                forge::Undo undo;
                acc = transition(board, acc, move, undo);
                snapshot(board, acc, ply, 2U, move);
            }
        }
        emit_trailer(count, seed);
        std::cout.flush();
        require(static_cast<bool>(std::cout), "oracle stdout write failed");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "nnue_million_oracle: " << error.what() << '\n';
        return 1;
    }
}
