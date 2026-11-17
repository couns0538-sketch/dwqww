// Independent mate oracle for the matelabels audit.
//
// Deliberately shares no code with forge: own mailbox board, own move
// generator, own attack detection, own search. Validated by perft against
// published values (see selftest.md) and against known mate problems.
//
// Query protocol (one query per stdin line):
//     <id> <mode> <plies> <deadline_ms> <fen...>
//   mode = win  : can the side to move force mate within <plies> plies?
//          loss : can the side to move be forced to be mated within <plies> plies?
//          dist : exact signed distance in plies (positive = side to move mates)
// Output: one JSON object per line on stdout.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

using u64 = std::uint64_t;

enum : int { EMPTY = 0, PAWN = 1, KNIGHT = 2, BISHOP = 3, ROOK = 4, QUEEN = 5, KING = 6 };
enum : int { WHITE = 0, BLACK = 1 };

inline int color_of(int piece) { return piece >= 9 ? BLACK : WHITE; }
inline int type_of(int piece) { return piece >= 9 ? piece - 8 : piece; }

// ---- board ----
struct Board {
    int sq[64];
    int side;
    int castling;      // 1 = WK, 2 = WQ, 4 = BK, 8 = BQ
    int ep;            // -1 or square
    int halfmove;
    int fullmove;

    bool in_check() const;
    bool attacked(int target, int by) const;
    bool king_square(int by, int& out) const;
};

struct Undo {
    int ep;
    int castling;
    int halfmove;
    int captured;
    int captured_sq;
};

// ---- move ----
struct Move {
    int from, to, promo, flags;  // flags: 1 ep, 2 castle, 4 double push
};

const char* piece_char = ".PNBRQK..pnbrqk";
inline int char_piece(char c) {
    switch (c) {
        case 'P': return PAWN; case 'N': return KNIGHT; case 'B': return BISHOP;
        case 'R': return ROOK; case 'Q': return QUEEN; case 'K': return KING;
        case 'p': return PAWN + 8; case 'n': return KNIGHT + 8; case 'b': return BISHOP + 8;
        case 'r': return ROOK + 8; case 'q': return QUEEN + 8; case 'k': return KING + 8;
        default: return EMPTY;
    }
}

inline int file_of(int s) { return s & 7; }
inline int rank_of(int s) { return s >> 3; }

const int knight_d[8][2] = {{1,2},{2,1},{2,-1},{1,-2},{-1,-2},{-2,-1},{-2,1},{-1,2}};
const int king_d[8][2] = {{1,0},{1,1},{0,1},{-1,1},{-1,0},{-1,-1},{0,-1},{1,-1}};
const int bishop_d[4][2] = {{1,1},{1,-1},{-1,1},{-1,-1}};
const int rook_d[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
const int queen_d[8][2] = {{1,1},{1,-1},{-1,1},{-1,-1},{1,0},{-1,0},{0,1},{0,-1}};

bool Board::king_square(int by, int& out) const {
    const int target = KING + (by == BLACK ? 8 : 0);
    for (int s = 0; s < 64; ++s) {
        if (sq[s] == target) { out = s; return true; }
    }
    return false;
}

bool Board::attacked(int target, int by) const {
    const int tf = file_of(target), tr = rank_of(target);
    // pawns
    if (by == WHITE) {
        if (tr > 0) {
            if (tf > 0 && sq[target - 9] == PAWN) return true;
            if (tf < 7 && sq[target - 7] == PAWN) return true;
        }
    } else {
        if (tr < 7) {
            if (tf > 0 && sq[target + 7] == PAWN + 8) return true;
            if (tf < 7 && sq[target + 9] == PAWN + 8) return true;
        }
    }
    const int kn = KNIGHT + (by == BLACK ? 8 : 0);
    for (auto& d : knight_d) {
        const int f = tf + d[0], r = tr + d[1];
        if (f >= 0 && f < 8 && r >= 0 && r < 8 && sq[r * 8 + f] == kn) return true;
    }
    const int kg = KING + (by == BLACK ? 8 : 0);
    for (auto& d : king_d) {
        const int f = tf + d[0], r = tr + d[1];
        if (f >= 0 && f < 8 && r >= 0 && r < 8 && sq[r * 8 + f] == kg) return true;
    }
    const int bi = BISHOP + (by == BLACK ? 8 : 0);
    const int qu = QUEEN + (by == BLACK ? 8 : 0);
    const int ro = ROOK + (by == BLACK ? 8 : 0);
    for (auto& d : bishop_d) {
        int f = tf + d[0], r = tr + d[1];
        while (f >= 0 && f < 8 && r >= 0 && r < 8) {
            const int p = sq[r * 8 + f];
            if (p != EMPTY) {
                if (p == bi || p == qu) return true;
                break;
            }
            f += d[0]; r += d[1];
        }
    }
    for (auto& d : rook_d) {
        int f = tf + d[0], r = tr + d[1];
        while (f >= 0 && f < 8 && r >= 0 && r < 8) {
            const int p = sq[r * 8 + f];
            if (p != EMPTY) {
                if (p == ro || p == qu) return true;
                break;
            }
            f += d[0]; r += d[1];
        }
    }
    return false;
}

bool Board::in_check() const {
    int ks;
    if (!king_square(side, ks)) return false;
    return attacked(ks, side ^ 1);
}

// ---- FEN ----
bool set_fen(Board& b, const std::string& fen, std::string& err) {
    std::memset(b.sq, 0, sizeof(b.sq));
    b.castling = 0; b.ep = -1; b.halfmove = 0; b.fullmove = 1; b.side = WHITE;
    std::vector<std::string> fields;
    std::string cur;
    for (char c : fen) {
        if (c == ' ') { if (!cur.empty()) { fields.push_back(cur); cur.clear(); } }
        else cur.push_back(c);
    }
    if (!cur.empty()) fields.push_back(cur);
    if (fields.size() < 4) { err = "too few fields"; return false; }
    int rank = 7, file = 0;
    for (char c : fields[0]) {
        if (c == '/') {
            if (file != 8) { err = "bad rank width"; return false; }
            --rank; file = 0;
            if (rank < 0) { err = "too many ranks"; return false; }
        } else if (c >= '1' && c <= '8') {
            file += c - '0';
            if (file > 8) { err = "rank overflow"; return false; }
        } else {
            const int p = char_piece(c);
            if (p == EMPTY) { err = "bad piece char"; return false; }
            if (file > 7 || rank < 0) { err = "placement overflow"; return false; }
            b.sq[rank * 8 + file] = p;
            ++file;
        }
    }
    if (rank != 0 || file != 8) { err = "incomplete board"; return false; }
    b.side = (fields[1] == "b") ? BLACK : WHITE;
    for (char c : fields[2]) {
        if (c == 'K') b.castling |= 1;
        else if (c == 'Q') b.castling |= 2;
        else if (c == 'k') b.castling |= 4;
        else if (c == 'q') b.castling |= 8;
    }
    if (fields[3] != "-") {
        if (fields[3].size() != 2) { err = "bad ep"; return false; }
        b.ep = (fields[3][1] - '1') * 8 + (fields[3][0] - 'a');
    }
    if (fields.size() > 4) b.halfmove = std::atoi(fields[4].c_str());
    if (fields.size() > 5) b.fullmove = std::atoi(fields[5].c_str());
    // king presence
    int dummy;
    if (!b.king_square(WHITE, dummy) || !b.king_square(BLACK, dummy)) {
        err = "missing king"; return false;
    }
    return true;
}

// ---- move generation ----
void add_pawn_moves(const Board& b, int from, std::vector<Move>& out) {
    const int c = b.side;
    const int dir = (c == WHITE) ? 8 : -8;
    const int start_rank = (c == WHITE) ? 1 : 6;
    const int promo_rank = (c == WHITE) ? 6 : 1;
    const int f = file_of(from), r = rank_of(from);
    auto push = [&](int to, int flags) {
        const int target_rank = rank_of(to);
        if (target_rank == (promo_rank + (c == WHITE ? 1 : -1))) {
            for (int p : {QUEEN, ROOK, BISHOP, KNIGHT}) {
                out.push_back({from, to, p + (c == BLACK ? 8 : 0), flags});
            }
        } else {
            out.push_back({from, to, 0, flags});
        }
    };
    const int one = from + dir;
    if (one >= 0 && one < 64 && b.sq[one] == EMPTY) {
        push(one, 0);
        if (r == start_rank) {
            const int two = from + 2 * dir;
            if (b.sq[two] == EMPTY) out.push_back({from, two, 0, 4});
        }
    }
    for (int df : {-1, 1}) {
        const int nf = f + df;
        if (nf < 0 || nf > 7) continue;
        const int to = (r + (c == WHITE ? 1 : -1)) * 8 + nf;
        if (to < 0 || to > 63) continue;
        if (b.sq[to] != EMPTY && color_of(b.sq[to]) != c) push(to, 0);
        else if (b.sq[to] == EMPTY && to == b.ep) out.push_back({from, to, 0, 1});
    }
}

void gen_pseudo(const Board& b, std::vector<Move>& out) {
    out.clear();
    const int c = b.side;
    for (int s = 0; s < 64; ++s) {
        const int p = b.sq[s];
        if (p == EMPTY || color_of(p) != c) continue;
        const int t = type_of(p);
        const int f = file_of(s), r = rank_of(s);
        switch (t) {
            case PAWN: add_pawn_moves(b, s, out); break;
            case KNIGHT:
                for (auto& d : knight_d) {
                    const int nf = f + d[0], nr = r + d[1];
                    if (nf < 0 || nf > 7 || nr < 0 || nr > 7) continue;
                    const int to = nr * 8 + nf;
                    if (b.sq[to] == EMPTY || color_of(b.sq[to]) != c) out.push_back({s, to, 0, 0});
                }
                break;
            case BISHOP: case ROOK: case QUEEN: {
                const int(*dirs)[2];
                int nd;
                if (t == BISHOP) { dirs = bishop_d; nd = 4; }
                else if (t == ROOK) { dirs = rook_d; nd = 4; }
                else { dirs = queen_d; nd = 8; }
                for (int k = 0; k < nd; ++k) {
                    int nf = f + dirs[k][0], nr = r + dirs[k][1];
                    while (nf >= 0 && nf < 8 && nr >= 0 && nr < 8) {
                        const int to = nr * 8 + nf;
                        if (b.sq[to] == EMPTY) out.push_back({s, to, 0, 0});
                        else {
                            if (color_of(b.sq[to]) != c) out.push_back({s, to, 0, 0});
                            break;
                        }
                        nf += dirs[k][0]; nr += dirs[k][1];
                    }
                }
                break;
            }
            case KING:
                for (auto& d : king_d) {
                    const int nf = f + d[0], nr = r + d[1];
                    if (nf < 0 || nf > 7 || nr < 0 || nr > 7) continue;
                    const int to = nr * 8 + nf;
                    if (b.sq[to] == EMPTY || color_of(b.sq[to]) != c) out.push_back({s, to, 0, 0});
                }
                // castling
                if (c == WHITE && s == 4) {
                    if ((b.castling & 1) && b.sq[5] == EMPTY && b.sq[6] == EMPTY &&
                        b.sq[7] == ROOK) out.push_back({4, 6, 0, 2});
                    if ((b.castling & 2) && b.sq[3] == EMPTY && b.sq[2] == EMPTY && b.sq[1] == EMPTY &&
                        b.sq[0] == ROOK) out.push_back({4, 2, 0, 2});
                } else if (c == BLACK && s == 60) {
                    if ((b.castling & 4) && b.sq[61] == EMPTY && b.sq[62] == EMPTY &&
                        b.sq[63] == ROOK + 8) out.push_back({60, 62, 0, 2});
                    if ((b.castling & 8) && b.sq[59] == EMPTY && b.sq[58] == EMPTY && b.sq[57] == EMPTY &&
                        b.sq[56] == ROOK + 8) out.push_back({60, 58, 0, 2});
                }
                break;
            default: break;
        }
    }
}

void make_move(Board& b, const Move& m, Undo& u) {
    u.ep = b.ep; u.castling = b.castling; u.halfmove = b.halfmove;
    const int p = b.sq[m.from];
    const int c = color_of(p);
    u.captured_sq = m.to;
    u.captured = b.sq[m.to];
    if (m.flags & 1) {  // en passant capture
        u.captured_sq = (c == WHITE) ? m.to - 8 : m.to + 8;
        u.captured = b.sq[u.captured_sq];
        b.sq[u.captured_sq] = EMPTY;
    }
    b.sq[m.to] = (m.promo != 0) ? m.promo : p;
    b.sq[m.from] = EMPTY;
    if (m.flags & 2) {  // castle: move the rook
        if (m.to == 6)       { b.sq[5] = b.sq[7];  b.sq[7] = EMPTY; }
        else if (m.to == 2)  { b.sq[3] = b.sq[0];  b.sq[0] = EMPTY; }
        else if (m.to == 62) { b.sq[61] = b.sq[63]; b.sq[63] = EMPTY; }
        else if (m.to == 58) { b.sq[59] = b.sq[56]; b.sq[56] = EMPTY; }
    }
    if (type_of(p) == KING) {
        b.castling &= (c == WHITE) ? ~3 : ~12;
    }
    if (m.from == 0 || m.to == 0) b.castling &= ~2;
    if (m.from == 7 || m.to == 7) b.castling &= ~1;
    if (m.from == 56 || m.to == 56) b.castling &= ~8;
    if (m.from == 63 || m.to == 63) b.castling &= ~4;
    b.ep = (m.flags & 4) ? ((c == WHITE) ? m.from + 8 : m.from - 8) : -1;
    b.halfmove = (type_of(p) == PAWN || u.captured != EMPTY) ? 0 : b.halfmove + 1;
    b.side ^= 1;
    if (c == BLACK) ++b.fullmove;
}

void unmake_move(Board& b, const Move& m, const Undo& u) {
    b.side ^= 1;
    const int c = b.side;
    const int moved = b.sq[m.to];
    b.sq[m.from] = (m.promo != 0) ? (PAWN + (c == BLACK ? 8 : 0)) : moved;
    b.sq[m.to] = EMPTY;
    if (m.flags & 1) b.sq[u.captured_sq] = u.captured;
    else if (u.captured != EMPTY) b.sq[m.to] = u.captured;
    if (m.flags & 2) {
        if (m.to == 6)       { b.sq[7] = b.sq[5];  b.sq[5] = EMPTY; }
        else if (m.to == 2)  { b.sq[0] = b.sq[3];  b.sq[3] = EMPTY; }
        else if (m.to == 62) { b.sq[63] = b.sq[61]; b.sq[61] = EMPTY; }
        else if (m.to == 58) { b.sq[56] = b.sq[59]; b.sq[59] = EMPTY; }
    }
    b.ep = u.ep; b.castling = u.castling; b.halfmove = u.halfmove;
    if (c == BLACK) --b.fullmove;
}

bool move_is_legal(Board& b, const Move& m) {
    // castling legality: king must not be in check, nor cross an attacked square
    if (m.flags & 2) {
        const int c = b.side;
        if (b.attacked(m.from, c ^ 1)) return false;
        const int step = (m.to > m.from) ? 1 : -1;
        int s = m.from + step;
        while (true) {
            if (b.attacked(s, c ^ 1)) return false;
            if (s == m.to) break;
            s += step;
        }
    }
    Undo u;
    make_move(b, m, u);
    int ks;
    const bool ok = !(b.king_square(b.side ^ 1, ks) && b.attacked(ks, b.side));
    unmake_move(b, m, u);
    return ok;
}

int legal_moves(Board& b, std::vector<Move>& out) {
    std::vector<Move> pseudo;
    gen_pseudo(b, pseudo);
    out.clear();
    for (const auto& m : pseudo) {
        if (move_is_legal(b, m)) out.push_back(m);
    }
    return static_cast<int>(out.size());
}

u64 perft(Board& b, int depth) {
    std::vector<Move> moves;
    legal_moves(b, moves);
    if (depth <= 1) return moves.size();
    u64 total = 0;
    for (const auto& m : moves) {
        Undo u;
        make_move(b, m, u);
        total += perft(b, depth - 1);
        unmake_move(b, m, u);
    }
    return total;
}

// ---- zobrist ----
u64 zob_piece[16][64];
u64 zob_side, zob_castle[16], zob_ep[65];

u64 compute_hash(const Board& b) {
    u64 h = 0;
    for (int s = 0; s < 64; ++s) {
        if (b.sq[s] != EMPTY) h ^= zob_piece[b.sq[s]][s];
    }
    if (b.side == BLACK) h ^= zob_side;
    h ^= zob_castle[b.castling];
    h ^= zob_ep[b.ep < 0 ? 64 : b.ep];
    return h;
}

// ---- mate search ----
struct Search {
    std::unordered_map<u64, bool> memo;
    long long nodes = 0;
    bool timeout = false;
    std::chrono::steady_clock::time_point deadline;

    bool expired() {
        if (timeout) return true;
        if ((nodes & 8191) == 0) {
            if (std::chrono::steady_clock::now() > deadline) timeout = true;
        }
        return timeout;
    }
};

bool win_within(Search& S, Board& b, int k);

// Does move m let the side that just moved force mate within the remaining budget?
bool all_replies_mate(Search& S, Board& b, int k) {
    // b: opponent (defender) to move. k = plies remaining including the mover's
    // move that got us here. The defender spends one ply, so the attacker has k-2.
    if (k < 2) return false;
    std::vector<Move> moves;
    legal_moves(b, moves);
    for (const auto& r : moves) {
        Undo u;
        make_move(b, r, u);
        const bool ok = win_within(S, b, k - 2);
        unmake_move(b, r, u);
        if (S.timeout) return false;
        if (!ok) return false;
    }
    return true;
}

bool win_within(Search& S, Board& b, int k) {
    if (k <= 0) return false;
    if (S.expired()) return false;
    const u64 key = compute_hash(b) ^ (static_cast<u64>(k) * 0x9E3779B97F4A7C15ULL);
    auto it = S.memo.find(key);
    if (it != S.memo.end()) return it->second;
    ++S.nodes;

    std::vector<Move> moves;
    legal_moves(b, moves);
    bool result = false;
    for (const auto& m : moves) {
        Undo u;
        make_move(b, m, u);
        bool ok = false;
        std::vector<Move> replies;
        const bool defender_has_moves = legal_moves(b, replies) > 0;
        if (!defender_has_moves) {
            ok = b.in_check();  // checkmate only; stalemate is not a win
        } else if (k >= 2) {
            ok = all_replies_mate(S, b, k);
        }
        unmake_move(b, m, u);
        if (S.timeout) return false;
        if (ok) { result = true; break; }
    }
    if (!S.timeout) S.memo[key] = result;
    return result;
}

// Can the side to move be forced to be mated within k plies (i.e. cannot avoid mate)?
bool loss_within(Search& S, Board& b, int k);

// Half (A) with the engine's move pinned: one subtree instead of every root move.
bool win_within_pinned(Search& S, Board& b, int k, const Move& only) {
    if (k <= 0) return false;
    if (S.expired()) return false;
    std::vector<Move> all;
    legal_moves(b, all);
    bool present = false;
    for (const auto& m : all) {
        if (m.from == only.from && m.to == only.to && m.promo == only.promo) { present = true; break; }
    }
    if (!present) return false;
    ++S.nodes;
    Undo u;
    make_move(b, only, u);
    bool ok = false;
    std::vector<Move> replies;
    const bool defender_has_moves = legal_moves(b, replies) > 0;
    if (!defender_has_moves) ok = b.in_check();
    else if (k >= 2) ok = all_replies_mate(S, b, k);
    unmake_move(b, only, u);
    return ok;
}

bool loss_within(Search& S, Board& b, int k) {
    if (S.expired()) return false;
    std::vector<Move> moves;
    legal_moves(b, moves);
    if (moves.empty()) return b.in_check();  // already mated
    if (k <= 0) return false;
    const u64 key = compute_hash(b) ^ (static_cast<u64>(k) * 0xC2B2AE3D27D4EB4FULL) ^ 0x5DEECE66DULL;
    auto it = S.memo.find(key);
    if (it != S.memo.end()) return it->second;
    ++S.nodes;
    for (const auto& r : moves) {
        Undo u;
        make_move(b, r, u);
        const bool ok = win_within(S, b, k - 1);
        unmake_move(b, r, u);
        if (S.timeout) return false;
        if (!ok) { S.memo[key] = false; return false; }
    }
    S.memo[key] = true;
    return true;
}

void init_zobrist() {
    u64 s = 0x246C1F3A5D7B9E01ULL;
    auto next = [&s]() {
        s ^= s << 13; s ^= s >> 7; s ^= s << 17;
        return s;
    };
    for (int p = 0; p < 16; ++p)
        for (int i = 0; i < 64; ++i) zob_piece[p][i] = next();
    zob_side = next();
    for (int i = 0; i < 16; ++i) zob_castle[i] = next();
    for (int i = 0; i < 65; ++i) zob_ep[i] = next();
}

}  // namespace

int main(int argc, char** argv) {
    init_zobrist();
    if (argc >= 4 && std::string(argv[1]) == "perft") {
        Board b;
        std::string err;
        if (!set_fen(b, argv[2], err)) { std::cout << "FEN_ERROR " << err << '\n'; return 2; }
        const int depth = std::stoi(argv[3]);
        const auto t0 = std::chrono::steady_clock::now();
        const u64 n = perft(b, depth);
        const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        std::printf("PERFT %d %llu %.3f\n", depth, static_cast<unsigned long long>(n), secs);
        return 0;
    }
    std::string line;
    // Banner so a caller can prove it is talking to this oracle.
    std::cout << "{\"banner\":\"matelabels-oracle\",\"version\":1}\n";
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        if (line[0] == '#') continue;
        // <id> <mode> <plies> <deadline_ms> <fen...>
        std::size_t p1 = line.find(' ');
        std::size_t p2 = line.find(' ', p1 + 1);
        std::size_t p3 = line.find(' ', p2 + 1);
        std::size_t p4 = line.find(' ', p3 + 1);
        if (p1 == std::string::npos || p2 == std::string::npos || p3 == std::string::npos ||
            p4 == std::string::npos) {
            std::cout << "{\"error\":\"bad request\",\"raw\":\"" << line << "\"}\n" << std::flush;
            continue;
        }
        const std::string id = line.substr(0, p1);
        const std::string mode = line.substr(p1 + 1, p2 - p1 - 1);
        const int plies = std::stoi(line.substr(p2 + 1, p3 - p2 - 1));
        const int deadline_ms = std::stoi(line.substr(p3 + 1, p4 - p3 - 1));
        std::string fen = line.substr(p4 + 1);

        // pinwin carries an extra leading move token before the FEN; strip it
        // HERE so the shared FEN parse below never sees it.
        std::string pin_mv;
        if (mode == "pinwin") {
            const std::size_t sp = fen.find(' ');
            if (sp == std::string::npos) {
                std::cout << "{\"id\":\"" << id << "\",\"error\":\"pinwin needs a move\"}\n" << std::flush;
                continue;
            }
            pin_mv = fen.substr(0, sp);
            fen = fen.substr(sp + 1);
        }

        Board b;
        std::string err;
        if (!set_fen(b, fen, err)) {
            std::cout << "{\"id\":\"" << id << "\",\"error\":\"fen:" << err << "\"}\n" << std::flush;
            continue;
        }
        Search S;
        S.deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(deadline_ms);
        bool value = false;
        if (mode == "win") {
            value = win_within(S, b, plies);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"" << mode << "\",\"plies\":" << plies
                      << ",\"value\":" << (value ? "true" : "false")
                      << ",\"status\":\"" << (S.timeout ? "timeout" : "ok") << "\""
                      << ",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else if (mode == "loss") {
            value = loss_within(S, b, plies);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"" << mode << "\",\"plies\":" << plies
                      << ",\"value\":" << (value ? "true" : "false")
                      << ",\"status\":\"" << (S.timeout ? "timeout" : "ok") << "\""
                      << ",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else if (mode == "dist") {
            // Iterative deepening on odd plies: the first k for which a forced
            // mate exists is the EXACT distance, because "mate within k" true and
            // "mate within k-2" false together pin it to exactly k.
            int found = 0;
            int tested_up_to = 0;
            for (int k = 1; k <= plies; k += 2) {
                if (S.expired()) break;
                tested_up_to = k;
                if (win_within(S, b, k)) { found = k; break; }
            }
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"dist\""
                      << ",\"exact_plies\":" << found
                      << ",\"tested_up_to\":" << tested_up_to
                      << ",\"searched_to\":" << plies
                      << ",\"status\":\"" << (S.timeout ? "timeout" : (found ? "ok" : "no_mate_in_budget")) << "\""
                      << ",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else if (mode == "pinwin") {
            // Half (A): pin the move and prove a forced mate within `plies`.
            const std::string& mv = pin_mv;
            if (mv.size() < 4) {
                std::cout << "{\"id\":\"" << id << "\",\"error\":\"bad move\"}\n" << std::flush;
                continue;
            }
            const int from = (mv[1] - '1') * 8 + (mv[0] - 'a');
            const int to = (mv[3] - '1') * 8 + (mv[2] - 'a');
            int promo = 0;
            if (mv.size() > 4) {
                switch (mv[4]) {
                    case 'q': promo = QUEEN + (b.side == BLACK ? 8 : 0); break;
                    case 'r': promo = ROOK + (b.side == BLACK ? 8 : 0); break;
                    case 'b': promo = BISHOP + (b.side == BLACK ? 8 : 0); break;
                    case 'n': promo = KNIGHT + (b.side == BLACK ? 8 : 0); break;
                    default: break;
                }
            }
            Move pin{from, to, promo, 0};
            // Resolve special flags from the generator so ep/castle are exact.
            std::vector<Move> gen;
            legal_moves(b, gen);
            bool found_move = false;
            for (const auto& g : gen) {
                if (g.from == from && g.to == to && g.promo == promo) { pin = g; found_move = true; break; }
            }
            if (!found_move) {
                std::cout << "{\"id\":\"" << id << "\",\"mode\":\"pinwin\",\"move\":\"" << mv
                          << "\",\"error\":\"illegal_move\"}\n" << std::flush;
                continue;
            }
            const bool ok = win_within_pinned(S, b, plies, pin);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"pinwin\",\"move\":\"" << mv
                      << "\",\"plies\":" << plies
                      << ",\"value\":" << (ok ? "true" : "false")
                      << ",\"status\":\"" << (S.timeout ? "timeout" : "ok") << "\""
                      << ",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else {
            std::cout << "{\"id\":\"" << id << "\",\"error\":\"mode\"}\n" << std::flush;
        }
    }
    return 0;
}
