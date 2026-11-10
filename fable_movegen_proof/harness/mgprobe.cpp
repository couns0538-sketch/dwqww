// mgprobe.cpp - auxiliary probe of job 3 (own test code, no engine source is changed).
//
// It is compiled together with the six engine units (bitboard, board, eval, eval_params, nnue, search) of ONE
// source tree and reads the fields the release executables do not print: the generated move lists in order,
// is_legal / gives_check per move, the checkers bitboard as make_move leaves it, has_legal_move, and the static
// evaluation with the net off and on. Two probes (lock tree and candidate tree) fed the same path file must
// write byte-identical transcripts after their identity frame. The probe is a separate artifact: it shares the
// source files with a release executable, not its code generation (no LTO, no PGO, another main()).
//
//   mgprobe id                                   one JSON line about this build
//   mgprobe gen  --seeds F --master HEX --chunk I --positions N      path chunk (text) on stdout, stats on stderr
//   mgprobe run  [--null 0|1]                    path chunk on stdin -> binary transcript on stdout
//   mgprobe uciscript --perft D [--expect FILE]  path chunk on stdin -> UCI commands on stdout; FILE gets one line
//                                                per position with this probe's legal moves in generation order
//   mgprobe keys --master HEX --positions N --part F:A-B [--part ...]   distinct-position statistics (JSON)
//
// Path chunk (text):  "H ..." header, "C" clear the worker's caches, "P <playout> <seedtag> <policy> <fen>",
// "M <uci> <uci> ..." the moves played from that seed. Every position on the path is one transcript record.
//
// The build script writes mgprobe_identity.h next to the output (tag, tree manifest, defines, sha256 of this
// file); the first frame of every transcript carries it, so a transcript says which probe wrote it.
//
// Random numbers: SplitMix64 for seeding and xoshiro256** for the stream, written from their public-domain
// descriptions (Blackman and Vigna). No code, table or constant of a GPL program is used.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include "mgprobe_identity.h"   // MGPROBE_TAG, MGPROBE_TREE_MANIFEST, MGPROBE_DEFS, MGPROBE_HARNESS_SHA256

#include <algorithm>
#include <array>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <vector>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

#define MGPROBE_VERSION "mgprobe-2"

#if FORGE_SPD_NO_ZERO_MOVELISTS < 2
#error "mgprobe needs the lock's generator: build with -DFORGE_SPD_NO_ZERO_MOVELISTS=2 (the lock's switch set)"
#endif

namespace forge {
// The engine's own test hook: search.hpp declares `friend struct SearcherTestProbe` in Worker.
struct SearcherTestProbe {
    static SearchStack* slot(Worker& w, int i) { return &w.stack_[static_cast<std::size_t>(i)]; }
    static int static_eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void record(Worker& w, SearchStack* ss, const Board& b, const Move& m) { w.record_move(ss, b, m); }
};
} // namespace forge

namespace {

using namespace forge;
using Probe = forge::SearcherTestProbe;
using u64 = std::uint64_t;
using u32 = std::uint32_t;

constexpr u32 FrameMagic = 0x3150474DU;   // "MGP1"
constexpr u64 AllOnes = ~0ULL;

[[noreturn]] void die(const char* what) {
    std::fprintf(stderr, "mgprobe: %s\n", what);
    std::exit(2);
}

u32 move_bits(Move m) {
    return static_cast<u32>(m.from) | (static_cast<u32>(m.to) << 8) | (static_cast<u32>(m.promotion) << 16) |
           (static_cast<u32>(m.flags) << 24);
}

// ---------------------------------------------------------------- random numbers
struct Rng {
    u64 s[4];
    static u64 splitmix(u64& x) {
        u64 z = (x += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }
    explicit Rng(u64 seed) {
        u64 x = seed;
        for (u64& v : s) v = splitmix(x);
    }
    static u64 rotl(u64 x, int k) { return (x << k) | (x >> (64 - k)); }
    u64 next() {
        const u64 result = rotl(s[1] * 5, 7) * 9;
        const u64 t = s[1] << 17;
        s[2] ^= s[0];
        s[3] ^= s[1];
        s[1] ^= s[2];
        s[0] ^= s[3];
        s[2] ^= t;
        s[3] = rotl(s[3], 45);
        return result;
    }
    // uniform in [0, n) by multiply-shift (the bias is below 2^-40 for the n used here)
    u64 below(u64 n) {
        __extension__ using u128 = unsigned __int128;
        return static_cast<u64>((static_cast<u128>(next()) * n) >> 64);
    }
};

// ---------------------------------------------------------------- output buffer
struct Out {
    std::vector<unsigned char> d;
    void clear() { d.clear(); }
    void raw(const void* p, std::size_t n) {
        const unsigned char* c = static_cast<const unsigned char*>(p);
        d.insert(d.end(), c, c + n);
    }
    void u8(unsigned v) { d.push_back(static_cast<unsigned char>(v)); }
    void u16(unsigned v) { const std::uint16_t x = static_cast<std::uint16_t>(v); raw(&x, 2); }
    void w32(u32 v) { raw(&v, 4); }
    void w64(u64 v) { raw(&v, 8); }
    void i32(int v) { const std::int32_t x = v; raw(&x, 4); }
    void str(const std::string& s) { u16(static_cast<unsigned>(s.size())); raw(s.data(), s.size()); }
    void moves(const MoveList& l) {
        u16(static_cast<unsigned>(l.size()));
        for (const Move m : l) w32(move_bits(m));
    }
};

void write_frame(const Out& o) {
    const u32 head[2] = {FrameMagic, static_cast<u32>(o.d.size())};
    if (std::fwrite(head, 4, 2, stdout) != 2 || std::fwrite(o.d.data(), 1, o.d.size(), stdout) != o.d.size())
        die("write failed");
}

// ---------------------------------------------------------------- seeds and path generation
struct Seeds {
    std::vector<std::string> cls[4];   // 0 F (fens12k), 1 E (edge), 2 B (bench), 3 S (start position)
};
constexpr char SeedTag[4] = {'F', 'E', 'B', 'S'};

void load_seeds(const char* path, Seeds& seeds) {
    std::FILE* f = std::fopen(path, "rb");
    if (f == nullptr) die("cannot read the seeds file");
    std::string line;
    int c;
    auto flush = [&]() {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.size() > 2 && line[1] == '\t') {
            for (int k = 0; k < 4; ++k)
                if (line[0] == SeedTag[k]) seeds.cls[k].push_back(line.substr(2));
        }
        line.clear();
    };
    while ((c = std::fgetc(f)) != EOF) {
        if (c == '\n') flush();
        else line.push_back(static_cast<char>(c));
    }
    flush();
    std::fclose(f);
}

struct Stats {
    u64 positions = 0, in_check = 0, double_check = 0, mates = 0, stalemates = 0, with_ep_square = 0;
    u64 playouts = 0, rejected_seeds = 0, clears = 0;
    u64 captures = 0, promotions = 0, castles = 0, en_passants = 0, checks_given = 0;
    u64 seed_class[4] = {0, 0, 0, 0};
};

// One chunk of N visited positions. The random stream does not depend on `out` or `keys`.
void gen_chunk(const Seeds& seeds, u64 master, u64 chunk, u64 n_positions, std::FILE* out, Stats& st,
               std::vector<u64>* keys) {
    Rng rng(master ^ ((chunk + 1) * 0x9E3779B97F4A7C15ULL));
    u64 count = 0, playout = 0;
    while (count < n_positions) {
        const u64 r = rng.below(100);
        int c = r < 70 ? 0 : r < 90 ? 1 : r < 95 ? 2 : 3;
        if (seeds.cls[c].empty()) c = 0;
        if (seeds.cls[c].empty()) {
            c = 0;
            while (c < 4 && seeds.cls[c].empty()) ++c;
            if (c == 4) die("no seeds");
        }
        const u64 idx = rng.below(seeds.cls[c].size());
        const int policy = static_cast<int>(rng.below(2));
        const int maxply = c >= 2 ? 20 + static_cast<int>(rng.below(141)) : 8 + static_cast<int>(rng.below(73));
        const bool clear = rng.below(16) == 0;
        const std::string& fen = seeds.cls[c][idx];
        Board b;
        if (!b.set_fen(fen)) {
            ++st.rejected_seeds;
            continue;
        }
        if (clear) {
            if (out != nullptr) std::fputs("C\n", out);
            ++st.clears;
        }
        if (out != nullptr)
            std::fprintf(out, "P %llu %c%llu %d %s\nM", static_cast<unsigned long long>(playout), SeedTag[c],
                         static_cast<unsigned long long>(idx), policy, fen.c_str());
        ++st.seed_class[c];
        int ply = 0;
        for (;;) {
            ++count;
            ++st.positions;
            const MoveList legal = b.legal_moves();
            if (b.in_check()) ++st.in_check;
            if (popcount(b.checkers()) > 1) ++st.double_check;
            if (b.ep_square() >= 0) ++st.with_ep_square;
            if (legal.empty()) {
                if (b.in_check()) ++st.mates;
                else ++st.stalemates;
            }
            if (keys != nullptr) keys->push_back(b.key());
            if (legal.empty() || ply >= maxply || count >= n_positions) break;
            std::size_t pick = 0;
            if (policy == 0) {
                pick = static_cast<std::size_t>(rng.below(legal.size()));
            } else {
                // semi-random: weight the special moves so that checks, captures, promotions, castling and
                // en passant are visited far more often than uniform play would
                std::array<u64, MoveList::Capacity> w{};
                u64 total = 0;
                for (std::size_t i = 0; i < legal.size(); ++i) {
                    const Move m = legal[i];
                    u64 x = 1;
                    if ((m.flags & EnPassant) != 0U) x *= 16;
                    else if ((m.flags & Capture) != 0U) x *= 4;
                    if (m.is_promotion()) x *= 8;
                    if (m.is_castle()) x *= 8;
                    if ((m.flags & DoublePush) != 0U) x *= 2;
                    if (piece_type(b.piece_at(m.from)) == King && !m.is_castle()) x *= 2;
                    if (b.gives_check(m)) x *= 6;
                    w[i] = x;
                    total += x;
                }
                u64 t = rng.below(total);
                while (pick + 1 < legal.size() && t >= w[pick]) {
                    t -= w[pick];
                    ++pick;
                }
            }
            const Move m = legal[pick];
            if (m.is_capture()) ++st.captures;
            if (m.is_promotion()) ++st.promotions;
            if (m.is_castle()) ++st.castles;
            if ((m.flags & EnPassant) != 0U) ++st.en_passants;
            if (b.gives_check(m)) ++st.checks_given;
            if (out != nullptr) {
                std::fputc(' ', out);
                std::fputs(Board::move_to_uci(m).c_str(), out);
            }
            Undo u;
            (void)b.make_move(m, u);
            ++ply;
        }
        if (out != nullptr) std::fputc('\n', out);
        ++playout;
        ++st.playouts;
    }
}

void print_stats(std::FILE* f, const Stats& st, const char* extra) {
    std::fprintf(f,
                 "{\"positions\":%llu,\"in_check\":%llu,\"double_check\":%llu,\"mates\":%llu,\"stalemates\":%llu,"
                 "\"with_ep_square\":%llu,\"playouts\":%llu,\"rejected_seeds\":%llu,\"cache_clears\":%llu,"
                 "\"captures\":%llu,\"promotions\":%llu,\"castles\":%llu,\"en_passants\":%llu,\"checks_given\":%llu,"
                 "\"seeds_F\":%llu,\"seeds_E\":%llu,\"seeds_B\":%llu,\"seeds_S\":%llu%s}\n",
                 static_cast<unsigned long long>(st.positions), static_cast<unsigned long long>(st.in_check),
                 static_cast<unsigned long long>(st.double_check), static_cast<unsigned long long>(st.mates),
                 static_cast<unsigned long long>(st.stalemates), static_cast<unsigned long long>(st.with_ep_square),
                 static_cast<unsigned long long>(st.playouts), static_cast<unsigned long long>(st.rejected_seeds),
                 static_cast<unsigned long long>(st.clears), static_cast<unsigned long long>(st.captures),
                 static_cast<unsigned long long>(st.promotions), static_cast<unsigned long long>(st.castles),
                 static_cast<unsigned long long>(st.en_passants), static_cast<unsigned long long>(st.checks_given),
                 static_cast<unsigned long long>(st.seed_class[0]), static_cast<unsigned long long>(st.seed_class[1]),
                 static_cast<unsigned long long>(st.seed_class[2]), static_cast<unsigned long long>(st.seed_class[3]),
                 extra);
}

// ---------------------------------------------------------------- the walker of `run`
const Board* g_at = nullptr;
const char* g_what = "";
Move g_move = Move::none();

void on_abort(int) {
    std::fprintf(stderr, "ENGINE ABORT during: %s | at %s | move %s\n", g_what,
                 g_at != nullptr ? g_at->fen().c_str() : "-",
                 g_move.is_none() ? "-" : Board::move_to_uci(g_move).c_str());
    std::fflush(stderr);
}

struct Walker {
    static constexpr int Base = 4, Window = 64, RefreshSlot = 100;
    SharedSearchState shared{1};
    std::unique_ptr<Worker> worker = std::make_unique<Worker>(shared, 0);
    std::unique_ptr<nnue::Accumulator> acc = std::make_unique<nnue::Accumulator>();
    Out rec;
    std::array<Board, 8> ring;
    std::array<int, 8> ring_off{}, ring_on{};
    u64 records = 0, hard = 0, soft = 0;
    bool with_null = true;

    void fail_hard(const char* what, const Board& b, Move m = Move::none()) {
        if (++hard <= 10)
            std::fprintf(stderr, "SELFCHECK FAILED: %s | at %s | move %s\n", what, b.fen().c_str(),
                         m.is_none() ? "-" : Board::move_to_uci(m).c_str());
    }

    SearchStack* inc_slot(int ply) { return Probe::slot(*worker, Base + (ply % Window)); }

    // net off: Worker::static_evaluate returns evaluator_.evaluate(board), the pawn-cache path
    int eval_off(const Board& b) {
        const bool was = nnue::enabled;
        nnue::enabled = false;
        const int v = Probe::static_eval(*worker, b, Probe::slot(*worker, RefreshSlot));
        nnue::enabled = was;
        return v;
    }
    // net on, refresh path: a slot whose own and parent accumulators are invalid
    int eval_on_refresh(const Board& b) {
        SearchStack* rs = Probe::slot(*worker, RefreshSlot);
        rs->ply = 0;
        rs->accumulator.valid = false;
        rs->runtime_psqt.valid = false;
        (rs - 1)->accumulator.valid = false;
        const bool was = nnue::enabled;
        nnue::enabled = true;
        const int v = Probe::static_eval(*worker, b, rs);
        nnue::enabled = was;
        return v;
    }
    // net on, incremental path along the playout (refresh at the start of every window of 64 plies)
    int eval_on_inc(const Board& b, int ply) {
        SearchStack* ss = inc_slot(ply);
        if (ply % Window == 0) {
            ss->ply = 0;
            ss->accumulator.valid = false;
            ss->runtime_psqt.valid = false;
            (ss - 1)->accumulator.valid = false;
        } else if (!(ss - 1)->accumulator.valid || ss->accumulator.valid || ss->ply < 1) {
            // inside a window the value must come from ONE update of the parent's accumulator: the parent is
            // valid, this slot was invalidated by record_move. Anything else would be a silent refresh.
            fail_hard("the incremental accumulator chain is broken (the value would not be incremental)", b);
        }
        const bool was = nnue::enabled;
        nnue::enabled = true;
        const int v = Probe::static_eval(*worker, b, ss);
        nnue::enabled = was;
        return v;
    }
    // called before the playout move is made from the position at `ply`
    void before_move(const Board& b, const Move& m, int ply) {
        if ((ply + 1) % Window == 0) return;
        SearchStack* ss = inc_slot(ply);
        const bool was = nnue::enabled;
        nnue::enabled = true;
        Probe::record(*worker, ss, b, m);
        (ss + 1)->ply = ss->ply + 1;
        nnue::enabled = was;
    }

    void visit(Board& x, const Board& twin, u32 playout, int ply) {
        const Board pristine = x;   // never queried: every copy of it starts without king lines
        g_at = &pristine;
        g_move = Move::none();
        g_what = "checkers, has_legal_move, generation";
        const Color us = x.side_to_move();
        Board fresh;
        const bool fresh_ok = fresh.set_fen(x.fen());
        const Bitboard direct = x.attackers_to(x.king_square(us)) & x.occupied(opposite(us));
        const Bitboard ck_main = x.checkers();
        const Bitboard ck_twin = twin.checkers();
        const Bitboard ck_fresh = fresh_ok ? fresh.checkers() : AllOnes;
        if (ck_main != direct || ck_twin != direct || ck_fresh != direct) fail_hard("checkers differ between routes", x);

        bool has_before;
        {
            Board f2 = pristine;
            has_before = f2.has_legal_move();
        }
        MoveList all, caps, quiets;
        x.generate_pseudo_legal(all, Board::GenMode::All);
        x.generate_pseudo_legal(caps, Board::GenMode::Captures);
        x.generate_pseudo_legal(quiets, Board::GenMode::Quiets);

        // bits: answers on the board that keeps its king lines (x). one_bits: the FIRST query on a board without
        // king lines, is_legal and gives_check each on its own copy. post_bits: asked again after the makes and
        // unmakes, when the king lines have been restored from an Undo (the state inside the search's move loop).
        std::array<unsigned char, MoveList::Capacity> bits{}, one_bits{}, post_bits{};
        std::array<u64, MoveList::Capacity> child_one{}, child_main{};
        MoveList filtered;
        g_what = "is_legal, gives_check, make on a copy after one query";
        for (std::size_t i = 0; i < all.size(); ++i) {
            const Move m = all[i];
            g_move = m;
            const bool ok = x.is_legal(m);
            Board q1 = pristine, q2 = pristine;
            const bool first_legal = q1.is_legal(m);
            const bool first_check = q2.gives_check(m);
            one_bits[i] = static_cast<unsigned char>((first_legal ? 1 : 0) | (first_check ? 2 : 0));
            {
                // as in the search: one earlier query on a board without king lines, then the make
                Board& one = (i & 1U) == 0U ? q1 : q2;
                Undo u;
                (void)one.make_move(m, u);
                child_one[i] = one.checkers();
            }
            unsigned char b = ok ? 1 : 0;
            if (ok) {
                filtered.push_back(m);
                if (x.gives_check(m)) b |= 2;
            }
            bits[i] = b;
            if (first_legal != ok) fail_hard("is_legal differs between a board with and without king lines", x, m);
            if (ok && first_check != ((b & 2) != 0)) fail_hard("gives_check differs between a board with and without king lines", x, m);
        }
        g_move = Move::none();
        g_what = "legal_moves, has_legal_move";
        const MoveList legal = x.legal_moves();
        const MoveList legal_caps = x.legal_moves(true);
        const bool has_after = x.has_legal_move();
        if (has_before != !legal.empty() || has_after != !legal.empty()) fail_hard("has_legal_move != (legal list not empty)", x);
        if (legal.size() != filtered.size()) fail_hard("legal_moves() != generated moves filtered by is_legal", x);
        else
            for (std::size_t i = 0; i < legal.size(); ++i)
                if (!(legal[i] == filtered[i])) { fail_hard("legal_moves() order != generation order", x, legal[i]); break; }
        {
            std::size_t k = 0;
            bool same = true;
            for (const Move m : caps)
                if (x.is_legal(m)) {
                    if (k >= legal_caps.size() || !(legal_caps[k] == m)) { same = false; break; }
                    ++k;
                }
            if (!same || k != legal_caps.size()) fail_hard("legal_moves(true) != capture list filtered by is_legal", x);
        }
        g_what = "make and unmake of a legal move on the board with king lines";
        const u64 key0 = x.key();
        for (std::size_t i = 0; i < all.size(); ++i) {
            if ((bits[i] & 1U) == 0U) { child_main[i] = AllOnes; continue; }
            const Move m = all[i];
            g_move = m;
            Undo u;
            (void)x.make_move(m, u);
            child_main[i] = x.checkers();
            x.unmake_move(m, u);
            if (child_main[i] != child_one[i]) fail_hard("checkers after make differ between the two boards", x, m);
        }
        g_move = Move::none();
        if (x.key() != key0 || x.checkers() != ck_main) fail_hard("make / unmake did not restore the position", x);
        g_what = "is_legal, gives_check after make and unmake";
        for (std::size_t i = 0; i < all.size(); ++i) {
            const Move m = all[i];
            g_move = m;
            unsigned char b = x.is_legal(m) ? 1 : 0;
            if (b != 0 && x.gives_check(m)) b |= 2;
            post_bits[i] = b;
            if (b != bits[i]) fail_hard("is_legal / gives_check differ after make and unmake", x, m);
        }
        g_move = Move::none();

        // static evaluation; the first touch of the pawn cache alternates between the two entry points
        g_what = "static evaluation";
        const int hce = Evaluator::evaluate_uncached(x);
        int off, on_refresh;
        if (((playout + static_cast<u32>(ply)) & 1U) == 0U) {
            off = eval_off(x);
            on_refresh = eval_on_refresh(x);
        } else {
            on_refresh = eval_on_refresh(x);
            off = eval_off(x);
        }
        const int on_inc = eval_on_inc(x, ply);
        nnue::refresh(x, *acc);
        const int net = nnue::evaluate(x, *acc);
        if (off != hce) fail_hard("eval through the pawn cache != eval without cache", x);
        const int want_on = nnue::residual() ? std::clamp(hce + net, -MateInMaxPly + 1, MateInMaxPly - 1) : net;
        if (on_refresh != want_on) fail_hard("static eval net on != expected from hand-crafted eval and net", x);
        if (on_inc != on_refresh) ++soft;
        // stale-cache probes: evaluate again the positions 1 and 8 plies back, with the cache as it is now
        int rev1_off = ValueNone, rev8_off = ValueNone, rev8_on = ValueNone;
        if (ply >= 1) {
            const std::size_t j = static_cast<std::size_t>((ply - 1) & 7);
            rev1_off = eval_off(ring[j]);
            if (rev1_off != ring_off[j]) fail_hard("re-evaluation one ply back differs (net off)", ring[j]);
        }
        if (ply >= 8) {
            const std::size_t j = static_cast<std::size_t>(ply & 7);
            rev8_off = eval_off(ring[j]);
            rev8_on = eval_on_refresh(ring[j]);
            if (rev8_off != ring_off[j]) fail_hard("re-evaluation eight plies back differs (net off)", ring[j]);
            if (rev8_on != ring_on[j]) fail_hard("re-evaluation eight plies back differs (net on)", ring[j]);
        }

        // the null-move child, as the search reaches it (never from a position in check)
        bool null_block = false, null_has = false;
        MoveList nall;
        std::array<unsigned char, MoveList::Capacity> nbits{};
        std::array<u64, MoveList::Capacity> nchild{};
        if (with_null && ck_main == 0) {
            g_what = "null move child";
            null_block = true;
            NullUndo nu;
            x.make_null_move(nu);
            {
                Board f3 = x;
                null_has = f3.has_legal_move();
            }
            x.generate_pseudo_legal(nall, Board::GenMode::All);
            bool any = false;
            for (std::size_t i = 0; i < nall.size(); ++i) {
                const Move m = nall[i];
                g_move = m;
                if (!x.is_legal(m)) { nbits[i] = 0; nchild[i] = AllOnes; continue; }
                any = true;
                nbits[i] = static_cast<unsigned char>(1 | (x.gives_check(m) ? 2 : 0));
                Undo u;
                (void)x.make_move(m, u);
                nchild[i] = x.checkers();
                const Color them = x.side_to_move();
                if ((x.attackers_to(x.king_square(them)) & x.occupied(opposite(them))) != nchild[i])
                    fail_hard("checkers after a make from the null-move child != attackers of the king", x, m);
                x.unmake_move(m, u);
            }
            g_move = Move::none();
            if (null_has != any) fail_hard("has_legal_move != (legal list not empty) at the null-move child", x);
            x.unmake_null_move(nu);
            if (x.key() != key0 || x.checkers() != ck_main) fail_hard("null unmake did not restore the position", x);
        }

        // ---- the record
        rec.clear();
        rec.w32(playout);
        rec.u16(static_cast<unsigned>(ply));
        rec.u8(0);
        rec.u8(null_block ? 1 : 0);
        rec.w64(x.key());
        rec.w64(x.pawn_key());
        rec.u8(us == White ? 0 : 1);
        rec.u8(x.castling_rights());
        rec.u8(static_cast<unsigned>(x.ep_square() + 1));
        rec.u8(0);
        rec.u16(static_cast<unsigned>(x.halfmove_clock()));
        rec.u16(static_cast<unsigned>(x.fullmove_number()));
        rec.w64(ck_main);
        rec.w64(ck_twin);
        rec.w64(ck_fresh);
        rec.w64(direct);
        rec.u8(has_before ? 1 : 0);
        rec.u8(has_after ? 1 : 0);
        rec.moves(all);
        rec.moves(caps);
        rec.moves(quiets);
        rec.raw(bits.data(), all.size());
        rec.raw(one_bits.data(), all.size());
        rec.raw(post_bits.data(), all.size());
        rec.moves(legal);
        rec.moves(legal_caps);
        rec.raw(child_one.data(), 8 * all.size());
        rec.raw(child_main.data(), 8 * all.size());
        rec.i32(hce);
        rec.i32(off);
        rec.i32(on_refresh);
        rec.i32(on_inc);
        rec.i32(net);
        rec.i32(rev1_off);
        rec.i32(rev8_off);
        rec.i32(rev8_on);
        if (null_block) {
            rec.u8(null_has ? 1 : 0);
            rec.moves(nall);
            rec.raw(nbits.data(), nall.size());
            rec.raw(nchild.data(), 8 * nall.size());
        }
        write_frame(rec);
        ++records;

        const std::size_t j = static_cast<std::size_t>(ply & 7);
        ring[j] = x;
        ring_off[j] = off;
        ring_on[j] = on_refresh;
        g_at = nullptr;
    }
};

void binary_stdout() {
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    static std::vector<char> buffer(1 << 22);
    std::setvbuf(stdout, buffer.data(), _IOFBF, buffer.size());
}

bool read_line(std::string& line) {
    line.clear();
    int c;
    bool any = false;
    while ((c = std::fgetc(stdin)) != EOF) {
        any = true;
        if (c == '\n') break;
        line.push_back(static_cast<char>(c));
    }
    while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
    return any;
}

// "P <playout> <seedtag> <policy> <fen>": returns the FEN and the playout number
bool parse_p(const std::string& line, u32& playout, std::string& fen) {
    std::size_t pos = 1;
    std::size_t field[3];
    for (int k = 0; k < 3; ++k) {
        while (pos < line.size() && line[pos] == ' ') ++pos;
        field[k] = pos;
        while (pos < line.size() && line[pos] != ' ') ++pos;
    }
    while (pos < line.size() && line[pos] == ' ') ++pos;
    if (pos >= line.size()) return false;
    playout = static_cast<u32>(std::strtoull(line.c_str() + field[0], nullptr, 10));
    fen = line.substr(pos);
    return true;
}

std::vector<std::string> tokens_after(const std::string& line, std::size_t pos) {
    std::vector<std::string> t;
    while (pos < line.size()) {
        while (pos < line.size() && line[pos] == ' ') ++pos;
        std::size_t e = pos;
        while (e < line.size() && line[e] != ' ') ++e;
        if (e > pos) t.push_back(line.substr(pos, e - pos));
        pos = e;
    }
    return t;
}

bool find_move(const Board& b, const std::string& text, Move& out) {
    for (const Move m : b.legal_moves())
        if (Board::move_to_uci(m) == text) { out = m; return true; }
    return false;
}

int cmd_run(bool with_null) {
    binary_stdout();
    std::signal(SIGABRT, on_abort);
    auto walker = std::make_unique<Walker>();
    walker->with_null = with_null;
    {
        // identity frame: which probe writes this transcript, and in which mode
        Out& r = walker->rec;
        r.clear();
        r.w32(0xFFFFFFFEU);
        r.u16(0);
        r.u8(253);
        r.u8(with_null ? 1 : 0);
        r.str(MGPROBE_VERSION);
        r.str(MGPROBE_TAG);
        r.str(MGPROBE_HARNESS_SHA256);
        r.str(MGPROBE_TREE_MANIFEST);
        r.str(MGPROBE_DEFS);
        write_frame(r);
    }
    Board x, twin;
    bool active = false;
    u32 playout = 0;
    int ply = 0;
    std::string line;
    while (read_line(line)) {
        if (line.empty() || line[0] == 'H' || line[0] == '#') continue;
        if (line[0] == 'C') {
            walker->worker->clear_caches();
            continue;
        }
        if (line[0] == 'P') {
            std::string fen, error;
            active = false;
            if (!parse_p(line, playout, fen)) die("malformed P line");
            Board nb;
            if (!nb.set_fen(fen, &error)) {
                Out& r = walker->rec;
                r.clear();
                r.w32(playout);
                r.u16(0);
                r.u8(2);
                r.u8(0);
                r.str(error);
                r.str(fen);
                write_frame(r);
                ++walker->records;
                continue;
            }
            x = nb;
            twin = nb;
            ply = 0;
            active = true;
            walker->visit(x, twin, playout, ply);
            continue;
        }
        if (line[0] == 'M') {
            if (!active) continue;
            for (const std::string& text : tokens_after(line, 1)) {
                Move m;
                if (!find_move(x, text, m)) {
                    Out& r = walker->rec;
                    r.clear();
                    r.w32(playout);
                    r.u16(static_cast<unsigned>(ply));
                    r.u8(1);
                    r.u8(0);
                    r.str(text);
                    write_frame(r);
                    ++walker->records;
                    active = false;
                    break;
                }
                walker->before_move(x, m, ply);
                Undo u, u2;
                (void)x.make_move(m, u);
                (void)twin.make_move(m, u2);
                ++ply;
                walker->visit(x, twin, playout, ply);
            }
            continue;
        }
        die("unknown line in the path file");
    }
    Out& r = walker->rec;
    r.clear();
    r.w32(0xFFFFFFFFU);
    r.u16(0);
    r.u8(254);
    r.u8(0);
    r.w64(walker->records);
    r.w64(walker->hard);
    r.w64(walker->soft);
    write_frame(r);
    std::fflush(stdout);
    std::fprintf(stderr, "mgprobe run (%s): %llu records, %llu self-check failures, %llu incremental/refresh differences\n",
                 MGPROBE_TAG, static_cast<unsigned long long>(walker->records), static_cast<unsigned long long>(walker->hard),
                 static_cast<unsigned long long>(walker->soft));
    return 0;
}

int cmd_uciscript(int depth, const char* expect_path) {
    binary_stdout();
    std::FILE* expect = nullptr;
    if (expect_path != nullptr) {
        expect = std::fopen(expect_path, "wb");
        if (expect == nullptr) die("uciscript: cannot write the --expect file");
    }
    auto note = [&](const Board& b) {
        // this probe's legal moves at the position the UCI line reaches, in generation order
        if (expect == nullptr) return;
        bool first = true;
        for (const Move m : b.legal_moves()) {
            if (!first) std::fputc(' ', expect);
            std::fputs(Board::move_to_uci(m).c_str(), expect);
            first = false;
        }
        std::fputc('\n', expect);
    };
    Board x;
    bool active = false;
    std::string line;
    u64 n = 0;
    while (read_line(line)) {
        if (line.empty() || line[0] == 'H' || line[0] == '#' || line[0] == 'C') continue;
        if (line[0] == 'P') {
            u32 playout = 0;
            std::string fen;
            if (!parse_p(line, playout, fen)) die("malformed P line");
            active = x.set_fen(fen);
            if (!active) die("uciscript: seed FEN rejected by this probe");
            std::fprintf(stdout, "position fen %s\ngo perft %d\n", x.fen().c_str(), depth);
            note(x);
            ++n;
            continue;
        }
        if (line[0] == 'M') {
            if (!active) continue;
            for (const std::string& text : tokens_after(line, 1)) {
                Move m;
                if (!find_move(x, text, m)) die("uciscript: path move is not legal for this probe");
                std::fprintf(stdout, "position fen %s moves %s\ngo perft %d\n", x.fen().c_str(), text.c_str(), depth);
                Undo u;
                (void)x.make_move(m, u);
                note(x);
                ++n;
            }
            continue;
        }
        die("unknown line in the path file");
    }
    std::fflush(stdout);
    if (expect != nullptr) std::fclose(expect);
    std::fprintf(stderr, "mgprobe uciscript: %llu positions\n", static_cast<unsigned long long>(n));
    return 0;
}

int cmd_id() {
    // the promotion byte of each promotion piece, read from the engine's own generator
    Board b;
    std::string map;
    if (b.set_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")) {
        for (const Move m : b.legal_moves())
            if (m.is_promotion()) {
                const std::string t = Board::move_to_uci(m);
                if (!map.empty()) map += ",";
                map += "\"" + std::to_string(static_cast<int>(m.promotion)) + "\":\"" + t.substr(4) + "\"";
            }
    }
    std::printf("{\"harness\":\"%s\",\"tag\":\"%s\",\"harness_sha256\":\"%s\",\"tree_manifest_sha256\":\"%s\",\"defines\":\"%s\","
                "\"nnue_available\":%d,\"nnue_residual\":%d,\"nnue_hidden\":%d,"
                "\"sizeof_pawn_entry\":%d,\"sizeof_board\":%d,\"max_ply\":%d,\"promotion_map\":{%s},"
                "\"king_lines\":%d,\"no_zero_movelists\":%d,\"search_speed2\":%d,\"prefetch_early\":%d,"
                "\"tt_notls\":%d,\"nnue_zmm\":%d,\"slider_pext\":%d,"
#ifdef FORGE_SPD_KING_PAWN_CACHE
                "\"king_pawn_cache\":%d,"
#else
                "\"king_pawn_cache\":null,"
#endif
                "\"compiler\":\"%s\"}\n",
                MGPROBE_VERSION, MGPROBE_TAG, MGPROBE_HARNESS_SHA256, MGPROBE_TREE_MANIFEST, MGPROBE_DEFS,
                nnue::available() ? 1 : 0, nnue::residual() ? 1 : 0, nnue::HiddenSize,
                static_cast<int>(sizeof(Evaluator::PawnEntry)), static_cast<int>(sizeof(Board)), MaxPly, map.c_str(),
                FORGE_SPD_KING_LINES, FORGE_SPD_NO_ZERO_MOVELISTS, FORGE_SEARCH_SPEED2, FORGE_SPD_PREFETCH_EARLY,
                FORGE_SPD_TT_NOTLS, FORGE_SPD_NNUE_ZMM, FORGE_SPD_SLIDER_PEXT,
#ifdef FORGE_SPD_KING_PAWN_CACHE
                FORGE_SPD_KING_PAWN_CACHE,
#endif
                __clang_version__);
    return 0;
}

const char* arg_value(int argc, char** argv, const char* name) {
    for (int i = 2; i + 1 < argc; ++i)
        if (std::strcmp(argv[i], name) == 0) return argv[i + 1];
    return nullptr;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: mgprobe id | gen | run | uciscript | keys (see the head of mgprobe.cpp)\n");
        return 1;
    }
    const std::string cmd = argv[1];
    if (cmd == "id") return cmd_id();
    if (cmd == "run") {
        const char* n = arg_value(argc, argv, "--null");
        return cmd_run(n == nullptr || std::atoi(n) != 0);
    }
    if (cmd == "uciscript") {
        const char* d = arg_value(argc, argv, "--perft");
        return cmd_uciscript(d != nullptr ? std::atoi(d) : 1, arg_value(argc, argv, "--expect"));
    }
    if (cmd == "gen") {
        const char* seeds_path = arg_value(argc, argv, "--seeds");
        const char* master = arg_value(argc, argv, "--master");
        const char* chunk = arg_value(argc, argv, "--chunk");
        const char* positions = arg_value(argc, argv, "--positions");
        if (seeds_path == nullptr || master == nullptr || chunk == nullptr || positions == nullptr) die("gen: missing argument");
        Seeds seeds;
        load_seeds(seeds_path, seeds);
        binary_stdout();
        const u64 m = std::strtoull(master, nullptr, 16);
        const u64 c = std::strtoull(chunk, nullptr, 10);
        const u64 n = std::strtoull(positions, nullptr, 10);
        std::fprintf(stdout, "H path-1 master=%016llx chunk=%llu positions=%llu\n",
                     static_cast<unsigned long long>(m), static_cast<unsigned long long>(c),
                     static_cast<unsigned long long>(n));
        Stats st;
        gen_chunk(seeds, m, c, n, stdout, st, nullptr);
        std::fflush(stdout);
        print_stats(stderr, st, "");
        return 0;
    }
    if (cmd == "keys") {
        const char* master = arg_value(argc, argv, "--master");
        const char* positions = arg_value(argc, argv, "--positions");
        if (master == nullptr || positions == nullptr) die("keys: missing argument");
        const u64 m = std::strtoull(master, nullptr, 16);
        const u64 n = std::strtoull(positions, nullptr, 10);
        std::vector<u64> keys;
        Stats st;
        u64 chunks = 0;
        for (int i = 2; i + 1 < argc; ++i) {
            if (std::strcmp(argv[i], "--part") != 0) continue;
            // --part <seeds file>:<first chunk>-<last chunk>   (the split is at the LAST colon: paths have one)
            const std::string part = argv[i + 1];
            const std::size_t colon = part.rfind(':');
            const std::size_t dash = part.rfind('-');
            if (colon == std::string::npos || dash == std::string::npos || dash < colon) die("keys: bad --part");
            Seeds seeds;
            load_seeds(part.substr(0, colon).c_str(), seeds);
            const u64 a = std::strtoull(part.c_str() + colon + 1, nullptr, 10);
            const u64 b = std::strtoull(part.c_str() + dash + 1, nullptr, 10);
            for (u64 c = a; c <= b; ++c) {
                gen_chunk(seeds, m, c, n, nullptr, st, &keys);
                ++chunks;
            }
        }
        std::sort(keys.begin(), keys.end());
        const u64 distinct = static_cast<u64>(std::unique(keys.begin(), keys.end()) - keys.begin());
        char extra[160];
        std::snprintf(extra, sizeof extra, ",\"chunks\":%llu,\"distinct_keys\":%llu,\"repeated\":%llu",
                      static_cast<unsigned long long>(chunks), static_cast<unsigned long long>(distinct),
                      static_cast<unsigned long long>(st.positions - distinct));
        print_stats(stdout, st, extra);
        return 0;
    }
    std::fprintf(stderr, "mgprobe: unknown command %s\n", cmd.c_str());
    return 1;
}
