// Standalone validation driver. Include the actual searched implementation so
// the file-local material-key function is exercised, rather than a copied table.
// Link against the matching frozen libforge_core.a without whole-archive.
#include "src/search.cpp"

#include <bit>
#include <charconv>
#include <cfenv>
#include <stdexcept>
#include <string>
#include <string_view>
#if defined(__SSE__)
#include <xmmintrin.h>
#endif
#if defined(_WIN32)
#include <cstdio>
#include <fcntl.h>
#include <io.h>
#endif

namespace {
constexpr std::size_t Slots = 10;
constexpr std::size_t CountValues = 65;
constexpr std::size_t RecordBytes = 8 + 8 + 4 + 2 * forge::nnue::HiddenSize * sizeof(float);
void require(bool good, const char* message) {
    if (!good) throw std::runtime_error(message);
}

std::uint64_t polynomial(const std::array<std::uint64_t, Slots>& counts) {
    std::uint64_t result = 0;
    for (const auto count : counts) result = result * 1099511628211ULL + count + 1U;
    return result * 0x9E3779B97F4A7C15ULL;
}

std::uint64_t original_key(const forge::Board& board) {
    std::array<std::uint64_t, Slots> counts{};
    std::size_t index = 0;
    for (const forge::Color color : {forge::White, forge::Black}) {
        for (int type = forge::Pawn; type <= forge::Queen; ++type) {
            counts[index++] = static_cast<std::uint64_t>(forge::popcount(board.pieces(color, static_cast<forge::PieceType>(type))));
        }
    }
    return polynomial(counts);
}

std::uint64_t checked_key(const forge::Board& board) {
    const auto actual = forge::material_key(board);
    require(actual == original_key(board), "actual material_key differs from the original polynomial");
    return actual;
}

std::uint64_t table_proof() {
#if defined(S11_REQUIRE_TABLE)
    static_assert(forge::MaterialKeyContributions.size() == Slots);
    static_assert(forge::MaterialKeyContributions[0].size() == CountValues);
    std::uint64_t checks = 0;
    for (std::size_t slot = 0; slot < Slots; ++slot) {
        for (std::size_t count = 0; count < CountValues; ++count) {
            std::array<std::uint64_t, Slots> basis{};
            basis[slot] = count;
            std::uint64_t actual = 0;
            for (std::size_t index = 0; index < Slots; ++index) {
                actual += forge::MaterialKeyContributions[index][basis[index]];
            }
            require(actual == polynomial(basis), "actual constexpr table basis mismatch");
            ++checks;
        }
    }
    return checks;
#else
    return 0;
#endif
}

struct State {
    std::string fen;
    std::uint64_t key;
    std::uint64_t pawn_key;
    forge::Bitboard checkers;
    std::vector<std::uint64_t> history;
    std::array<forge::Bitboard, 13> pieces;
    std::array<forge::Bitboard, 2> occupancy;
    std::array<int, 2> kings;
};

State state(const forge::Board& board) {
    State result{board.fen(), board.key(), board.pawn_key(), board.checkers(), board.key_history(), {}, {}, {}};
    for (int piece = 0; piece < 13; ++piece) result.pieces[static_cast<std::size_t>(piece)] = board.pieces(static_cast<forge::Piece>(piece));
    for (const auto color : {forge::White, forge::Black}) {
        result.occupancy[static_cast<std::size_t>(color)] = board.occupied(color);
        result.kings[static_cast<std::size_t>(color)] = board.king_square(color);
    }
    return result;
}

void unchanged(const forge::Board& board, const State& previous) {
    const auto now = state(board);
    require(now.fen == previous.fen && now.key == previous.key && now.pawn_key == previous.pawn_key &&
            now.checkers == previous.checkers && now.history == previous.history && now.pieces == previous.pieces &&
            now.occupancy == previous.occupancy && now.kings == previous.kings, "make/unmake state changed");
}

template<typename Word> void word(Word value) {
    for (std::size_t byte = 0; byte < sizeof(Word); ++byte) std::cout.put(static_cast<char>((value >> (byte * 8U)) & 255U));
}

void snapshot(const forge::Board& board, std::uint64_t key) {
    forge::nnue::Accumulator accumulator;
    forge::nnue::refresh(board, accumulator);
    const auto eval = forge::nnue::evaluate(board, accumulator);
    std::array<char, RecordBytes> bytes{};
    std::size_t offset = 0;
    auto append = [&]<typename Word>(Word value) {
        for (std::size_t byte = 0; byte < sizeof(Word); ++byte) bytes[offset++] = static_cast<char>((value >> (byte * 8U)) & 255U);
    };
    append(key);
    append(board.key());
    append(static_cast<std::uint32_t>(eval));
    for (const auto& perspective : accumulator.values)
        for (float value : perspective) append(std::bit_cast<std::uint32_t>(value));
    require(offset == bytes.size(), "snapshot size mismatch");
    std::cout.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
}

std::uint64_t number(std::string_view text) {
    std::uint64_t value = 0;
    const auto parsed = std::from_chars(text.data(), text.data() + text.size(), value);
    require(parsed.ec == std::errc{} && parsed.ptr == text.data() + text.size(), "invalid unsigned count");
    return value;
}
}

int main(int argc, char** argv) {
    try {
#if defined(_WIN32)
        require(_setmode(_fileno(stdout), _O_BINARY) != -1, "binary stdout unavailable");
#endif
        std::ios::sync_with_stdio(false);
        std::uint64_t expected = 0;
        std::uint64_t child_limit = 4096;
        for (int index = 1; index < argc; ++index) {
            const std::string_view arg(argv[index]);
            require(index + 1 < argc, "option value missing");
            if (arg == "--positions") expected = number(argv[++index]);
            else if (arg == "--child-limit") child_limit = number(argv[++index]);
            else throw std::runtime_error("unknown argument");
        }
        require(expected > 0 && expected <= 1000000U && child_limit <= expected, "invalid finite position/child budget");
        require(forge::nnue::HiddenSize == 256 && forge::nnue::available() && forge::nnue::residual(), "pinned H256 residual weights required");
        require(std::fegetround() == FE_TONEAREST, "round-to-nearest required");
        const auto table_checks = table_proof();
        word<std::uint32_t>(0x4b313146U); // F11K, explicit little endian.
        word<std::uint32_t>(1U);
        word<std::uint32_t>(forge::nnue::HiddenSize);
        word<std::uint32_t>(static_cast<std::uint32_t>(RecordBytes));
        word<std::uint64_t>(expected);
        word<std::uint64_t>(child_limit);
#if defined(__SSE__)
        word<std::uint32_t>(_mm_getcsr() & 0x0000ffc0U);
#else
        word<std::uint32_t>(0xffffffffU);
#endif
        forge::Board board;
        std::uint64_t positions = 0, children = 0, nulls = 0, captures = 0, promotions = 0, castles = 0, ep = 0;
        std::string line;
        while (std::getline(std::cin, line)) {
            require(positions < expected, "more than the exact requested positions");
            require(board.set_fen(line), "invalid FEN input; never skipped");
            const auto key = checked_key(board);
            if (positions < child_limit) {
                const auto original = state(board);
                for (const auto move : board.legal_moves()) {
                    forge::Undo undo;
                    require(board.make_move(move, undo), "legal child rejected");
                    (void)checked_key(board);
                    board.unmake_move(move, undo);
                    unchanged(board, original);
                    require(checked_key(board) == key, "material key not restored");
                    ++children;
                    captures += move.is_capture(); promotions += move.is_promotion(); castles += move.is_castle();
                    ep += (move.flags & forge::EnPassant) != 0U;
                }
                if (!board.in_check()) {
                    forge::NullUndo undo;
                    board.make_null_move(undo);
                    require(checked_key(board) == key, "null move changed material key");
                    board.unmake_null_move(undo);
                    unchanged(board, original);
                    ++nulls;
                }
            }
            snapshot(board, key);
            ++positions;
        }
        require(std::cin.eof() && positions == expected, "input error or incomplete corpus");
        std::cout.flush();require(static_cast<bool>(std::cout), "snapshot output failed");
        std::cerr << "{\"positions\":" << positions << ",\"record_bytes\":" << RecordBytes
                  << ",\"header_bytes\":36,\"actual_table_basis_checks\":" << table_checks
                  << ",\"legal_children\":" << children << ",\"nulls\":" << nulls
                  << ",\"captures\":" << captures << ",\"promotions\":" << promotions
                  << ",\"castles\":" << castles << ",\"en_passant\":" << ep
                  << ",\"material_key_mismatches\":0,\"state_mismatches\":0}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "S11 oracle FAIL: " << error.what() << '\n';
        return 1;
    }
}
