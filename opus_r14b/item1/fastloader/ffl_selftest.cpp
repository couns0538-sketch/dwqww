// ffl_selftest.cpp - Opus R14-B: self-test of forge_fastloader on generated binpack files (own code).
// Built together with forge_fastloader.cpp, e.g. in CI with -fsanitize=address,undefined or -fsanitize=thread:
//   g++ -std=gnu++20 -O1 -g -fsanitize=... -pthread ffl_selftest.cpp forge_fastloader.cpp -o ffl_selftest
//   ./ffl_selftest <scratch dir>          (exit 0 = all checks passed)
// Checks: (1) no-filter stream = an independent reference (parse + features written here + std::shuffle of the
// arrival order); (2) the filtered stream is identical for 1 / 2 / 5 builder threads, cyclic and finite, with
// windows that do not divide into batches; (3) row invariants; (4) every format error stops the stream with a
// message; (5) destroying a stream while its threads run.

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <numeric>
#include <random>
#include <string>
#include <vector>

struct FflConfig {
    int batch_size, threads, cyclic, window_entries, random_fen_skipping, early_fen_skipping,
        soft_early_fen_skipping, filtered, wld_filtered, simple_eval_skipping, max_live_windows, ring_batches;
    double pc_y[5], ply_x[4], ply_y[4];
};
struct BatchView {
    int num_inputs, size;
    float *is_white, *outcome, *score;
    int num_active_white_features, num_active_black_features, max_active_features;
    int *white, *black, *piece_count, *queen_bucket;
};
extern "C" {
void* ffl_create(const FflConfig*, const char*);
const char* ffl_create_error();
BatchView* ffl_next(void*);
void ffl_release(void*, BatchView*);
void ffl_stats(void*, std::uint64_t*, std::uint64_t*, std::uint64_t*);
int ffl_error(void*, char*, int);
void ffl_destroy(void*);
}

static int g_fail = 0;
#define CHECK(c, msg)                                                         \
    do {                                                                      \
        if (!(c)) {                                                           \
            std::fprintf(stderr, "FAIL %s:%d %s\n", __FILE__, __LINE__, msg); \
            ++g_fail;                                                         \
        }                                                                     \
    } while (0)

// ---- fixture writer (format of LOADER_SPEC.md section 2) ----
struct Rec {
    std::uint64_t occ = 0;
    std::uint8_t code[64] = {};  // piece code per square (as stored), valid where occ has a bit
    int score = 0, ply = 40, result = 0, chain = 0;
};

static std::uint16_t zig16(int v) {
    std::uint16_t r = static_cast<std::uint16_t>(static_cast<std::int16_t>(v));
    if (r & 0x8000)
        r ^= 0x7FFF;
    return static_cast<std::uint16_t>((r << 1) | (r >> 15));
}

static void put_rec(std::vector<unsigned char>& out, const Rec& r) {
    for (int i = 7; i >= 0; --i)
        out.push_back(static_cast<unsigned char>(r.occ >> (8 * i)));
    unsigned char nib[16] = {};
    int j = 0;
    for (int sq = 0; sq < 64; ++sq)
        if ((r.occ >> sq & 1) && j < 32) {  // a record with more than 32 pieces keeps 32 nibbles (error test)
            nib[j >> 1] |= static_cast<unsigned char>((r.code[sq] & 0xF) << ((j & 1) * 4));
            ++j;
        }
    out.insert(out.end(), nib, nib + 16);
    out.push_back(0x12);  // move (unused)
    out.push_back(0x34);
    const std::uint16_t s = zig16(r.score), pr = static_cast<std::uint16_t>((r.ply & 0x3FFF) | (zig16(r.result) << 14));
    out.push_back(static_cast<unsigned char>(s >> 8));
    out.push_back(static_cast<unsigned char>(s));
    out.push_back(static_cast<unsigned char>(pr >> 8));
    out.push_back(static_cast<unsigned char>(pr));
    out.push_back(0);
    out.push_back(3);  // fifty-move counter (unused)
    out.push_back(static_cast<unsigned char>(r.chain >> 8));
    out.push_back(static_cast<unsigned char>(r.chain));
}

static Rec random_rec(std::mt19937& g, int max_extra) {
    Rec r;
    std::vector<int> sq(64);
    std::iota(sq.begin(), sq.end(), 0);
    std::shuffle(sq.begin(), sq.end(), g);
    const bool black_to_move = g() & 1;
    r.code[sq[0]] = 10;
    r.code[sq[1]] = black_to_move ? 15 : 11;
    r.occ = (1ULL << sq[0]) | (1ULL << sq[1]);
    const int extra = static_cast<int>(g() % static_cast<unsigned>(max_extra + 1));
    for (int i = 0; i < extra; ++i) {
        const int s = sq[2 + i];
        int c = static_cast<int>(g() % 10);              // pawns .. queens of both colours
        const unsigned roll = g() % 20;
        if (roll == 0 && ((s >> 3) == 3 || (s >> 3) == 4))
            c = 12;                                      // pawn with an en-passant square
        else if (roll == 1)
            c = 13 + static_cast<int>(g() % 2);          // rook with a castling right
        r.code[s] = static_cast<std::uint8_t>(c);
        r.occ |= 1ULL << s;
    }
    const unsigned t = g() % 50;
    r.score = t == 0 ? 32002 : (t == 1 ? 0 : static_cast<int>(g() % 6001) - 3000);
    r.ply = (g() % 4 == 0) ? static_cast<int>(g() % 60) : 40;
    r.result = static_cast<int>(g() % 3) - 1;
    return r;
}

static std::vector<Rec> write_file(const std::string& path, int records, unsigned seed, int max_extra = 30) {
    std::mt19937 g(seed);
    std::vector<Rec> recs;
    std::vector<unsigned char> file;
    int left = records;
    while (left > 0) {
        const int n = std::min(left, 1 + static_cast<int>(g() % 3000));
        std::vector<unsigned char> payload;
        for (int i = 0; i < n; ++i) {
            recs.push_back(random_rec(g, max_extra));
            put_rec(payload, recs.back());
        }
        if (g() % 3 == 0)
            payload.insert(payload.end(), g() % 34, 0xAB);  // short tail: ignored by the reader
        const auto sz = static_cast<std::uint32_t>(payload.size());
        const unsigned char hdr[8] = {'B', 'I', 'N', 'P', static_cast<unsigned char>(sz), static_cast<unsigned char>(sz >> 8),
                                      static_cast<unsigned char>(sz >> 16), static_cast<unsigned char>(sz >> 24)};
        file.insert(file.end(), hdr, hdr + 8);
        file.insert(file.end(), payload.begin(), payload.end());
        left -= n;
    }
    std::FILE* f = std::fopen(path.c_str(), "wb");
    std::fwrite(file.data(), 1, file.size(), f);
    std::fclose(f);
    return recs;
}

static void write_raw(const std::string& path, const std::vector<unsigned char>& bytes) {
    std::FILE* f = std::fopen(path.c_str(), "wb");
    if (!bytes.empty())
        std::fwrite(bytes.data(), 1, bytes.size(), f);
    std::fclose(f);
}

// ---- independent reference for one row (LOADER_SPEC.md section 5) ----
struct RefRow {
    float w, o, s;
    int pc, qb, feat[2][32];
};

static RefRow ref_row(const Rec& r) {
    RefRow x{};
    int piece[64];
    std::fill(piece, piece + 64, -1);
    int stm = 0;
    for (int sq = 0; sq < 64; ++sq) {
        if (!(r.occ >> sq & 1))
            continue;
        int c = r.code[sq];
        if (c == 12)
            c = (sq / 8 == 3) ? 0 : 1;
        if (c == 13)
            c = 6;
        if (c == 14)
            c = 7;
        if (c == 15) {
            c = 11;
            stm = 1;
        }
        piece[sq] = c;
    }
    int ksq[2] = {-1, -1};
    bool q[2] = {false, false}, rq = false;
    for (int sq = 0; sq < 64; ++sq) {
        if (piece[sq] < 0)
            continue;
        const int type = piece[sq] / 2, col = piece[sq] % 2;
        if (type == 5 && ksq[col] < 0)
            ksq[col] = sq;
        if (type == 4)
            q[col] = rq = true;
        if (type == 3)
            rq = true;
    }
    x.w = stm == 0 ? 1.0f : 0.0f;
    x.o = (r.result + 1.0f) / 2.0f;
    x.s = static_cast<float>(static_cast<std::int16_t>(r.score));
    x.qb = (q[stm] ? 2 : 0) + (q[1 - stm] ? 1 : 0);
    for (int c = 0; c < 2; ++c) {
        auto orient = [&](int s) {
            int f = s % 8, rank = s / 8;
            if (c == 1)
                rank = 7 - rank;
            if (ksq[c] % 8 < 4)
                f = 7 - f;
            return rank * 8 + f;
        };
        const int ok = orient(ksq[c]);
        const int bucket = 31 - (4 * (ok / 8) + (ok % 8) - 4);
        const int state = q[1 - c] ? 2 : (rq ? 1 : 0);
        int n = 0;
        for (int sq = 0; sq < 64; ++sq)
            if (piece[sq] >= 0) {
                const int type = piece[sq] / 2, col = piece[sq] % 2;
                x.feat[c][n++] = orient(sq) + 64 * (2 * type + (col != c ? 1 : 0)) + 768 * (32 * state + bucket);
            }
        x.pc = n;
    }
    return x;
}

static FflConfig base_config(int batch, int threads, bool cyclic, int window, bool filter) {
    FflConfig c{};
    c.batch_size = batch;
    c.threads = threads;
    c.cyclic = cyclic ? 1 : 0;
    c.window_entries = window;
    c.random_fen_skipping = filter ? 3 : 0;
    c.early_fen_skipping = filter ? 2 : -1;
    c.soft_early_fen_skipping = filter ? 20 : 0;
    c.simple_eval_skipping = -1;
    const double pcy[5] = {0.0, 0.4, 1.0, 1.0, 0.75};
    const double px[4] = {0, 6, 10, 18}, py[4] = {0.1, 0.15, 0.25, 0.75};
    std::copy(pcy, pcy + 5, c.pc_y);
    std::copy(px, px + 4, c.ply_x);
    std::copy(py, py + 4, c.ply_y);
    return c;
}

static std::uint64_t mix(std::uint64_t h, const void* p, std::size_t n) {
    const auto* b = static_cast<const unsigned char*>(p);
    for (std::size_t i = 0; i < n; ++i)
        h = (h ^ b[i]) * 1099511628211ULL;
    return h;
}

static bool check_rows(const BatchView& b) {
    bool ok = b.num_inputs == 73728 && b.max_active_features == 32 && b.size > 0;
    long active = 0;
    for (int i = 0; i < b.size && ok; ++i) {
        const int pc = b.piece_count[i];
        ok = pc >= 2 && pc <= 32 && b.queen_bucket[i] >= 0 && b.queen_bucket[i] <= 3
          && (b.is_white[i] == 0.0f || b.is_white[i] == 1.0f)
          && (b.outcome[i] == 0.0f || b.outcome[i] == 0.5f || b.outcome[i] == 1.0f);
        for (int side = 0; side < 2 && ok; ++side) {
            const int* f = (side == 0 ? b.white : b.black) + 32 * i;
            for (int j = 0; j < 32 && ok; ++j)
                ok = j < pc ? (f[j] >= 0 && f[j] < 73728) : f[j] == -1;
        }
        active += pc;
    }
    return ok && active == b.num_active_white_features && active == b.num_active_black_features;
}

// Hash of the first `batches` batches (or until the end of a finite stream).
static std::uint64_t run_hash(const std::string& path, FflConfig c, int batches, long* rows_out, bool* rows_ok) {
    void* h = ffl_create(&c, path.c_str());
    if (!h) {
        std::fprintf(stderr, "create failed: %s\n", ffl_create_error());
        ++g_fail;
        return 0;
    }
    std::uint64_t hash = 1469598103934665603ULL;
    long rows = 0;
    bool ok = true;
    for (int k = 0; k < batches; ++k) {
        BatchView* b = ffl_next(h);
        if (!b)
            break;
        ok = ok && check_rows(*b);
        hash = mix(hash, b->is_white, sizeof(float) * 3 * static_cast<std::size_t>(b->size));
        hash = mix(hash, b->white, sizeof(int) * (66 * static_cast<std::size_t>(b->size)));
        rows += b->size;
        ffl_release(h, b);
    }
    char err[256];
    if (ffl_error(h, err, sizeof err)) {
        std::fprintf(stderr, "stream error: %s\n", err);
        ++g_fail;
    }
    ffl_destroy(h);
    if (rows_out)
        *rows_out = rows;
    if (rows_ok)
        *rows_ok = ok;
    return hash;
}

static bool stream_fails(const std::string& path, const char* what, bool filter = true) {
    FflConfig c = base_config(64, 2, false, 1024, filter);  // no filter: every record is kept (decoded)
    void* h = ffl_create(&c, path.c_str());
    if (!h)
        return true;
    bool failed = false;
    for (int k = 0; k < 100000; ++k) {
        BatchView* b = ffl_next(h);
        if (!b)
            break;
        ffl_release(h, b);
    }
    char err[256];
    failed = ffl_error(h, err, sizeof err) > 0;
    ffl_destroy(h);
    if (!failed)
        std::fprintf(stderr, "expected an error for %s\n", what);
    return failed;
}

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    const std::string dir = argc > 1 ? argv[1] : ".";
    const std::string fa = dir + "/ffl_a.binpack";

    // (1) No-filter, finite, one window larger than the file: output = std::shuffle of the arrival order.
    {
        const std::vector<Rec> recs = write_file(fa, 7000, 11);
        FflConfig c = base_config(512, 3, false, 1 << 20, false);
        void* h = ffl_create(&c, fa.c_str());
        CHECK(h != nullptr, "create (no filter)");
        std::vector<std::uint32_t> order(recs.size());
        std::iota(order.begin(), order.end(), 0u);
        std::mt19937_64 rng;  // the loader's engine, default seed; no draws happen before the seal
        std::shuffle(order.begin(), order.end(), rng);
        std::size_t row = 0;
        bool same = true;
        while (BatchView* b = ffl_next(h)) {
            for (int i = 0; i < b->size && same; ++i, ++row) {
                const RefRow x = ref_row(recs[order[row]]);
                same = b->is_white[i] == x.w && b->outcome[i] == x.o && b->score[i] == x.s
                    && b->piece_count[i] == x.pc && b->queen_bucket[i] == x.qb
                    && std::equal(x.feat[0], x.feat[0] + x.pc, b->white + 32 * i)
                    && std::equal(x.feat[1], x.feat[1] + x.pc, b->black + 32 * i);
            }
            ffl_release(h, b);
        }
        CHECK(same, "no-filter stream equals the independent reference");
        CHECK(row == recs.size(), "no-filter stream keeps every record");
        std::uint64_t pre = 0, tot = 0;
        ffl_stats(h, &pre, &tot, nullptr);
        CHECK(pre == recs.size() && tot == recs.size(), "stats: read = kept = records");
        ffl_destroy(h);
        std::printf("(1) no-filter reference: %zu rows %s\n", row, same ? "OK" : "DIFF");
    }

    // (2) Filtered streams: same output for 1 / 2 / 5 builders; windows (1500) do not divide into batches (700).
    {
        write_file(fa, 60000, 12);
        long r1 = 0, r2 = 0, r5 = 0;
        bool ok1 = true, ok2 = true, ok5 = true;
        const auto h1 = run_hash(fa, base_config(700, 1, true, 1500, true), 400, &r1, &ok1);
        const auto h2 = run_hash(fa, base_config(700, 2, true, 1500, true), 400, &r2, &ok2);
        const auto h5 = run_hash(fa, base_config(700, 5, true, 1500, true), 400, &r5, &ok5);
        CHECK(h1 == h2 && h1 == h5 && r1 == 400 * 700 && r1 == r2 && r1 == r5, "cyclic: thread count changes nothing");
        CHECK(ok1 && ok2 && ok5, "cyclic: row invariants");
        long f1 = 0, f3 = 0;
        const auto g1 = run_hash(fa, base_config(700, 1, false, 1500, true), 1 << 30, &f1, &ok1);
        const auto g3 = run_hash(fa, base_config(700, 3, false, 1500, true), 1 << 30, &f3, &ok2);
        CHECK(g1 == g3 && f1 == f3 && f1 > 0 && f1 < 60000, "finite: thread count changes nothing");
        CHECK(ok1 && ok2, "finite: row invariants");
        std::printf("(2) filtered: cyclic %ld rows x3 %s, finite %ld rows %s\n", r1,
                    (h1 == h2 && h1 == h5) ? "equal" : "DIFF", f1, g1 == g3 ? "equal" : "DIFF");
    }

    // (3) Format errors stop the stream with a message.
    {
        std::vector<unsigned char> good;
        std::mt19937 g(5);
        Rec r = random_rec(g, 10);
        put_rec(good, r);
        auto chunk = [](std::vector<unsigned char> payload) {
            const auto sz = static_cast<std::uint32_t>(payload.size());
            std::vector<unsigned char> f = {'B', 'I', 'N', 'P', static_cast<unsigned char>(sz),
                                            static_cast<unsigned char>(sz >> 8), static_cast<unsigned char>(sz >> 16),
                                            static_cast<unsigned char>(sz >> 24)};
            f.insert(f.end(), payload.begin(), payload.end());
            return f;
        };
        Rec chained = r;
        chained.chain = 1;
        std::vector<unsigned char> p1;
        put_rec(p1, chained);
        write_raw(dir + "/e_chain.binpack", chunk(p1));
        auto bad_magic = chunk(good);
        bad_magic[0] = 'X';
        write_raw(dir + "/e_magic.binpack", bad_magic);
        auto trunc = chunk(good);
        trunc.resize(trunc.size() - 5);
        write_raw(dir + "/e_trunc.binpack", trunc);
        Rec nok = r;  // drop the black king
        for (int sq = 0; sq < 64; ++sq)
            if ((nok.occ >> sq & 1) && (nok.code[sq] == 11 || nok.code[sq] == 15))
                nok.occ &= ~(1ULL << sq);
        std::vector<unsigned char> p2;
        put_rec(p2, nok);
        write_raw(dir + "/e_king.binpack", chunk(p2));
        Rec many = r;
        many.occ = ~0ULL >> 20;  // 44 squares
        std::vector<unsigned char> p3;
        put_rec(p3, many);
        write_raw(dir + "/e_many.binpack", chunk(p3));
        write_raw(dir + "/e_empty.binpack", {});
        write_raw(dir + "/e_short.binpack", chunk(std::vector<unsigned char>(20, 0)));
        CHECK(stream_fails(dir + "/e_chain.binpack", "chain"), "chained record rejected");
        CHECK(stream_fails(dir + "/e_magic.binpack", "magic"), "bad magic rejected");
        CHECK(stream_fails(dir + "/e_trunc.binpack", "truncated"), "truncated chunk rejected");
        CHECK(stream_fails(dir + "/e_king.binpack", "king", false), "missing king rejected (kept record)");
        CHECK(stream_fails(dir + "/e_many.binpack", "pieces"), "more than 32 pieces rejected");
        CHECK(stream_fails(dir + "/e_empty.binpack", "empty"), "empty file rejected");
        CHECK(stream_fails(dir + "/e_short.binpack", "short"), "chunk shorter than a record rejected");
        FflConfig bad = base_config(64, 1, true, 1024, true);
        bad.filtered = 1;
        CHECK(ffl_create(&bad, fa.c_str()) == nullptr, "filtered config rejected at create");
        CHECK(ffl_create(&bad, (dir + "/missing.binpack").c_str()) == nullptr, "missing file rejected");
        std::printf("(3) format errors checked\n");
    }

    // (4) Destroy while the threads run (small ring, many builders), several times, with the newest batch still
    // held by the consumer (a consumer may hold at most ring - 1 batches and still make progress).
    {
        for (int rep = 0; rep < 5; ++rep) {
            FflConfig c = base_config(256, 8, true, 1024, true);
            c.ring_batches = 3;
            void* h = ffl_create(&c, fa.c_str());
            CHECK(h != nullptr, "create (destroy test)");
            BatchView* held = nullptr;
            for (int k = 0; k < 3 + rep * 7; ++k) {
                BatchView* b = ffl_next(h);
                if (!b)
                    break;
                if (held)
                    ffl_release(h, held);
                held = b;
            }
            ffl_destroy(h);
        }
        std::printf("(4) destroy while running: done\n");
    }

    // (5) Window much smaller than the batch (3 * 1024 < 5000): must not hang; thread count changes nothing.
    {
        long c1 = 0, c3 = 0, f1 = 0, f3 = 0;
        bool o1 = true, o3 = true;
        const auto h1 = run_hash(fa, base_config(5000, 1, true, 1024, true), 40, &c1, &o1);
        const auto h3 = run_hash(fa, base_config(5000, 3, true, 1024, true), 40, &c3, &o3);
        const auto g1 = run_hash(fa, base_config(5000, 1, false, 1024, true), 1 << 30, &f1, &o1);
        const auto g3 = run_hash(fa, base_config(5000, 3, false, 1024, true), 1 << 30, &f3, &o3);
        CHECK(h1 == h3 && c1 == 40 * 5000 && c3 == c1 && o1 && o3, "window < batch, cyclic");
        CHECK(g1 == g3 && f1 == f3 && f1 > 0, "window < batch, finite");
        std::printf("(5) window 1024 < batch 5000: cyclic %ld rows, finite %ld rows, no hang\n", c1, f1);
    }

    // (6) Acceptance exactly 0 (pc_y1 = 0 gives weight 0 to 2..7 pieces): the threshold saturates, such rows are
    // always rejected, on every compiler / instruction set.
    {
        const std::string fl = dir + "/ffl_low.binpack";
        write_file(fl, 30000, 13, 5);  // 2..7 pieces
        FflConfig c = base_config(512, 2, false, 4096, true);
        c.pc_y[1] = 0.0;
        void* h = ffl_create(&c, fl.c_str());
        CHECK(h != nullptr, "create (pc_y1 = 0)");
        long rows = 0;
        while (BatchView* b = ffl_next(h)) {
            rows += b->size;
            ffl_release(h, b);
        }
        std::uint64_t pre = 0, tot = 0;
        ffl_stats(h, &pre, &tot, nullptr);
        ffl_destroy(h);
        CHECK(rows == 0 && tot == 0 && pre == 30000, "acceptance 0 always rejects");
        std::printf("(6) acceptance 0: read %llu, kept %llu\n", static_cast<unsigned long long>(pre),
                    static_cast<unsigned long long>(tot));
    }

    // (7) Releasing a batch twice stops the stream with an error (no buffer is shared by two builders).
    {
        FflConfig c = base_config(256, 2, true, 1024, true);
        void* h = ffl_create(&c, fa.c_str());
        BatchView* b = ffl_next(h);
        CHECK(b != nullptr, "first batch");
        ffl_release(h, b);
        ffl_release(h, b);
        char err[256];
        CHECK(ffl_error(h, err, sizeof err) > 0, "double release reported");
        CHECK(ffl_next(h) == nullptr, "stream stopped after a double release");
        ffl_destroy(h);
        std::printf("(7) double release: %s\n", err);
    }

    std::printf("%s (%d failures)\n", g_fail ? "FAILED" : "ALL PASSED", g_fail);
    return g_fail ? 1 : 0;
}
