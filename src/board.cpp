#include "forge/board.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <sstream>

namespace forge {
namespace {

constexpr std::uint8_t WhiteKingSide = 1;
constexpr std::uint8_t WhiteQueenSide = 2;
constexpr std::uint8_t BlackKingSide = 4;
constexpr std::uint8_t BlackQueenSide = 8;

constexpr std::array<int, 7> SeeValue{0, 100, 300, 300, 500, 900, 0};

// Rare target-only LVA exchange path. The ordinary threshold SEE is unchanged.
// Pawn promotions add material immediately and change the next victim's value.
int promotion_recapture_exchange(const Board& board, const Move& move, int captured_square) {
    const Color us = board.side_to_move();
    const int from = move.from;
    const int to = move.to;
    std::array<int, 64> gain{};
    gain[0] = SeeValue[static_cast<std::size_t>(piece_type(board.piece_at(captured_square)))];
    int victim = SeeValue[static_cast<std::size_t>(piece_type(board.piece_at(from)))];
    if (move.is_promotion()) {
        gain[0] += SeeValue[move.promotion] - SeeValue[Pawn];
        victim = SeeValue[move.promotion];
    }

    Bitboard occupancy = (board.occupied() ^ square_bb(from) ^ square_bb(captured_square)) | square_bb(to);
    Color stm = us;
    Bitboard attackers = board.attackers_to(to, occupancy);
    const Bitboard diagonals = board.pieces(Bishop) | board.pieces(Queen);
    const Bitboard lines = board.pieces(Rook) | board.pieces(Queen);
    std::size_t depth = 0;
    // Each accepted recapture consumes a distinct occupied origin; a king ends
    // the exchange. The bound also makes every gain write fit for any board.
    while (depth + 1 < gain.size()) {
        stm = opposite(stm);
        attackers &= occupancy;
        Bitboard stm_attackers = attackers & board.occupied(stm);
        const Bitboard king_attackers = stm_attackers & board.pieces(stm, King);
        if ((stm_attackers & ~king_attackers) != 0) {
            const Color enemy = opposite(stm);
            const int king = board.king_square(stm);
            const Bitboard live = occupancy & ~square_bb(to);
            const Bitboard queens = board.pieces(enemy, Queen) & live;
            bool checked =
                (attacks::pawn(stm, king) & board.pieces(enemy, Pawn) & live) != 0 ||
                (attacks::knight(king) & board.pieces(enemy, Knight) & live) != 0 ||
                (attacks::king(king) & board.pieces(enemy, King) & live) != 0;
            Bitboard pinners =
                (attacks::bishop(king, 0) & ((board.pieces(enemy, Bishop) & live) | queens)) |
                (attacks::rook(king, 0) & ((board.pieces(enemy, Rook) & live) | queens));
            Bitboard forbidden = 0;
            while (!checked && pinners != 0) {
                const int pinner = pop_lsb(pinners);
                const Bitboard blockers = attacks::between(king, pinner) & occupancy;
                if (blockers == 0) checked = true;
                else if (!more_than_one(blockers)) forbidden |= blockers;
            }
            stm_attackers = checked ? king_attackers : stm_attackers & ~forbidden;
        }
        if (stm_attackers == 0) break;

        Bitboard bb = 0;
        PieceType attacker_type = NoPieceType;
        if ((bb = stm_attackers & board.pieces(stm, Pawn)) != 0) {
            attacker_type = Pawn;
        } else if ((bb = stm_attackers & board.pieces(stm, Knight)) != 0) {
            attacker_type = Knight;
        } else if ((bb = stm_attackers & board.pieces(stm, Bishop)) != 0) {
            attacker_type = Bishop;
        } else if ((bb = stm_attackers & board.pieces(stm, Rook)) != 0) {
            attacker_type = Rook;
        } else if ((bb = stm_attackers & board.pieces(stm, Queen)) != 0) {
            attacker_type = Queen;
        } else {
            // Preserve source16's geometric king-defender test. A king capture
            // is terminal, and a defended target permits no king capture.
            if ((attackers & ~board.occupied(stm)) != 0) break;
            const std::size_t next = depth + 1;
            gain[next] = victim - gain[depth];
            depth = next;
            break;
        }

        const bool promotes = attacker_type == Pawn && rank_of(to) == (stm == White ? 7 : 0);
        const int promotion_gain = promotes ? SeeValue[Queen] - SeeValue[Pawn] : 0;
        const std::size_t next = depth + 1;
        gain[next] = victim + promotion_gain - gain[depth];
        depth = next;
        victim = promotes ? SeeValue[Queen] : SeeValue[static_cast<std::size_t>(attacker_type)];

        occupancy ^= square_bb(lsb(bb));
        if (attacker_type == Pawn || attacker_type == Bishop) {
            attackers |= attacks::bishop(to, occupancy) & diagonals;
        } else if (attacker_type == Rook) {
            attackers |= attacks::rook(to, occupancy) & lines;
        } else if (attacker_type == Queen) {
            attackers |= (attacks::bishop(to, occupancy) & diagonals) | (attacks::rook(to, occupancy) & lines);
        }
    }
    while (depth != 0) {
        gain[depth - 1] = std::min(gain[depth - 1], -gain[depth]);
        --depth;
    }
    return gain[0];
}


constexpr std::uint64_t mix(std::uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27U)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31U);
}

struct Zobrist {
    std::array<std::array<std::uint64_t, 64>, 13> piece{};
    std::array<std::uint64_t, 16> castling{};
    std::array<std::uint64_t, 8> ep{};
    std::uint64_t side = 0;

    constexpr Zobrist() {
        for (int p = 0; p < 13; ++p) {
            for (int s = 0; s < 64; ++s) {
                piece[static_cast<std::size_t>(p)][static_cast<std::size_t>(s)] =
                    p == Empty ? 0 : mix(1 + static_cast<std::uint64_t>(s) * 13U + static_cast<std::uint64_t>(p));
            }
        }
        for (int c = 0; c < 16; ++c) castling[static_cast<std::size_t>(c)] = mix(900 + static_cast<std::uint64_t>(c));
        for (int f = 0; f < 8; ++f) ep[static_cast<std::size_t>(f)] = mix(1000 + static_cast<std::uint64_t>(f));
        side = mix(1100);
    }
};

constexpr Zobrist Z{};

constexpr std::uint64_t piece_key(int square, Piece piece) {
    return Z.piece[static_cast<std::size_t>(piece)][static_cast<std::size_t>(square)];
}

Piece char_to_piece(char c) {
    constexpr std::string_view chars = " PNBRQKpnbrqk";
    const auto position = chars.find(c);
    return position == std::string_view::npos || position == 0 ? Empty : static_cast<Piece>(position);
}

char piece_to_char(Piece piece) {
    constexpr std::array<char, 13> chars{' ', 'P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k'};
    return chars[static_cast<std::size_t>(piece)];
}

// Castling rights cleared when a piece moves from or to a square.
constexpr std::array<std::uint8_t, 64> make_castling_masks() {
    std::array<std::uint8_t, 64> masks{};
    for (auto& m : masks) m = 0xFF;
    masks[0] = static_cast<std::uint8_t>(~WhiteQueenSide);
    masks[7] = static_cast<std::uint8_t>(~WhiteKingSide);
    masks[4] = static_cast<std::uint8_t>(~(WhiteKingSide | WhiteQueenSide));
    masks[56] = static_cast<std::uint8_t>(~BlackQueenSide);
    masks[63] = static_cast<std::uint8_t>(~BlackKingSide);
    masks[60] = static_cast<std::uint8_t>(~(BlackKingSide | BlackQueenSide));
    return masks;
}
constexpr auto CastlingMasks = make_castling_masks();

} // namespace

Board::Board() {
    attacks::init();
    key_history_.reserve(512);
    (void)set_fen(StandardStartFen);
}

void Board::put_piece(Piece piece, int square) {
    squares_[static_cast<std::size_t>(square)] = piece;
    const Bitboard bit = square_bb(square);
    bitboards_[static_cast<std::size_t>(piece)] |= bit;
    occupied_[static_cast<std::size_t>(color_of(piece))] |= bit;
}

void Board::remove_piece(int square) {
    const Piece piece = squares_[static_cast<std::size_t>(square)];
    const Bitboard bit = square_bb(square);
    bitboards_[static_cast<std::size_t>(piece)] &= ~bit;
    occupied_[static_cast<std::size_t>(color_of(piece))] &= ~bit;
    squares_[static_cast<std::size_t>(square)] = Empty;
}

void Board::move_piece(int from, int to) {
    const Piece piece = squares_[static_cast<std::size_t>(from)];
    const Bitboard bits = square_bb(from) | square_bb(to);
    bitboards_[static_cast<std::size_t>(piece)] ^= bits;
    occupied_[static_cast<std::size_t>(color_of(piece))] ^= bits;
    squares_[static_cast<std::size_t>(from)] = Empty;
    squares_[static_cast<std::size_t>(to)] = piece;
}

bool Board::set_fen(std::string_view fen_text, std::string* error) {
    std::istringstream input{std::string(fen_text)};
    std::string placement;
    std::string side;
    std::string castling;
    std::string ep;
    long long halfmove = 0;
    long long fullmove = 1;
    if (!(input >> placement >> side >> castling >> ep >> halfmove >> fullmove)) {
        if (error != nullptr) *error = "FEN must contain six fields";
        return false;
    }
    std::string trailing;
    if (input >> trailing) {
        if (error != nullptr) *error = "FEN must contain exactly six fields";
        return false;
    }

    std::array<Piece, 64> parsed{};
    int rank = 7;
    int file = 0;
    int kings[2] = {0, 0};
    std::array<int, 13> piece_counts{};
    int king_squares[2] = {-1, -1};
    for (char c : placement) {
        if (c == '/') {
            if (file != 8 || rank == 0) {
                if (error != nullptr) *error = "invalid FEN rank";
                return false;
            }
            --rank;
            file = 0;
        } else if (c >= '1' && c <= '8') {
            file += c - '0';
        } else {
            const Piece piece = char_to_piece(c);
            if (piece == Empty || file >= 8 || rank < 0) {
                if (error != nullptr) *error = "invalid FEN placement";
                return false;
            }
            parsed[static_cast<std::size_t>(rank * 8 + file)] = piece;
            ++piece_counts[static_cast<std::size_t>(piece)];
            if ((piece == WP || piece == BP) && (rank == 0 || rank == 7)) {
                if (error != nullptr) *error = "pawn on promotion rank";
                return false;
            }
            if (piece == WK) { ++kings[White]; king_squares[White] = rank * 8 + file; }
            if (piece == BK) { ++kings[Black]; king_squares[Black] = rank * 8 + file; }
            ++file;
        }
        if (file > 8) {
            if (error != nullptr) *error = "too many squares in FEN rank";
            return false;
        }
    }
    if (rank != 0 || file != 8 || kings[White] != 1 || kings[Black] != 1 ||
        (side != "w" && side != "b") || halfmove < 0 || fullmove < 1) {
        if (error != nullptr) *error = "invalid FEN fields";
        return false;
    }
    if (square_distance(king_squares[White], king_squares[Black]) <= 1) {
        if (error != nullptr) *error = "kings may not be adjacent";
        return false;
    }
    for (const Color color : {White, Black}) {
        const int offset = color == White ? 0 : 6;
        const int pawns = piece_counts[static_cast<std::size_t>(WP + offset)];
        int total = 0;
        for (int type = 1; type <= 6; ++type) total += piece_counts[static_cast<std::size_t>(type + offset)];
        const int promoted = std::max(0, piece_counts[static_cast<std::size_t>(WN + offset)] - 2) +
                             std::max(0, piece_counts[static_cast<std::size_t>(WB + offset)] - 2) +
                             std::max(0, piece_counts[static_cast<std::size_t>(WR + offset)] - 2) +
                             std::max(0, piece_counts[static_cast<std::size_t>(WQ + offset)] - 1);
        if (pawns > 8 || total > 16 || promoted > 8 - pawns) {
            if (error != nullptr) *error = "impossible piece inventory";
            return false;
        }
    }

    std::uint8_t rights = 0;
    if (castling != "-") {
        for (char c : castling) {
            const std::uint8_t previous = rights;
            switch (c) {
            case 'K': rights |= WhiteKingSide; break;
            case 'Q': rights |= WhiteQueenSide; break;
            case 'k': rights |= BlackKingSide; break;
            case 'q': rights |= BlackQueenSide; break;
            default:
                if (error != nullptr) *error = "invalid castling rights";
                return false;
            }
            if (rights == previous) {
                if (error != nullptr) *error = "duplicate castling right";
                return false;
            }
        }
    }
    if (((rights & WhiteKingSide) != 0U && (parsed[4] != WK || parsed[7] != WR)) ||
        ((rights & WhiteQueenSide) != 0U && (parsed[4] != WK || parsed[0] != WR)) ||
        ((rights & BlackKingSide) != 0U && (parsed[60] != BK || parsed[63] != BR)) ||
        ((rights & BlackQueenSide) != 0U && (parsed[60] != BK || parsed[56] != BR))) {
        if (error != nullptr) *error = "castling right without king and rook";
        return false;
    }
    const Color parsed_side = side == "w" ? White : Black;
    int ep_square = -1;
    if (ep != "-") {
        if (ep.size() != 2 || ep[0] < 'a' || ep[0] > 'h' || (ep[1] != '3' && ep[1] != '6')) {
            if (error != nullptr) *error = "invalid en-passant square";
            return false;
        }
        ep_square = (ep[1] - '1') * 8 + (ep[0] - 'a');
        const int pawn_square = parsed_side == White ? ep_square - 8 : ep_square + 8;
        const int origin_square = parsed_side == White ? ep_square + 8 : ep_square - 8;
        const Piece expected_pawn = parsed_side == White ? BP : WP;
        if ((parsed_side == White && ep[1] != '6') || (parsed_side == Black && ep[1] != '3') ||
            parsed[static_cast<std::size_t>(ep_square)] != Empty ||
            parsed[static_cast<std::size_t>(origin_square)] != Empty ||
            parsed[static_cast<std::size_t>(pawn_square)] != expected_pawn) {
            if (error != nullptr) *error = "inconsistent en-passant square";
            return false;
        }
    }

    // Commit into a scratch board first so a late validation failure (side
    // that just moved left in check) leaves the current position untouched.
    Board candidate(*this);
    candidate.squares_.fill(Empty);
    candidate.bitboards_.fill(0);
    candidate.occupied_.fill(0);
    for (int square = 0; square < 64; ++square) {
        if (parsed[static_cast<std::size_t>(square)] != Empty) {
            candidate.put_piece(parsed[static_cast<std::size_t>(square)], square);
        }
    }
    candidate.king_squares_ = {king_squares[White], king_squares[Black]};
    candidate.side_ = parsed_side;
    candidate.castling_ = rights;
    candidate.ep_square_ = static_cast<std::int8_t>(ep_square);
    candidate.halfmove_ = static_cast<std::uint16_t>(std::min<long long>(halfmove, 65535));
    candidate.fullmove_ = static_cast<std::uint16_t>(std::min<long long>(fullmove, 65535));
    if (candidate.square_attacked(king_squares[opposite(parsed_side)], parsed_side)) {
        if (error != nullptr) *error = "side that moved left its king in check";
        return false;
    }
    candidate.key_ = candidate.compute_key();
    candidate.pawn_key_ = candidate.compute_pawn_key();
    candidate.checkers_ = candidate.compute_checkers();
    candidate.plies_from_null_ = 1024;
    candidate.key_history_.clear();
    candidate.key_history_.push_back(candidate.key_);
    *this = std::move(candidate);
    return true;
}

std::string Board::fen() const {
    std::ostringstream out;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const Piece piece = squares_[static_cast<std::size_t>(rank * 8 + file)];
            if (piece == Empty) {
                ++empty;
            } else {
                if (empty != 0) out << empty;
                empty = 0;
                out << piece_to_char(piece);
            }
        }
        if (empty != 0) out << empty;
        if (rank != 0) out << '/';
    }
    out << (side_ == White ? " w " : " b ");
    if (castling_ == 0) out << '-';
    if ((castling_ & WhiteKingSide) != 0U) out << 'K';
    if ((castling_ & WhiteQueenSide) != 0U) out << 'Q';
    if ((castling_ & BlackKingSide) != 0U) out << 'k';
    if ((castling_ & BlackQueenSide) != 0U) out << 'q';
    out << ' ';
    if (ep_square_ < 0) {
        out << '-';
    } else {
        out << static_cast<char>('a' + file_of(ep_square_)) << static_cast<char>('1' + rank_of(ep_square_));
    }
    out << ' ' << halfmove_ << ' ' << fullmove_;
    return out.str();
}

Bitboard Board::attackers_to(int square, Bitboard occupancy) const {
    return (attacks::pawn(Black, square) & pieces(WP)) | (attacks::pawn(White, square) & pieces(BP)) |
           (attacks::knight(square) & pieces(Knight)) | (attacks::king(square) & pieces(King)) |
           (attacks::bishop(square, occupancy) & (pieces(Bishop) | pieces(Queen))) |
           (attacks::rook(square, occupancy) & (pieces(Rook) | pieces(Queen)));
}

bool Board::square_attacked_with_occupancy(int square, Color by, Bitboard occupancy, Bitboard removed) const {
    const Bitboard available = ~removed;
    if ((attacks::pawn(opposite(by), square) & pieces(by, Pawn) & available) != 0) return true;
    if ((attacks::knight(square) & pieces(by, Knight) & available) != 0) return true;
    if ((attacks::king(square) & pieces(by, King) & available) != 0) return true;
    const Bitboard queens = pieces(by, Queen) & available;
    if ((attacks::bishop(square, occupancy) & ((pieces(by, Bishop) & available) | queens)) != 0) return true;
    return (attacks::rook(square, occupancy) & ((pieces(by, Rook) & available) | queens)) != 0;
}

bool Board::square_attacked(int square, Color by) const {
    return square_attacked_with_occupancy(square, by, occupied());
}

bool Board::in_check(Color color) const {
    const int square = king_square(color);
    return square >= 0 && square_attacked(square, opposite(color));
}

Bitboard Board::compute_checkers() const {
    const int king = king_square(side_);
    if (king < 0) return 0;
    return attackers_to(king, occupied()) & occupied(opposite(side_));
}

void Board::generate_pseudo_legal(MoveList& moves, bool captures_only) const {
    const Color us = side_;
    const Color them = opposite(us);
    const Bitboard own = occupied(us);
    const Bitboard enemy = occupied(them);
    const Bitboard occ = own | enemy;
    const Bitboard empty = ~occ;
    const int up = pawn_push_delta(us);

    auto push = [&](int from, int to, std::uint8_t flags) {
        moves.push_back(Move{static_cast<std::uint8_t>(from), static_cast<std::uint8_t>(to), 0, flags});
    };
    auto push_promotions = [&](int from, int to, std::uint8_t flags) {
        moves.push_back(Move{static_cast<std::uint8_t>(from), static_cast<std::uint8_t>(to), Queen,
                             static_cast<std::uint8_t>(flags | Promotion)});
        for (const int promotion : {Rook, Bishop, Knight}) {
            moves.push_back(Move{static_cast<std::uint8_t>(from), static_cast<std::uint8_t>(to), static_cast<std::uint8_t>(promotion),
                                 static_cast<std::uint8_t>(flags | Promotion)});
        }
    };

    const Bitboard pawns = pieces(us, Pawn);
    const Bitboard seventh = us == White ? Rank7BB : Rank2BB;
    const Bitboard third = us == White ? Rank3BB : Rank6BB;
    const Bitboard promoting = pawns & seventh;
    const Bitboard regular = pawns & ~seventh;

    if (!captures_only) {
        Bitboard single = pawn_push(us, regular) & empty;
        Bitboard twice = pawn_push(us, single & third) & empty;
        while (single != 0) {
            const int to = pop_lsb(single);
            push(to - up, to, Quiet);
        }
        while (twice != 0) {
            const int to = pop_lsb(twice);
            push(to - 2 * up, to, DoublePush);
        }
    }
    Bitboard promo_push = pawn_push(us, promoting) & empty;
    while (promo_push != 0) {
        const int to = pop_lsb(promo_push);
        push_promotions(to - up, to, Quiet);
    }
    Bitboard capturers = pawns;
    while (capturers != 0) {
        const int from = pop_lsb(capturers);
        Bitboard targets = attacks::pawn(us, from) & enemy;
        const bool promotes = (square_bb(from) & seventh) != 0;
        while (targets != 0) {
            const int to = pop_lsb(targets);
            if (promotes) push_promotions(from, to, Capture);
            else push(from, to, Capture);
        }
    }
    if (ep_square_ >= 0) {
        Bitboard ep_attackers = attacks::pawn(them, ep_square_) & pawns;
        while (ep_attackers != 0) {
            push(pop_lsb(ep_attackers), ep_square_, static_cast<std::uint8_t>(Capture | EnPassant));
        }
    }

    const Bitboard targets_mask = captures_only ? enemy : ~own;
    auto emit = [&](int from, Bitboard targets) {
        while (targets != 0) {
            const int to = pop_lsb(targets);
            push(from, to, (square_bb(to) & enemy) != 0 ? Capture : Quiet);
        }
    };
    Bitboard knights = pieces(us, Knight);
    while (knights != 0) {
        const int from = pop_lsb(knights);
        emit(from, attacks::knight(from) & targets_mask);
    }
    Bitboard bishops = pieces(us, Bishop);
    while (bishops != 0) {
        const int from = pop_lsb(bishops);
        emit(from, attacks::bishop(from, occ) & targets_mask);
    }
    Bitboard rooks = pieces(us, Rook);
    while (rooks != 0) {
        const int from = pop_lsb(rooks);
        emit(from, attacks::rook(from, occ) & targets_mask);
    }
    Bitboard queens = pieces(us, Queen);
    while (queens != 0) {
        const int from = pop_lsb(queens);
        emit(from, attacks::queen(from, occ) & targets_mask);
    }
    const int king = king_square(us);
    emit(king, attacks::king(king) & targets_mask);

    if (!captures_only && checkers_ == 0) {
        if (us == White && king == 4) {
            if ((castling_ & WhiteKingSide) != 0U && (occ & (square_bb(5) | square_bb(6))) == 0 &&
                piece_at(7) == WR && !square_attacked(5, Black) && !square_attacked(6, Black)) {
                push(4, 6, KingCastle);
            }
            if ((castling_ & WhiteQueenSide) != 0U &&
                (occ & (square_bb(1) | square_bb(2) | square_bb(3))) == 0 &&
                piece_at(0) == WR && !square_attacked(3, Black) && !square_attacked(2, Black)) {
                push(4, 2, QueenCastle);
            }
        } else if (us == Black && king == 60) {
            if ((castling_ & BlackKingSide) != 0U && (occ & (square_bb(61) | square_bb(62))) == 0 &&
                piece_at(63) == BR && !square_attacked(61, White) && !square_attacked(62, White)) {
                push(60, 62, KingCastle);
            }
            if ((castling_ & BlackQueenSide) != 0U &&
                (occ & (square_bb(57) | square_bb(58) | square_bb(59))) == 0 &&
                piece_at(56) == BR && !square_attacked(59, White) && !square_attacked(58, White)) {
                push(60, 58, QueenCastle);
            }
        }
    }
}

MoveList Board::pseudo_legal_moves(bool captures_only) const {
    MoveList moves;
    generate_pseudo_legal(moves, captures_only);
    return moves;
}

MoveList Board::legal_moves(bool captures_only) const {
    MoveList moves = pseudo_legal_moves(captures_only);
    std::size_t write = 0;
    for (const Move move : moves) {
        if (is_legal(move)) moves[write++] = move;
    }
    moves.resize(write);
    return moves;
}

bool Board::has_legal_move() const {
    // A single legal quiet pawn push proves non-terminal without generating
    // the full move list. Promotions and every failed witness use the original
    // complete fallback; exact king-safety testing handles checks and pins.
    const Bitboard pushes = pawn_push(side_, pieces(side_, Pawn)) & ~occupied() & ~(Rank1BB | Rank8BB);
    if (pushes != 0) {
        const int to = lsb(pushes);
        const Move witness{static_cast<std::uint8_t>(to - pawn_push_delta(side_)),
                           static_cast<std::uint8_t>(to), 0, Quiet};
        if (is_legal(witness)) return true;
    }
    MoveList moves;
    generate_pseudo_legal(moves, false);
    for (const Move move : moves) {
        if (is_legal(move)) return true;
    }
    return false;
}

bool Board::is_legal(const Move& move) const {
    const Color us = side_;
    const Piece moving = squares_[move.from];
    Bitboard occupancy = occupied() & ~square_bb(move.from);
    int captured_square = move.to;
    if ((move.flags & EnPassant) != 0U) captured_square = move.to - pawn_push_delta(us);
    Bitboard removed = 0;
    if (move.is_capture()) {
        removed = square_bb(captured_square);
        occupancy &= ~removed;
    }
    occupancy |= square_bb(move.to);
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        occupancy &= ~square_bb(rook_from);
        occupancy |= square_bb(rook_to);
    }
    const int king = piece_type(moving) == King ? static_cast<int>(move.to) : king_square(us);
    return !square_attacked_with_occupancy(king, opposite(us), occupancy, removed);
}

bool Board::is_pseudo_legal(const Move& move) const {
    if (move.from >= 64 || move.to >= 64 || move.from == move.to) return false;
    const Color us = side_;
    const Piece moving = squares_[move.from];
    if (moving == Empty || color_of(moving) != us) return false;
    const Piece target = squares_[move.to];
    if (target != Empty && (color_of(target) == us || piece_type(target) == King)) return false;
    const int type = piece_type(moving);
    const Bitboard occ = occupied();
    const int up = pawn_push_delta(us);
    const std::uint8_t special = static_cast<std::uint8_t>(move.flags & (DoublePush | KingCastle | QueenCastle | EnPassant | Promotion));

    if (move.is_castle()) {
        if (type != King || checkers_ != 0 || special != (move.flags & (KingCastle | QueenCastle))) return false;
        if ((move.flags & Capture) != 0U || move.promotion != 0) return false;
        const bool king_side = (move.flags & KingCastle) != 0U;
        if (king_side && (move.flags & QueenCastle) != 0U) return false;
        if (us == White) {
            if (move.from != 4 || move.to != (king_side ? 6 : 2)) return false;
            if (king_side) {
                return (castling_ & WhiteKingSide) != 0U && (occ & (square_bb(5) | square_bb(6))) == 0 &&
                       piece_at(7) == WR && !square_attacked(5, Black) && !square_attacked(6, Black);
            }
            return (castling_ & WhiteQueenSide) != 0U && (occ & (square_bb(1) | square_bb(2) | square_bb(3))) == 0 &&
                   piece_at(0) == WR && !square_attacked(3, Black) && !square_attacked(2, Black);
        }
        if (move.from != 60 || move.to != (king_side ? 62 : 58)) return false;
        if (king_side) {
            return (castling_ & BlackKingSide) != 0U && (occ & (square_bb(61) | square_bb(62))) == 0 &&
                   piece_at(63) == BR && !square_attacked(61, White) && !square_attacked(62, White);
        }
        return (castling_ & BlackQueenSide) != 0U && (occ & (square_bb(57) | square_bb(58) | square_bb(59))) == 0 &&
               piece_at(56) == BR && !square_attacked(59, White) && !square_attacked(58, White);
    }

    if (type == Pawn) {
        const bool promotes = relative_rank(us, move.from) == 6;
        if (promotes != move.is_promotion()) return false;
        if (move.is_promotion() && (move.promotion < Knight || move.promotion > Queen)) return false;
        if (!move.is_promotion() && move.promotion != 0) return false;
        if ((move.flags & EnPassant) != 0U) {
            if (ep_square_ < 0 || move.to != ep_square_ || (move.flags & Capture) == 0U) return false;
            if ((move.flags & (DoublePush | Promotion)) != 0U) return false;
            return (attacks::pawn(us, move.from) & square_bb(move.to)) != 0;
        }
        if ((move.flags & Capture) != 0U) {
            if (target == Empty || (move.flags & DoublePush) != 0U) return false;
            return (attacks::pawn(us, move.from) & square_bb(move.to)) != 0;
        }
        if (target != Empty) return false;
        if ((move.flags & DoublePush) != 0U) {
            if (relative_rank(us, move.from) != 1 || move.to != move.from + 2 * up) return false;
            return squares_[static_cast<std::size_t>(move.from + up)] == Empty;
        }
        return move.to == move.from + up;
    }

    if (special != 0 || move.promotion != 0) return false;
    if (((move.flags & Capture) != 0U) != (target != Empty)) return false;
    Bitboard reach = 0;
    switch (type) {
    case Knight: reach = attacks::knight(move.from); break;
    case Bishop: reach = attacks::bishop(move.from, occ); break;
    case Rook: reach = attacks::rook(move.from, occ); break;
    case Queen: reach = attacks::queen(move.from, occ); break;
    case King: reach = attacks::king(move.from); break;
    default: return false;
    }
    return (reach & square_bb(move.to)) != 0;
}

bool Board::gives_check(const Move& move) const {
    const Color us = side_;
    const Color them = opposite(us);
    const int ksq = king_square(them);
    const Bitboard king_bit = square_bb(ksq);
    Bitboard occ = (occupied() ^ square_bb(move.from)) | square_bb(move.to);
    if ((move.flags & EnPassant) != 0U) occ &= ~square_bb(move.to - pawn_push_delta(us));
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        occ = (occ & ~square_bb(rook_from)) | square_bb(rook_to);
        if ((attacks::rook(rook_to, occ) & king_bit) != 0) return true;
    }
    const int type = move.is_promotion() ? move.promotion : piece_type(squares_[move.from]);
    Bitboard direct = 0;
    switch (type) {
    case Pawn: direct = attacks::pawn(us, move.to); break;
    case Knight: direct = attacks::knight(move.to); break;
    case Bishop: direct = attacks::bishop(move.to, occ); break;
    case Rook: direct = attacks::rook(move.to, occ); break;
    case Queen: direct = attacks::queen(move.to, occ); break;
    default: break;
    }
    if ((direct & king_bit) != 0) return true;
    const Bitboard moved = square_bb(move.from);
    const Bitboard diagonals = (pieces(us, Bishop) | pieces(us, Queen)) & ~moved;
    const Bitboard lines = (pieces(us, Rook) | pieces(us, Queen)) & ~moved;
    if (diagonals != 0 && (attacks::bishop(ksq, occ) & diagonals) != 0) return true;
    return lines != 0 && (attacks::rook(ksq, occ) & lines) != 0;
}

bool Board::has_legal_en_passant_capture() const {
    if (ep_square_ < 0) return false;
    const Color us = side_;
    Bitboard candidates = attacks::pawn(opposite(us), ep_square_) & pieces(us, Pawn);
    if (candidates == 0) return false;
    const int king = king_square(us);
    const int captured_square = ep_square_ - pawn_push_delta(us);
    const Bitboard captured_bit = square_bb(captured_square);
    while (candidates != 0) {
        const int from = pop_lsb(candidates);
        const Bitboard occupancy = ((occupied() & ~square_bb(from)) & ~captured_bit) | square_bb(ep_square_);
        if (!square_attacked_with_occupancy(king, opposite(us), occupancy, captured_bit)) return true;
    }
    return false;
}

bool Board::make_move(const Move& move, Undo& undo) {
    const Color us = side_;
    const Color them = opposite(us);
    const Piece moving = squares_[move.from];
    undo.captured = squares_[move.to];
    undo.castling = castling_;
    undo.ep_square = ep_square_;
    undo.halfmove = halfmove_;
    undo.fullmove = fullmove_;
    undo.key = key_;
    undo.pawn_key = pawn_key_;
    undo.checkers = checkers_;
    undo.plies_from_null = plies_from_null_;

    if (ep_square_ >= 0 && has_legal_en_passant_capture()) {
        key_ ^= Z.ep[static_cast<std::size_t>(file_of(ep_square_))];
    }
    ep_square_ = -1;
    halfmove_ = static_cast<std::uint16_t>(std::min<int>(halfmove_ + 1, 65535));

    if ((move.flags & EnPassant) != 0U) {
        const int captured_square = move.to - pawn_push_delta(us);
        undo.captured = squares_[static_cast<std::size_t>(captured_square)];
        key_ ^= piece_key(captured_square, undo.captured);
        pawn_key_ ^= piece_key(captured_square, undo.captured);
        remove_piece(captured_square);
    } else if (undo.captured != Empty) {
        key_ ^= piece_key(move.to, undo.captured);
        if (piece_type(undo.captured) == Pawn) pawn_key_ ^= piece_key(move.to, undo.captured);
        remove_piece(move.to);
    }
    if (undo.captured != Empty || piece_type(moving) == Pawn) halfmove_ = 0;

    key_ ^= piece_key(move.from, moving);
    if (piece_type(moving) == Pawn) pawn_key_ ^= piece_key(move.from, moving);
    move_piece(move.from, move.to);
    if (move.is_promotion()) {
        const Piece promoted = make_piece(us, move.promotion);
        remove_piece(move.to);
        put_piece(promoted, move.to);
        key_ ^= piece_key(move.to, promoted);
    } else {
        key_ ^= piece_key(move.to, moving);
        if (piece_type(moving) == Pawn) pawn_key_ ^= piece_key(move.to, moving);
    }
    if (piece_type(moving) == King) king_squares_[static_cast<std::size_t>(us)] = move.to;

    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        const Piece rook = squares_[static_cast<std::size_t>(rook_from)];
        key_ ^= piece_key(rook_from, rook) ^ piece_key(rook_to, rook);
        move_piece(rook_from, rook_to);
    }

    key_ ^= Z.castling[castling_];
    castling_ &= static_cast<std::uint8_t>(CastlingMasks[move.from] & CastlingMasks[move.to]);
    key_ ^= Z.castling[castling_];

    if ((move.flags & DoublePush) != 0U) ep_square_ = static_cast<std::int8_t>((move.from + move.to) / 2);
    if (us == Black) fullmove_ = static_cast<std::uint16_t>(std::min<int>(fullmove_ + 1, 65535));
    side_ = them;
    key_ ^= Z.side;
    if (ep_square_ >= 0 && has_legal_en_passant_capture()) {
        key_ ^= Z.ep[static_cast<std::size_t>(file_of(ep_square_))];
    }
    checkers_ = attackers_to(king_square(them), occupied()) & occupied(us);
    plies_from_null_ = static_cast<std::uint16_t>(std::min<int>(plies_from_null_ + 1, 1024));
    key_history_.push_back(key_);
    return true;
}

void Board::unmake_move(const Move& move, const Undo& undo) {
    key_history_.pop_back();
    side_ = opposite(side_);
    const Color us = side_;
    if (move.is_promotion()) {
        remove_piece(move.to);
        put_piece(make_piece(us, Pawn), move.to);
    }
    move_piece(move.to, move.from);
    if (piece_type(squares_[move.from]) == King) king_squares_[static_cast<std::size_t>(us)] = move.from;
    if ((move.flags & EnPassant) != 0U) {
        put_piece(undo.captured, move.to - pawn_push_delta(us));
    } else if (undo.captured != Empty) {
        put_piece(undo.captured, move.to);
    }
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        move_piece(rook_to, rook_from);
    }
    castling_ = undo.castling;
    ep_square_ = undo.ep_square;
    halfmove_ = undo.halfmove;
    fullmove_ = undo.fullmove;
    key_ = undo.key;
    pawn_key_ = undo.pawn_key;
    checkers_ = undo.checkers;
    plies_from_null_ = undo.plies_from_null;
}

void Board::make_null_move(NullUndo& undo) {
    undo.ep_square = ep_square_;
    undo.key = key_;
    undo.halfmove = halfmove_;
    undo.plies_from_null = plies_from_null_;
    undo.checkers = checkers_;
    if (ep_square_ >= 0 && has_legal_en_passant_capture()) {
        key_ ^= Z.ep[static_cast<std::size_t>(file_of(ep_square_))];
    }
    ep_square_ = -1;
    side_ = opposite(side_);
    key_ ^= Z.side;
    halfmove_ = static_cast<std::uint16_t>(std::min<int>(halfmove_ + 1, 65535));
    plies_from_null_ = 0;
    checkers_ = 0;
    key_history_.push_back(key_);
}

void Board::unmake_null_move(const NullUndo& undo) {
    key_history_.pop_back();
    side_ = opposite(side_);
    ep_square_ = undo.ep_square;
    key_ = undo.key;
    halfmove_ = undo.halfmove;
    plies_from_null_ = undo.plies_from_null;
    checkers_ = undo.checkers;
}

std::optional<Move> Board::parse_uci(std::string_view text) {
    if (text.size() != 4 && text.size() != 5) return std::nullopt;
    for (const Move move : legal_moves()) {
        if (move_to_uci(move) == text) return move;
    }
    return std::nullopt;
}

std::string Board::move_to_uci(const Move& move) {
    std::string text;
    text += static_cast<char>('a' + file_of(move.from));
    text += static_cast<char>('1' + rank_of(move.from));
    text += static_cast<char>('a' + file_of(move.to));
    text += static_cast<char>('1' + rank_of(move.to));
    if (move.is_promotion()) {
        constexpr std::array<char, 7> promotion_chars{' ', ' ', 'n', 'b', 'r', 'q', ' '};
        text += promotion_chars[move.promotion];
    }
    return text;
}

std::uint64_t Board::perft(int depth) {
    if (depth <= 0) return 1;
    MoveList moves;
    generate_pseudo_legal(moves, false);
    if (depth == 1) {
        std::uint64_t count = 0;
        for (const Move move : moves) count += is_legal(move) ? 1 : 0;
        return count;
    }
    std::uint64_t nodes = 0;
    for (const Move move : moves) {
        if (!is_legal(move)) continue;
        Undo undo;
        (void)make_move(move, undo);
        nodes += perft(depth - 1);
        unmake_move(move, undo);
    }
    return nodes;
}

bool Board::is_repetition() const {
    if (key_history_.size() < 5) return false;
    int matches = 0;
    const std::size_t reversible = std::min<std::size_t>(halfmove_, key_history_.size() - 1);
    const std::size_t begin = key_history_.size() - 1 - reversible;
    for (std::size_t i = begin; i + 1 < key_history_.size(); ++i) {
        if (key_history_[i] == key_) ++matches;
    }
    return matches >= 2;
}

bool Board::is_repetition(std::size_t root_index) const {
    const std::ptrdiff_t size = static_cast<std::ptrdiff_t>(key_history_.size());
    const std::ptrdiff_t span = std::min<std::ptrdiff_t>(std::min<int>(halfmove_, plies_from_null_), size - 1);
    if (span < 4) return false;
    const std::ptrdiff_t limit = size - 1 - span;
    int count = 0;
    for (std::ptrdiff_t i = size - 5; i >= limit; i -= 2) {
        if (key_history_[static_cast<std::size_t>(i)] == key_) {
            if (i >= static_cast<std::ptrdiff_t>(root_index)) return true;
            if (++count >= 2) return true;
        }
    }
    return false;
}

bool Board::can_claim_threefold_by_next_move() const {
    // The position after a reversible move (opponent to move) would be history
    // index `size`. Its window starts after the last irreversible move (halfmove
    // clock + 1 plies back) and strictly after the most recent null move, whose
    // position is virtual. Two earlier occurrences need at least 8 plies.
    const std::ptrdiff_t size = static_cast<std::ptrdiff_t>(key_history_.size());
    const std::ptrdiff_t span = std::min<std::ptrdiff_t>(static_cast<std::ptrdiff_t>(halfmove_) + 1,
                                                         static_cast<std::ptrdiff_t>(plies_from_null_));
    if (span < 8) return false;
    const std::ptrdiff_t lo = std::max<std::ptrdiff_t>(size - span, 0);
    const auto key_at = [this](std::ptrdiff_t i) { return key_history_[static_cast<std::size_t>(i)]; };

    // A claim needs an exactly duplicated key on that parity. The bucket mask only
    // skips comparisons; it never grants anything by itself.
    std::uint64_t buckets = 0;
    bool duplicated = false;
    for (std::ptrdiff_t i = size - 2; i >= lo && !duplicated; i -= 2) {
        const std::uint64_t key = key_at(i);
        const std::uint64_t bucket = 1ULL << (key & 63U);
        if ((buckets & bucket) != 0U) {
            for (std::ptrdiff_t j = i + 2; j <= size - 2; j += 2) {
                if (key_at(j) == key) {
                    duplicated = true;
                    break;
                }
            }
        }
        buckets |= bucket;
    }
    if (!duplicated) return false;

    // Only quiet non-pawn moves can recreate an earlier position: captures, pawn
    // moves and promotions are irreversible, and castling drops a right that every
    // position in the window still had. The resulting key mirrors make_move().
    const std::uint64_t ep_key = ep_square_ >= 0 && has_legal_en_passant_capture()
                                     ? Z.ep[static_cast<std::size_t>(file_of(ep_square_))] : 0;
    const std::uint64_t base = key_ ^ ep_key ^ Z.side ^ Z.castling[castling_];
    MoveList moves;
    generate_pseudo_legal(moves, false);
    for (const Move move : moves) {
        if (move.flags != Quiet) continue;
        const Piece piece = squares_[move.from];
        if (piece_type(piece) == Pawn) continue;
        const auto castling = static_cast<std::uint8_t>(castling_ & CastlingMasks[move.from] & CastlingMasks[move.to]);
        const std::uint64_t next = base ^ Z.castling[castling] ^ piece_key(move.from, piece) ^ piece_key(move.to, piece);
        int count = 0;
        for (std::ptrdiff_t i = size - 2; i >= lo && count < 2; i -= 2) {
            if (key_at(i) == next) ++count;
        }
        if (count >= 2 && is_legal(move)) return true;
    }
    return false;
}

bool Board::is_insufficient_material() const {
    const Bitboard pawns_rooks_queens = pieces(Pawn) | pieces(Rook) | pieces(Queen);
    if (pawns_rooks_queens != 0) return false;
    const Bitboard knights = pieces(Knight);
    const Bitboard bishops = pieces(Bishop);
    const int minor_count = popcount(knights | bishops);
    if (minor_count <= 1) return true;
    return knights == 0 && ((bishops & DarkSquares) == 0 || (bishops & LightSquares) == 0);
}

bool Board::has_non_pawn_material(Color color) const {
    return (pieces(color, Knight) | pieces(color, Bishop) | pieces(color, Rook) | pieces(color, Queen)) != 0;
}

bool Board::see_ge(const Move& move, int threshold) const {
    if (move.is_castle()) return 0 >= threshold;
    const Color us = side_;
    const int from = move.from;
    const int to = move.to;
    const int captured_square = (move.flags & EnPassant) != 0U ? to - pawn_push_delta(us) : to;
    const int target_rank = rank_of(to);
    if ((target_rank == 0 || target_rank == 7) &&
        piece_type(squares_[static_cast<std::size_t>(from)]) != King) {
        const Color promoter = target_rank == 7 ? White : Black;
        const Bitboard promoting_pawns =
            pieces(promoter, Pawn) & attacks::pawn(opposite(promoter), to) &
            ~(square_bb(from) | square_bb(captured_square));
        if (promoting_pawns != 0) {
            return promotion_recapture_exchange(*this, move, captured_square) >= threshold;
        }
    }
    int swap = SeeValue[static_cast<std::size_t>(piece_type(squares_[static_cast<std::size_t>(captured_square)]))] - threshold;
    int attacker_value = SeeValue[static_cast<std::size_t>(piece_type(squares_[static_cast<std::size_t>(from)]))];
    if (move.is_promotion()) {
        swap += SeeValue[move.promotion] - SeeValue[Pawn];
        attacker_value = SeeValue[move.promotion];
    }
    if (swap < 0) return false;
    swap = attacker_value - swap;
    if (swap <= 0) return true;

    Bitboard occupancy = (occupied() ^ square_bb(from) ^ square_bb(captured_square)) | square_bb(to);
    Color stm = us;
    Bitboard attackers = attackers_to(to, occupancy);
    const Bitboard diagonals = pieces(Bishop) | pieces(Queen);
    const Bitboard lines = pieces(Rook) | pieces(Queen);
    int result = 1;
    while (true) {
        stm = opposite(stm);
        attackers &= occupancy;
        Bitboard stm_attackers = attackers & occupied(stm);
        // Every candidate only removes its own origin; the target stays occupied.
        // Existing checks reject every non-king; singleton ray blockers identify
        // exactly the origins whose departure would expose a live enemy slider.
        const Bitboard king_attackers = stm_attackers & pieces(stm, King);
        if ((stm_attackers & ~king_attackers) != 0) {
            const Color enemy = opposite(stm);
            const int king = king_square(stm);
            const Bitboard live = occupancy & ~square_bb(to);
            const Bitboard queens = pieces(enemy, Queen) & live;
            bool checked =
                (attacks::pawn(stm, king) & pieces(enemy, Pawn) & live) != 0 ||
                (attacks::knight(king) & pieces(enemy, Knight) & live) != 0 ||
                (attacks::king(king) & pieces(enemy, King) & live) != 0;
            Bitboard pinners =
                (attacks::bishop(king, 0) & ((pieces(enemy, Bishop) & live) | queens)) |
                (attacks::rook(king, 0) & ((pieces(enemy, Rook) & live) | queens));
            Bitboard forbidden = 0;
            while (!checked && pinners != 0) {
                const int pinner = pop_lsb(pinners);
                const Bitboard blockers = attacks::between(king, pinner) & occupancy;
                if (blockers == 0) checked = true;
                else if (!more_than_one(blockers)) forbidden |= blockers;
            }
            stm_attackers = checked ? king_attackers : stm_attackers & ~forbidden;
        }
        if (stm_attackers == 0) break;
        result ^= 1;
        Bitboard bb = 0;
        if ((bb = stm_attackers & pieces(stm, Pawn)) != 0) {
            if ((swap = SeeValue[Pawn] - swap) < result) break;
            occupancy ^= square_bb(lsb(bb));
            attackers |= attacks::bishop(to, occupancy) & diagonals;
        } else if ((bb = stm_attackers & pieces(stm, Knight)) != 0) {
            if ((swap = SeeValue[Knight] - swap) < result) break;
            occupancy ^= square_bb(lsb(bb));
        } else if ((bb = stm_attackers & pieces(stm, Bishop)) != 0) {
            if ((swap = SeeValue[Bishop] - swap) < result) break;
            occupancy ^= square_bb(lsb(bb));
            attackers |= attacks::bishop(to, occupancy) & diagonals;
        } else if ((bb = stm_attackers & pieces(stm, Rook)) != 0) {
            if ((swap = SeeValue[Rook] - swap) < result) break;
            occupancy ^= square_bb(lsb(bb));
            attackers |= attacks::rook(to, occupancy) & lines;
        } else if ((bb = stm_attackers & pieces(stm, Queen)) != 0) {
            if ((swap = SeeValue[Queen] - swap) < result) break;
            occupancy ^= square_bb(lsb(bb));
            attackers |= (attacks::bishop(to, occupancy) & diagonals) | (attacks::rook(to, occupancy) & lines);
        } else {
            // Only the king is left to capture; it may do so only if the
            // opponent has no further attackers.
            return (attackers & ~occupied(stm)) != 0 ? result ^ 1 : result;
        }
    }
    return result != 0;
}

int Board::static_exchange(const Move& move) const {
    int low = -2000;
    int high = 2000;
    while (low < high) {
        const int mid = low + (high - low + 1) / 2;
        if (see_ge(move, mid)) low = mid;
        else high = mid - 1;
    }
    return low;
}

std::uint64_t Board::compute_key() const {
    std::uint64_t key = 0;
    for (int square = 0; square < 64; ++square) {
        const Piece piece = squares_[static_cast<std::size_t>(square)];
        if (piece != Empty) key ^= piece_key(square, piece);
    }
    key ^= Z.castling[castling_];
    if (has_legal_en_passant_capture()) key ^= Z.ep[static_cast<std::size_t>(file_of(ep_square_))];
    if (side_ == Black) key ^= Z.side;
    return key;
}

std::uint64_t Board::compute_pawn_key() const {
    std::uint64_t key = 0;
    Bitboard pawns = pieces(Pawn);
    while (pawns != 0) {
        const int square = pop_lsb(pawns);
        key ^= piece_key(square, squares_[static_cast<std::size_t>(square)]);
    }
    return key;
}

} // namespace forge
