// dtmref.cpp -- independent exhaustive DTM reference.
//
// Deliberately a SECOND implementation, not shared with mateverify.cpp. It
// works from a 64-square mailbox with explicit offsets, its own legality test
// and its own transposition-free retrograde-by-iterative-deepening loop over
// *both* sides, so agreement between the two programs is real evidence.
//
// Purpose: give the verifier an oracle it did not provide itself. KQvK and KRvK
// distances are known to be bounded (10 and 31 moves), so the reference can be
// checked against a published bound before it is used to grade anything.
//
// Modes:
//   --dtm FEN          signed plies to mate for the side to move (0 = already mated)
//                      prints "none" when no forced mate exists within the cap
//   --batch            FEN per line on stdin -> "FEN\t<plies|none>"

#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

// Mailbox board: 8x8 with explicit (file, rank) arithmetic -- a different
// representation from mateverify's bitboards.
struct Bd {
    char sq[8][8];  // [file][rank]; '.' empty; uppercase white, lowercase black
    bool whiteToMove;
    int epFile, epRank;
    bool epValid;
    int castle;  // bit 0 W-king, 1 W-queen, 2 B-king, 3 B-queen
    int halfmove;
    int kingFile[2], kingRank[2];
};

inline bool onBoard(int f, int r) { return f >= 0 && f < 8 && r >= 0 && r < 8; }
inline bool isWhite(char c) { return c >= 'A' && c <= 'Z'; }
inline bool isEmpty(char c) { return c == '.'; }
inline bool own(char c, bool white) { return white ? isWhite(c) : (c >= 'a' && c <= 'z'); }
inline bool enemy(char c, bool white) {
    return white ? (c >= 'a' && c <= 'z') : isWhite(c);
}

bool attacked(const Bd& b, int f, int r, bool byWhite) {
    // pawns
    const int pr = byWhite ? r - 1 : r + 1;
    if (onBoard(f - 1, pr)) {
        char c = b.sq[f - 1][pr];
        if (byWhite ? c == 'P' : c == 'p') return true;
    }
    if (onBoard(f + 1, pr)) {
        char c = b.sq[f + 1][pr];
        if (byWhite ? c == 'P' : c == 'p') return true;
    }
    // knights
    static const int kn[8][2] = {{1, 2},  {2, 1},  {2, -1},  {1, -2},
                                 {-1, -2}, {-2, -1}, {-2, 1}, {-1, 2}};
    for (auto& d : kn) {
        const int nf = f + d[0], nr = r + d[1];
        if (!onBoard(nf, nr)) continue;
        char c = b.sq[nf][nr];
        if (byWhite ? c == 'N' : c == 'n') return true;
    }
    // king
    for (int df = -1; df <= 1; ++df)
        for (int dr = -1; dr <= 1; ++dr) {
            if (!df && !dr) continue;
            const int nf = f + df, nr = r + dr;
            if (!onBoard(nf, nr)) continue;
            char c = b.sq[nf][nr];
            if (byWhite ? c == 'K' : c == 'k') return true;
        }
    // sliders -- walk outward square by square
    static const int diag[4][2] = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
    static const int orth[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    for (auto& d : diag) {
        int nf = f + d[0], nr = r + d[1];
        while (onBoard(nf, nr)) {
            char c = b.sq[nf][nr];
            if (!isEmpty(c)) {
                if (byWhite ? (c == 'B' || c == 'Q') : (c == 'b' || c == 'q')) return true;
                break;
            }
            nf += d[0];
            nr += d[1];
        }
    }
    for (auto& d : orth) {
        int nf = f + d[0], nr = r + d[1];
        while (onBoard(nf, nr)) {
            char c = b.sq[nf][nr];
            if (!isEmpty(c)) {
                if (byWhite ? (c == 'R' || c == 'Q') : (c == 'r' || c == 'q')) return true;
                break;
            }
            nf += d[0];
            nr += d[1];
        }
    }
    return false;
}

inline bool inCheck(const Bd& b, bool white) {
    return attacked(b, b.kingFile[white ? 0 : 1], b.kingRank[white ? 0 : 1], !white);
}

struct Mv {
    int f1, r1, f2, r2;
    char promo;
};

void genPseudo(const Bd& b, std::vector<Mv>& out) {
    out.clear();
    const bool white = b.whiteToMove;
    for (int f = 0; f < 8; ++f)
        for (int r = 0; r < 8; ++r) {
            const char c = b.sq[f][r];
            if (!own(c, white)) continue;
            const char u = white ? static_cast<char>(c - 'A' + 'a') : static_cast<char>(c - 'a' + 'A');
            (void)u;
            if (c == 'P' || c == 'p') {
                const int dir = white ? 1 : -1;
                const int startRank = white ? 1 : 6;
                const int promoRank = white ? 7 : 0;
                const int r1 = r + dir;
                if (onBoard(f, r1) && isEmpty(b.sq[f][r1])) {
                    if (r1 == promoRank) {
                        for (char p : {'Q', 'R', 'B', 'N'}) out.push_back({f, r, f, r1, p});
                    } else {
                        out.push_back({f, r, f, r1, 0});
                        const int r2 = r + 2 * dir;
                        if (r == startRank && isEmpty(b.sq[f][r2])) out.push_back({f, r, f, r2, 0});
                    }
                }
                for (int df : {-1, 1}) {
                    const int nf = f + df, nr = r + dir;
                    if (!onBoard(nf, nr)) continue;
                    char t = b.sq[nf][nr];
                    if (enemy(t, white)) {
                        if (nr == promoRank) {
                            for (char p : {'Q', 'R', 'B', 'N'}) out.push_back({f, r, nf, nr, p});
                        } else out.push_back({f, r, nf, nr, 0});
                    } else if (b.epValid && nf == b.epFile && nr == b.epRank && isEmpty(t)) {
                        out.push_back({f, r, nf, nr, 0});
                    }
                }
            } else if (c == 'N' || c == 'n') {
                static const int kn[8][2] = {{1, 2},  {2, 1},  {2, -1},  {1, -2},
                                             {-1, -2}, {-2, -1}, {-2, 1}, {-1, 2}};
                for (auto& d : kn) {
                    const int nf = f + d[0], nr = r + d[1];
                    if (!onBoard(nf, nr)) continue;
                    if (own(b.sq[nf][nr], white)) continue;
                    out.push_back({f, r, nf, nr, 0});
                }
            } else if (c == 'B' || c == 'b' || c == 'R' || c == 'r' || c == 'Q' || c == 'q') {
                const bool isDiag = (c == 'B' || c == 'b');
                const bool isOrth = (c == 'R' || c == 'r');
                static const int diag[4][2] = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
                static const int orth[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
                auto ray = [&](const int d[4][2]) {
                    for (int i = 0; i < 4; ++i) {
                        int nf = f + d[i][0], nr = r + d[i][1];
                        while (onBoard(nf, nr)) {
                            if (own(b.sq[nf][nr], white)) break;
                            out.push_back({f, r, nf, nr, 0});
                            if (!isEmpty(b.sq[nf][nr])) break;
                            nf += d[i][0];
                            nr += d[i][1];
                        }
                    }
                };
                if (!isOrth) ray(diag);
                if (!isDiag) ray(orth);
            } else if (c == 'K' || c == 'k') {
                for (int df = -1; df <= 1; ++df)
                    for (int dr = -1; dr <= 1; ++dr) {
                        if (!df && !dr) continue;
                        const int nf = f + df, nr = r + dr;
                        if (!onBoard(nf, nr) || own(b.sq[nf][nr], white)) continue;
                        out.push_back({f, r, nf, nr, 0});
                    }
                // castling
                if (white) {
                    if ((b.castle & 1) && b.sq[5][0] == '.' && b.sq[6][0] == '.' && b.sq[7][0] == 'R' &&
                        b.sq[4][0] == 'K' && !attacked(b, 4, 0, false) && !attacked(b, 5, 0, false) &&
                        !attacked(b, 6, 0, false))
                        out.push_back({4, 0, 6, 0, 0});
                    if ((b.castle & 2) && b.sq[3][0] == '.' && b.sq[2][0] == '.' && b.sq[1][0] == '.' &&
                        b.sq[0][0] == 'R' && b.sq[4][0] == 'K' && !attacked(b, 4, 0, false) &&
                        !attacked(b, 3, 0, false) && !attacked(b, 2, 0, false))
                        out.push_back({4, 0, 2, 0, 0});
                } else {
                    if ((b.castle & 4) && b.sq[5][7] == '.' && b.sq[6][7] == '.' && b.sq[7][7] == 'r' &&
                        b.sq[4][7] == 'k' && !attacked(b, 4, 7, true) && !attacked(b, 5, 7, true) &&
                        !attacked(b, 6, 7, true))
                        out.push_back({4, 7, 6, 7, 0});
                    if ((b.castle & 8) && b.sq[3][7] == '.' && b.sq[2][7] == '.' && b.sq[1][7] == '.' &&
                        b.sq[0][7] == 'r' && b.sq[4][7] == 'k' && !attacked(b, 4, 7, true) &&
                        !attacked(b, 3, 7, true) && !attacked(b, 2, 7, true))
                        out.push_back({4, 7, 2, 7, 0});
                }
            }
        }
}

struct Un {
    char captured;
    int capF, capR;
    bool epCapture;
    int castle, epFile, epRank, halfmove;
    bool epValid;
};

void makeMove(Bd& b, const Mv& m, Un& u) {
    u.captured = '.';
    u.epCapture = false;
    u.capF = u.capR = -1;
    u.castle = b.castle;
    u.epFile = b.epFile;
    u.epRank = b.epRank;
    u.epValid = b.epValid;
    u.halfmove = b.halfmove;

    const bool white = b.whiteToMove;
    const char pc = b.sq[m.f1][m.r1];
    const bool isPawn = (pc == 'P' || pc == 'p');

    if (isPawn && b.epValid && m.f2 == b.epFile && m.r2 == b.epRank && isEmpty(b.sq[m.f2][m.r2])) {
        const int capR = white ? m.r2 - 1 : m.r2 + 1;
        u.captured = b.sq[m.f2][capR];
        u.capF = m.f2;
        u.capR = capR;
        u.epCapture = true;
        b.sq[m.f2][capR] = '.';
    } else if (!isEmpty(b.sq[m.f2][m.r2])) {
        u.captured = b.sq[m.f2][m.r2];
        u.capF = m.f2;
        u.capR = m.r2;
    }

    b.sq[m.f2][m.r2] = m.promo ? (white ? m.promo : static_cast<char>(m.promo - 'A' + 'a')) : pc;
    b.sq[m.f1][m.r1] = '.';

    if (pc == 'K' || pc == 'k') {
        b.kingFile[white ? 0 : 1] = m.f2;
        b.kingRank[white ? 0 : 1] = m.r2;
        if (m.f1 == 4 && m.f2 == 6) { b.sq[5][m.r1] = b.sq[7][m.r1]; b.sq[7][m.r1] = '.'; }
        if (m.f1 == 4 && m.f2 == 2) { b.sq[3][m.r1] = b.sq[0][m.r1]; b.sq[0][m.r1] = '.'; }
    }

    if (m.f1 == 4 || m.f2 == 4) b.castle &= ~3;
    if (m.f1 == 7 || m.f2 == 7) b.castle &= ~1;
    if (m.f1 == 0 || m.f2 == 0) b.castle &= ~2;
    if (m.f1 == 4 || m.f2 == 4) b.castle &= ~12;
    if (m.f1 == 7 || m.f2 == 7) b.castle &= ~4;
    if (m.f1 == 0 || m.f2 == 0) b.castle &= ~8;

    b.epValid = false;
    if (isPawn && std::abs(m.r2 - m.r1) == 2) {
        b.epValid = true;
        b.epFile = m.f1;
        b.epRank = (m.r1 + m.r2) / 2;
    }
    b.halfmove = (isPawn || u.captured != '.') ? 0 : u.halfmove + 1;
    b.whiteToMove = !white;
}

void unmakeMove(Bd& b, const Mv& m, const Un& u) {
    const bool moverWhite = !b.whiteToMove;
    const char pc = b.sq[m.f2][m.r2];
    b.sq[m.f1][m.r1] = m.promo ? (moverWhite ? 'P' : 'p') : pc;
    b.sq[m.f2][m.r2] = '.';
    if (u.captured != '.') b.sq[u.capF][u.capR] = u.captured;
    if (pc == 'K' || pc == 'k') {
        b.kingFile[moverWhite ? 0 : 1] = m.f1;
        b.kingRank[moverWhite ? 0 : 1] = m.r1;
        if (m.f1 == 4 && m.f2 == 6) { b.sq[7][m.r1] = b.sq[5][m.r1]; b.sq[5][m.r1] = '.'; }
        if (m.f1 == 4 && m.f2 == 2) { b.sq[0][m.r1] = b.sq[3][m.r1]; b.sq[3][m.r1] = '.'; }
    }
    b.castle = u.castle;
    b.epFile = u.epFile;
    b.epRank = u.epRank;
    b.epValid = u.epValid;
    b.halfmove = u.halfmove;
    b.whiteToMove = moverWhite;
}

// ---- Exact DTM by iterative deepening over signed mate scores.
//
// Value convention (identical in spirit to any signed minimax, but written
// independently here): positive = the side to move forces mate, magnitude is
// plies from this node; negative = the side to move gets mated; 0 = no mate
// within the horizon.
//
// The 0 case is what makes this correct rather than merely deep. A defender
// move that escapes the horizon scores 0, and 0 beats any negative score, so
// the defender prefers it -- which stops the search from claiming a mate that a
// longer defence would avoid. An earlier version dropped such moves with
// `continue`, which let the attacker claim a truncated mate; that is the
// horizon-truncation fault this comment exists to prevent.
constexpr int NONE = 1000000;
constexpr int NONE_MATE = 32000;  // mate band origin; a mate at ply p is +-(NONE_MATE - p)

struct Ctx {
    long long nodes = 0;
    long long cap = 0;
    std::chrono::steady_clock::time_point deadline;
    bool aborted = false;
};

int solve(Bd& b, int depth, int ply, Ctx& ctx) {
    if (ctx.aborted) return 0;
    if (++ctx.nodes > ctx.cap) { ctx.aborted = true; return 0; }
    if ((ctx.nodes & 8191) == 0 && std::chrono::steady_clock::now() > ctx.deadline) {
        ctx.aborted = true;
        return 0;
    }
    if (b.halfmove >= 100) return 0;

    std::vector<Mv> mvs;
    genPseudo(b, mvs);
    const bool white = b.whiteToMove;

    int legal = 0;
    int best = -NONE;
    Un u;
    for (auto& m : mvs) {
        makeMove(b, m, u);
        if (inCheck(b, white)) {  // illegal: own king left in check
            unmakeMove(b, m, u);
            continue;
        }
        ++legal;
        int child;
        if (depth <= 1) child = 0;  // horizon edge: no mate proven below
        else child = solve(b, depth - 1, ply + 1, ctx);
        unmakeMove(b, m, u);
        if (ctx.aborted) return 0;
        const int score = -child;
        if (score > best) best = score;
        if (best > 0) break;  // any forced mate is enough at this node
    }

    if (legal == 0) return inCheck(b, white) ? -(NONE_MATE - ply) : 0;
    if (depth <= 0) return 0;
    return best == -NONE ? 0 : best;
}

// Iteratively deepen. The first horizon at which a mate appears yields the exact
// distance: every shallower horizon proved no faster mate exists, and a forced
// mate of distance k is fully visible at horizon k.
int exactDtm(Bd b, int capPlies, Ctx& ctx) {
    for (int d = 1; d <= capPlies; ++d) {
        Bd work = b;
        const int v = solve(work, d, 0, ctx);
        if (ctx.aborted) return NONE;
        if (v != 0) return v;
    }
    return NONE;
}

bool parseFen(const std::string& fen, Bd& b, std::string& err) {
    std::memset(&b, 0, sizeof(b));
    for (int f = 0; f < 8; ++f)
        for (int r = 0; r < 8; ++r) b.sq[f][r] = '.';
    b.whiteToMove = true;
    b.epValid = false;
    b.castle = 0;
    b.halfmove = 0;
    b.kingFile[0] = b.kingFile[1] = -1;
    b.kingRank[0] = b.kingRank[1] = -1;

    std::vector<std::string> f;
    {
        std::string cur;
        for (char c : fen) {
            if (c == ' ' || c == '\t') {
                if (!cur.empty()) { f.push_back(cur); cur.clear(); }
            } else cur.push_back(c);
        }
        if (!cur.empty()) f.push_back(cur);
    }
    if (f.size() < 4) { err = "fen needs >=4 fields"; return false; }

    int r = 7, file = 0;
    for (char c : f[0]) {
        if (c == '/') {
            if (file != 8) { err = "bad rank width"; return false; }
            --r;
            file = 0;
            if (r < 0) { err = "too many ranks"; return false; }
        } else if (c >= '1' && c <= '8') {
            file += c - '0';
            if (file > 8) { err = "rank overflow"; return false; }
        } else {
            if (file > 7) { err = "rank overflow"; return false; }
            b.sq[file][r] = c;
            if (c == 'K') { b.kingFile[0] = file; b.kingRank[0] = r; }
            if (c == 'k') { b.kingFile[1] = file; b.kingRank[1] = r; }
            ++file;
        }
    }
    if (r != 0 || file != 8) { err = "missing ranks"; return false; }
    if (b.kingFile[0] < 0 || b.kingFile[1] < 0) { err = "missing king"; return false; }
    if (f[1] != "w" && f[1] != "b") { err = "bad side"; return false; }
    b.whiteToMove = (f[1] == "w");
    for (char c : f[2]) {
        if (c == 'K') b.castle |= 1;
        else if (c == 'Q') b.castle |= 2;
        else if (c == 'k') b.castle |= 4;
        else if (c == 'q') b.castle |= 8;
        else if (c != '-') { err = "bad castling"; return false; }
    }
    if (f[3] != "-") {
        if (f[3].size() != 2) { err = "bad ep"; return false; }
        b.epValid = true;
        b.epFile = f[3][0] - 'a';
        b.epRank = f[3][1] - '1';
        if (b.epFile < 0 || b.epFile > 7 || b.epRank < 0 || b.epRank > 7) { err = "bad ep"; return false; }
    }
    b.halfmove = f.size() > 4 ? std::atoi(f[4].c_str()) : 0;
    if (inCheck(b, !b.whiteToMove)) { err = "side not to move is in check"; return false; }
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "--help";
    long long cap = 50000000LL;
    double secs = 300.0;

    auto one = [&](const std::string& fen) -> std::string {
        Bd b;
        std::string err;
        if (!parseFen(fen, b, err)) return std::string("BADFEN:") + err;
        if (inCheck(b, b.whiteToMove)) {
            // already mated?
            std::vector<Mv> mvs;
            genPseudo(b, mvs);
            int legal = 0;
            Un u;
            for (auto& m : mvs) {
                const bool w = b.whiteToMove;
                makeMove(b, m, u);
                if (!inCheck(b, w)) ++legal;
                unmakeMove(b, m, u);
            }
            if (legal == 0) return "0";
        }
        Ctx ctx;
        ctx.cap = cap;
        ctx.deadline = std::chrono::steady_clock::now() +
                       std::chrono::milliseconds(static_cast<long long>(secs * 1000));
        const int v = exactDtm(b, 64, ctx);
        if (ctx.aborted) return "capped";
        if (v == NONE) return "none";
        return std::to_string(v);
    };

    if (mode == "--dtm") {
        if (argc < 3) { std::fprintf(stderr, "usage: --dtm FEN [nodes] [secs]\n"); return 2; }
        if (argc > 3) cap = std::atoll(argv[3]);
        if (argc > 4) secs = std::atof(argv[4]);
        std::printf("%s\n", one(argv[2]).c_str());
        return 0;
    }
    if (mode == "--batch") {
        if (argc > 2) cap = std::atoll(argv[2]);
        if (argc > 3) secs = std::atof(argv[3]);
        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;
            std::printf("%s\t%s\n", line.c_str(), one(line).c_str());
            std::fflush(stdout);
        }
        return 0;
    }
    std::fprintf(stderr, "dtmref -- independent DTM oracle\n  --dtm FEN [nodes] [secs]\n  --batch [nodes] [secs]\n");
    return 2;
}
