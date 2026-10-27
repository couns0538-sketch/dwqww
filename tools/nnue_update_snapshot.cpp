// Link this same driver against each frozen core and compare stdout with cmp.
// The oracle is the other executable's actual NNUE API, not a copied updater.
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#endif
#if defined(_WIN32)
#include <cstdio>
#include <fcntl.h>
#include <io.h>
#endif

namespace {

std::uint64_t random_state = 0x243f6a8885a308d3ULL;
std::uint64_t random_word() {
    random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return random_state;
}

struct Coverage {
    std::uint32_t cases = 0;
    std::uint32_t snapshots = 0;
    std::uint32_t parent_checks = 0;
    std::uint32_t in_place_checks = 0;
    std::array<std::array<std::uint32_t, 16>, 5> dirty_masks{};
    std::array<std::uint32_t, 2> moves{};
    std::array<std::uint32_t, 2> null_moves{};
    std::array<std::array<std::uint32_t, 2>, 2> castles{};
    std::array<std::uint32_t, 2> en_passant{};
    std::array<std::array<std::uint32_t, 4>, 2> quiet_promotions{};
    std::array<std::array<std::uint32_t, 4>, 2> capture_promotions{};
} coverage;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void emit(std::uint32_t word) {
    // Fixed little-endian words, without struct padding or platform newlines.
    for (int shift = 0; shift < 32; shift += 8)
        std::cout.put(static_cast<char>((word >> shift) & 255U));
}

bool same_values(const forge::nnue::Accumulator& a, const forge::nnue::Accumulator& b) {
    for (std::size_t side = 0; side < a.values.size(); ++side)
        for (std::size_t h = 0; h < a.values[side].size(); ++h)
            if (std::bit_cast<std::uint32_t>(a.values[side][h]) !=
                std::bit_cast<std::uint32_t>(b.values[side][h])) return false;
    return true;
}

void snapshot(const forge::Board& board, const forge::nnue::Accumulator& accumulator,
              std::uint32_t kind, std::uint32_t case_id) {
    emit(kind);
    emit(case_id);
    for (const auto& side : accumulator.values) {
        for (float value : side) {
            require(std::isfinite(value), "nonfinite output accumulator");
            emit(std::bit_cast<std::uint32_t>(value));
        }
    }
    emit(static_cast<std::uint32_t>(forge::nnue::evaluate(board, accumulator)));
    emit(accumulator.valid ? 1U : 0U);
    ++coverage.snapshots;
}

forge::nnue::Accumulator update_case(const forge::Board& board,
                                    const forge::nnue::Accumulator& input,
                                    const forge::nnue::DirtyPieces& dirty) {
    require(dirty.count >= 0 && dirty.count <= 4, "invalid driver dirty count");
    unsigned mask = 0;
    for (int i = 0; i < dirty.count; ++i)
        if (dirty.changes[static_cast<std::size_t>(i)].add) mask |= 1U << i;
    ++coverage.dirty_masks[static_cast<std::size_t>(dirty.count)][mask];
    const std::uint32_t case_id = coverage.cases++;
    const forge::nnue::Accumulator before = input;
    forge::nnue::Accumulator child;
    for (auto& side : child.values) side.fill(-0x1.fffffep10F);
    child.valid = false;
    forge::nnue::update(input, child, dirty);
    require(same_values(input, before) && input.valid == before.valid,
            "distinct update changed its parent");
    ++coverage.parent_checks;
    require(child.valid, "distinct update did not mark its child valid");
    if (dirty.count == 0) require(same_values(child, input), "zero-count update did not copy values");
    snapshot(board, child, 1U, case_id);

    forge::nnue::Accumulator in_place = input;
    forge::nnue::update(in_place, in_place, dirty);
    require(in_place.valid, "in-place update did not mark its child valid");
    require(same_values(child, in_place), "distinct and in-place updates differ");
    ++coverage.in_place_checks;
    snapshot(board, in_place, 2U, case_id);
    return child;
}

void record_move(forge::Color color, forge::Move move) {
    const auto side = static_cast<std::size_t>(color);
    ++coverage.moves[side];
    if (move.is_castle())
        ++coverage.castles[side][(move.flags & forge::KingCastle) != 0U ? 0U : 1U];
    if ((move.flags & forge::EnPassant) != 0U) ++coverage.en_passant[side];
    if (move.is_promotion()) {
        require(move.promotion >= forge::Knight && move.promotion <= forge::Queen,
                "unexpected promotion type");
        const auto type = static_cast<std::size_t>(move.promotion - forge::Knight);
        auto& counts = move.is_capture() ? coverage.capture_promotions : coverage.quiet_promotions;
        ++counts[side][type];
    }
}

void legal_cases() {
    // Every legal first move guarantees both colors' castles, en passant, and
    // all four quiet/capturing promotions; the walks also exercise chained updates.
    constexpr std::array<const char*, 10> starts{
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
    forge::Board board;
    for (const char* fen : starts) {
        require(board.set_fen(fen), "invalid legal fixture");
        forge::nnue::Accumulator accumulator;
        forge::nnue::refresh(board, accumulator);
        require(accumulator.valid, "refresh did not mark its accumulator valid");
        snapshot(board, accumulator, 3U, coverage.cases);
        for (const auto move : board.legal_moves()) {
            const auto dirty = forge::nnue::dirty_pieces(board, move);
            record_move(board.side_to_move(), move);
            forge::Undo undo;
            require(board.make_move(move, undo), "legal first move rejected");
            (void)update_case(board, accumulator, dirty);
            forge::nnue::Accumulator fresh;
            forge::nnue::refresh(board, fresh);
            snapshot(board, fresh, 4U, coverage.cases - 1U);
            board.unmake_move(move, undo);
        }
        if (!board.in_check()) {
            ++coverage.null_moves[static_cast<std::size_t>(board.side_to_move())];
            forge::NullUndo undo;
            board.make_null_move(undo);
            (void)update_case(board, accumulator, forge::nnue::DirtyPieces{});
            board.unmake_null_move(undo);
        }
        for (int ply = 0; ply < 48; ++ply) {
            const auto moves = board.legal_moves();
            if (moves.empty()) break;
            const auto move = moves[static_cast<std::size_t>(random_word() % moves.size())];
            const auto dirty = forge::nnue::dirty_pieces(board, move);
            record_move(board.side_to_move(), move);
            forge::Undo undo;
            require(board.make_move(move, undo), "legal walk move rejected");
            accumulator = update_case(board, accumulator, dirty);
            forge::nnue::Accumulator fresh;
            forge::nnue::refresh(board, fresh);
            snapshot(board, fresh, 4U, coverage.cases - 1U);
        }
    }
}

void synthetic_cases() {
    // Input generation uses constants/random bits only, independently of either
    // core. Repeated features additionally exercise subtract/add cancellation.
    constexpr std::array<float, 24> edges{
        -0.0F, 0.0F, -0x1p-149F, 0x1p-149F,
        -0x1.fffffcp-127F, 0x1.fffffcp-127F, -0x1p-126F, 0x1p-126F,
        -0x1p-12F, 0x1p-12F, -0x1.fffffep-1F, 0x1.fffffep-1F,
        -1.0F, 1.0F, -0x1.000002p0F, 0x1.000002p0F,
        -0x1p13F, 0x1p13F, -0x1.000002p13F, 0x1.000002p13F,
        -0x1p24F, 0x1p24F, -0x1.fffffep127F, 0x1.fffffep127F
    };
    forge::Board board;
    for (int count = 0; count <= 4; ++count) {
        for (unsigned mask = 0; mask < (1U << count); ++mask) {
            for (int sample = 0; sample < 32; ++sample) {
                require(board.set_fen(sample % 2 == 0 ? forge::Board::StandardStartFen :
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
                    "invalid synthetic side fixture");
                forge::nnue::DirtyPieces dirty;
                for (int i = 0; i < count; ++i) {
                    const auto word = random_word();
                    auto piece = static_cast<forge::Piece>(1U + (word >> 32U) % 12U);
                    int square = static_cast<int>((word >> 8U) % 64U);
                    if (i == 1 && sample % 4 == 0) {
                        piece = dirty.changes[0].piece;
                        square = dirty.changes[0].square;
                    }
                    if ((mask & (1U << i)) != 0U) dirty.add(piece, square);
                    else dirty.remove(piece, square);
                }
                forge::nnue::Accumulator parent;
                parent.valid = sample % 2 != 0;
                std::size_t lane = 0;
                for (auto& side : parent.values) {
                    for (float& value : side) {
                        const auto word = random_word();
                        if (sample < 16) value = edges[(lane + static_cast<std::size_t>(sample)) % edges.size()];
                        else if (sample < 24)
                            value = static_cast<float>(static_cast<int>((word >> 32U) % 16385U) - 8192) / 4096.0F;
                        else {
                            auto bits = static_cast<std::uint32_t>(word >> 32U);
                            if ((bits & 0x7f800000U) == 0x7f800000U) bits ^= 0x00800000U;
                            value = std::bit_cast<float>(bits);
                        }
                        ++lane;
                    }
                }
                (void)update_case(board, parent, dirty);
            }
        }
    }
}

void emit_coverage() {
    require(coverage.parent_checks == coverage.cases && coverage.in_place_checks == coverage.cases,
            "incomplete API invariant checks");
    for (std::size_t side = 0; side < 2; ++side) {
        require(coverage.moves[side] != 0 && coverage.null_moves[side] != 0,
                "missing both-color real move/null coverage");
        require(coverage.castles[side][0] != 0 && coverage.castles[side][1] != 0 &&
                coverage.en_passant[side] != 0, "missing both-color special-move coverage");
        for (std::size_t type = 0; type < 4; ++type)
            require(coverage.quiet_promotions[side][type] != 0 && coverage.capture_promotions[side][type] != 0,
                    "missing both-color quiet/capture promotion coverage");
    }
    emit(0x45564f43U); // COVE trailer in little-endian byte order
    emit(coverage.cases);
    emit(coverage.snapshots);
    emit(coverage.parent_checks);
    emit(coverage.in_place_checks);
    for (std::size_t count = 0; count <= 4; ++count) {
        for (std::size_t mask = 0; mask < (std::size_t{1} << count); ++mask) {
            require(coverage.dirty_masks[count][mask] >= 32U, "missing synthetic dirty mask coverage");
            emit(coverage.dirty_masks[count][mask]);
        }
    }
    for (std::size_t side = 0; side < 2; ++side) {
        emit(coverage.moves[side]);
        emit(coverage.null_moves[side]);
        for (auto count : coverage.castles[side]) emit(count);
        emit(coverage.en_passant[side]);
        for (auto count : coverage.quiet_promotions[side]) emit(count);
        for (auto count : coverage.capture_promotions[side]) emit(count);
    }
    std::cerr << "cases=" << coverage.cases << " snapshots=" << coverage.snapshots
              << " parent_checks=" << coverage.parent_checks
              << " in_place_checks=" << coverage.in_place_checks
              << " synthetic_cases=992 all_dirty_masks=31 special_move_coverage=both_colors\n";
}

} // namespace

int main() {
    try {
#if defined(_WIN32)
        require(_setmode(_fileno(stdout), _O_BINARY) != -1, "binary stdout unavailable");
#endif
        require(forge::nnue::available(), "NNUE weights are required");
        require(std::fegetround() == FE_TONEAREST, "round-to-nearest is required");
        emit(0x3155554eU); // NUU1 format/version marker in little-endian byte order
        emit(static_cast<std::uint32_t>(forge::nnue::HiddenSize));
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
        // Record FTZ/DAZ, rounding and exception masks, excluding sticky flags.
        emit(_mm_getcsr() & 0x0000ffc0U);
#else
        emit(0xffffffffU); // Non-SSE floating-point control is frozen externally.
#endif
        legal_cases();
        synthetic_cases();
        emit_coverage();
        std::cout.flush();
        require(static_cast<bool>(std::cout), "snapshot output failed");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "nnue_update_snapshot: " << error.what() << '\n';
        return 1;
    }
}
