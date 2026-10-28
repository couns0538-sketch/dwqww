// UCI HistRework (Astra A1): lesser-attacker threat maps, the history blend, the joint-correction key and its
// gravity update, the Worker glue at the overflow bounds of every table, and whole searches with the option at
// its maximum and the related tunables at their UCI maxima (run under ASan+UBSan on CI).
// Reference values are computed independently here (ray-walking attacks, int64 arithmetic).
#include "forge/board.hpp"
#include "forge/hist_rework.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static ButterflyHistory& main(Worker& w) { return *w.histories_.main_history; }
    static LesserThreatHistory& threat(Worker& w) { return *w.threat_history_; }
    static ContinuationHistory& cont(Worker& w) { return *w.histories_.continuation_history; }
    static CorrectionHistory& pawns(Worker& w) { return *w.correction_history_; }
    static CorrectionHistory& material(Worker& w) { return *w.material_correction_; }
    static CorrectionHistory& joint(Worker& w) { return *w.joint_correction_; }
    static hist_rework::LesserThreats& maps(Worker& w, int ply) { return w.threat_maps_[static_cast<std::size_t>(ply)]; }
    static SearchStack* frame(Worker& w, int ply) {
        SearchStack* ss = &w.stack_[static_cast<std::size_t>(4 + ply)];
        ss->ply = ply;
        return ss;
    }
    static int quiet(const Worker& w, const Board& b, const SearchStack* ss, Move m) { return w.quiet_history(b, ss, m); }
    static int eval(const Worker& w, const Board& b, int raw) { return w.corrected_eval(b, raw); }
    static void update_corr(Worker& w, const Board& b, int depth, int best, int corrected) {
        w.update_correction(b, depth, best, corrected);
    }
    static void update_quiets(Worker& w, const Board& b, SearchStack* ss, Move best, int depth, const Move* quiets, int n) {
        w.update_quiet_stats(b, ss, best, depth, quiets, n);
    }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;

namespace {
int failures = 0;
long long checks = 0;

void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) {
        ++failures;
        std::cout << "FAIL " << name << '\n';
    }
}
// A check that reaches an overflow bound: printed on success too, so the log shows the bound being hit.
void bound(bool okay, const std::string& name) {
    check(okay, name);
    if (okay) std::cout << "PASS BOUND " << name << '\n';
}
// One summary line per section; individual failures are printed by check().
void section(const std::string& name, long long first_check, int first_failure) {
    std::cout << (failures == first_failure ? "PASS " : "FAIL ") << name << " checks=" << (checks - first_check) << '\n';
}

Board position(const std::string& fen) {
    Board b;
    if (!b.set_fen(fen)) throw std::runtime_error("invalid fixture FEN: " + fen);
    return b;
}

int square(const char* name) { return (name[1] - '1') * 8 + (name[0] - 'a'); }

Move find_move(const Board& b, const char* from, const char* to) {
    const MoveList legal = b.legal_moves();
    for (const Move m : legal) {
        if (m.from == square(from) && m.to == square(to) && !m.is_promotion()) return m;
    }
    throw std::runtime_error(std::string("fixture move not legal: ") + from + to);
}

// ---------------------------------------------------------------- independent attack reference
Bitboard ref_attacks(int type, Color color, int sq, Bitboard occupancy) {
    const int r = sq / 8, f = sq % 8;
    Bitboard out = 0;
    auto add = [&](int rr, int ff) {
        if (rr >= 0 && rr < 8 && ff >= 0 && ff < 8) out |= 1ULL << (rr * 8 + ff);
    };
    auto ray = [&](int dr, int df) {
        for (int rr = r + dr, ff = f + df; rr >= 0 && rr < 8 && ff >= 0 && ff < 8; rr += dr, ff += df) {
            out |= 1ULL << (rr * 8 + ff);
            if ((occupancy >> (rr * 8 + ff)) & 1ULL) break;
        }
    };
    switch (type) {
    case Pawn: {
        const int dir = color == White ? 1 : -1;
        add(r + dir, f - 1);
        add(r + dir, f + 1);
        break;
    }
    case Knight:
        for (const auto& d : std::array<std::array<int, 2>, 8>{{{1, 2}, {2, 1}, {-1, 2}, {-2, 1}, {1, -2}, {2, -1}, {-1, -2}, {-2, -1}}})
            add(r + d[0], f + d[1]);
        break;
    case Bishop:
        ray(1, 1); ray(1, -1); ray(-1, 1); ray(-1, -1);
        break;
    case Rook:
        ray(1, 0); ray(-1, 0); ray(0, 1); ray(0, -1);
        break;
    default:
        break;
    }
    return out;
}

struct RefThreats { Bitboard by_pawn = 0, by_minor = 0, by_rook = 0; };

RefThreats ref_threats(const Board& b) {
    const Color them = opposite(b.side_to_move());
    RefThreats t;
    for (int sq = 0; sq < 64; ++sq) {
        for (int type : {Pawn, Knight, Bishop, Rook}) {
            if (!((b.pieces(them, static_cast<PieceType>(type)) >> sq) & 1ULL)) continue;
            const Bitboard a = ref_attacks(type, them, sq, b.occupied());
            if (type == Pawn) t.by_pawn |= a;
            if (type <= Bishop) t.by_minor |= a;
            t.by_rook |= a;
        }
    }
    return t;
}

bool maps_match(const Board& b) {
    const hist_rework::LesserThreats got = hist_rework::lesser_threats(b);
    const RefThreats ref = ref_threats(b);
    return got.by_type[0] == 0 && got.by_type[Pawn] == ref.by_pawn && got.by_type[Knight] == ref.by_pawn &&
           got.by_type[Bishop] == ref.by_pawn && got.by_type[Rook] == ref.by_minor && got.by_type[Queen] == ref.by_rook &&
           got.by_type[King] == 0;
}

// ---------------------------------------------------------------- arithmetic references (int64)
long long ref_blend(long long plain, long long threat, long long quarters) {
    return (plain * (4 - quarters) + threat * quarters) / 4; // int64 division truncates toward zero, as int does
}
long long ref_gravity_unclamped(long long entry, long long step, long long limit) {
    return entry + step - entry * (step < 0 ? -step : step) / limit;
}
// The lock's apply_history (search.cpp), re-derived from its source text.
int ref_apply_history(int entry, int bonus) {
    const long long clamped = std::clamp(bonus, -16384, 16384);
    return static_cast<int>(entry + clamped - static_cast<long long>(entry) * (clamped < 0 ? -clamped : clamped) / 16384);
}

const std::vector<std::string> Fens = {
    std::string(Board::StandardStartFen),
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
};

// ---------------------------------------------------------------- sections
void test_levels() {
    const long long c0 = checks; const int f0 = failures;
    check(hist_rework::threat_quarters(1) == 2 && hist_rework::threat_quarters(2) == 3 && hist_rework::threat_quarters(3) == 4,
          "levels 1..3 read 2/3/4 quarters of the threat-keyed twin");
    check(hist_rework::joint_weight(1) == 50 && hist_rework::joint_weight(2) == 75 && hist_rework::joint_weight(3) == 100,
          "levels 1..3 weigh the joint correction 50/75/100");
    for (int level = -5; level <= 9; ++level) {
        const int q = hist_rework::threat_quarters(level), w = hist_rework::joint_weight(level);
        check(q >= 2 && q <= 4 && w >= 50 && w <= 100, "out-of-range level is clamped " + std::to_string(level));
    }
    check(search_options::hist_rework == 0, "the option defaults to 0 (lock)");
    section("hist_rework levels: quarters, weights, clamp, default 0", c0, f0);
}

void test_threat_maps() {
    const long long c0 = checks; const int f0 = failures;
    std::mt19937 rng(20261027U);
    long long positions = 0;
    for (const std::string& fen : Fens) {
        Board b = position(fen);
        check(maps_match(b), "lesser-attacker maps equal the ray-walking reference: " + fen);
        for (int walk = 0; walk < 12; ++walk) {
            Board w = position(fen);
            for (int ply = 0; ply < 80; ++ply) {
                const MoveList legal = w.legal_moves();
                if (legal.empty()) break;
                const Move m = *(legal.begin() + static_cast<std::ptrdiff_t>(rng() % legal.size()));
                Undo undo;
                (void)w.make_move(m, undo);
                ++positions;
                if (!maps_match(w)) {
                    check(false, "random walk maps mismatch at " + w.fen());
                    break;
                }
                ++checks;
            }
        }
    }
    // Hand-checked fixture: which pieces count as "lesser" for each mover.
    // White to move. Black: pawns d5 h6, knight b4, bishop c7, rook f8 (f-file open).
    const Board b = position("5rk1/2b5/7p/3p4/1n2N3/8/8/R2QK2B w - - 0 1");
    const hist_rework::LesserThreats t = hist_rework::lesser_threats(b);
    auto bit = [&](int type, const char* sq) { return hist_rework::square_bit(t.by_type[static_cast<std::size_t>(type)], square(sq)); };
    check(bit(Knight, "e4") == 1, "knight on e4 attacked by the d5 pawn (from bit)");
    check(bit(Knight, "g5") == 1 && bit(Knight, "c3") == 0, "knight to g5 meets the h6 pawn, c3 is safe from pawns");
    check(bit(Knight, "d3") == 0, "a knight attack (b4 -> d3) is not lesser for a knight");
    check(bit(Rook, "a5") == 1, "rook to a5 meets the c7 bishop (minor is lesser than rook)");
    check(bit(Rook, "d3") == 1 && bit(Rook, "c2") == 1, "rook squares attacked by the b4 knight");
    check(bit(Bishop, "f3") == 0 && bit(Rook, "f3") == 0, "f3 attacked only by the f8 rook: not lesser for bishop or rook");
    check(bit(Queen, "f3") == 1 && bit(Queen, "a5") == 1, "queen squares attacked by a rook or a minor");
    check(t.by_type[King] == 0 && t.by_type[0] == 0, "king and no-piece entries are empty");
    std::cout << "INFO threat-map positions checked: " << positions << '\n';
    section("lesser-attacker maps: reference over fixtures + random walks, hand-checked fixture", c0, f0);
}

void test_blend() {
    const long long c0 = checks; const int f0 = failures;
    std::vector<int> values = {-16384, -16383, -16382, -8193, -8192, -4097, -2, -1, 0, 1, 2, 4097, 8191, 8192, 16382, 16383, 16384};
    for (int v = -16384; v <= 16384; v += 97) values.push_back(v);
    long long local = 0;
    bool all_ok = true;
    int max_abs = 0;
    for (int q = 0; q <= 4; ++q) {
        for (const int p : values) {
            for (const int t : values) {
                const int got = hist_rework::blend(p, t, q);
                const long long ref = ref_blend(p, t, q);
                max_abs = std::max(max_abs, std::abs(got));
                if (got != ref || std::abs(got) > hist_rework::HistoryLimit) all_ok = false;
                ++local;
            }
        }
    }
    check(all_ok, "blend equals the int64 reference and stays within +-16384");
    checks += local - 1;
    bound(max_abs == hist_rework::HistoryLimit, "blend: max |result| over the grid = 16384 = HistoryLimit (int numerator <= 65536)");
    for (int q = 0; q <= 4; ++q) {
        check(hist_rework::blend(16384, 16384, q) == 16384 && hist_rework::blend(-16384, -16384, q) == -16384,
              "blend of two saturated entries is saturated, quarters " + std::to_string(q));
    }
    check(hist_rework::blend(1234, -777, 0) == 1234 && hist_rework::blend(1234, -777, 4) == -777, "quarters 0/4 select one table");
    section("blend: exhaustive grid incl. +-16384, quarters 0..4", c0, f0);
}

void test_gravity() {
    const long long c0 = checks; const int f0 = failures;
    const int L = hist_rework::CorrectionEntryLimit;
    // Reachable domain: |entry| <= 8192, |step| <= 2048 * 16 / 256 = 128 (update_correction).
    bool reach_ok = true;
    long long local = 0;
    for (int e = -L; e <= L; ++e) {
        for (int s = -128; s <= 128; ++s) {
            const long long ref = ref_gravity_unclamped(e, s, L);
            const std::int32_t got = hist_rework::gravity(e, s, L);
            if (got != ref || ref < -L || ref > L) reach_ok = false;
            ++local;
        }
    }
    check(reach_ok, "gravity on the reachable domain equals the unclamped formula (guard never active), |result| <= 8192");
    checks += local - 1;
    // Proof domain: |step| <= limit.
    bool proof_ok = true;
    std::vector<int> steps = {-L, -L + 1, -4097, -4096, -129, 129, 4096, 4097, L - 1, L};
    for (int s = -L; s <= L; s += 61) steps.push_back(s);
    local = 0;
    for (int e = -L; e <= L; ++e) {
        for (const int s : steps) {
            const long long ref = ref_gravity_unclamped(e, s, L);
            if (ref < -L || ref > L || hist_rework::gravity(e, s, L) != ref) proof_ok = false;
            ++local;
        }
    }
    check(proof_ok, "|entry|,|step| <= limit keeps the unclamped result within +-limit (proof domain grid)");
    checks += local - 1;
    // Saturation: repeated maximal steps reach the bound exactly and stay there.
    for (const int s : {128, -128}) {
        std::int32_t e = 0;
        int steps_taken = 0;
        bool within = true;
        while (std::abs(e) < L && steps_taken < 20000) {
            e = hist_rework::gravity(e, s, L);
            within = within && std::abs(e) <= L;
            ++steps_taken;
        }
        const std::int32_t again = hist_rework::gravity(e, s, L);
        bound(within && e == (s > 0 ? L : -L) && again == e,
              "constant step " + std::to_string(s) + " saturates at exactly " + std::to_string(s > 0 ? L : -L) +
                  " after " + std::to_string(steps_taken) + " updates");
    }
    section("gravity: reachable domain exhaustive, proof domain grid, exact saturation", c0, f0);
}

void test_joint_key() {
    const long long c0 = checks; const int f0 = failures;
    const Board start = position(std::string(Board::StandardStartFen));
    check(hist_rework::non_pawn_material(start) == 0x22212221U, "startpos signature: W N2 B2 R2 Q1, B N2 B2 R2 Q1");
    check(hist_rework::joint_key(start) == (start.pawn_key() ^ hist_rework::mix64(0x22212222ULL)), "joint key formula");
    // Same pawn structure, different non-pawn material: distinct indices (and distinct from the pawn index).
    const std::vector<std::string> variants = {
        std::string(Board::StandardStartFen),
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R1BQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RN1QKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
        "r1bqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    };
    std::set<std::uint64_t> indices;
    for (const std::string& fen : variants) {
        const Board b = position(fen);
        check(b.pawn_key() == start.pawn_key(), "variant keeps the pawn structure: " + fen);
        indices.insert(hist_rework::joint_key(b) & (CorrectionSize - 1U));
    }
    check(indices.size() == variants.size(), "six material variants of one pawn structure use six joint slots");
    // Make/unmake and null move: the key depends only on pawn placement and non-pawn counts.
    std::mt19937 rng(7U);
    bool stable = true, quiet_piece_keeps = true, changes_ok = true;
    for (const std::string& fen : Fens) {
        Board b = position(fen);
        for (int ply = 0; ply < 60; ++ply) {
            const MoveList legal = b.legal_moves();
            if (legal.empty()) break;
            const Move m = *(legal.begin() + static_cast<std::ptrdiff_t>(rng() % legal.size()));
            const std::uint64_t before = hist_rework::joint_key(b);
            const std::uint32_t sig_before = hist_rework::non_pawn_material(b);
            const std::uint64_t pawn_before = b.pawn_key();
            const int mover = piece_type(b.moved_piece(m));
            Undo undo;
            (void)b.make_move(m, undo);
            const std::uint64_t after = hist_rework::joint_key(b);
            const bool same_inputs = b.pawn_key() == pawn_before && hist_rework::non_pawn_material(b) == sig_before;
            if (same_inputs != (after == before)) changes_ok = false;
            if (mover != Pawn && !m.is_capture() && !m.is_promotion() && after != before) quiet_piece_keeps = false;
            b.unmake_move(m, undo);
            if (hist_rework::joint_key(b) != before) stable = false;
            (void)b.make_move(m, undo);
            ++checks;
        }
        if (!b.in_check()) {
            const std::uint64_t before = hist_rework::joint_key(b);
            NullUndo nu;
            b.make_null_move(nu);
            if (hist_rework::joint_key(b) != before) stable = false;
            b.unmake_null_move(nu);
        }
    }
    check(stable, "joint key restored by unmake and unchanged by a null move");
    check(quiet_piece_keeps, "a quiet non-pawn move keeps the joint key");
    check(changes_ok, "the key changes exactly when the pawn key or the non-pawn signature changes (random walks)");
    section("joint key: signature, formula, distinct slots, make/unmake/null stability", c0, f0);
}

void test_glue_off() {
    const long long c0 = checks; const int f0 = failures;
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    search_options::hist_rework = 0;
    tune::MaterialCorrectionWeight = 100;
    const Board b = position(Fens[2]);
    SearchStack* ss = Probe::frame(w, 3);
    Probe::maps(w, 3) = hist_rework::lesser_threats(b);
    const Move best = find_move(b, "f3", "g5");
    const Move other = find_move(b, "a2", "a3");
    const std::array<Move, 2> quiets{other, best};
    Probe::update_quiets(w, b, ss, best, 9, quiets.data(), 2);
    Probe::update_corr(w, b, 12, 140, 100);
    bool joint_zero = true, threat_zero = true;
    for (const auto& side : Probe::joint(w)) for (const std::int32_t e : side) joint_zero = joint_zero && e == 0;
    for (const auto& a : Probe::threat(w)) for (const auto& bb : a) for (const auto& c : bb) for (const auto& d : c) for (const std::int16_t e : d)
        threat_zero = threat_zero && e == 0;
    check(joint_zero && threat_zero, "option 0: the joint and threat tables are never written");
    const int main_entry = Probe::main(w)[White][best.from][best.to];
    check(Probe::quiet(w, b, ss, best) == main_entry, "option 0: quiet_history is the lock term (main + continuations)");
    // The lock correction rule: diff = clamp(40 * 256, +-2048) = 2048, weight 13: step 2048 * 13 / 256 = 104.
    check(Probe::pawns(w)[White][b.pawn_key() & (CorrectionSize - 1U)] == 104, "option 0: pawn correction follows the lock rule");
    check(Probe::eval(w, b, 50) == 50 + (104 + 104) / 256, "option 0: corrected eval = raw + (pawn + material) / 256");
    section("glue, option 0: new tables untouched, lock read/update rules", c0, f0);
}

void test_glue_history_bounds() {
    const long long c0 = checks; const int f0 = failures;
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    const int saved_max = tune::HistoryBonusMax, saved_q = tune::HistoryBonusQuadratic, saved_l = tune::HistoryBonusLinear;
    // Tunables at their UCI maxima: history_bonus(depth >= 10) = min(10000, 100 d^2 + 500 d - 32) = 10000.
    tune::HistoryBonusMax = 10000;
    tune::HistoryBonusQuadratic = 100;
    tune::HistoryBonusLinear = 500;
    // White knight e4 attacked by the d5 pawn; Ne4-c3 is safe, Ne4-g5 walks into the h6 pawn.
    const Board b = position("5rk1/2b5/7p/3p4/1n2N3/8/8/R2QK2B w - - 0 1");
    const Move best = find_move(b, "e4", "c3");
    const Move other = find_move(b, "e4", "g5");
    const std::array<Move, 2> quiets{other, best};
    for (int level = 1; level <= 3; ++level) {
        w.clear();
        search_options::hist_rework = level;
        SearchStack* ss = Probe::frame(w, 5);
        Probe::maps(w, 5) = hist_rework::lesser_threats(b);
        auto& t = Probe::threat(w);
        int expect_best = 0, expect_other = 0, steps = 0;
        bool exact = true, bounded = true;
        while ((expect_best != 16384 || expect_other != -16384) && steps < 64) {
            Probe::update_quiets(w, b, ss, best, 20, quiets.data(), 2);
            expect_best = ref_apply_history(expect_best, 10000);
            expect_other = ref_apply_history(expect_other, -10000);
            const int got_best = t[White][1][0][best.from][best.to];
            const int got_other = t[White][1][1][other.from][other.to];
            exact = exact && got_best == expect_best && got_other == expect_other;
            bounded = bounded && std::abs(got_best) <= 16384 && std::abs(got_other) <= 16384;
            ++steps;
        }
        bound(exact && bounded && expect_best == 16384 && expect_other == -16384,
              "level " + std::to_string(level) + ": threat slots [W][1][0] e4c3 / [W][1][1] e4g5 follow the lock gravity "
              "and saturate at exactly +16384 / -16384 after " + std::to_string(steps) + " updates (bonus 10000)");
        int nonzero = 0;
        for (const auto& a : t) for (const auto& bb : a) for (const auto& c : bb) for (const auto& d : c) for (const std::int16_t e : d)
            nonzero += e != 0;
        check(nonzero == 2, "exactly the two predicted threat slots are written");
        check(Probe::main(w)[White][best.from][best.to] == 16384, "the lock butterfly entry saturates as before");
        // Read: blend of the saturated entries, plus continuation entries seeded at the bound.
        auto& cont = Probe::cont(w);
        (ss - 1)->continuation = &cont[BN][square("b4")];
        (ss - 2)->continuation = &cont[WQ][square("d1")];
        (*(ss - 1)->continuation)[WN][best.to] = -16384;
        (*(ss - 2)->continuation)[WN][best.to] = -16384;
        Probe::main(w)[White][best.from][best.to] = -16384;
        t[White][1][0][best.from][best.to] = -16384;
        bound(Probe::quiet(w, b, ss, best) == -49152,
              "level " + std::to_string(level) + ": worst-case quiet_history read = -3 * 16384 = -49152 exactly");
        Probe::main(w)[White][best.from][best.to] = 16384;
        const long long ref = ref_blend(16384, -16384, hist_rework::threat_quarters(level)) - 32768;
        check(Probe::quiet(w, b, ss, best) == ref, "mixed-sign read equals the int64 reference, level " + std::to_string(level));
        (ss - 1)->continuation = nullptr;
        (ss - 2)->continuation = nullptr;
    }
    tune::HistoryBonusMax = saved_max;
    tune::HistoryBonusQuadratic = saved_q;
    tune::HistoryBonusLinear = saved_l;
    search_options::hist_rework = 0;
    section("glue, history: predicted threat slots, saturation at +-16384 with bonus 10000, read bounds", c0, f0);
}

void test_glue_correction_bounds() {
    const long long c0 = checks; const int f0 = failures;
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    const int saved_mw = tune::MaterialCorrectionWeight;
    const Board b = position(Fens[4]);
    const std::size_t side = static_cast<std::size_t>(b.side_to_move());
    const std::size_t joint_index = hist_rework::joint_key(b) & (CorrectionSize - 1U);
    for (int level = 1; level <= 3; ++level) {
        search_options::hist_rework = level;
        const int jw = hist_rework::joint_weight(level);
        for (const int sign : {1, -1}) {
            w.clear();
            tune::MaterialCorrectionWeight = 300; // UCI maximum
            Probe::pawns(w)[side].fill(sign * 8192);
            Probe::material(w)[side].fill(sign * 8192);
            Probe::joint(w)[side].fill(sign * 8192);
            const long long correction = sign * (8192LL + 8192LL * 300 / 100 + 8192LL * jw / 100);
            bound(Probe::eval(w, b, 1000) == 1000 + correction / 256,
                  "worst-case corrected eval, level " + std::to_string(level) + " sign " + std::to_string(sign) + ": raw + " +
                      std::to_string(correction / 256));
            check(Probe::eval(w, b, sign * (MateInMaxPly - 20)) == sign * (MateInMaxPly - 1), "mate-range clamp holds at the bound");
            // Update with the largest residual the search can pass (non-mate best vs the clamped corrected eval):
            // |best - eval| * 256 <= 63742 * 256 = 16318 * 1000 < 2^31; diff clamps to +-2048, weight 16, step +-128.
            const int far = MateInMaxPly - 1;
            Probe::update_corr(w, b, 15, sign * far, -sign * far);
            bound(Probe::joint(w)[side][joint_index] == sign * 8192,
                  "joint entry at the bound stays at exactly " + std::to_string(sign * 8192) + " under a same-sign maximal step");
            check(Probe::pawns(w)[side][b.pawn_key() & (CorrectionSize - 1U)] == sign * 8192, "pawn entry clamps as in the lock");
            Probe::update_corr(w, b, 15, -sign * far, sign * far);
            check(Probe::joint(w)[side][joint_index] == ref_gravity_unclamped(sign * 8192, -sign * 128, 8192),
                  "opposite-sign maximal step equals the gravity reference (" + std::to_string(sign * (8192 - 256)) + ")");
        }
        // From zero, maximal steps of one sign saturate the joint entry at exactly the bound.
        w.clear();
        tune::MaterialCorrectionWeight = 100;
        int updates = 0;
        while (Probe::joint(w)[side][joint_index] != 8192 && updates < 20000) {
            Probe::update_corr(w, b, 30, MateInMaxPly - 1, -(MateInMaxPly - 1));
            ++updates;
        }
        bound(Probe::joint(w)[side][joint_index] == 8192, "joint entry reaches exactly +8192 (" + std::to_string(updates) + " maximal updates)");
    }
    tune::MaterialCorrectionWeight = saved_mw;
    search_options::hist_rework = 0;
    section("glue, correction: worst-case read (+-160 cp), joint update at +-8192, exact saturation", c0, f0);
}

struct SearchResult { std::uint64_t nodes = 0; int threat_nonzero = 0, joint_nonzero = 0; bool bounded = true; };

SearchResult run_searches(int level, int depth) {
    search_options::hist_rework = level;
    SearchResult r;
    Searcher searcher(16, 1);
    for (std::size_t i = 0; i < 3; ++i) {
        Board b = position(Fens[i == 2 ? 5 : i]);
        searcher.clear();
        SearchLimits limits;
        limits.depth = depth;
        r.nodes += searcher.search(b, limits).nodes;
        Worker& w = searcher.main_worker();
        for (const auto& a : Probe::threat(w)) for (const auto& bb : a) for (const auto& c : bb) for (const auto& d : c) for (const std::int16_t e : d) {
            r.threat_nonzero += e != 0;
            r.bounded = r.bounded && std::abs(e) <= 16384;
        }
        for (const auto& s : Probe::main(w)) for (const auto& row : s) for (const std::int16_t e : row) r.bounded = r.bounded && std::abs(e) <= 16384;
        for (const auto* table : {&Probe::joint(w), &Probe::pawns(w), &Probe::material(w)})
            for (const auto& s : *table) for (const std::int32_t e : s) r.bounded = r.bounded && std::abs(e) <= 8192;
        for (const auto& s : Probe::joint(w)) for (const std::int32_t e : s) r.joint_nonzero += e != 0;
    }
    search_options::hist_rework = 0;
    return r;
}

void test_searches() {
    const long long c0 = checks; const int f0 = failures;
    std::array<SearchResult, 4> first{}, second{};
    for (int level = 0; level <= 3; ++level) {
        first[static_cast<std::size_t>(level)] = run_searches(level, 8);
        second[static_cast<std::size_t>(level)] = run_searches(level, 8);
        const SearchResult& r = first[static_cast<std::size_t>(level)];
        std::cout << "INFO level " << level << " depth 8 nodes " << r.nodes << " threat_nonzero " << r.threat_nonzero
                  << " joint_nonzero " << r.joint_nonzero << '\n';
        check(r.nodes == second[static_cast<std::size_t>(level)].nodes, "Threads 1 determinism, level " + std::to_string(level));
        check(r.bounded, "every table entry within its bound after the searches, level " + std::to_string(level));
        if (level == 0) {
            check(r.threat_nonzero == 0 && r.joint_nonzero == 0, "level 0 searches leave the new tables untouched");
        } else {
            check(r.nodes != first[0].nodes, "level " + std::to_string(level) + " changes the node count");
            check(r.threat_nonzero > 100 && r.joint_nonzero > 10, "level " + std::to_string(level) + " fills both new tables");
        }
    }
    // Maximum stress: option at its maximum, history-bonus and material-weight tunables at their UCI maxima.
    const int saved_max = tune::HistoryBonusMax, saved_q = tune::HistoryBonusQuadratic, saved_l = tune::HistoryBonusLinear,
              saved_mw = tune::MaterialCorrectionWeight;
    tune::HistoryBonusMax = 10000;
    tune::HistoryBonusQuadratic = 100;
    tune::HistoryBonusLinear = 500;
    tune::MaterialCorrectionWeight = 300;
    const SearchResult stress = run_searches(hist_rework::MaxLevel, 9);
    std::cout << "INFO stress level 3 depth 9 nodes " << stress.nodes << " threat_nonzero " << stress.threat_nonzero << '\n';
    bound(stress.bounded && stress.threat_nonzero > 100, "level 3 with tunables at their maxima: searches complete, all entries bounded");
    tune::HistoryBonusMax = saved_max;
    tune::HistoryBonusQuadratic = saved_q;
    tune::HistoryBonusLinear = saved_l;
    tune::MaterialCorrectionWeight = saved_mw;
    section("searches: determinism, OFF untouched, ON changes nodes, max-value stress with bounded tables", c0, f0);
}
} // namespace

int main() {
    std::cout << "HistRework (A1) tests\n";
    try {
        test_levels();
        test_threat_maps();
        test_blend();
        test_gravity();
        test_joint_key();
        test_glue_off();
        test_glue_history_bounds();
        test_glue_correction_bounds();
        test_searches();
    } catch (const std::exception& e) {
        std::cout << "FAIL exception: " << e.what() << '\n';
        ++failures;
    }
    std::cout << "SUMMARY checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
