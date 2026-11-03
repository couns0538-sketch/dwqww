// Original standard-chess state transitions and bounded reachability.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace chain {

enum Piece { Pawn = 1, Knight, Bishop, Rook, Queen, King };
enum Rights { WK = 1, WQ = 2, BK = 4, BQ = 8 };

struct Board {
    std::array<int, 64> squares{};
    int side = 1;
    int rights = 0;
    int ep = -1;
    std::int64_t half = 0;
    std::int64_t full = 1;
    bool operator==(const Board& b) const {
        return squares == b.squares && side == b.side && rights == b.rights &&
               ep == b.ep && half == b.half && full == b.full;
    }
};

struct Move {
    int from, to, promotion = 0;
    bool ep = false, castle = false;
};

int color(int p) { return (p > 0) - (p < 0); }
int file(int sq) { return sq % 8; }
int rank(int sq) { return sq / 8; }
bool inside(int f, int r) { return f >= 0 && f < 8 && r >= 0 && r < 8; }
std::string square_name(int sq) {
    return std::string{static_cast<char>('a' + file(sq)), static_cast<char>('1' + rank(sq))};
}

int king_square(const Board& b, int side) {
    for (int sq = 0; sq < 64; ++sq) if (b.squares[sq] == side * King) return sq;
    return -1;
}

bool attacked(const Board& b, int sq, int by) {
    const int f = file(sq), r = rank(sq);
    for (int df : {-1, 1}) {
        const int pf = f + df, pr = r - by;
        if (inside(pf, pr) && b.squares[pr * 8 + pf] == by * Pawn) return true;
    }
    constexpr int knight_steps[8][2] = {{1,2},{2,1},{2,-1},{1,-2},{-1,-2},{-2,-1},{-2,1},{-1,2}};
    for (const auto& step : knight_steps) {
        const int nf = f + step[0], nr = r + step[1];
        if (inside(nf, nr) && b.squares[nr * 8 + nf] == by * Knight) return true;
    }
    for (int df = -1; df <= 1; ++df) for (int dr = -1; dr <= 1; ++dr) {
        if (df == 0 && dr == 0) continue;
        int nf = f + df, nr = r + dr, distance = 1;
        while (inside(nf, nr)) {
            const int p = b.squares[nr * 8 + nf];
            if (p) {
                if (color(p) == by) {
                    const int type = std::abs(p);
                    if (distance == 1 && type == King) return true;
                    if (type == Queen || (df != 0 && dr != 0 ? type == Bishop : type == Rook)) return true;
                }
                break;
            }
            nf += df; nr += dr; ++distance;
        }
    }
    return false;
}

std::int64_t unsigned_number(const std::string& text, std::int64_t maximum) {
    if (text.empty()) throw std::runtime_error("empty integer");
    std::int64_t value = 0;
    for (unsigned char ch : text) {
        if (ch < '0' || ch > '9' || value > (maximum - (ch - '0')) / 10)
            throw std::runtime_error("invalid integer");
        value = value * 10 + ch - '0';
    }
    if (value > maximum) throw std::runtime_error("integer too large");
    return value;
}

Board parse_fen(const std::string& text) {
    std::istringstream input(text);
    std::array<std::string, 6> fields;
    for (auto& field : fields) if (!(input >> field)) throw std::runtime_error("six FEN fields required");
    std::string extra;
    if (input >> extra) throw std::runtime_error("extra FEN fields");
    Board b;
    int r = 7, f = 0;
    bool previous_digit = false;
    std::array<int, 2> kings{}, pawns{}, pieces{};
    for (char ch : fields[0]) {
        if (ch == '/') {
            if (f != 8 || r == 0) throw std::runtime_error("invalid FEN rank");
            --r; f = 0;
            previous_digit = false;
        } else if (ch >= '1' && ch <= '8') {
            if (previous_digit) throw std::runtime_error("consecutive FEN digits");
            f += ch - '0';
            previous_digit = true;
            if (f > 8) throw std::runtime_error("FEN rank overflow");
        } else {
            previous_digit = false;
            const std::string symbols = "PNBRQKpnbrqk";
            const auto at = symbols.find(ch);
            if (at == std::string::npos || f >= 8) throw std::runtime_error("invalid FEN piece");
            const int side = at < 6 ? 1 : -1, type = static_cast<int>(at % 6) + 1;
            const int index = side == 1 ? 0 : 1;
            b.squares[r * 8 + f++] = side * type;
            ++pieces[index];
            if (type == King) ++kings[index];
            if (type == Pawn) {
                ++pawns[index];
                if (r == 0 || r == 7) throw std::runtime_error("pawn on back rank");
            }
        }
    }
    if (r != 0 || f != 8 || kings[0] != 1 || kings[1] != 1 ||
        pawns[0] > 8 || pawns[1] > 8 || pieces[0] > 16 || pieces[1] > 16)
        throw std::runtime_error("invalid FEN board");
    if (fields[1] != "w" && fields[1] != "b") throw std::runtime_error("invalid side");
    b.side = fields[1] == "w" ? 1 : -1;
    if (fields[2] != "-") for (char ch : fields[2]) {
        const std::string codes = "KQkq";
        const auto at = codes.find(ch);
        if (at == std::string::npos || (b.rights & (1 << at))) throw std::runtime_error("invalid rights");
        b.rights |= 1 << at;
    }
    for (int side : {1, -1}) {
        const int base = side == 1 ? 0 : 56, shift = side == 1 ? 0 : 2;
        if ((b.rights & (3 << shift)) && b.squares[base + 4] != side * King)
            throw std::runtime_error("rights without king");
        if ((b.rights & (1 << shift)) && b.squares[base + 7] != side * Rook)
            throw std::runtime_error("rights without rook");
        if ((b.rights & (2 << shift)) && b.squares[base] != side * Rook)
            throw std::runtime_error("rights without rook");
    }
    if (fields[3] != "-") {
        if (fields[3].size() != 2 || fields[3][0] < 'a' || fields[3][0] > 'h' ||
            fields[3][1] != (b.side == 1 ? '6' : '3')) throw std::runtime_error("invalid EP square");
        b.ep = (fields[3][1] - '1') * 8 + fields[3][0] - 'a';
        if (b.squares[b.ep] || b.squares[b.ep - b.side * 8] != -b.side * Pawn ||
            b.squares[b.ep + b.side * 8]) throw std::runtime_error("invalid EP state");
    }
    b.half = unsigned_number(fields[4], 1000000000);
    b.full = unsigned_number(fields[5], 1000000000);
    if (!b.full) throw std::runtime_error("fullmove must be positive");
    if (attacked(b, king_square(b, -b.side), b.side)) throw std::runtime_error("opposite king in check");
    return b;
}

std::string fen(const Board& b) {
    std::string out;
    const std::string symbols = " PNBRQK";
    for (int r = 7; r >= 0; --r) {
        int empty = 0;
        for (int f = 0; f < 8; ++f) {
            const int p = b.squares[r * 8 + f];
            if (!p) { ++empty; continue; }
            if (empty) { out += static_cast<char>('0' + empty); empty = 0; }
            char ch = symbols[std::abs(p)];
            if (p < 0) ch += 'a' - 'A';
            out += ch;
        }
        if (empty) out += static_cast<char>('0' + empty);
        if (r) out += '/';
    }
    out += b.side == 1 ? " w " : " b ";
    if (!b.rights) out += '-';
    else {
        const std::string codes = "KQkq";
        for (int i = 0; i < 4; ++i) if (b.rights & (1 << i)) out += codes[i];
    }
    out += ' '; out += b.ep < 0 ? "-" : square_name(b.ep);
    out += ' '; out += std::to_string(b.half); out += ' '; out += std::to_string(b.full);
    return out;
}

std::string uci(const Move& m) {
    std::string out = square_name(m.from) + square_name(m.to);
    if (m.promotion) out += std::string(" pnbrqk")[m.promotion];
    return out;
}

Board apply(const Board& b, const Move& m) {
    Board next = b;
    const int p = b.squares[m.from], side = color(p), type = std::abs(p);
    const bool capture = b.squares[m.to] != 0 || m.ep;
    next.squares[m.from] = 0;
    next.squares[m.to] = m.promotion ? side * m.promotion : p;
    if (m.ep) next.squares[m.to - side * 8] = 0;
    if (m.castle) {
        const int base = side == 1 ? 0 : 56;
        const bool short_side = file(m.to) == 6;
        next.squares[base + (short_side ? 7 : 0)] = 0;
        next.squares[base + (short_side ? 5 : 3)] = side * Rook;
    }
    if (type == King) next.rights &= side == 1 ? ~(WK | WQ) : ~(BK | BQ);
    if (m.from == 0 || m.to == 0) next.rights &= ~WQ;
    if (m.from == 7 || m.to == 7) next.rights &= ~WK;
    if (m.from == 56 || m.to == 56) next.rights &= ~BQ;
    if (m.from == 63 || m.to == 63) next.rights &= ~BK;
    next.ep = type == Pawn && std::abs(m.to - m.from) == 16 ? (m.to + m.from) / 2 : -1;
    next.half = type == Pawn || capture ? 0 : b.half + 1;
    next.full = b.full + (b.side == -1 ? 1 : 0);
    next.side = -b.side;
    return next;
}

std::vector<std::pair<Move, Board>> successors(const Board& b) {
    std::vector<Move> pseudo;
    pseudo.reserve(64);
    const int side = b.side;
    auto add_pawn = [&](int from, int to, bool ep = false) {
        if (rank(to) == 0 || rank(to) == 7) {
            for (int promotion : {Knight, Bishop, Rook, Queen}) pseudo.push_back({from, to, promotion, ep, false});
        } else pseudo.push_back({from, to, 0, ep, false});
    };
    constexpr int knight_steps[8][2] = {{1,2},{2,1},{2,-1},{1,-2},{-1,-2},{-2,-1},{-2,1},{-1,2}};
    for (int from = 0; from < 64; ++from) {
        const int p = b.squares[from];
        if (color(p) != side) continue;
        const int type = std::abs(p), f = file(from), r = rank(from);
        if (type == Pawn) {
            const int nr = r + side;
            if (!inside(f, nr)) continue;
            const int forward = nr * 8 + f;
            if (!b.squares[forward]) {
                add_pawn(from, forward);
                if (r == (side == 1 ? 1 : 6) && !b.squares[from + 16 * side])
                    pseudo.push_back({from, from + 16 * side});
            }
            for (int df : {-1, 1}) if (inside(f + df, nr)) {
                const int to = nr * 8 + f + df;
                if (color(b.squares[to]) == -side && std::abs(b.squares[to]) != King) add_pawn(from, to);
                else if (to == b.ep && !b.squares[to] && b.squares[to - side * 8] == -side * Pawn)
                    add_pawn(from, to, true);
            }
        } else if (type == Knight) {
            for (const auto& step : knight_steps) {
                const int nf = f + step[0], nr = r + step[1];
                if (!inside(nf, nr)) continue;
                const int to = nr * 8 + nf;
                if (color(b.squares[to]) != side && std::abs(b.squares[to]) != King) pseudo.push_back({from, to});
            }
        } else {
            for (int df = -1; df <= 1; ++df) for (int dr = -1; dr <= 1; ++dr) {
                if ((!df && !dr) || (type == Bishop && (!df || !dr)) || (type == Rook && df && dr)) continue;
                int nf = f + df, nr = r + dr;
                while (inside(nf, nr)) {
                    const int to = nr * 8 + nf, target = b.squares[to];
                    if (color(target) == side || std::abs(target) == King) break;
                    pseudo.push_back({from, to});
                    if (target || type == King) break;
                    nf += df; nr += dr;
                }
            }
            if (type == King) {
                const int base = side == 1 ? 0 : 56, shift = side == 1 ? 0 : 2;
                if (from != base + 4 || attacked(b, from, -side)) continue;
                for (bool short_side : {true, false}) {
                    const int bit = (short_side ? 1 : 2) << shift;
                    if (!(b.rights & bit) || b.squares[base + (short_side ? 7 : 0)] != side * Rook) continue;
                    const int step = short_side ? 1 : -1;
                    if (b.squares[from + step] || b.squares[from + 2 * step] ||
                        (!short_side && b.squares[base + 1])) continue;
                    Board middle = b;
                    middle.squares[from] = 0;
                    middle.squares[from + step] = side * King;
                    if (!attacked(middle, from + step, -side)) pseudo.push_back({from, from + 2 * step, 0, false, true});
                }
            }
        }
    }
    std::vector<std::pair<Move, Board>> legal;
    legal.reserve(pseudo.size());
    for (const Move& move : pseudo) {
        Board next = apply(b, move);
        const int king = king_square(next, side);
        if (king >= 0 && !attacked(next, king, -side)) legal.emplace_back(move, std::move(next));
    }
    return legal;
}

std::int64_t absolute_ply(const Board& b) { return 2 * (b.full - 1) + (b.side == -1 ? 1 : 0); }

// Each missing target piece needs a move by that side. Castling is the sole
// move that can place two own pieces onto their target squares simultaneously.
bool impossible(const Board& b, const Board& target, int remaining) {
    if ((target.rights & ~b.rights) != 0) return true;
    if (target.half > b.half + remaining) return true;
    if (target.half >= remaining && target.half != b.half + remaining) return true;
    for (int side : {1, -1}) {
        int missing = 0, current_count = 0, target_count = 0, current_pawns = 0, target_pawns = 0;
        for (int sq = 0; sq < 64; ++sq) {
            if (color(target.squares[sq]) == side) {
                ++target_count;
                if (target.squares[sq] != b.squares[sq]) ++missing;
                if (target.squares[sq] == side * Pawn) ++target_pawns;
            }
            if (color(b.squares[sq]) == side) {
                ++current_count;
                if (b.squares[sq] == side * Pawn) ++current_pawns;
            }
        }
        if (target_count > current_count || target_pawns > current_pawns) return true;
        const int turns = (remaining + (b.side == side ? 1 : 0)) / 2;
        const int castle_bonus = (b.rights & (side == 1 ? 3 : 12)) ? 1 : 0;
        if (missing > turns + castle_bonus) return true;
    }
    return false;
}

int target_distance(const Board& b, const Board& target) {
    int distance = 0;
    for (int sq = 0; sq < 64; ++sq) if (b.squares[sq] != target.squares[sq]) ++distance;
    return distance;
}

enum class Status { Reachable, Unreachable, Unknown };
const char* status_name(Status s) {
    return s == Status::Reachable ? "REACHABLE" : s == Status::Unreachable ? "UNREACHABLE" : "UNKNOWN";
}

struct Search {
    const Board& target;
    std::uint64_t limit, nodes = 0;
    std::unordered_set<std::string> proved_no;
    std::vector<std::string> path, witness;

    Search(const Board& destination, std::uint64_t node_limit) : target(destination), limit(node_limit) {}

    Status visit(const Board& b, int remaining) {
        if (nodes >= limit) return Status::Unknown;
        ++nodes;
        if (!remaining) {
            if (b == target) { witness = path; return Status::Reachable; }
            return Status::Unreachable;
        }
        if (impossible(b, target, remaining)) return Status::Unreachable;
        const std::string key = fen(b);
        if (proved_no.find(key) != proved_no.end()) return Status::Unreachable;
        auto moves = successors(b);
        std::stable_sort(moves.begin(), moves.end(), [&](const auto& a, const auto& z) {
            return target_distance(a.second, target) < target_distance(z.second, target);
        });
        for (const auto& child : moves) {
            path.push_back(uci(child.first));
            const Status result = visit(child.second, remaining - 1);
            path.pop_back();
            if (result != Status::Unreachable) return result;
        }
        proved_no.insert(key);
        return Status::Unreachable;
    }
};

std::vector<std::string> split_tabs(const std::string& line) {
    std::vector<std::string> fields;
    std::size_t first = 0;
    while (true) {
        const auto end = line.find('\t', first);
        fields.push_back(line.substr(first, end == std::string::npos ? end : end - first));
        if (end == std::string::npos) return fields;
        first = end + 1;
    }
}

std::string json_string(const std::string& text) {
    std::string out = "\"";
    const char* hex = "0123456789abcdef";
    for (unsigned char ch : text) {
        if (ch == '\"' || ch == '\\') { out += '\\'; out += ch; }
        else if (ch < 32) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
        else out += ch;
    }
    out += '\"';
    return out;
}

int parse_result(const std::string& text) {
    if (text.empty()) throw std::runtime_error("missing result");
    std::size_t used = 0;
    const double value = std::stod(text, &used);
    if (used != text.size() || (value != 0.0 && value != 0.5 && value != 1.0))
        throw std::runtime_error("invalid result");
    return static_cast<int>(value * 2);
}

void emit_pair(const std::string& id, Status status, const std::string& reason,
               std::uint64_t nodes = 0, const std::vector<std::string>& witness = {}) {
    std::cout << "{\"id\":" << json_string(id) << ",\"status\":\"" << status_name(status)
              << "\",\"reason\":" << json_string(reason) << ",\"nodes\":" << nodes << ",\"witness\":[";
    for (std::size_t i = 0; i < witness.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << json_string(witness[i]);
    }
    std::cout << "]}\n";
}

void pair_line(const std::vector<std::string>& fields) {
    if (fields.size() != 7) throw std::runtime_error("seven TSV fields required");
    const Board start = parse_fen(fields[1]), target = parse_fen(fields[3]);
    const int result1 = parse_result(fields[2]), result2 = parse_result(fields[4]);
    const int k = static_cast<int>(unsigned_number(fields[5], 64));
    const auto cap = static_cast<std::uint64_t>(unsigned_number(fields[6], 1000000000));
    if (k < 1 || cap < 1) throw std::runtime_error("positive K and node limit required");
    if (result1 != result2) { emit_pair(fields[0], Status::Unreachable, "result_mismatch"); return; }
    const auto delta = absolute_ply(target) - absolute_ply(start);
    if (delta <= 0) { emit_pair(fields[0], Status::Unreachable, "nonpositive_ply_gap"); return; }
    if (delta > k) { emit_pair(fields[0], Status::Unknown, "gap_exceeds_k"); return; }
    Search search{target, cap};
    const Status status = search.visit(start, static_cast<int>(delta));
    emit_pair(fields[0], status, status == Status::Reachable ? "legal_witness" :
              status == Status::Unknown ? "node_limit" : "exhaustive_no_path", search.nodes, search.witness);
}

void moves_line(const std::vector<std::string>& fields) {
    if (fields.size() != 2) throw std::runtime_error("two TSV fields required");
    const Board b = parse_fen(fields[1]);
    auto moves = successors(b);
    std::sort(moves.begin(), moves.end(), [](const auto& a, const auto& z) { return uci(a.first) < uci(z.first); });
    std::cout << "{\"id\":" << json_string(fields[0]) << ",\"status\":\"OK\",\"moves\":[";
    for (std::size_t i = 0; i < moves.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << "{\"uci\":" << json_string(uci(moves[i].first)) << ",\"fen\":" << json_string(fen(moves[i].second)) << '}';
    }
    std::cout << "]}\n";
}
} // namespace chain

int main(int argc, char** argv) {
    std::ios::sync_with_stdio(false);
    std::cin.tie(&std::cout);
    const std::string mode = argc == 1 ? "--pairs" : argv[1];
    if (argc > 2 || (mode != "--pairs" && mode != "--moves" && mode != "--help")) {
        std::cerr << "Usage: chain_native [--pairs|--moves|--help]\n";
        return 2;
    }
    if (mode == "--help") {
        std::cout << "--pairs TSV: id,fen1,result1,fen2,result2,K,node_limit; one JSON result per line.\n"
                     "--moves TSV: id,fen; one sorted legal-successor JSON result per line.\n";
        return 0;
    }
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        auto fields = chain::split_tabs(line);
        try {
            if (mode == "--moves") chain::moves_line(fields);
            else chain::pair_line(fields);
        } catch (const std::exception&) {
            chain::emit_pair(fields.empty() ? "" : fields[0], chain::Status::Unknown, "invalid_input");
        }
    }
    return std::cin.bad() || !std::cout ? 1 : 0;
}
