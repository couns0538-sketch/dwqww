// Concurrent first use of forge::Board. Nothing in this process may construct a
// Board, or call attacks::init, before the worker threads pass the barrier.
// ThreadSanitizer is what shows a data race; a clean AddressSanitizer run does not.

#include "forge/board.hpp"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr int kThreads = 8;
constexpr const char* kStartMoves[] = {
    "a2a3", "a2a4", "b2b3", "b2b4", "c2c3", "c2c4", "d2d3", "d2d4",
    "e2e3", "e2e4", "f2f3", "f2f4", "g2g3", "g2g4", "h2h3", "h2h4",
    "b1a3", "b1c3", "g1f3", "g1h3",
};
constexpr const char* kKiwipete =
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";

forge::Bitboard slow_rook_empty(int square) {
    forge::Bitboard result = 0;
    const int file = forge::file_of(square);
    const int rank = forge::rank_of(square);
    for (int f = 0; f < 8; ++f) {
        if (f != file) result |= forge::square_bb(forge::make_square(f, rank));
    }
    for (int r = 0; r < 8; ++r) {
        if (r != rank) result |= forge::square_bb(forge::make_square(file, r));
    }
    return result;
}

forge::Bitboard slow_bishop_empty(int square) {
    forge::Bitboard result = 0;
    constexpr int kDirs[4][2] = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
    for (const auto& dir : kDirs) {
        int file = forge::file_of(square);
        int rank = forge::rank_of(square);
        while (true) {
            file += dir[0];
            rank += dir[1];
            if (file < 0 || file > 7 || rank < 0 || rank > 7) break;
            result |= forge::square_bb(forge::make_square(file, rank));
        }
    }
    return result;
}

std::uint64_t attack_fingerprint() {
    std::uint64_t hash = 0x9E3779B97F4A7C15ULL;
    auto mix = [&](std::uint64_t value) {
        hash ^= value + 0x9E3779B97F4A7C15ULL + (hash << 6) + (hash >> 2);
    };
    for (int square = 0; square < 64; ++square) {
        mix(forge::attacks::knight(square));
        mix(forge::attacks::king(square));
        mix(forge::attacks::pawn(forge::White, square));
        mix(forge::attacks::pawn(forge::Black, square));
        mix(forge::attacks::rook(square, 0));
        mix(forge::attacks::bishop(square, 0));
        const forge::Bitboard occupancy =
            forge::square_bb((square * 3 + 1) & 63) | forge::square_bb((square * 5 + 11) & 63);
        mix(forge::attacks::rook(square, occupancy));
        mix(forge::attacks::bishop(square, occupancy));
    }
    return hash;
}

bool same_moves(const std::vector<std::string>& left, const std::vector<std::string>& right) {
    if (left.size() != right.size()) return false;
    for (std::size_t i = 0; i < left.size(); ++i) {
        if (left[i] != right[i]) return false;
    }
    return true;
}

struct Result {
    bool ok = false;
    std::uint64_t fingerprint = 0;
    std::string why;
    std::vector<std::string> kiwipete;
};

Result check_one() {
    Result result;
    forge::Board board;
    const forge::MoveList start = board.legal_moves();
    if (start.size() != 20) {
        result.why = "start legal count " + std::to_string(start.size());
        return result;
    }
    for (const char* text : kStartMoves) {
        bool found = false;
        for (const forge::Move move : start) {
            if (forge::Board::move_to_uci(move) == text) {
                found = true;
                break;
            }
        }
        if (!found) {
            result.why = std::string("missing start move ") + text;
            return result;
        }
    }
    if (forge::attacks::knight(0) != ((1ULL << 10) | (1ULL << 17))) {
        result.why = "knight a1 attacks are wrong";
        return result;
    }
    for (int square = 0; square < 64; ++square) {
        if (forge::attacks::rook(square, 0) != slow_rook_empty(square)) {
            result.why = "empty-board rook mismatch at " + std::to_string(square);
            return result;
        }
        if (forge::attacks::bishop(square, 0) != slow_bishop_empty(square)) {
            result.why = "empty-board bishop mismatch at " + std::to_string(square);
            return result;
        }
    }
    if (!board.set_fen(kKiwipete)) {
        result.why = "kiwipete fen rejected";
        return result;
    }
    const forge::MoveList kiwipete = board.legal_moves();
    if (kiwipete.size() != 48) {
        result.why = "kiwipete legal count " + std::to_string(kiwipete.size());
        return result;
    }
    result.kiwipete.reserve(kiwipete.size());
    for (const forge::Move move : kiwipete) result.kiwipete.push_back(forge::Board::move_to_uci(move));
    result.fingerprint = attack_fingerprint();
    if (result.fingerprint == 0) {
        result.why = "attack fingerprint is zero";
        return result;
    }
    result.ok = true;
    return result;
}

}  // namespace

int main() {
    std::atomic<int> arrived{0};
    std::atomic<bool> go{false};
    std::vector<Result> results(static_cast<std::size_t>(kThreads));
    std::vector<std::thread> threads;
    threads.reserve(static_cast<std::size_t>(kThreads));

    for (int index = 0; index < kThreads; ++index) {
        threads.emplace_back([&, index] {
            arrived.fetch_add(1, std::memory_order_acq_rel);
            while (!go.load(std::memory_order_acquire)) {
            }
            // Threads 0-3 enter init together. Threads 4-7 wait long enough to
            // arrive while a magic fill is still running, then after it has
            // published. This is the process's first initialization.
            if (index >= 4) {
                std::this_thread::sleep_for(std::chrono::microseconds(80 * (index - 3)));
            }
            results[static_cast<std::size_t>(index)] = check_one();
        });
    }

    while (arrived.load(std::memory_order_acquire) < kThreads) {
    }
    go.store(true, std::memory_order_release);
    for (std::thread& thread : threads) thread.join();

    for (int index = 0; index < kThreads; ++index) {
        if (!results[static_cast<std::size_t>(index)].ok) {
            std::cerr << "thread " << index << " " << results[static_cast<std::size_t>(index)].why << '\n';
            return 1;
        }
    }
    const Result& reference = results[0];
    for (int index = 1; index < kThreads; ++index) {
        const Result& other = results[static_cast<std::size_t>(index)];
        if (other.fingerprint != reference.fingerprint) {
            std::cerr << "fingerprint mismatch on thread " << index << '\n';
            return 1;
        }
        if (!same_moves(other.kiwipete, reference.kiwipete)) {
            std::cerr << "kiwipete move list mismatch on thread " << index << '\n';
            return 1;
        }
    }
    std::cout << "PASS concurrent first init threads " << kThreads << " fingerprint " << std::hex
              << reference.fingerprint << std::dec << '\n';
    return 0;
}
