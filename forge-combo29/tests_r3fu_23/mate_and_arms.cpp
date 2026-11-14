// Follow-up for SoundMatePruning.
// The mate claim is checked by a full legal-move tree, every defender reply,
// not by replaying one line. The three arms are forced one at a time.
// A failed check returns non-zero.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr const char* Fen = "kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1";
constexpr int MatePlies = 7;
constexpr int MateScore = 32000 - MatePlies;

struct CacheKey {
    std::uint64_t key = 0;
    int limit = 0;
    int kind = 0;
    bool operator==(const CacheKey& other) const {
        return key == other.key && limit == other.limit && kind == other.kind;
    }
};

struct CacheHash {
    std::size_t operator()(const CacheKey& key) const {
        return static_cast<std::size_t>(key.key ^ (static_cast<std::uint64_t>(key.limit) << 8U) ^
                                        (static_cast<std::uint64_t>(key.kind) << 1U));
    }
};

std::unordered_map<CacheKey, int, CacheHash> cache;
std::uint64_t defender_replies = 0;
std::uint64_t prover_nodes = 0;

void reset_prover() {
    cache.clear();
    defender_replies = 0;
    prover_nodes = 0;
}

bool can_force(forge::Board& board, int limit);

// True when the side to move can avoid mate for `limit` plies.
bool defender_escapes(forge::Board& board, int limit) {
    if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) return true;
    const CacheKey key{board.key(), limit, 1};
    if (const auto found = cache.find(key); found != cache.end()) return found->second != 0;
    ++prover_nodes;
    const forge::MoveList moves = board.legal_moves();
    bool escapes = false;
    if (moves.empty()) {
        escapes = !board.in_check();
    } else if (limit <= 0) {
        escapes = true;
    } else {
        escapes = false;
        for (const forge::Move move : moves) {
            ++defender_replies;
            forge::Undo undo;
            (void)board.make_move(move, undo);
            const bool forced = can_force(board, limit - 1);
            board.unmake_move(move, undo);
            if (!forced) {
                escapes = true;
                break;
            }
        }
    }
    cache.emplace(key, escapes ? 1 : 0);
    return escapes;
}

bool can_force(forge::Board& board, int limit) {
    if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) return false;
    const CacheKey key{board.key(), limit, 0};
    if (const auto found = cache.find(key); found != cache.end()) return found->second != 0;
    ++prover_nodes;
    bool forced = false;
    const forge::MoveList moves = board.legal_moves();
    if (!moves.empty() && limit > 0) {
        for (const forge::Move move : moves) {
            forge::Undo undo;
            (void)board.make_move(move, undo);
            const forge::MoveList replies = board.legal_moves();
            const bool mated_now = replies.empty() && board.in_check();
            const bool holds = mated_now || !defender_escapes(board, limit - 1);
            board.unmake_move(move, undo);
            if (holds) {
                forced = true;
                break;
            }
        }
    }
    cache.emplace(key, forced ? 1 : 0);
    return forced;
}

int fail(const std::string& message) {
    std::cerr << "FAIL " << message << '\n';
    return 1;
}

void reset_arms() {
    forge::tune::SoundMatePruning = false;
    forge::tune::SoundArmPv = forge::tune::SoundPruneArm::FollowOption;
    forge::tune::SoundArmInCheck = forge::tune::SoundPruneArm::FollowOption;
    forge::tune::SoundArmMateAlpha = forge::tune::SoundPruneArm::FollowOption;
    forge::tune::SoundPruneTrace = false;
    forge::tune::sound_prune_trace = {};
}

void force_one(forge::tune::SoundPruneArm* arm) {
    reset_arms();
    forge::tune::SoundArmPv = forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundArmInCheck = forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundArmMateAlpha = forge::tune::SoundPruneArm::ForceOff;
    *arm = forge::tune::SoundPruneArm::ForceOn;
    forge::tune::SoundPruneTrace = true;
}

forge::SearchInfo search_fen(const std::string& fen, int depth) {
    forge::Board board;
    if (!board.set_fen(fen)) return {};
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
}

std::uint64_t search_nodes(const std::string& fen, int depth) {
    return search_fen(fen, depth).nodes;
}

bool pv_mates(const forge::Board& start, const forge::SearchInfo& info) {
    if (info.pv.empty()) return false;
    forge::Board board = start;
    for (const forge::Move move : info.pv) {
        if (!board.is_legal(move)) return false;
        forge::Undo undo;
        (void)board.make_move(move, undo);
    }
    return board.legal_moves().empty() && board.in_check();
}

const std::vector<std::string> CaseFens{
    Fen,
    forge::Board::StandardStartFen.data(),
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3",
    "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQ - 4 6",
    "2r3k1/5ppp/p7/1pP5/1P1r4/P4N2/5PPP/2R3K1 w - - 0 1",
};

} // namespace

int main() {
    forge::Board root;
    if (!root.set_fen(Fen)) return fail("fen rejected");

    reset_prover();
    const bool mate_in_five = can_force(root, 5);
    const bool mate_in_six = can_force(root, 6);
    const bool mate_in_seven = can_force(root, 7);
    const std::uint64_t tree_nodes = prover_nodes;
    const std::uint64_t tree_replies = defender_replies;
    std::cout << "exhaustive can_force 5=" << mate_in_five << " 6=" << mate_in_six << " 7=" << mate_in_seven
              << " nodes=" << tree_nodes << " defender_replies=" << tree_replies << '\n';
    if (mate_in_five || mate_in_six || !mate_in_seven || tree_replies < 2) {
        return fail("exhaustive horizon is not a forced mate in 7 against every defence");
    }

    reset_arms();
    const forge::SearchInfo option_off = search_fen(Fen, 8);
    std::cout << "option off depth 8 score=" << option_off.score
              << " best=" << forge::Board::move_to_uci(option_off.best_move) << '\n';
    if (option_off.score >= MateScore || option_off.best_move.is_none()) {
        return fail("option off already reports the forced 7-ply mate");
    }

    forge::tune::SoundMatePruning = true;
    const forge::SearchInfo option_on = search_fen(Fen, 8);
    const forge::SearchInfo option_on_9 = search_fen(Fen, 9);
    std::cout << "option on depth 8 score=" << option_on.score
              << " best=" << forge::Board::move_to_uci(option_on.best_move)
              << " depth 9 score=" << option_on_9.score << '\n';
    if (option_on.score != MateScore || option_on_9.score != MateScore || !pv_mates(root, option_on)) {
        return fail("option on did not return the forced 7-ply mate");
    }

    forge::Board after = root;
    {
        forge::Undo undo;
        if (!root.is_legal(option_on.best_move)) return fail("option-on move is illegal");
        (void)after.make_move(option_on.best_move, undo);
    }
    reset_prover();
    const int replies = static_cast<int>(after.legal_moves().size());
    int losing = 0;
    for (const forge::Move reply : after.legal_moves()) {
        forge::Board line = after;
        forge::Undo undo;
        (void)line.make_move(reply, undo);
        reset_prover();
        const bool forced = can_force(line, MatePlies - 2);
        std::cout << "defence " << forge::Board::move_to_uci(reply)
                  << " white_forces_within_" << (MatePlies - 2) << "=" << forced << '\n';
        if (!forced) return fail("a defence escapes the claimed mate");
        ++losing;
    }
    if (replies < 2 || losing != replies) return fail("defence sweep did not cover every reply");

    // Mate-alpha arm alone. The other two arms stay off.
    force_one(&forge::tune::SoundArmMateAlpha);
    const forge::SearchInfo mate_arm = search_fen(Fen, 8);
    const auto mate_trace = forge::tune::sound_prune_trace;
    std::cout << "mate-alpha arm score=" << mate_arm.score
              << " trace mate=" << mate_trace.mate_alpha << " pv=" << mate_trace.pv
              << " check=" << mate_trace.in_check
              << " quiet_check_after=" << mate_trace.quiet_check_after_quiet_fail << '\n';
    if (mate_arm.score != MateScore || mate_trace.mate_alpha != 0) {
        return fail("mate-alpha arm did not keep the forced mate without pruning on mate alpha");
    }

    force_one(&forge::tune::SoundArmPv);
    const forge::SearchInfo pv_only = search_fen(Fen, 8);
    std::cout << "pv arm only score=" << pv_only.score << '\n';
    force_one(&forge::tune::SoundArmInCheck);
    const forge::SearchInfo check_only = search_fen(Fen, 8);
    std::cout << "in-check arm only score=" << check_only.score << '\n';
    if (pv_only.score != MateScore) return fail("pv arm alone missed the forced mate");
    if (check_only.score == MateScore) return fail("in-check arm alone reproduced the mate result");

    // Each case must prune something with the arms off, and that case's counter
    // must stay zero when only that arm is on. A quiet check after an earlier
    // quiet skip is part of the same sweep.
    forge::tune::SoundPruneTraceCounts off_counts{};
    std::uint64_t off_nodes = 0;
    reset_arms();
    forge::tune::SoundPruneTrace = true;
    for (const std::string& fen : CaseFens) {
        const forge::SearchInfo info = search_fen(fen, 8);
        off_nodes += info.nodes;
    }
    off_counts = forge::tune::sound_prune_trace;
    std::cout << "arms off trace pv=" << off_counts.pv << " check=" << off_counts.in_check
              << " mate=" << off_counts.mate_alpha
              << " quiet_check_after=" << off_counts.quiet_check_after_quiet_fail
              << " quiet_check_pv=" << off_counts.quiet_check_on_pv
              << " quiet_check_in_check=" << off_counts.quiet_check_in_check
              << " quiet_check_mate=" << off_counts.quiet_check_on_mate_alpha
              << " nodes=" << off_nodes << '\n';
    if (off_counts.pv == 0 || off_counts.in_check == 0 || off_counts.mate_alpha == 0 ||
        off_counts.quiet_check_on_pv == 0 || off_counts.quiet_check_on_mate_alpha == 0) {
        return fail("arms-off search did not hit every prune case, including quiet checks after quiet failures");
    }

    auto arm_clears = [&](forge::tune::SoundPruneArm* arm, std::uint64_t forge::tune::SoundPruneTraceCounts::*field,
                          const char* name) {
        force_one(arm);
        std::uint64_t nodes = 0;
        for (const std::string& fen : CaseFens) nodes += search_nodes(fen, 8);
        const auto counts = forge::tune::sound_prune_trace;
        const std::uint64_t value = counts.*field;
        std::cout << name << " arm trace field=" << value << " nodes=" << nodes << " off_nodes=" << off_nodes << '\n';
        if (value != 0) return fail(std::string(name) + " arm still pruned that case");
        if (nodes == off_nodes) return fail(std::string(name) + " arm did not change the searched tree");
        const std::uint64_t quiet_bucket = arm == &forge::tune::SoundArmPv ? counts.quiet_check_on_pv
                                           : arm == &forge::tune::SoundArmInCheck ? counts.quiet_check_in_check
                                                                                  : counts.quiet_check_on_mate_alpha;
        std::cout << name << " quiet_check_bucket=" << quiet_bucket << '\n';
        if (quiet_bucket != 0) return fail(std::string(name) + " arm still skipped a quiet check after a quiet failure");
        return 0;
    };
    if (const int pv_rc = arm_clears(&forge::tune::SoundArmPv, &forge::tune::SoundPruneTraceCounts::pv, "pv")) return pv_rc;
    if (const int check_rc = arm_clears(&forge::tune::SoundArmInCheck, &forge::tune::SoundPruneTraceCounts::in_check, "in-check")) {
        return check_rc;
    }
    if (const int mate_rc =
            arm_clears(&forge::tune::SoundArmMateAlpha, &forge::tune::SoundPruneTraceCounts::mate_alpha, "mate-alpha")) {
        return mate_rc;
    }

    reset_arms();
    std::cout << "PASS mate_and_arms\n";
    return 0;
}
