// Standalone observer for frozen Forge23 source 1d3ed25bea2c8b781f7ee5a178af0f66061b3984.
// Link against that actual forge_core; no engine/search/SEE implementation is copied here.
// Prepared only: compilation and execution belong to the parent task.
// Known gains below are existing tests/tests.cpp expectations, not a new SEE oracle.
// Runtime FNV-1a digests are compact reproducibility checks, not cryptographic hashes.
#include "forge/board.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
constexpr int Low = -2400;
constexpr int High = 2400;
constexpr int Unknown = std::numeric_limits<int>::max();
constexpr std::uint64_t Seed = 0x243f6a8885a308d3ULL;
constexpr std::uint64_t FnvOffset = 14695981039346656037ULL;
constexpr std::uint64_t FnvPrime = 1099511628211ULL;

void hash_byte(std::uint64_t& hash, unsigned char value) {
    hash ^= value;
    hash *= FnvPrime;
}
void hash_text(std::uint64_t& hash, std::string_view value) {
    for (const unsigned char c : value) hash_byte(hash, c);
    hash_byte(hash, 0); // Unambiguous separator for the NUL-free textual fields.
}
std::string hex64(std::uint64_t value) {
    std::ostringstream stream;
    stream << std::hex << std::setfill('0') << std::setw(16) << value;
    return stream.str();
}

struct Fixture {
    std::string_view name;
    std::string_view fen;
    std::string_view move;
    int expected;
    bool legal = true;
};

// First seven rows: tests/tests.cpp:304-326. Next 28: its complete
// test_pinned_static_exchange corpus (338-367), including all initial Q/R/B/N
// quiet/capture identities and five later-promoting-recapture rows.
constexpr Fixture Fixtures[]{
    {"free-rook", "4k3/8/8/3r4/8/8/8/3QK3 w - - 0 1", "d1d5", 500},
    {"poisoned-pawn", "3qk3/8/8/3p4/8/8/8/3QK3 w - - 0 1", "d1d5", -800},
    {"opening-knight", "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", "f3e5", -200},
    {"initial-promotion-king-recapture", "4k3/8/8/8/8/8/4p3/3RK3 b - - 0 1", "e2d1q", 400},
    {"start-quiet", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e2e4", 0},
    // Existing safe-knight test asserts ge(0), not an exact gain: keep gain unknown.
    {"safe-knight-quiet", "4k3/8/8/4p3/8/8/8/3NK3 w - - 0 1", "d1f2", Unknown},
    {"losing-knight-quiet", "4k3/8/8/8/4p3/8/8/2N1K3 w - - 0 1", "c1d3", -300},
    {"absolute-pin", "4k3/4n3/8/3p4/8/8/8/3QR1K1 w - - 0 1", "d1d5", 100},
    {"unpinned-defender", "4k3/4n3/8/3p4/8/8/8/3Q2K1 w - - 0 1", "d1d5", -800},
    {"capture-along-pin", "4k3/4r3/8/8/8/8/4p3/3QR1K1 w - - 0 1", "d1e2", -300},
    {"legal-king-recapture", "8/8/4k3/3p4/8/8/8/3Q2K1 w - - 0 1", "d1d5", -800},
    {"protected-king-destination", "8/8/4k3/3p4/8/8/6B1/3Q2K1 w - - 0 1", "d1d5", 100},
    {"captured-rook-ghost", "k7/8/8/8/8/2Np4/4r3/3QK3 w - - 0 1", "d1e2", -300},
    {"new-orthogonal-pin", "k3r3/8/8/8/3p4/4b3/4N3/3QK3 w - - 0 1", "d1d4", -800},
    {"diagonal-pin", "7k/6n1/8/5p2/8/8/8/B4Q1K w - - 0 1", "f1f5", 100},
    {"capture-along-diagonal-pin", "7k/8/5b2/8/3p4/8/8/B2Q3K w - - 0 1", "d1d4", -500},
    {"departed-pinner", "4k3/8/8/8/8/4n3/8/3bR1K1 w - - 0 1", "e1d1", -200},
    {"second-same-value-attacker", "4k3/8/5n2/3p4/8/4n3/8/3QR1K1 w - - 0 1", "d1d5", -800},
    {"ep-unrecaptured", "7k/8/8/3pP3/8/8/8/7K w - d6 0 1", "e5d6", 100},
    {"ep-rook-recapture", "3r3k/8/8/3pP3/8/8/8/7K w - d6 0 1", "e5d6", 0},
    {"capture-queen-promotion", "r6k/1P6/8/8/8/8/8/7K w - - 0 1", "b7a8q", 1300},
    {"quiet-queen-promotion", "1r5k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8q", -100},
    {"capture-rook-promotion", "r6k/1P6/8/8/8/8/8/7K w - - 0 1", "b7a8r", 900},
    {"quiet-rook-promotion", "1r5k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8r", -100},
    {"capture-bishop-promotion", "r6k/1P6/8/8/8/8/8/7K w - - 0 1", "b7a8b", 700},
    {"quiet-bishop-promotion", "1r5k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8b", -100},
    {"capture-knight-promotion", "r6k/1P6/8/8/8/8/8/7K w - - 0 1", "b7a8n", 700},
    {"quiet-knight-promotion", "1r5k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8n", -100},
    {"captured-bishop-ghost", "k7/8/8/8/8/2p2N2/3b4/3QK3 w - - 0 1", "d1d2", -500},
    {"new-diagonal-pin", "b7/7k/8/8/3Q1p2/5r2/6N1/7K w - - 0 1", "d4f4", -800},
    {"later-promotion-saves-capture", "1r6/P1Q5/2n4k/8/8/8/8/7K w - - 0 1", "c7b8", 500},
    {"enemy-promotion-poisons-capture", "7k/8/8/8/8/7K/p2N4/1r6 w - - 0 1", "d2b1", -600},
    {"pinned-promoting-recapturer", "k7/8/8/8/8/7K/p2N4/Rr6 w - - 0 1", "d2b1", 500},
    {"promoted-recapturer-taken-by-king", "7k/8/8/8/8/8/p2N4/1rK5 w - - 0 1", "d2b1", 300},
    {"promotion-recapture-changes-victim", "7k/8/8/8/8/1Q5K/p7/1r6 w - - 0 1", "b3b1", -1200},
    // Actual legal-versus-pinned EP controls: tests/tests.cpp:227-230.
    {"ep-legal-control", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5d6", Unknown},
    {"ep-pinned-illegal-control", "k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5d6", Unknown, false},
    // tests/tests.cpp:210-225: four quiet and four capture promotions per side.
    {"complete-promotion-identities", "1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1", "a7b8q", Unknown},
};

std::string mirror_fen(std::string_view text) {
    std::istringstream input{std::string(text)};
    std::array<std::string, 6> field;
    for (auto& value : field) if (!(input >> value)) throw std::runtime_error("mirror FEN fields");
    std::vector<std::string> ranks;
    std::istringstream placement(field[0]);
    std::string rank;
    while (std::getline(placement, rank, '/')) ranks.push_back(rank);
    if (ranks.size() != 8) throw std::runtime_error("mirror FEN ranks");
    std::string flipped;
    for (auto it = ranks.rbegin(); it != ranks.rend(); ++it) {
        if (!flipped.empty()) flipped += '/';
        for (const char ch : *it) {
            const auto c = static_cast<unsigned char>(ch);
            flipped += std::islower(c) ? static_cast<char>(std::toupper(c))
                       : std::isupper(c) ? static_cast<char>(std::tolower(c)) : ch;
        }
    }
    for (char& ch : field[2]) {
        const auto c = static_cast<unsigned char>(ch);
        if (std::isalpha(c)) ch = std::islower(c) ? static_cast<char>(std::toupper(c))
                                                : static_cast<char>(std::tolower(c));
    }
    if (field[3] != "-") field[3][1] = static_cast<char>('1' + ('8' - field[3][1]));
    return flipped + ' ' + (field[1] == "w" ? "b" : "w") + ' ' + field[2] + ' ' + field[3] + ' ' + field[4] + ' ' + field[5];
}
std::string mirror_move(std::string text) {
    text[1] = static_cast<char>('1' + ('8' - text[1]));
    text[3] = static_cast<char>('1' + ('8' - text[3]));
    return text;
}

struct Snapshot {
    std::string fen;
    std::uint64_t key;
    std::uint64_t pawn_key;
    forge::Bitboard checkers;
    std::vector<std::uint64_t> history;
    explicit Snapshot(const forge::Board& board)
        : fen(board.fen()), key(board.key()), pawn_key(board.pawn_key()),
          checkers(board.checkers()), history(board.key_history()) {}
    bool matches(const forge::Board& board) const {
        return key == board.key() && pawn_key == board.pawn_key() &&
               checkers == board.checkers() && history == board.key_history() && fen == board.fen();
    }
};

struct Counts {
    std::uint64_t failures = 0, positions = 0, fixture_positions = 0, generated_positions = 0;
    std::uint64_t legal_captures = 0, legal_promotions = 0, moves = 0, calls = 0;
    std::uint64_t ge_zero_true = 0, negative_implications = 0, illegal_controls = 0;
    std::uint64_t corpus_hash = FnvOffset, predicates_hash = FnvOffset;
    std::array<std::uint64_t, 7> mover_types{}, victim_types{}, promotion_types{};
    std::array<std::uint64_t, 2> colors{};
    std::uint64_t ep = 0, quiet = 0, captures = 0, known_rows = 0;
};
Counts counts;

void fail(std::string_view kind, std::string_view label, std::string_view move,
          int threshold, std::string_view detail) {
    ++counts.failures;
    std::cout << "FAIL kind=" << kind << " label=" << std::quoted(std::string(label))
              << " move=" << move << " threshold=" << threshold << " detail="
              << std::quoted(std::string(detail)) << '\n';
}

void sweep(forge::Board& board, const forge::Move& move, std::string_view label, int expected) {
    const Snapshot before(board);
    const std::string uci = forge::Board::move_to_uci(move);
    ++counts.moves;
    ++counts.colors[static_cast<std::size_t>(board.side_to_move())];
    ++counts.mover_types[static_cast<std::size_t>(forge::piece_type(board.moved_piece(move)))];
    ++counts.victim_types[static_cast<std::size_t>(forge::piece_type(board.captured_piece(move)))];
    if (move.is_capture()) ++counts.captures;
    if (move.is_quiet()) ++counts.quiet;
    if ((move.flags & forge::EnPassant) != 0U) ++counts.ep;
    if (move.is_promotion()) ++counts.promotion_types[move.promotion];
    if (expected != Unknown) ++counts.known_rows;
    const bool ge_zero = board.see_ge(move, 0);
    ++counts.calls;
    if (ge_zero) ++counts.ge_zero_true;
    bool previous = true;
    int last_true = Low - 1, first_false = High + 1;
    int rising = 0, transitions = 0, true_count = 0;
    std::uint64_t predicate_hash = FnvOffset;
    for (int threshold = Low; threshold <= High; ++threshold) {
        const bool value = board.see_ge(move, threshold);
        ++counts.calls;
        hash_byte(predicate_hash, value ? 1 : 0);
        if (value) { last_true = threshold; ++true_count; }
        else if (first_false == High + 1) first_false = threshold;
        if (threshold > Low && value != previous) ++transitions;
        if (threshold > Low && !previous && value) {
            ++rising;
            fail("nonmonotone", label, uci, threshold, "false followed by true");
        }
        if (threshold == 0 && value != ge_zero)
            fail("unstable-ge0", label, uci, threshold, "repeated ge(0) differs");
        if (threshold <= 0 && ge_zero) {
            ++counts.negative_implications;
            if (!value) fail("ge0-implication", label, uci, threshold, "ge(0) true but ge(t<=0) false");
        }
        if (expected != Unknown && value != (expected >= threshold))
            fail("existing-fixture-gain", label, uci, threshold, "predicate disagrees with existing named test gain");
        previous = value;
    }
    const bool preserved = before.matches(board);
    if (!preserved) fail("board-changed", label, uci, 0, "FEN/key/pawn-key/checkers/history differs after sweep");
    const std::string identity = uci + ':' + std::to_string(move.from) + ':' + std::to_string(move.to) + ':' +
                                 std::to_string(move.promotion) + ':' + std::to_string(move.flags);
    hash_text(counts.corpus_hash, identity);
    hash_text(counts.corpus_hash, expected == Unknown ? "unknown" : std::to_string(expected));
    hash_text(counts.predicates_hash, label);
    hash_text(counts.predicates_hash, identity);
    hash_text(counts.predicates_hash, hex64(predicate_hash));
    std::cout << "MOVE label=" << std::quoted(std::string(label)) << " uci=" << uci
              << " from=" << int(move.from) << " to=" << int(move.to)
              << " promotion=" << int(move.promotion) << " flags=" << int(move.flags)
              << " capture=" << move.is_capture() << " ge0=" << ge_zero << " expected=";
    if (expected == Unknown) std::cout << "NA"; else std::cout << expected;
    std::cout << " first_false=" << first_false << " last_true=" << last_true
              << " true_count=" << true_count << " transitions=" << transitions << " rising=" << rising
              << " predicate_fnv1a64=" << hex64(predicate_hash) << " board_preserved=" << preserved << '\n';
}

bool inspect_position(forge::Board& board, const std::string& label, const std::string& designated,
                      int expected, bool should_be_legal, bool generated, bool promotion_matrix) {
    ++counts.positions;
    if (generated) ++counts.generated_positions; else ++counts.fixture_positions;
    const Snapshot before(board);
    const auto parsed = designated.empty() ? std::optional<forge::Move>{} : board.parse_uci(designated);
    if (!designated.empty() && parsed.has_value() != should_be_legal)
        fail("fixture-legality", label, designated, 0, "designated move legal status differs");
    std::vector<forge::Move> legal;
    for (const auto& move : board.legal_moves()) legal.push_back(move);
    std::sort(legal.begin(), legal.end(), [](const auto& a, const auto& b) {
        return forge::Board::move_to_uci(a) < forge::Board::move_to_uci(b);
    });
    std::set<std::string> identities;
    std::array<int, 7> quiet_promotions{}, capture_promotions{};
    std::uint64_t captures = 0, promotions = 0;
    int designated_count = 0;
    for (const auto& move : legal) {
        const auto text = forge::Board::move_to_uci(move);
        if (!identities.insert(text).second) fail("duplicate-identity", label, text, 0, "duplicate UCI identity in legal list");
        if (!board.is_legal(move)) fail("illegal-generated-move", label, text, 0, "legal_moves returned illegal move");
        if (text == designated) {
            ++designated_count;
            if (parsed && !(*parsed == move)) fail("move-identity", label, text, 0, "parse and legal-list flags differ");
        }
        if (move.is_capture()) ++captures;
        if (move.is_promotion()) {
            ++promotions;
            ++(move.is_capture() ? capture_promotions : quiet_promotions)[move.promotion];
        }
    }
    if (!designated.empty() && designated_count != (should_be_legal ? 1 : 0))
        fail("fixture-identity-count", label, designated, 0, "designated legal-list count differs");
    if (!should_be_legal) ++counts.illegal_controls;
    if (promotion_matrix) {
        for (const int type : {forge::Queen, forge::Rook, forge::Bishop, forge::Knight})
            if (quiet_promotions[static_cast<std::size_t>(type)] != 1 || capture_promotions[static_cast<std::size_t>(type)] != 1)
                fail("promotion-coverage", label, designated, type, "expected exactly one quiet and one capture identity of each Q/R/B/N");
    }
    counts.legal_captures += captures;
    counts.legal_promotions += promotions;
    hash_text(counts.corpus_hash, label);
    hash_text(counts.corpus_hash, before.fen);
    hash_text(counts.corpus_hash, hex64(before.key));
    for (const auto key : before.history) hash_text(counts.corpus_hash, hex64(key));
    std::cout << "POSITION label=" << std::quoted(label) << " generated=" << generated
              << " fen=" << std::quoted(before.fen) << " key=" << hex64(before.key)
              << " pawn_key=" << hex64(before.pawn_key) << " history_size=" << before.history.size()
              << " legal_moves=" << legal.size() << " legal_captures=" << captures
              << " legal_promotions=" << promotions << " designated=" << designated
              << " designated_legal=" << parsed.has_value() << " history=";
    for (const auto key : before.history) std::cout << hex64(key) << ',';
    std::cout << '\n';
    // All legal captures and promotions; designated existing-test quiet controls;
    // generated positions additionally get their first sorted quiet move.
    bool quiet_added = false;
    for (const auto& move : legal) {
        const bool named = forge::Board::move_to_uci(move) == designated;
        const bool generated_quiet = generated && !quiet_added && move.is_quiet();
        if (!(move.is_capture() || move.is_promotion() || named || generated_quiet)) continue;
        if (generated_quiet) quiet_added = true;
        sweep(board, move, label, named && should_be_legal ? expected : Unknown);
    }
    if (!before.matches(board)) {
        fail("position-board-changed", label, designated, 0, "position processing changed public Board state");
        return false;
    }
    return true;
}

int replay_file(const char* path) {
    std::ifstream input(path);
    if (!input) {
        std::cout << "REPLAY_FAIL kind=open path=" << std::quoted(path) << '\n';
        return 2;
    }
    std::uint64_t rows = 0, moves = 0, failures = 0, digest = FnvOffset;
    std::string line;
    while (std::getline(input, line)) {
        ++rows;
        if (!line.empty() && line.back() == '\r') line.pop_back();
        const auto tab = line.find('\t');
        if (tab == std::string::npos || line.find('\t', tab + 1) != std::string::npos) {
            ++failures;
            std::cout << "REPLAY_FAIL row=" << rows << " kind=format expected=FEN-TAB-space-separated-UCI\n";
            continue;
        }
        const std::string fen = line.substr(0, tab);
        const std::string texts = line.substr(tab + 1);
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) {
            ++failures;
            std::cout << "REPLAY_FAIL row=" << rows << " kind=fen error=" << std::quoted(error)
                      << " fen=" << std::quoted(fen) << '\n';
            continue;
        }
        hash_text(digest, fen);
        hash_text(digest, texts);
        std::istringstream tokens(texts);
        std::string text;
        std::uint64_t row_moves = 0;
        bool valid = true;
        while (tokens >> text) {
            const Snapshot before(board);
            const auto move = board.parse_uci(text);
            if (!before.matches(board)) {
                ++failures;
                std::cout << "REPLAY_FAIL row=" << rows << " ply=" << row_moves
                          << " kind=parse-state move=" << text << '\n';
                valid = false;
                break;
            }
            if (!move || !board.is_legal(*move) || forge::Board::move_to_uci(*move) != text) {
                ++failures;
                std::cout << "REPLAY_FAIL row=" << rows << " ply=" << row_moves
                          << " kind=illegal-or-noncanonical move=" << text << " fen=" << std::quoted(board.fen()) << '\n';
                valid = false;
                break;
            }
            forge::Undo undo;
            if (!board.make_move(*move, undo)) {
                ++failures;
                std::cout << "REPLAY_FAIL row=" << rows << " ply=" << row_moves
                          << " kind=make move=" << text << '\n';
                valid = false;
                break;
            }
            ++row_moves;
            ++moves;
        }
        if (row_moves == 0 && valid) {
            ++failures;
            valid = false;
            std::cout << "REPLAY_FAIL row=" << rows << " kind=empty-move-sequence\n";
        }
        std::cout << "REPLAY_ROW row=" << rows << " moves=" << row_moves << " valid=" << valid
                  << " initial_fen=" << std::quoted(fen) << " moves_uci=" << std::quoted(texts)
                  << " final_fen=" << std::quoted(board.fen()) << " final_key=" << hex64(board.key())
                  << " history_size=" << board.history_size() << '\n';
    }
    if (input.bad() || rows == 0) {
        ++failures;
        std::cout << "REPLAY_FAIL kind=" << (input.bad() ? "read" : "empty-file") << '\n';
    }
    std::cout << "REPLAY_SUMMARY rows=" << rows << " moves=" << moves << " failures=" << failures
              << " corpus_fnv1a64=" << hex64(digest) << " result=" << (failures == 0 ? "PASS" : "FAIL") << '\n';
    return failures == 0 ? 0 : 1;
}
} // namespace

int main(int argc, char** argv) {
    std::cout << std::unitbuf;
    if (argc == 3 && std::string_view(argv[1]) == "--replay") {
        try { return replay_file(argv[2]); }
        catch (const std::exception& error) {
            std::cout << "REPLAY_FAIL kind=exception error=" << std::quoted(error.what()) << '\n';
            return 2;
        }
    }
    if (argc != 1) {
        std::cout << "USAGE see_threshold_driver [--replay PATH]\n";
        return 2;
    }
    std::cout << "CONFIG source=1d3ed25bea2c8b781f7ee5a178af0f66061b3984 threshold_low=" << Low
              << " threshold_high=" << High << " threshold_step=1 generated_limit=64 seed=" << hex64(Seed)
              << " predicate_encoding=one-byte-0-or-1-in-ascending-threshold-order hash=fnv1a64\n";
    try {
        for (const auto& fixture : Fixtures) {
            for (const bool mirrored : {false, true}) {
                forge::Board board;
                const std::string label = std::string(fixture.name) + (mirrored ? "/mirror" : "/original");
                const std::string fen = mirrored ? mirror_fen(fixture.fen) : std::string(fixture.fen);
                const std::string move = mirrored ? mirror_move(std::string(fixture.move)) : std::string(fixture.move);
                std::string error;
                if (!board.set_fen(fen, &error)) { fail("invalid-fixture", label, move, 0, error); continue; }
                if (!inspect_position(board, label, move, fixture.expected, fixture.legal, false,
                                      fixture.name == "complete-promotion-identities")) return 2;
            }
        }
        forge::Board board;
        if (!board.set_fen(forge::Board::StandardStartFen)) throw std::runtime_error("generated start FEN rejected");
        std::uint64_t state = Seed;
        // Exactly 64 inspected positions at most. Each successor is made through
        // the actual Board legal-list/make_move API; history is retained. A terminal
        // position causes a documented start reset, never an invented move.
        for (int index = 0; index < 64; ++index) {
            const std::string label = "legal-play/" + std::to_string(index);
            if (!inspect_position(board, label, "", Unknown, true, true, false)) return 2;
            if (index == 63) break;
            std::vector<forge::Move> legal;
            for (const auto& move : board.legal_moves()) legal.push_back(move);
            if (legal.empty()) {
                std::cout << "WALK_RESET after=" << index << " reason=terminal\n";
                if (!board.set_fen(forge::Board::StandardStartFen)) throw std::runtime_error("generated reset rejected");
                continue;
            }
            std::sort(legal.begin(), legal.end(), [](const auto& a, const auto& b) {
                return forge::Board::move_to_uci(a) < forge::Board::move_to_uci(b);
            });
            state = state * 6364136223846793005ULL + 1442695040888963407ULL;
            std::vector<forge::Move> captures;
            for (const auto& move : legal) if (move.is_capture() || move.is_promotion()) captures.push_back(move);
            const auto& choices = (index % 2 == 1 && !captures.empty()) ? captures : legal;
            const auto move = choices[static_cast<std::size_t>(state % choices.size())];
            const Snapshot before(board);
            forge::Undo undo;
            if (!board.make_move(move, undo)) { fail("walk-make", label, forge::Board::move_to_uci(move), 0, "legal move rejected"); return 2; }
            // Actual make/unmake restoration provides a history-preserving walk check.
            const Snapshot after(board);
            board.unmake_move(move, undo);
            if (!before.matches(board)) { fail("walk-unmake", label, forge::Board::move_to_uci(move), 0, "unmake failed public-state restoration"); return 2; }
            forge::Undo replay_undo;
            if (!board.make_move(move, replay_undo) || !after.matches(board)) {
                fail("walk-replay", label, forge::Board::move_to_uci(move), 0, "replay differs from original successor"); return 2;
            }
            std::cout << "WALK after=" << index << " move=" << forge::Board::move_to_uci(move)
                      << " state=" << hex64(state) << " choices=" << choices.size()
                      << " capture_biased=" << (index % 2 == 1 && !captures.empty()) << '\n';
        }
    } catch (const std::exception& error) {
        fail("exception", "driver", "-", 0, error.what());
    }
    if (counts.generated_positions != 64) fail("corpus-size", "driver", "-", 0, "did not inspect 64 generated positions");
    for (const int type : {forge::Queen, forge::Rook, forge::Bishop, forge::Knight})
        if (counts.promotion_types[static_cast<std::size_t>(type)] == 0)
            fail("missing-promotion-type", "driver", "-", type, "no swept initial promotion of this type");
    std::cout << "TYPE_COUNTS mover=";
    for (std::size_t i = 0; i < counts.mover_types.size(); ++i) std::cout << i << ':' << counts.mover_types[i] << ',';
    std::cout << " victim=";
    for (std::size_t i = 0; i < counts.victim_types.size(); ++i) std::cout << i << ':' << counts.victim_types[i] << ',';
    std::cout << " promotion=";
    for (std::size_t i = 0; i < counts.promotion_types.size(); ++i) std::cout << i << ':' << counts.promotion_types[i] << ',';
    std::cout << '\n';
    std::cout << "SUMMARY failures=" << counts.failures << " positions=" << counts.positions
              << " fixture_positions=" << counts.fixture_positions << " generated_positions=" << counts.generated_positions
              << " moves=" << counts.moves << " see_calls=" << counts.calls << " captures=" << counts.captures
              << " quiet=" << counts.quiet << " ep=" << counts.ep << " white=" << counts.colors[0] << " black=" << counts.colors[1]
              << " legal_capture_rows=" << counts.legal_captures << " legal_promotion_rows=" << counts.legal_promotions
              << " known_gain_rows=" << counts.known_rows << " ge_zero_true=" << counts.ge_zero_true
              << " negative_implications=" << counts.negative_implications << " illegal_controls=" << counts.illegal_controls
              << " corpus_fnv1a64=" << hex64(counts.corpus_hash) << " predicates_fnv1a64=" << hex64(counts.predicates_hash)
              << " result=" << (counts.failures == 0 ? "PASS" : "FAIL") << '\n';
    return counts.failures == 0 ? 0 : 1;
}
