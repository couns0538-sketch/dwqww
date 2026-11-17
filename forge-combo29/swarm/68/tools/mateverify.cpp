// mateverify.cpp -- standalone exhaustive mate verifier.
//
// Independent of the engine under audit: own board representation, own move
// generation, own search. It includes no engine header and links no engine
// code. Its only inputs are a FEN and a claimed mate distance.
//
// A mate score `mate N` is VERIFIED only when the exact minimax distance from
// the root equals the distance the label implies:
//   win  (N > 0): 2N-1 plies   (side to move delivers the mate)
//   loss (N < 0): 2N   plies   (side to move is mated)
// Exact minimax distance proves both halves at once: that a forced mate exists
// in D plies, and (because the value is the minimum over all defences) that no
// forced mate exists in fewer.
//
// Modes:
//   --perft N FEN        perft from the FEN on argv (movegen validation)
//   --one FEN N          verify one claimed mate distance
//   --batch              read "FEN<TAB>N<TAB>meta" per line from stdin,
//                        write one JSON object per line to stdout

#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr int MATE = 32000;
constexpr int INF = 32001;

enum PieceType { EMPTY = 0, PAWN = 1, KNIGHT = 2, BISHOP = 3, ROOK = 4, QUEEN = 5, KING = 6 };
enum { WHITE = 0, BLACK = 1 };

uint64_t knightAtt[64], kingAtt[64], pawnAtt[2][64], rayAtt[8][64];

void init_tables() {
    const int knightD[8][2] = {{1, 2},  {2, 1},  {2, -1},  {1, -2},
                               {-1, -2}, {-2, -1}, {-2, 1}, {-1, 2}};
    const int kingD[8][2] = {{1, 0},  {1, 1},  {0, 1},  {-1, 1},
                             {-1, 0}, {-1, -1}, {0, -1}, {1, -1}};
    const int rayD[8][2] = {{0, 1}, {1, 1}, {1, 0}, {1, -1},
                            {0, -1}, {-1, -1}, {-1, 0}, {-1, 1}};
    for (int s = 0; s < 64; ++s) {
        const int f = s & 7, r = s >> 3;
        for (int i = 0; i < 8; ++i) {
            const int nf = f + knightD[i][0], nr = r + knightD[i][1];
            if (nf >= 0 && nf < 8 && nr >= 0 && nr < 8) knightAtt[s] |= 1ULL << (nr * 8 + nf);
            const int kf = f + kingD[i][0], kr = r + kingD[i][1];
            if (kf >= 0 && kf < 8 && kr >= 0 && kr < 8) kingAtt[s] |= 1ULL << (kr * 8 + kf);
        }
        if (r < 7) {
            if (f > 0) pawnAtt[WHITE][s] |= 1ULL << ((r + 1) * 8 + f - 1);
            if (f < 7) pawnAtt[WHITE][s] |= 1ULL << ((r + 1) * 8 + f + 1);
        }
        if (r > 0) {
            if (f > 0) pawnAtt[BLACK][s] |= 1ULL << ((r - 1) * 8 + f - 1);
            if (f < 7) pawnAtt[BLACK][s] |= 1ULL << ((r - 1) * 8 + f + 1);
        }
        for (int d = 0; d < 8; ++d) {
            int nf = f + rayD[d][0], nr = r + rayD[d][1];
            while (nf >= 0 && nf < 8 && nr >= 0 && nr < 8) {
                rayAtt[d][s] |= 1ULL << (nr * 8 + nf);
                nf += rayD[d][0];
                nr += rayD[d][1];
            }
        }
    }
}

inline int file_of(int s) { return s & 7; }
inline int rank_of(int s) { return s >> 3; }
inline uint64_t bit(int s) { return 1ULL << s; }

// ---------------------------------------------------------------- zobrist
uint64_t zPiece[2][7][64], zSide, zCastle[16], zEp[64];

uint64_t splitmix(uint64_t& x) {
    uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

void init_zobrist() {
    uint64_t seed = 0x1234567890ABCDEFULL;
    for (int c = 0; c < 2; ++c)
        for (int p = 0; p < 7; ++p)
            for (int s = 0; s < 64; ++s) zPiece[c][p][s] = splitmix(seed);
    zSide = splitmix(seed);
    for (int i = 0; i < 16; ++i) zCastle[i] = splitmix(seed);
    for (int i = 0; i < 64; ++i) zEp[i] = splitmix(seed);
}

// ---------------------------------------------------------------- position
struct Pos {
    int8_t b[64];
    uint64_t bb[2][7];
    uint64_t occ[2];
    int side = WHITE;
    int castling = 0;  // 1 = white O-O, 2 = white O-O-O, 4 = black O-O, 8 = black O-O-O
    int ep = -1;
    int halfmove = 0;
    int kingSq[2] = {-1, -1};
    uint64_t key = 0;
};

struct Move {
    int from, to, promo, flags;  // flags: 1 = en passant, 2 = castle, 4 = double push
};

struct Undo {
    int captured;
    int capturedSq;
    int castling, ep, halfmove;
    uint64_t key;
};

struct MoveList {
    Move m[256];
    int n = 0;
    void add(int f, int t, int promo = 0, int flags = 0) {
        if (n < 256) m[n++] = Move{f, t, promo, flags};
    }
};

inline void clear_pos(Pos& p) {
    std::memset(p.b, 0, sizeof(p.b));
    std::memset(p.bb, 0, sizeof(p.bb));
    p.occ[0] = p.occ[1] = 0;
    p.side = WHITE;
    p.castling = 0;
    p.ep = -1;
    p.halfmove = 0;
    p.kingSq[0] = p.kingSq[1] = -1;
    p.key = 0;
}

inline void put_piece(Pos& p, int sq, int color, int type) {
    p.b[sq] = static_cast<int8_t>(color == WHITE ? type : -type);
    p.bb[color][type] |= bit(sq);
    p.occ[color] |= bit(sq);
    if (type == KING) p.kingSq[color] = sq;
}

inline void remove_piece(Pos& p, int sq) {
    const int8_t v = p.b[sq];
    if (!v) return;
    const int color = v > 0 ? WHITE : BLACK;
    const int type = v > 0 ? v : -v;
    p.bb[color][type] &= ~bit(sq);
    p.occ[color] &= ~bit(sq);
    p.b[sq] = 0;
}

// Nearest occupied square along one ray from `sq`, scanning outward.
// All squares on a ray share a direction, so Manhattan distance is monotone.
int nearest_on_ray(uint64_t occAll, int sq, uint64_t ray) {
    const uint64_t blockers = ray & occAll;
    if (!blockers) return -1;
    int closest = -1, bestDist = 99;
    uint64_t t = blockers;
    while (t) {
        const int s2 = __builtin_ctzll(t);
        t &= t - 1;
        const int d = std::abs(file_of(s2) - file_of(sq)) + std::abs(rank_of(s2) - rank_of(sq));
        if (d < bestDist) { bestDist = d; closest = s2; }
    }
    return closest;
}

bool attacked(const Pos& p, int sq, int by) {
    if (pawnAtt[1 - by][sq] & p.bb[by][PAWN]) return true;
    if (knightAtt[sq] & p.bb[by][KNIGHT]) return true;
    if (kingAtt[sq] & p.bb[by][KING]) return true;
    const uint64_t occAll = p.occ[0] | p.occ[1];
    const uint64_t diag = p.bb[by][BISHOP] | p.bb[by][QUEEN];
    const uint64_t orth = p.bb[by][ROOK] | p.bb[by][QUEEN];
    static const int diagRay[4] = {1, 3, 5, 7};
    static const int orthRay[4] = {0, 2, 4, 6};
    for (int i = 0; i < 4; ++i) {
        const int s2 = nearest_on_ray(occAll, sq, rayAtt[diagRay[i]][sq]);
        if (s2 >= 0 && (bit(s2) & diag)) return true;
    }
    for (int i = 0; i < 4; ++i) {
        const int s2 = nearest_on_ray(occAll, sq, rayAtt[orthRay[i]][sq]);
        if (s2 >= 0 && (bit(s2) & orth)) return true;
    }
    return false;
}

inline bool in_check(const Pos& p, int side) {
    return attacked(p, p.kingSq[side], 1 - side);
}

uint64_t compute_key(const Pos& p) {
    uint64_t k = 0;
    for (int sq = 0; sq < 64; ++sq) {
        const int8_t v = p.b[sq];
        if (!v) continue;
        k ^= zPiece[v > 0 ? WHITE : BLACK][v > 0 ? v : -v][sq];
    }
    if (p.side == BLACK) k ^= zSide;
    k ^= zCastle[p.castling & 15];
    if (p.ep >= 0) k ^= zEp[p.ep];
    return k;
}

void gen_pseudo(const Pos& p, MoveList& ml) {
    const int us = p.side, them = 1 - us;
    const uint64_t occAll = p.occ[0] | p.occ[1];
    const uint64_t enemy = p.occ[them];

    uint64_t pawns = p.bb[us][PAWN];
    while (pawns) {
        const int s = __builtin_ctzll(pawns);
        pawns &= pawns - 1;
        const int f = file_of(s), r = rank_of(s);
        const int fwd = us == WHITE ? 8 : -8;
        const int startRank = us == WHITE ? 1 : 6;
        const int promoRank = us == WHITE ? 7 : 0;
        const int one = s + fwd;
        if (one >= 0 && one < 64 && !p.b[one]) {
            if (rank_of(one) == promoRank) {
                ml.add(s, one, QUEEN);
                ml.add(s, one, ROOK);
                ml.add(s, one, BISHOP);
                ml.add(s, one, KNIGHT);
            } else {
                ml.add(s, one, 0, 0);
                if (r == startRank) {
                    const int two = s + 2 * fwd;
                    if (two >= 0 && two < 64 && !p.b[two]) ml.add(s, two, 0, 4);
                }
            }
        }
        const int caps[2] = {f > 0 ? one - 1 : -1, f < 7 ? one + 1 : -1};
        for (int i = 0; i < 2; ++i) {
            const int t = caps[i];
            if (t < 0 || t >= 64) continue;
            if (enemy & bit(t)) {
                if (rank_of(t) == promoRank) {
                    ml.add(s, t, QUEEN);
                    ml.add(s, t, ROOK);
                    ml.add(s, t, BISHOP);
                    ml.add(s, t, KNIGHT);
                } else {
                    ml.add(s, t, 0, 0);
                }
            } else if (t == p.ep && !p.b[t]) {
                ml.add(s, t, 0, 1);
            }
        }
    }

    uint64_t kn = p.bb[us][KNIGHT];
    while (kn) {
        const int s = __builtin_ctzll(kn);
        kn &= kn - 1;
        uint64_t t = knightAtt[s] & ~p.occ[us];
        while (t) {
            const int to = __builtin_ctzll(t);
            t &= t - 1;
            ml.add(s, to, 0, 0);
        }
    }

    static const int diagRay[4] = {1, 3, 5, 7};
    static const int orthRay[4] = {0, 2, 4, 6};
    // Direction deltas in (file, rank); ray index order matches rayAtt.
    static const int dFile[8] = {0, 1, 1, 1, 0, -1, -1, -1};
    static const int dRank[8] = {1, 1, 0, -1, -1, -1, 0, 1};
    for (int piece = 0; piece < 2; ++piece) {
        uint64_t sl = piece == 0 ? (p.bb[us][BISHOP] | p.bb[us][QUEEN])
                                 : (p.bb[us][ROOK] | p.bb[us][QUEEN]);
        const int* rays = piece == 0 ? diagRay : orthRay;
        while (sl) {
            const int s = __builtin_ctzll(sl);
            sl &= sl - 1;
            for (int i = 0; i < 4; ++i) {
                const int d = rays[i];
                int f = file_of(s) + dFile[d];
                int r = rank_of(s) + dRank[d];
                while (f >= 0 && f < 8 && r >= 0 && r < 8) {
                    const int to = r * 8 + f;
                    if (p.b[to]) {
                        if (enemy & bit(to)) ml.add(s, to, 0, 0);
                        break;
                    }
                    ml.add(s, to, 0, 0);
                    f += dFile[d];
                    r += dRank[d];
                }
            }
        }
    }

    {
        const int s = p.kingSq[us];
        uint64_t t = kingAtt[s] & ~p.occ[us];
        while (t) {
            const int to = __builtin_ctzll(t);
            t &= t - 1;
            ml.add(s, to, 0, 0);
        }
        if (us == WHITE) {
            if ((p.castling & 1) && !p.b[5] && !p.b[6] && p.b[4] == KING && p.b[7] == ROOK &&
                !attacked(p, 4, BLACK) && !attacked(p, 5, BLACK) && !attacked(p, 6, BLACK))
                ml.add(4, 6, 0, 2);
            if ((p.castling & 2) && !p.b[3] && !p.b[2] && !p.b[1] && p.b[4] == KING &&
                p.b[0] == ROOK && !attacked(p, 4, BLACK) && !attacked(p, 3, BLACK) &&
                !attacked(p, 2, BLACK))
                ml.add(4, 2, 0, 2);
        } else {
            if ((p.castling & 4) && !p.b[61] && !p.b[62] && p.b[60] == -KING && p.b[63] == -ROOK &&
                !attacked(p, 60, WHITE) && !attacked(p, 61, WHITE) && !attacked(p, 62, WHITE))
                ml.add(60, 62, 0, 2);
            if ((p.castling & 8) && !p.b[59] && !p.b[58] && !p.b[57] && p.b[60] == -KING &&
                p.b[56] == -ROOK && !attacked(p, 60, WHITE) && !attacked(p, 59, WHITE) &&
                !attacked(p, 58, WHITE))
                ml.add(60, 58, 0, 2);
        }
    }
}

inline void make_move(Pos& p, const Move& m, Undo& u) {
    u.castling = p.castling;
    u.ep = p.ep;
    u.halfmove = p.halfmove;
    u.key = p.key;
    u.captured = 0;
    u.capturedSq = -1;

    const int us = p.side, them = 1 - us;
    const int from = m.from, to = m.to;

    if (m.flags & 1) {
        const int capSq = us == WHITE ? to - 8 : to + 8;
        u.captured = PAWN;
        u.capturedSq = capSq;
        remove_piece(p, capSq);
    } else if (p.b[to]) {
        const int8_t v = p.b[to];
        u.captured = v > 0 ? v : -v;
        u.capturedSq = to;
        remove_piece(p, to);
    }

    const int8_t moving = p.b[from];
    const int type = moving > 0 ? moving : -moving;
    remove_piece(p, from);
    put_piece(p, to, us, m.promo ? m.promo : type);

    if (m.flags & 2) {
        if (to == 6) { remove_piece(p, 7); put_piece(p, 5, WHITE, ROOK); }
        else if (to == 2) { remove_piece(p, 0); put_piece(p, 3, WHITE, ROOK); }
        else if (to == 62) { remove_piece(p, 63); put_piece(p, 61, BLACK, ROOK); }
        else if (to == 58) { remove_piece(p, 56); put_piece(p, 59, BLACK, ROOK); }
    }

    if (from == 4 || to == 4) p.castling &= ~3;
    if (from == 7 || to == 7) p.castling &= ~1;
    if (from == 0 || to == 0) p.castling &= ~2;
    if (from == 60 || to == 60) p.castling &= ~12;
    if (from == 63 || to == 63) p.castling &= ~4;
    if (from == 56 || to == 56) p.castling &= ~8;

    if (m.flags & 4) p.ep = us == WHITE ? from + 8 : from - 8;
    else p.ep = -1;

    p.halfmove = (type == PAWN || u.captured) ? 0 : u.halfmove + 1;

    p.side = them;
    // The key is only used to label positions in evidence output, so a full
    // recompute is correct and costs nothing that matters at verifier volumes.
    p.key = compute_key(p);
}

inline void unmake_move(Pos& p, const Move& m, const Undo& u) {
    const int us = 1 - p.side;
    const int from = m.from, to = m.to;
    const int8_t moved = p.b[to];
    // A promotion moved a PAWN from `from`; the promoted piece on `to` must not
    // be carried back, or the pawn reappears as a queen/rook/bishop/knight.
    const int type = m.promo ? PAWN : (moved > 0 ? moved : -moved);
    remove_piece(p, to);
    put_piece(p, from, us, type);
    if (m.flags & 2) {
        if (to == 6) { remove_piece(p, 5); put_piece(p, 7, WHITE, ROOK); }
        else if (to == 2) { remove_piece(p, 3); put_piece(p, 0, WHITE, ROOK); }
        else if (to == 62) { remove_piece(p, 61); put_piece(p, 63, BLACK, ROOK); }
        else if (to == 58) { remove_piece(p, 59); put_piece(p, 56, BLACK, ROOK); }
    }
    if (u.captured) put_piece(p, u.capturedSq, 1 - us, u.captured);
    p.castling = u.castling;
    p.ep = u.ep;
    p.halfmove = u.halfmove;
    p.key = u.key;
    p.side = us;
}

// ---------------------------------------------------------------- search
struct SearchCtx {
    uint64_t nodes = 0;
    uint64_t nodeCap = 4000000;
    std::chrono::steady_clock::time_point deadline;
    bool aborted = false;
    std::vector<uint64_t> path;
};

// Transposition table. Mate scores are stored relative to the NODE (distance
// from this node to the mate) rather than to the root, and converted on the way
// in and out. Storing a root-relative score and reading it at another ply is the
// classic way to invent a mate distance that is off by an arbitrary amount, and
// this verifier's entire output is a mate distance.
struct TTEntry {
    uint64_t key = 0;
    int16_t value = 0;
    int16_t depth = -1;
    bool valid = false;
};

constexpr size_t TT_BITS = 22;  // 4M entries
constexpr size_t TT_SIZE = 1ULL << TT_BITS;
std::vector<TTEntry> tt;

inline size_t ttIndex(uint64_t key) { return static_cast<size_t>(key) & (TT_SIZE - 1); }

// +-(MATE - d) where d is plies from the root -> +-(MATE - (d - ply))
inline int ttStore(int score, int ply) {
    if (score >= MATE - 255) return score + ply;
    if (score <= -(MATE - 255)) return score - ply;
    return score;
}

inline int ttLoad(int score, int ply) {
    if (score >= MATE - 255) return score - ply;
    if (score <= -(MATE - 255)) return score + ply;
    return score;
}

// Exact minimax over `depth` remaining plies. Value: +-(MATE - ply) when a
// forced mate is delivered at `ply`, 0 when neither side forces mate inside the
// horizon. Full width, no reductions and no pruning, so the returned mate
// distance is the game-theoretic DTM whenever that DTM is <= depth.
//
// SEMANTICS: this is standard DTM. It ignores the fifty-move rule and ignores
// threefold repetition. That is deliberate, for two reasons:
//   * the ground truth it is validated against (retrograde tables) uses the same
//     state space, so the two are comparable;
//   * a value that depends on the path taken cannot be cached, and without a
//     cache a 31-ply KRvK verification does not finish.
// A label graded here therefore means "a forced mate in exactly this many
// plies exists", not "and the game would not be drawn first".
//
// The table is only consulted when the stored search was at least as deep as
// the current one. Entries are exact, so no bound flags are stored.
int nega(Pos& p, int depth, int ply, SearchCtx& ctx) {
    if (ctx.aborted) return 0;
    if (++ctx.nodes > ctx.nodeCap) { ctx.aborted = true; return 0; }
    if ((ctx.nodes & 2047) == 0 && std::chrono::steady_clock::now() > ctx.deadline) {
        ctx.aborted = true;
        return 0;
    }

    const size_t slot = ttIndex(p.key);
    if (tt[slot].valid && tt[slot].key == p.key && tt[slot].depth >= depth) {
        return ttLoad(tt[slot].value, ply);
    }

    const bool check = in_check(p, p.side);
    MoveList ml;
    gen_pseudo(p, ml);

    // Horizon: with no plies left, report only what is on the board now --
    // checkmate or stalemate -- and value everything else as "no mate proven".
    // Mate at distance d is found at horizon d because the node where the mate
    // lands is reached with depth 0 and returns its terminal value there.
    int legal = 0;
    int best = -INF;
    Undo u;
    for (int i = 0; i < ml.n; ++i) {
        const Move m = ml.m[i];
        make_move(p, m, u);
        if (in_check(p, 1 - p.side)) { unmake_move(p, m, u); continue; }
        ++legal;
        if (depth <= 0) { unmake_move(p, m, u); continue; }
        const int score = -nega(p, depth - 1, ply + 1, ctx);
        unmake_move(p, m, u);
        if (ctx.aborted) return 0;
        if (score > best) best = score;
    }

    if (legal == 0) return check ? -(MATE - ply) : 0;
    if (depth <= 0) return 0;
    if (best == -INF) return 0;

    if (!(tt[slot].valid && tt[slot].key == p.key && tt[slot].depth > depth)) {
        tt[slot].key = p.key;
        tt[slot].value = static_cast<int16_t>(ttStore(best, ply));
        tt[slot].depth = static_cast<int16_t>(depth);
        tt[slot].valid = true;
    }
    return best;
}

// ---------------------------------------------------------------- FEN
bool parse_fen(const std::string& fen, Pos& p, std::string& err) {
    clear_pos(p);
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
    const std::string& bd = f[0];
    int rank = 7, file = 0;
    for (char c : bd) {
        if (c == '/') {
            if (file != 8 || rank == 0) { err = "bad rank width"; return false; }
            --rank;
            file = 0;
        } else if (c >= '1' && c <= '8') {
            file += c - '0';
            if (file > 8) { err = "rank overflow"; return false; }
        } else {
            int color, type;
            switch (c) {
                case 'P': color = WHITE; type = PAWN; break;
                case 'N': color = WHITE; type = KNIGHT; break;
                case 'B': color = WHITE; type = BISHOP; break;
                case 'R': color = WHITE; type = ROOK; break;
                case 'Q': color = WHITE; type = QUEEN; break;
                case 'K': color = WHITE; type = KING; break;
                case 'p': color = BLACK; type = PAWN; break;
                case 'n': color = BLACK; type = KNIGHT; break;
                case 'b': color = BLACK; type = BISHOP; break;
                case 'r': color = BLACK; type = ROOK; break;
                case 'q': color = BLACK; type = QUEEN; break;
                case 'k': color = BLACK; type = KING; break;
                default: err = "bad piece char"; return false;
            }
            if (file > 7) { err = "rank overflow"; return false; }
            put_piece(p, rank * 8 + file, color, type);
            ++file;
        }
    }
    if (rank != 0 || file != 8) { err = "missing ranks"; return false; }
    if (p.kingSq[WHITE] < 0 || p.kingSq[BLACK] < 0) { err = "missing king"; return false; }
    if (f[1] != "w" && f[1] != "b") { err = "bad side"; return false; }
    p.side = (f[1] == "w") ? WHITE : BLACK;
    for (char c : f[2]) {
        if (c == 'K') p.castling |= 1;
        else if (c == 'Q') p.castling |= 2;
        else if (c == 'k') p.castling |= 4;
        else if (c == 'q') p.castling |= 8;
        else if (c != '-') { err = "bad castling"; return false; }
    }
    if (f[3] != "-") {
        if (f[3].size() != 2) { err = "bad ep"; return false; }
        const int fl = f[3][0] - 'a', rk = f[3][1] - '1';
        if (fl < 0 || fl > 7 || rk < 0 || rk > 7) { err = "bad ep"; return false; }
        p.ep = rk * 8 + fl;
    }
    p.halfmove = f.size() > 4 ? std::atoi(f[4].c_str()) : 0;
    p.key = compute_key(p);
    if (in_check(p, 1 - p.side)) { err = "side not to move is in check"; return false; }
    return true;
}

uint64_t perft(Pos& p, int depth) {
    if (depth == 0) return 1;
    MoveList ml;
    gen_pseudo(p, ml);
    uint64_t total = 0;
    Undo u;
    for (int i = 0; i < ml.n; ++i) {
        const Move m = ml.m[i];
        make_move(p, m, u);
        if (in_check(p, 1 - p.side)) { unmake_move(p, m, u); continue; }
        total += perft(p, depth - 1);
        unmake_move(p, m, u);
    }
    return total;
}

std::string json_escape(const std::string& s) {
    std::string o;
    for (char c : s) {
        if (c == '"' || c == '\\') { o.push_back('\\'); o.push_back(c); }
        else o.push_back(c);
    }
    return o;
}

const char* color_name(int c) { return c == WHITE ? "white" : "black"; }

inline int mateDistance(int v) {  // plies from root; 0 = mate at root
    const int a = std::abs(v);
    return a >= MATE - 255 ? MATE - a : -1;  // -1 = no mate
}

struct Verdict {
    std::string status;     // CORRECT / WRONG / INCONCLUSIVE / BADFEN
    std::string direction;  // over / under / none
    int dtmPlies = 0;
    int errorMoves = 0;
    int attacker = -1;      // resolved from the sign of the exact score
    std::string detail;
};

Verdict verify(Pos& p, int claimed, uint64_t nodeCap, double timeLimitSec) {
    Verdict v;
    const int N = std::abs(claimed);
    if (N <= 0) { v.status = "INCONCLUSIVE"; v.detail = "claimed mate 0"; return v; }
    const int expected = claimed > 0 ? 2 * N - 1 : 2 * N;

    // Exact DTM by iterative deepening. The first horizon at which a mate
    // appears yields the exact distance, because every shallower horizon proved
    // that no faster mate exists. Deepening rather than single-shot matters here:
    // the label may be wrong in EITHER direction, and only an exact distance
    // says which.
    SearchCtx ctx;
    ctx.nodeCap = nodeCap;
    ctx.deadline = std::chrono::steady_clock::now() +
                   std::chrono::milliseconds(static_cast<long long>(timeLimitSec * 1000));

    const int cap = expected + 12;
    int found = 0;   // signed plies; 0 = none yet
    for (int d = 1; d <= cap; ++d) {
        const int val = nega(p, d, 0, ctx);
        if (ctx.aborted) break;
        // The search returns +-(MATE - pliesToMate); convert to a signed ply count.
        const int d2 = mateDistance(val);
        if (d2 >= 0) {
            found = val > 0 ? d2 : -d2;
            break;
        }
    }

    if (ctx.aborted && found == 0) {
        v.status = "INCONCLUSIVE";
        v.detail = "node/time cap at depth " + std::to_string(cap) + " (" +
                   std::to_string(ctx.nodes) + " nodes)";
        return v;
    }

    if (found == 0) {
        v.status = "WRONG";
        v.direction = "none";
        v.dtmPlies = 0;
        v.errorMoves = 0;
        v.detail = "no forced mate within " + std::to_string(cap) + " plies";
        return v;
    }

    const int dist = std::abs(found);
    const bool attackerIsStm = found > 0;
    const int signedPlies = attackerIsStm ? dist : -dist;
    v.dtmPlies = signedPlies;
    v.attacker = attackerIsStm ? p.side : 1 - p.side;

    const bool labelPositive = claimed > 0;
    if (attackerIsStm != labelPositive) {
        v.status = "WRONG";
        v.direction = "none";
        v.errorMoves = 0;
        v.detail = std::string("attacker is ") + color_name(v.attacker) + " (from the sign of the "
                   "exact score), label says " + color_name(labelPositive ? p.side : 1 - p.side);
        return v;
    }

    if (dist == expected) {
        v.status = "CORRECT";
        v.direction = "none";
        v.detail = "exact DTM is " + std::to_string(dist) + " plies, label implies " +
                   std::to_string(expected);
        return v;
    }

    const int trueMoves = attackerIsStm ? (dist + 1) / 2 : dist / 2;
    v.status = "WRONG";
    v.errorMoves = N - trueMoves;
    v.direction = v.errorMoves > 0 ? "over" : "under";
    v.detail = "exact DTM is mate in " + std::to_string(trueMoves) + " (" + std::to_string(dist) +
               " plies), label says " + std::to_string(N);
    return v;
}

}  // namespace

int main(int argc, char** argv) {
    init_tables();
    init_zobrist();
    tt.assign(TT_SIZE, TTEntry{});

    const std::string mode = argc > 1 ? argv[1] : "--help";

    if (mode == "--perft") {
        if (argc < 4) { std::fprintf(stderr, "usage: --perft N FEN\n"); return 2; }
        Pos p;
        std::string err;
        if (!parse_fen(argv[3], p, err)) { std::fprintf(stderr, "BADFEN\t%s\n", err.c_str()); return 2; }
        std::printf("%llu\n", static_cast<unsigned long long>(perft(p, std::atoi(argv[2]))));
        return 0;
    }

    if (mode == "--one") {
        if (argc < 4) { std::fprintf(stderr, "usage: --one FEN N\n"); return 2; }
        Pos p;
        std::string err;
        if (!parse_fen(argv[2], p, err)) {
            std::printf("{\"status\":\"BADFEN\",\"detail\":\"%s\"}\n", json_escape(err).c_str());
            return 2;
        }
        const int claimed = std::atoi(argv[3]);
        const Verdict v = verify(p, claimed, 40000000ULL, 180.0);
        const int attacker = v.attacker >= 0 ? v.attacker : p.side;
        std::printf("{\"status\":\"%s\",\"direction\":\"%s\",\"claimed\":%d,\"attacker\":\"%s\","
                    "\"attacker_from\":\"sign_of_exact_score\",\"stm\":\"%s\",\"dtm_plies\":%d,"
                    "\"error_moves\":%d,\"detail\":\"%s\"}\n",
                    v.status.c_str(), v.direction.c_str(), claimed, color_name(attacker),
                    color_name(p.side), v.dtmPlies, v.errorMoves, json_escape(v.detail).c_str());
        return v.status == "CORRECT" ? 0 : 1;
    }

    if (mode == "--batch") {
        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;
            std::vector<std::string> f;
            std::string cur;
            for (char c : line) {
                if (c == '\t') { f.push_back(cur); cur.clear(); }
                else cur.push_back(c);
            }
            f.push_back(cur);
            if (f.size() < 2) continue;
            Pos p;
            std::string err;
            const std::string meta = f.size() > 2 ? f[2] : "";
            if (!parse_fen(f[0], p, err)) {
                std::printf("{\"fen\":\"%s\",\"status\":\"BADFEN\",\"detail\":\"%s\",\"meta\":\"%s\"}\n",
                            json_escape(f[0]).c_str(), json_escape(err).c_str(), json_escape(meta).c_str());
                std::fflush(stdout);
                continue;
            }
            const int claimed = std::atoi(f[1].c_str());
            const Verdict v = verify(p, claimed, 40000000ULL, 90.0);
            const int attacker = v.attacker >= 0 ? v.attacker : p.side;
            std::printf("{\"fen\":\"%s\",\"claimed\":%d,\"attacker\":\"%s\",\"stm\":\"%s\","
                        "\"status\":\"%s\",\"direction\":\"%s\",\"dtm_plies\":%d,"
                        "\"error_moves\":%d,\"detail\":\"%s\",\"meta\":\"%s\"}\n",
                        json_escape(f[0]).c_str(), claimed, color_name(attacker),
                        color_name(p.side), v.status.c_str(), v.direction.c_str(), v.dtmPlies,
                        v.errorMoves, json_escape(v.detail).c_str(), json_escape(meta).c_str());
            std::fflush(stdout);
        }
        return 0;
    }

    std::fprintf(stderr,
                 "mateverify -- independent exhaustive mate verifier\n"
                 "  --perft N FEN        node count (movegen validation)\n"
                 "  --one FEN N          verify one claimed mate distance\n"
                 "  --batch              FEN<TAB>N<TAB>meta lines on stdin -> JSONL\n");
    return 2;
}
