// Exercise actual correction feedback, table coupling and saturation through the test friendship.
// Second part (corrplus_tests below): the CorrHistPlus keys, indices, update / decay / clamp / blend
// rules and their search glue (forge/correction_plus.hpp, src/search/correction_plus.inc).
#include "forge/search.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static int eval(const Worker& w, const Board& b, int raw) { return w.corrected_eval(b, raw); }
    static void update(Worker& w, const Board& b, int depth, int best, int corrected) {
        w.update_correction(b, depth, best, corrected);
    }
    static CorrectionHistory& pawns(Worker& w) { return *w.correction_history_; }
    static CorrectionHistory& material(Worker& w) { return *w.material_correction_; }
    // CorrHistPlus state.
    static corrplus::Tables* plus(Worker& w) { return w.correction_plus_.get(); }
    static std::size_t& root_history_index(Worker& w) { return w.root_history_index_; }
    static SearchStack& frame(Worker& w, std::size_t index) { return w.stack_[index]; }
};
}
using namespace forge;
using Probe = SearcherTestProbe;
namespace {
int failures = 0, checks = 0;
void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << name << '\n';
}
Board position(const std::string& fen) {
    Board b;
    if (!b.set_fen(fen)) throw std::runtime_error("invalid fixture FEN: " + fen);
    return b;
}
std::size_t pawn_index(const Board& b) { return b.pawn_key() & (CorrectionSize - 1U); }
std::size_t find_material(Worker& w, const Board& b) {
    w.clear();
    tune::MaterialCorrectionWeight = 100;
    Probe::update(w, b, 15, 106, 100);
    const auto side = static_cast<std::size_t>(b.side_to_move());
    std::size_t found = CorrectionSize, count = 0;
    for (std::size_t i = 0; i < CorrectionSize; ++i) {
        if (Probe::material(w)[side][i] != 0) { found = i; ++count; }
    }
    check(count == 1, "actual method writes exactly one material index");
    if (count != 1) throw std::runtime_error("material-slot discovery failed");
    w.clear();
    return found;
}
int& pawn(Worker& w, const Board& b) { return Probe::pawns(w)[b.side_to_move()][pawn_index(b)]; }
int& material(Worker& w, const Board& b, std::size_t index) { return Probe::material(w)[b.side_to_move()][index]; }
void state(const std::string& label, Worker& w, const Board& b, std::size_t mi, int raw, int n) {
    std::cout << "STATE " << label << " iteration=" << n << " pawn=" << pawn(w,b)
              << " material=" << material(w,b,mi) << " corrected=" << Probe::eval(w,b,raw) << '\n';
}
}

// ============================================================================
// CorrHistPlus. Each section prints one PASS/FAIL line with its check count;
// individual checks print only when they fail. References are written out
// independently of forge/correction_plus.hpp (mailbox scans instead of
// bitboards, explicit truncating division, a plain loop over the index space).
// ============================================================================
namespace corrplus_tests {

int printed = 0;
void expect(bool okay, const std::string& name) {
    ++checks;
    if (!okay) {
        ++failures;
        if (++printed <= 40) std::cout << "FAIL " << name << '\n';
    }
}

struct Section {
    std::string name;
    int checks_before = checks;
    int failures_before = failures;
    explicit Section(std::string n) : name(std::move(n)) {}
    ~Section() {
        std::cout << (failures == failures_before ? "PASS " : "FAIL ") << "corrplus " << name
                  << " checks=" << checks - checks_before << '\n';
    }
};

struct Rng {  // SplitMix64: deterministic, platform independent
    std::uint64_t state;
    std::uint64_t next() {
        std::uint64_t z = (state += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31U);
    }
};

long long trunc_div(long long a, long long b) { return a >= 0 ? a / b : -((-a) / b); }
long long clamp_ll(long long v, long long lo, long long hi) { return v < lo ? lo : (v > hi ? hi : v); }

// Piece placement signatures from the mailbox (the keys hash bitboards).
using Signature = std::vector<std::pair<int, int>>;
Signature minor_signature(const Board& b) {
    Signature s;
    for (int sq = 0; sq < 64; ++sq) {
        const Piece p = b.piece_at(sq);
        if (p == WN || p == WB || p == BN || p == BB || p == WK || p == BK) s.emplace_back(p, sq);
    }
    return s;
}
Signature non_pawn_signature(const Board& b, Color c) {
    Signature s;
    for (int sq = 0; sq < 64; ++sq) {
        const Piece p = b.piece_at(sq);
        if (p != Empty && color_of(p) == c && piece_type(p) != Pawn) s.emplace_back(p, sq);
    }
    return s;
}

struct Keys {
    std::uint64_t minor, white, black;
    bool operator==(const Keys&) const = default;
};
Keys keys_of(const Board& b) {
    return {corrplus::minor_piece_key(b), corrplus::non_pawn_key(b, White), corrplus::non_pawn_key(b, Black)};
}

const std::vector<std::string>& walk_fens() {
    static const std::vector<std::string> fens{
        std::string(Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",  // en passant
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",                         // promotions, under-promotions
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",                            // castling
    };
    return fens;
}

// Keys stable under make/unmake and null moves, equal for equal positions
// (transpositions, FEN round trip), and changing exactly when the hashed
// pieces change.
void keys_walk() {
    Section section("keys: make/unmake, null move, FEN round trip, change iff hashed pieces change");
    Rng rng{20261026};
    std::array<int, 3> changed{}, unchanged{};
    for (const std::string& fen : walk_fens()) {
        for (int walk = 0; walk < 4; ++walk) {
            Board b = position(fen);
            for (int ply = 0; ply < 120; ++ply) {
                const MoveList moves = b.legal_moves();
                if (moves.empty()) break;
                const Keys before = keys_of(b);
                const std::string fen_before = b.fen();
                const Signature minor_before = minor_signature(b);
                const Signature white_before = non_pawn_signature(b, White);
                const Signature black_before = non_pawn_signature(b, Black);
                if (!b.in_check()) {
                    NullUndo null_undo;
                    b.make_null_move(null_undo);
                    expect(keys_of(b) == before, "null move leaves the keys unchanged: " + fen_before);
                    b.unmake_null_move(null_undo);
                }
                const Move move = moves[static_cast<std::size_t>(rng.next() % moves.size())];
                Undo undo;
                (void)b.make_move(move, undo);
                const Keys after = keys_of(b);
                const bool minor_same = minor_signature(b) == minor_before;
                const bool white_same = non_pawn_signature(b, White) == white_before;
                const bool black_same = non_pawn_signature(b, Black) == black_before;
                const std::string where = fen_before + " " + Board::move_to_uci(move);
                expect((after.minor == before.minor) == minor_same, "minor key changes iff knights/bishops/kings change: " + where);
                expect((after.white == before.white) == white_same, "white non-pawn key changes iff white N/B/R/Q/K change: " + where);
                expect((after.black == before.black) == black_same, "black non-pawn key changes iff black N/B/R/Q/K change: " + where);
                (minor_same ? unchanged : changed)[0]++;
                (white_same ? unchanged : changed)[1]++;
                (black_same ? unchanged : changed)[2]++;
                expect(keys_of(position(b.fen())) == after, "keys equal after a FEN round trip: " + where);
                expect(corrplus::key_index(after.minor) < CorrectionSize && corrplus::key_index(after.white) < CorrectionSize &&
                           corrplus::key_index(after.black) == (after.black & (CorrectionSize - 1U)),
                       "key_index is the low 14 bits");
                b.unmake_move(move, undo);
                expect(keys_of(b) == before && b.fen() == fen_before, "keys restored by unmake_move: " + where);
                (void)b.make_move(move, undo);
            }
        }
    }
    for (int k = 0; k < 3; ++k) {
        expect(changed[static_cast<std::size_t>(k)] > 100 && unchanged[static_cast<std::size_t>(k)] > 100,
               "walks exercise both outcomes for key " + std::to_string(k));
    }
    // Transposition: the same position reached by two move orders.
    Board x = position(std::string(Board::StandardStartFen));
    Board y = x;
    for (const char* m : {"g1f3", "g8f6", "b1c3", "b8c6"}) { Undo u; (void)x.make_move(*x.parse_uci(m), u); }
    for (const char* m : {"b1c3", "b8c6", "g1f3", "g8f6"}) { Undo u; (void)y.make_move(*y.parse_uci(m), u); }
    expect(keys_of(x) == keys_of(y), "keys equal for a transposition");
    // Colour separation: a white knight move changes only the minor and white keys.
    Board z = position(std::string(Board::StandardStartFen));
    const Keys start = keys_of(z);
    { Undo u; (void)z.make_move(*z.parse_uci("g1f3"), u); }
    const Keys knight = keys_of(z);
    expect(knight.minor != start.minor && knight.white != start.white && knight.black == start.black,
           "Ng1-f3 changes the minor and white keys only");
    { Undo u; (void)z.make_move(*z.parse_uci("e7e5"), u); }
    expect(keys_of(z) == knight, "a pawn move changes none of the keys");
}

// The continuation index is a bijection from (side, our type, to, their type,
// to) onto [0, ContinuationSize) in the documented order.
void continuation_index_bijection() {
    Section section("continuation index: exact value, in range, bijective");
    std::vector<unsigned char> seen(corrplus::ContinuationSize, 0);
    long long mismatches = 0, out_of_range = 0;
    for (int side = 0; side < 2; ++side) {
        for (int ot = 1; ot <= 6; ++ot) {
            for (int oto = 0; oto < 64; ++oto) {
                for (int tt = 1; tt <= 6; ++tt) {
                    for (int tto = 0; tto < 64; ++tto) {
                        const std::size_t index = corrplus::continuation_index(static_cast<Color>(side), ot, oto, tt, tto);
                        const long long reference = (((static_cast<long long>(side) * 6 + (ot - 1)) * 64 + oto) * 6 + (tt - 1)) * 64 + tto;
                        if (static_cast<long long>(index) != reference) ++mismatches;
                        if (index >= corrplus::ContinuationSize) ++out_of_range;
                        else ++seen[index];
                    }
                }
            }
        }
    }
    expect(corrplus::ContinuationSize == 2U * 6U * 64U * 6U * 64U, "ContinuationSize = 294912");
    expect(mismatches == 0, "index equals the reference formula (" + std::to_string(mismatches) + " mismatches)");
    expect(out_of_range == 0, "every index is in range (" + std::to_string(out_of_range) + " out of range)");
    expect(std::all_of(seen.begin(), seen.end(), [](unsigned char c) { return c == 1; }), "every slot is hit exactly once");
    expect(corrplus::continuation_index(White, 1, 0, 1, 0) == 0, "first slot is 0");
    expect(corrplus::continuation_index(Black, 6, 63, 6, 63) == corrplus::ContinuationSize - 1, "last slot is size - 1");
}

// The division helpers equal the C++ operator (rounding toward zero) on a
// range far beyond any value the engine produces (|x| <= 41000 for /256,
// 2^20 for /8192, about 10^7 for /100).
void division_helpers() {
    Section section("division helpers: div_pow2<8>, div_pow2<13>, div100 equal the / operator");
    long long bad8 = 0, bad13 = 0, bad100 = 0;
    for (int x = -(1 << 22); x <= (1 << 22); ++x) {
        if (corrplus::div_pow2<8>(x) != x / 256) ++bad8;
        if (corrplus::div_pow2<13>(x) != x / 8192) ++bad13;
    }
    for (int x = -(1 << 25); x <= (1 << 25); ++x) {
        if (corrplus::div100(x) != x / 100) ++bad100;
    }
    for (const int x : {2147483647, -2147483647 - 1, 2147483600, -2147483600, 2147483599, -2147483599, 1000000000, -1000000001}) {
        if (corrplus::div100(x) != x / 100) ++bad100;
    }
    expect(bad8 == 0, "div_pow2<8>(x) == x / 256 for |x| <= 2^22 (" + std::to_string(bad8) + " mismatches)");
    expect(bad13 == 0, "div_pow2<13>(x) == x / 8192 for |x| <= 2^22 (" + std::to_string(bad13) + " mismatches)");
    expect(bad100 == 0, "div100(x) == x / 100 for |x| <= 2^25 and the int extremes (" + std::to_string(bad100) + " mismatches)");
}

// step / apply (decay and clamp) / blend against independent references.
void update_rules() {
    Section section("update rules: step, decay, clamp, blend (exhaustive entry x step domain)");
    long long step_mismatch = 0;
    for (int depth = -1; depth <= 40; ++depth) {
        for (int delta : {-100000, -1000, -9, -8, -7, -6, -1, 0, 1, 2, 5, 6, 7, 8, 9, 1000, 100000}) {
            const long long residual = clamp_ll(static_cast<long long>(delta) * 256, -2048, 2048);
            const long long reference = trunc_div(residual * std::min(depth + 1, 16), 256);
            if (corrplus::step(100 + delta, 100, depth) != reference) ++step_mismatch;
        }
    }
    expect(step_mismatch == 0, "step = clamp(residual x 256, +-2048) x min(depth+1,16) / 256 (" + std::to_string(step_mismatch) + " mismatches)");
    expect(corrplus::step(106, 100, 15) == 96 && corrplus::step(94, 100, 15) == -96 && corrplus::step(500, 0, 30) == 128 &&
               corrplus::step(103, 100, 0) == 3,
           "step anchors 96 / -96 / 128 / 3");
    long long apply_mismatch = 0, outside = 0;
    for (int entry = -CorrectionLimit; entry <= CorrectionLimit; ++entry) {
        for (int step = -128; step <= 128; ++step) {
            const long long decay = trunc_div(static_cast<long long>(entry) * (step < 0 ? -step : step), 8192);
            const long long reference = clamp_ll(entry + step - decay, -8192, 8192);
            const int got = corrplus::apply(entry, step);
            if (got != reference) ++apply_mismatch;
            if (got < -8192 || got > 8192) ++outside;
        }
    }
    expect(apply_mismatch == 0, "apply = clamp(entry + step - entry x |step| / 8192, +-8192) over the whole domain (" +
                                    std::to_string(apply_mismatch) + " mismatches)");
    expect(outside == 0, "clamp holds: no entry leaves +-8192");
    expect(corrplus::apply(8192, -128) == 7936 && corrplus::apply(7936, 128) == 7940 && corrplus::apply(-8192, 128) == -7936 &&
               corrplus::apply(8191, 128) == 8192 && corrplus::apply(8192, 128) == 8192 && corrplus::apply(8192, 0) == 8192 &&
               corrplus::apply(-8192, -128) == -8192 && corrplus::apply(100, 0) == 100,
           "decay anchors");
    // Decay: alternating +-128 pulls a saturated entry toward 0, monotonically.
    int entry = 8192;
    bool monotone = true;
    for (int pair = 0; pair < 200; ++pair) {
        const int before = entry;
        entry = corrplus::apply(corrplus::apply(entry, -128), 128);
        if (std::abs(entry) > std::abs(before)) monotone = false;
    }
    expect(monotone && std::abs(entry) < 256, "alternating steps decay a saturated entry (" + std::to_string(entry) + ")");
    // Constant step: non-decreasing, reaches the limit exactly and stays there.
    entry = 0;
    bool non_decreasing = true;
    for (int n = 0; n < 4000; ++n) {
        const int next = corrplus::apply(entry, 128);
        if (next < entry) non_decreasing = false;
        entry = next;
    }
    expect(non_decreasing && entry == CorrectionLimit, "constant step converges to exactly +8192");
    // Blend: weighted sum / 100, clamped to +-TotalLimit.
    expect(corrplus::TotalLimit == 16384, "TotalLimit = 2 x CorrectionLimit = 64 cp");
    long long blend_mismatch = 0;
    for (long long sum = -1700000; sum <= 1700000; sum += 37) {
        const long long reference = clamp_ll(trunc_div(sum, 100), -16384, 16384);
        if (corrplus::blend(static_cast<int>(sum)) != reference) ++blend_mismatch;
    }
    for (int sum : {1638400, 1638499, 1638500, -1638400, -1638499, -1638500, 99, -99, 100, -100, 0}) {
        if (corrplus::blend(sum) != clamp_ll(trunc_div(sum, 100), -16384, 16384)) ++blend_mismatch;
    }
    expect(blend_mismatch == 0, "blend = clamp(sum / 100, +-16384) (" + std::to_string(blend_mismatch) + " mismatches)");
    expect(corrplus::blend(1638400) == 16384 && corrplus::blend(-1638400) == -16384 && corrplus::blend(1638399) == 16383,
           "blend reaches the clamp exactly at 16384");
}

long long nonzero(const corrplus::Tables& t) {
    long long n = 0;
    for (const auto& side : t.minor) n += std::count_if(side.begin(), side.end(), [](corrplus::Entry e) { return e != 0; });
    for (const auto& colour : t.non_pawn)
        for (const auto& side : colour) n += std::count_if(side.begin(), side.end(), [](corrplus::Entry e) { return e != 0; });
    n += std::count_if(t.continuation.begin(), t.continuation.end(), [](corrplus::Entry e) { return e != 0; });
    return n;
}
long long nonzero_continuation(const corrplus::Tables& t) {
    return std::count_if(t.continuation.begin(), t.continuation.end(), [](corrplus::Entry e) { return e != 0; });
}

// Frames as Worker::search sets them up: stack_[i].ply = i - 4, no moves.
void reset_frames(Worker& w) {
    for (std::size_t i = 0; i < MaxPly + 8; ++i) {
        SearchStack& ss = Probe::frame(w, i);
        ss.ply = static_cast<int>(i) - 4;
        ss.current_move = Move::none();
        ss.moved_piece = Empty;
    }
}

// The Worker glue: which entries an update touches, what corrected_eval reads.
void worker_glue() {
    Section section("worker glue: OFF untouched, one entry per key, read formula, frame and null-move rules, clamps, clear");
    SharedSearchState shared(1);
    auto owner = std::make_unique<Worker>(shared, 0);
    Worker& w = *owner;
    auto reference_owner = std::make_unique<Worker>(shared, 1);
    Worker& r = *reference_owner;
    const Board b = position("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4");
    const auto side = static_cast<std::size_t>(b.side_to_move());
    const std::size_t minor_slot = corrplus::key_index(corrplus::minor_piece_key(b));
    const std::size_t white_slot = corrplus::key_index(corrplus::non_pawn_key(b, White));
    const std::size_t black_slot = corrplus::key_index(corrplus::non_pawn_key(b, Black));
    options::corr_hist_plus = 0;
    const std::size_t material_slot = find_material(w, b);
    tune::MaterialCorrectionWeight = 100;
    tune::CorrContWeight = tune::CorrMinorWeight = tune::CorrNonPawnWeight = 100;

    // OFF: no tables, the lock path.
    options::corr_hist_plus = 0;
    w.clear();
    Probe::update(w, b, 15, 106, 100);
    expect(Probe::plus(w) == nullptr, "OFF: an update allocates no CorrHistPlus tables");

    // One entry per key, the same step as the pawn table; pawn/material tables as with OFF.
    for (const int bit : {corrplus::MinorPiece, corrplus::NonPawn}) {
        const std::string tag = "bit " + std::to_string(bit) + ": ";
        options::corr_hist_plus = 0;
        r.clear();
        Probe::update(r, b, 15, 106, 100);
        options::corr_hist_plus = static_cast<std::uint8_t>(bit);
        w.clear();
        Probe::update(w, b, 15, 106, 100);
        corrplus::Tables* t = Probe::plus(w);
        expect(t != nullptr, tag + "the first update allocates the tables");
        if (t == nullptr) continue;
        if (bit == corrplus::MinorPiece) {
            expect(t->minor[side][minor_slot] == 96 && nonzero(*t) == 1, tag + "exactly the minor entry learns the step (96)");
        } else {
            expect(t->non_pawn[White][side][white_slot] == 96 && t->non_pawn[Black][side][black_slot] == 96 && nonzero(*t) == 2,
                   tag + "exactly the two non-pawn entries learn the step (96)");
        }
        expect(Probe::pawns(w) == Probe::pawns(r) && Probe::material(w) == Probe::material(r),
               tag + "pawn and material tables updated exactly as with OFF");
        // Read formula with seeded entries and non-trivial weights:
        // corrected = raw + (pawn + material x MW / 100 + blend(sum of entry x weight)) / 256.
        Probe::pawns(w)[side][pawn_index(b)] = 1000;
        Probe::material(w)[side][material_slot] = -600;
        t->minor[side][minor_slot] = 5000;
        t->non_pawn[White][side][white_slot] = -3000;
        t->non_pawn[Black][side][black_slot] = 7000;
        tune::MaterialCorrectionWeight = 33;
        tune::CorrMinorWeight = 70;
        tune::CorrNonPawnWeight = 130;
        const long long weighted = bit == corrplus::MinorPiece ? 5000LL * 70 : (-3000LL + 7000LL) * 130;
        const long long extra = clamp_ll(trunc_div(weighted, 100), -16384, 16384);
        const long long expected = 100 + trunc_div(1000 + trunc_div(-600LL * 33, 100) + extra, 256);
        expect(Probe::eval(w, b, 100) == expected, tag + "corrected_eval = raw + (pawn + material + blend(entries x weights)) / 256");
        tune::MaterialCorrectionWeight = 100;
        tune::CorrMinorWeight = tune::CorrNonPawnWeight = 100;
    }

    // Blend clamp through the Worker: both non-pawn entries saturated, weight 200.
    options::corr_hist_plus = corrplus::NonPawn;
    w.clear();
    Probe::update(w, b, 15, 100, 100);  // zero residual: allocates, learns nothing
    expect(Probe::plus(w) != nullptr && nonzero(*Probe::plus(w)) == 0, "zero residual allocates and learns nothing");
    tune::CorrNonPawnWeight = 200;
    for (const int sign : {1, -1}) {
        Probe::plus(w)->non_pawn[White][side][white_slot] = static_cast<corrplus::Entry>(sign * CorrectionLimit);
        Probe::plus(w)->non_pawn[Black][side][black_slot] = static_cast<corrplus::Entry>(sign * CorrectionLimit);
        expect(Probe::eval(w, b, 100) == 100 + sign * 64, "blend clamp: two saturated tables at weight 200 add exactly 64 cp");
    }
    tune::CorrNonPawnWeight = 100;
    // Entry clamp through the Worker: a constant large residual saturates at exactly +-8192.
    for (const int sign : {1, -1}) {
        w.clear();
        bool inside = true;
        for (int n = 0; n < 3000; ++n) {
            Probe::update(w, b, 15, 100 + sign * 500, 100);
            const int white = Probe::plus(w)->non_pawn[White][side][white_slot];
            if (white < -CorrectionLimit || white > CorrectionLimit) inside = false;
        }
        expect(inside && Probe::plus(w)->non_pawn[White][side][white_slot] == sign * CorrectionLimit &&
                   Probe::plus(w)->non_pawn[Black][side][black_slot] == sign * CorrectionLimit,
               "clamp holds under a constant residual and the limit is reached");
    }
    // clear() drops the tables; the next read sees nothing learned.
    w.clear();
    expect(Probe::plus(w) == nullptr && Probe::eval(w, b, 100) == 100, "clear() frees the tables");

    // Continuation key: the frame is derived from the board history (ply =
    // moves since the root index, frame = stack_[4 + ply]); observed through
    // the entry an update writes.
    options::corr_hist_plus = corrplus::Continuation;
    w.clear();
    Board c = position(std::string(Board::StandardStartFen));
    Probe::root_history_index(w) = c.history_size() - 1;
    reset_frames(w);
    const Move e2e4 = *c.parse_uci("e2e4");
    Probe::frame(w, 4).current_move = e2e4;
    Probe::frame(w, 4).moved_piece = WP;
    { Undo u; (void)c.make_move(e2e4, u); }
    Probe::update(w, c, 15, 106, 100);  // ply 1: the move two plies back is the root sentinel
    expect(Probe::plus(w) != nullptr && nonzero_continuation(*Probe::plus(w)) == 0, "ply 1: no continuation key");
    const Move e7e5 = *c.parse_uci("e7e5");
    Probe::frame(w, 5).current_move = e7e5;
    Probe::frame(w, 5).moved_piece = BP;
    { Undo u; (void)c.make_move(e7e5, u); }
    const std::size_t slot = corrplus::continuation_index(White, Pawn, 28, Pawn, 36);
    w.clear();  // also resets the frames: set them up again
    reset_frames(w);
    Probe::frame(w, 4).current_move = e2e4;
    Probe::frame(w, 4).moved_piece = WP;
    Probe::frame(w, 5).current_move = e7e5;
    Probe::frame(w, 5).moved_piece = BP;
    Probe::update(w, c, 15, 106, 100);  // ply 2: (White, our pawn to e4, their pawn to e5)
    expect(Probe::plus(w) != nullptr && Probe::plus(w)->continuation[slot] == 96 && nonzero(*Probe::plus(w)) == 1,
           "ply 2: exactly the (White, P-e4, P-e5) continuation entry learns the step");
    Probe::plus(w)->continuation[slot] = 2560;
    // pawn + material part of c's correction (MaterialCorrectionWeight 100), from the current tables.
    auto base_c = [&] {
        long long material_sum = 0;
        for (std::size_t i = 0; i < CorrectionSize; ++i) material_sum += Probe::material(w)[0][i];
        return Probe::pawns(w)[0][c.pawn_key() & (CorrectionSize - 1U)] + material_sum;
    };
    tune::CorrContWeight = 50;
    expect(Probe::eval(w, c, 100) == 100 + trunc_div(base_c() + 1280, 256), "continuation entry read with its weight");
    tune::CorrContWeight = 100;
    // A frame whose ply does not match is rejected (no read, no write).
    Probe::frame(w, 6).ply = 99;
    expect(Probe::eval(w, c, 100) == 100 + trunc_div(base_c(), 256), "frame with a wrong ply: entry not read");
    Probe::update(w, c, 15, 106, 100);
    expect(Probe::plus(w)->continuation[slot] == 2560, "frame with a wrong ply: entry not written");
    Probe::frame(w, 6).ply = 2;
    expect(Probe::eval(w, c, 100) == 100 + trunc_div(base_c() + 2560, 256), "frame restored: entry read again");
    // A null move in between gives no key.
    Probe::frame(w, 5).current_move = Move::none();
    Probe::frame(w, 5).moved_piece = Empty;
    Probe::update(w, c, 15, 106, 100);
    expect(Probe::plus(w)->continuation[slot] == 2560 && nonzero_continuation(*Probe::plus(w)) == 1,
           "null move: the update touches no continuation entry");
    // Colours must alternate (guards against a mis-derived frame).
    Probe::frame(w, 5).current_move = e7e5;
    Probe::frame(w, 5).moved_piece = WP;
    Probe::update(w, c, 15, 106, 100);
    expect(Probe::plus(w)->continuation[slot] == 2560 && nonzero_continuation(*Probe::plus(w)) == 1,
           "same-colour pair: no key");
    Probe::frame(w, 5).moved_piece = BP;
    // Outside a search (board history before the root index): no frame.
    Probe::root_history_index(w) = c.history_size() + 3;
    Probe::update(w, c, 15, 106, 100);
    expect(Probe::plus(w)->continuation[slot] == 2560, "board history before the root: no frame");
    Probe::root_history_index(w) = c.history_size() - 1 - 2;
    Probe::update(w, c, 15, 106, 100);
    expect(Probe::plus(w)->continuation[slot] == corrplus::apply(2560, 96), "frame restored: the entry learns again");
    Probe::root_history_index(w) = 0;

    // Twins: with every key on and all weights 0, the cold twins reproduce
    // the lock's pawn/material updates and corrected evaluation exactly.
    tune::CorrContWeight = tune::CorrMinorWeight = tune::CorrNonPawnWeight = 0;
    Rng rng{77};
    std::vector<Board> boards;
    for (const std::string& fen : walk_fens()) boards.push_back(position(fen));
    for (const int mw : {100, 33, 0}) {
        tune::MaterialCorrectionWeight = mw;
        options::corr_hist_plus = 0;
        r.clear();
        options::corr_hist_plus = corrplus::AllKeys;
        w.clear();
        bool same_eval = true;
        for (int n = 0; n < 3000; ++n) {
            const Board& x = boards[static_cast<std::size_t>(rng.next() % boards.size())];
            const int depth = static_cast<int>(rng.next() % 24) - 2;
            const int stat = static_cast<int>(rng.next() % 801) - 400;
            const int best = stat + static_cast<int>(rng.next() % 61) - 30;
            options::corr_hist_plus = 0;
            Probe::update(r, x, depth, best, stat);
            const int ref_eval = Probe::eval(r, x, stat);
            options::corr_hist_plus = corrplus::AllKeys;
            Probe::update(w, x, depth, best, stat);
            if (Probe::eval(w, x, stat) != ref_eval) same_eval = false;
        }
        expect(Probe::pawns(w) == Probe::pawns(r) && Probe::material(w) == Probe::material(r),
               "twin update = lock update (MaterialCorrectionWeight " + std::to_string(mw) + ")");
        expect(same_eval, "twin corrected_eval = lock corrected_eval at weight 0 (MaterialCorrectionWeight " + std::to_string(mw) + ")");
    }
    tune::MaterialCorrectionWeight = 100;
    tune::CorrContWeight = tune::CorrMinorWeight = tune::CorrNonPawnWeight = 100;
    options::corr_hist_plus = 0;
}

// Real searches: deterministic, different from OFF, the continuation frames
// are found during search.
void search_smoke() {
    Section section("search: Threads 1 determinism, ON differs from OFF, tables filled during search");
    const std::vector<std::string> fens{std::string(Board::StandardStartFen),
                                        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"};
    std::array<std::uint64_t, 8> totals{};
    for (const int bits : {0, 1, 2, 4, 7}) {
        options::corr_hist_plus = static_cast<std::uint8_t>(bits);
        std::array<std::uint64_t, 2> runs{};
        for (std::size_t run = 0; run < 2; ++run) {
            Searcher searcher(16, 1);
            for (const std::string& fen : fens) {
                SearchLimits limits;
                limits.depth = 9;
                searcher.clear();
                const SearchInfo info = searcher.search(position(fen), limits);
                runs[run] += info.nodes;
                if (bits == corrplus::Continuation && run == 0 && fen == fens.front()) {
                    const corrplus::Tables* t = Probe::plus(searcher.main_worker());
                    expect(t != nullptr && nonzero_continuation(*t) > 200,
                           "continuation entries learned during a real search (" +
                               std::to_string(t ? nonzero_continuation(*t) : 0) + ")");
                }
            }
        }
        expect(runs[0] == runs[1], "bits " + std::to_string(bits) + ": two runs give the same nodes");
        totals[static_cast<std::size_t>(bits)] = runs[0];
        std::cout << "INFO corrplus search bits=" << bits << " nodes(depth 9, 2 positions)=" << runs[0] << '\n';
    }
    for (const int bits : {1, 2, 4, 7}) {
        expect(totals[static_cast<std::size_t>(bits)] != totals[0], "bits " + std::to_string(bits) + ": nodes differ from OFF");
    }
    options::corr_hist_plus = 0;
}

void run_all() {
    keys_walk();
    continuation_index_bijection();
    division_helpers();
    update_rules();
    worker_glue();
    search_smoke();
}

} // namespace corrplus_tests
int main() {
    std::cout << "Correction-history residual increment contract\n";
    const auto a = position("4k3/8/8/8/8/8/P7/4K3 w - - 0 1");
    const auto b = position("4k3/8/8/8/8/8/1P6/4K3 w - - 0 1");
    const auto opposite = position("4k3/8/8/8/8/8/P7/4K3 b - - 0 1");
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    auto& w = *worker;
    const auto mi = find_material(w,a), mbi = find_material(w,b);
    check(mi == mbi && pawn_index(a) != pawn_index(b), "fixtures share actual material index and have distinct pawn indices");
    std::cout << "FIXTURE a=" << a.fen() << " pawn_index=" << pawn_index(a) << " material_index=" << mi << '\n';
    std::cout << "FIXTURE b=" << b.fen() << " pawn_index=" << pawn_index(b) << " material_index=" << mbi << '\n';
    for (const auto [depth, expected] : std::array<std::pair<int,int>,4>{{{0,6},{14,90},{15,96},{100,96}}}) {
        for (int sign : {-1,1}) {
            w.clear(); tune::MaterialCorrectionWeight = 0;
            Probe::update(w,a,depth,100+sign*6,100);
            check(pawn(w,a) == sign*expected && material(w,a,mi) == 0,
                  "signed depth weight depth=" + std::to_string(depth) + " sign=" + std::to_string(sign));
        }
    }
    for (int sign : {-1,1}) {
        w.clear(); tune::MaterialCorrectionWeight = 100;
        Probe::update(w,a,15,100+sign*100,100);
        check(pawn(w,a) == sign*128 && material(w,a,mi) == sign*128, "diff clips at signed eight cp");
        check(Probe::eval(w,a,100) == 100+sign, "two fixed-point tables combine before division");
        w.clear(); tune::MaterialCorrectionWeight = 0;
        pawn(w,a) = sign*512;
        const int corrected = Probe::eval(w,a,100);
        Probe::update(w,a,15,corrected,corrected);
        check(pawn(w,a) == sign*512, "zero-residual update retains learned feedback");
        pawn(w,a) = sign;
        Probe::update(w,a,15,100,100);
        check(pawn(w,a) == sign, "signed truncation on subgrain seeded entry");
        w.clear(); pawn(w,a) = sign*CorrectionLimit;
        Probe::update(w,a,15,100+sign*100,100);
        check(pawn(w,a) == sign*8192, "seeded endpoint with outward residual");
        state("endpoint",w,a,mi,100,1);
        w.clear(); tune::MaterialCorrectionWeight = 33;
        material(w,a,mi) = sign*777;
        check(Probe::eval(w,a,100) == 100+sign, "signed material coefficient33 rounds before grain division");
        material(w,a,mi) = sign*775;
        check(Probe::eval(w,a,100) == 100, "signed subgrain material correction truncates toward zero");
        Probe::update(w,a,15,106,100);
        check(pawn(w,a) == 96 && material(w,a,mi) == sign*775+96,
              "material coefficient affects read scale but not update gain");
        for (int mw : {0,100}) {
            w.clear(); tune::MaterialCorrectionWeight = mw;
            const std::string label = "delta" + std::to_string(sign*6) + "_material" + std::to_string(mw);
            for (int n = 1; n <= 4096; ++n) {
                Probe::update(w,a,15,100+sign*6,Probe::eval(w,a,100));
                if (n==1 || n==16 || n==64 || n==256 || n==4096) state(label,w,a,mi,100,n);
            }
            const int expected_entry = mw==0 ? 1536 : 768;
            const int expected_cp = 6;
            check(pawn(w,a) == sign*expected_entry && Probe::eval(w,a,100) == 100+sign*expected_cp,
                  "fixed delta6 convergence " + label);
            check(material(w,a,mi) == (mw==0 ? 0 : pawn(w,a)), "one-table isolation or equal two-table entries");
            check(Probe::eval(w,opposite,100) == 100, "opposite-side table remains untouched");
            check(Probe::eval(w,b,100) == 100 + (mw==0 ? 0 : material(w,a,mi)/CorrectionGrain),
                  "shared material transfers correction to distinct pawn structure");
            const int before_material = material(w,a,mi), before_pawn_a = pawn(w,a);
            Probe::update(w,b,15,100-sign*6,Probe::eval(w,b,100));
            check(pawn(w,a) == before_pawn_a && (mw==0 ? material(w,a,mi) == before_material : material(w,a,mi) != before_material),
                  mw==0 ? "disabled material control" : "other pawn structure changes shared material entry");
            state(label+"_after_conflict",w,a,mi,100,4097);
            w.clear(); tune::MaterialCorrectionWeight = mw;
            for (int n=1; n<=4096; ++n) Probe::update(w,a,15,100+sign*100,Probe::eval(w,a,100));
            state("large_residual_material"+std::to_string(mw),w,a,mi,100,4096);
            check(std::abs(pawn(w,a)) == CorrectionLimit, "reachable range under constant clipped residual");
        }
    }
    w.clear(); tune::MaterialCorrectionWeight = 100;
    pawn(w,a)=1024; material(w,a,mi)=-512;
    Probe::update(w,a,15,106,Probe::eval(w,a,100));
    check(pawn(w,a)==1088 && material(w,a,mi)==-448,
          "unequal tables consume same precomputed joint residual");
    state("unequal_tables",w,a,mi,100,1);
    w.clear(); pawn(w,a)=CorrectionLimit; material(w,a,mi)=CorrectionLimit;
    check(Probe::eval(w,a,MateInMaxPly-2)==MateInMaxPly-1, "upper output mate boundary clamps");
    pawn(w,a)=-CorrectionLimit; material(w,a,mi)=-CorrectionLimit;
    check(Probe::eval(w,a,-MateInMaxPly+2)==-MateInMaxPly+1, "lower output mate boundary clamps");
    tune::MaterialCorrectionWeight=100;
    std::cout << "CorrHistPlus (extra correction keys)\n";
    corrplus_tests::run_all();
    std::cout << "SUMMARY checks=" << checks << " failures=" << failures << '\n';
    return failures==0 ? 0 : 1;
}
