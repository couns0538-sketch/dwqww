// Loader probe: exercises forge::nnue::v3::load() and nothing else.
//
// Subcommands:
//   load <net>            load, print ACCEPTED/REFUSED and the exact error.
//                         Exit 0 = accepted, 1 = refused.
//   loadalloc <net>       the same, with global operator new counted, so "did the
//                         loader allocate the header's claim before validating it"
//                         is answered in bytes rather than inferred from RSS.
//   eval <net> <fen>      load, then evaluate the FEN on the reference path, so an
//                         accepted-but-broken net cannot hide behind "it loaded".
//   seq <good> <bad>      good, then bad, then good again: does a failed load leave
//                         the previous net loaded, or nothing, or the module broken?
//   plant-asan            deliberate use-after-free (ASan must report it)
//   plant-ubsan           deliberate signed overflow (UBSan must report it)
//
// The plant-* commands are the proof the sanitizer arm is live: they are compiled
// and linked exactly like `load`.
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v3.hpp"

#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <string>

namespace alloc_stat {
std::atomic<long long> bytes{0};
std::atomic<long long> calls{0};
std::atomic<long long> largest{0};

// Every allocation >= 1 MiB, in order, so a report can say "the largest thing the
// loader ever asked for was X" and compare it with what the header claimed.
constexpr int kBigMax = 64;
std::atomic<int> big_count{0};
long long big_bytes[kBigMax];

void note(std::size_t n) {
    bytes.fetch_add(static_cast<long long>(n), std::memory_order_relaxed);
    calls.fetch_add(1, std::memory_order_relaxed);
    long long cur = largest.load(std::memory_order_relaxed);
    while (static_cast<long long>(n) > cur &&
           !largest.compare_exchange_weak(cur, static_cast<long long>(n), std::memory_order_relaxed)) {
    }
    if (n >= (1U << 20)) {
        const int slot = big_count.fetch_add(1, std::memory_order_relaxed);
        if (slot < kBigMax) big_bytes[slot] = static_cast<long long>(n);
    }
}

void reset() {
    bytes.store(0);
    calls.store(0);
    largest.store(0);
    big_count.store(0);
}
} // namespace alloc_stat

void* operator new(std::size_t n) {
    alloc_stat::note(n);
    void* p = std::malloc(n == 0 ? 1 : n);
    if (p == nullptr) throw std::bad_alloc();
    return p;
}
void* operator new[](std::size_t n) {
    alloc_stat::note(n);
    void* p = std::malloc(n == 0 ? 1 : n);
    if (p == nullptr) throw std::bad_alloc();
    return p;
}
void* operator new(std::size_t n, std::align_val_t a) {
    alloc_stat::note(n);
    const std::size_t align = static_cast<std::size_t>(a);
    const std::size_t rounded = ((n == 0 ? 1 : n) + align - 1) / align * align;
    void* p = std::aligned_alloc(align, rounded);
    if (p == nullptr) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }
void operator delete(void* p, std::align_val_t) noexcept { std::free(p); }
void operator delete[](void* p, std::align_val_t) noexcept { std::free(p); }
void operator delete(void* p, std::size_t, std::align_val_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t, std::align_val_t) noexcept { std::free(p); }

namespace {

using forge::Board;
using namespace forge::nnue::v3;

// Volatile so the optimiser cannot delete the fault or reason about its extent.
volatile int g_sink = 0;

int cmd_load(const std::string& path) {
    std::string error;
    if (!load(path, &error)) {
        std::printf("REFUSED\t%s\n", error.c_str());
        std::fflush(stdout);
        return 1;
    }
    const Net& net = *loaded();
    Board board;
    (void)board.set_fen(Board::StandardStartFen);
    const int startpos = evaluate_reference(net, board);
    std::printf("ACCEPTED\t%s\tstartpos_eval %d\n", describe(net).c_str(), startpos);
    std::fflush(stdout);
    return 0;
}

long read_status_kb(const char* key) {
    std::FILE* handle = std::fopen("/proc/self/status", "r");
    if (handle == nullptr) return -1;
    char line[256];
    long value = -1;
    const std::string needle(key);
    while (std::fgets(line, sizeof line, handle) != nullptr) {
        const std::string text(line);
        if (text.rfind(needle, 0) == 0) {
            value = std::strtol(line + needle.size(), nullptr, 10);
            break;
        }
    }
    std::fclose(handle);
    return value;
}

int cmd_loadalloc(const std::string& path) {
    alloc_stat::reset();
    const long hwm_before = read_status_kb("VmHWM:");
    std::string error;
    const bool ok = load(path, &error);
    const long hwm_after = read_status_kb("VmHWM:");
    std::printf("ALLOC\t%s\ttotal_bytes %lld\tcalls %lld\tlargest %lld\tpeak_rss_kb %ld\tbig",
                ok ? "ACCEPTED" : "REFUSED",
                alloc_stat::bytes.load(), alloc_stat::calls.load(), alloc_stat::largest.load(), hwm_after);
    const int big = alloc_stat::big_count.load();
    for (int i = 0; i < big && i < alloc_stat::kBigMax; ++i) {
        std::printf(" %lld", alloc_stat::big_bytes[i]);
    }
    if (big == 0) std::printf(" none");
    std::printf("\t%s\n", ok ? describe(*loaded()).c_str() : error.c_str());
    std::fflush(stdout);
    (void)hwm_before;
    return ok ? 0 : 1;
}

int cmd_eval(const std::string& path, const char* fen) {
    std::string error;
    if (!load(path, &error)) {
        std::printf("REFUSED\t%s\n", error.c_str());
        std::fflush(stdout);
        return 1;
    }
    Board board;
    if (!board.set_fen(fen)) {
        std::printf("BADFEN\n");
        return 2;
    }
    const int value = evaluate_reference(*loaded(), board);
    std::printf("EVAL\t%d\n", value);
    std::fflush(stdout);
    return 0;
}

int cmd_seq(const std::string& good, const std::string& bad) {
    std::string error;
    int step = 0;
    auto report = [&step](const char* what, bool ok, const std::string& text) {
        const Net* net = loaded();
        std::printf("SEQ%d\t%-12s\t%-8s\tloaded %s\t%s\n", ++step, what, ok ? "ACCEPTED" : "REFUSED",
                    net == nullptr ? "NO" : "YES", ok ? describe(*net).c_str() : text.c_str());
    };
    bool ok = load(good, &error);
    report("good", ok, ok ? "" : error);
    ok = load(bad, &error);
    report("mutant", ok, ok ? "" : error);
    std::printf("SEQ-final\tnet_loaded %s\n", loaded() == nullptr ? "NO" : "YES");
    ok = load(good, &error);
    report("good-again", ok, ok ? "" : error);
    return 0;
}

int cmd_lane(const std::string& path, const char* fen, int feature, int lane) {
    std::string error;
    if (!load(path, &error)) {
        std::printf("REFUSED\t%s\n", error.c_str());
        return 1;
    }
    Board board;
    if (!board.set_fen(fen)) {
        std::printf("BADFEN\n");
        return 2;
    }
    const Net& net = *loaded();
    auto accumulator = std::make_unique<Accumulator>();
    refresh(net, board, *accumulator);
    // Which features actually contributed: recompute the set the refresh walked.
    int hits = 0;
    for (const forge::Color perspective : {forge::White, forge::Black}) {
        const KingKey key = king_key(net, perspective, board.king_square(perspective));
        forge::Bitboard occupied = board.occupied();
        while (occupied != 0) {
            const int square = forge::pop_lsb(occupied);
            const int index = feature_index(key, perspective, board.piece_at(square), square);
            if (index == feature) ++hits;
        }
    }
    const std::int16_t* white = accumulator->values[0].data();
    const std::int16_t* black = accumulator->values[1].data();
    const std::int16_t* col = net.w1.data() + static_cast<std::size_t>(feature) * static_cast<std::size_t>(net.hidden);
    std::printf("LANE\tfeature %d lane %d\twhite_acc %d\tblack_acc %d\tw1 %d\thits %d\n", feature, lane,
                static_cast<int>(white[lane]), static_cast<int>(black[lane]),
                static_cast<int>(col[lane]), hits);
    std::fflush(stdout);
    return 0;
}

int cmd_plant_asan() {
    // Use-after-free, not a heap overrun: UBSan's object-size pass catches an
    // overrun first in a combined binary, so the fault that only ASan's shadow map
    // and quarantine can see is the one that proves ASan itself is live.
    char* heap = static_cast<char*>(std::malloc(8));
    heap[0] = 1;
    std::free(heap);
    char* stale = heap;
    stale[0] = 2;                    // heap-use-after-free
    std::printf("plant-asan SURVIVED (sanitizer NOT live)\n");
    return 0;
}

int cmd_plant_ubsan() {
    volatile int big = 2147483647;
    const int one = 1;
    g_sink = big + one;              // signed integer overflow
    std::printf("plant-ubsan SURVIVED (sanitizer NOT live)\n");
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr,
                     "usage: loadprobe load <net> | loadalloc <net> | eval <net> <fen> | "
                     "seq <good> <bad> | plant-asan | plant-ubsan\n");
        return 2;
    }
    const std::string cmd = argv[1];
    if (cmd == "plant-asan") return cmd_plant_asan();
    if (cmd == "plant-ubsan") return cmd_plant_ubsan();
    if (cmd == "load" && argc >= 3) return cmd_load(argv[2]);
    if (cmd == "loadalloc" && argc >= 3) return cmd_loadalloc(argv[2]);
    if (cmd == "eval" && argc >= 4) return cmd_eval(argv[2], argv[3]);
    if (cmd == "seq" && argc >= 4) return cmd_seq(argv[2], argv[3]);
    if (cmd == "lane" && argc >= 6) return cmd_lane(argv[2], argv[3], std::atoi(argv[4]), std::atoi(argv[5]));
    std::fprintf(stderr, "bad usage\n");
    return 2;
}
