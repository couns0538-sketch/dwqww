#include "forge/board.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cctype>
#include <sstream>

namespace forge {
namespace {

constexpr std::uint8_t WhiteKingSide = 1;
constexpr std::uint8_t WhiteQueenSide = 2;
constexpr std::uint8_t BlackKingSide = 4;
constexpr std::uint8_t BlackQueenSide = 8;

constexpr bool on_board(int square) { return square >= 0 && square < 64; }
constexpr int file_of(int square) { return square & 7; }
constexpr int rank_of(int square) { return square >> 3; }
constexpr int abs_int(int value) { return value < 0 ? -value : value; }
constexpr std::array<int, 7> SeeValue{0, 100, 320, 330, 500, 900, 20000};

template <std::size_t N>
constexpr std::array<std::array<std::int8_t, N>, 64> make_jump_targets(const std::array<int, N>& offsets,
                                                                       int max_file_delta) {
    std::array<std::array<std::int8_t, N>, 64> targets{};
    for (auto& row : targets) row.fill(-1);
    for (int square = 0; square < 64; ++square) {
        for (std::size_t i = 0; i < N; ++i) {
            const int target = square + offsets[i];
            if (on_board(target) && abs_int(file_of(target) - file_of(square)) <= max_file_delta) {
                targets[static_cast<std::size_t>(square)][i] = static_cast<std::int8_t>(target);
            }
        }
    }
    return targets;
}

constexpr std::array<int, 8> KnightOffsets{17, 15, 10, 6, -6, -10, -15, -17};
constexpr std::array<int, 8> KingOffsets{9, 8, 7, 1, -1, -7, -8, -9};
constexpr std::array<int, 8> RayDirections{9, 7, -7, -9, 8, -8, 1, -1};
constexpr auto KnightTargets = make_jump_targets(KnightOffsets, 2);
constexpr auto KingTargets = make_jump_targets(KingOffsets, 1);

constexpr std::array<std::array<std::array<std::int8_t, 7>, 8>, 64> make_rays() {
    std::array<std::array<std::array<std::int8_t, 7>, 8>, 64> rays{};
    for (auto& square : rays) for (auto& ray : square) ray.fill(-1);
    for (int square = 0; square < 64; ++square) {
        for (std::size_t d = 0; d < RayDirections.size(); ++d) {
            int from = square;
            std::size_t step = 0;
            while (step < 7) {
                const int target = from + RayDirections[d];
                if (!on_board(target) || abs_int(file_of(target) - file_of(from)) > 1) break;
                rays[static_cast<std::size_t>(square)][d][step++] = static_cast<std::int8_t>(target);
                from = target;
            }
        }
    }
    return rays;
}

constexpr auto RayTargets = make_rays();

template <std::size_t N>
constexpr std::array<std::uint64_t, 64> make_jump_masks(
    const std::array<std::array<std::int8_t, N>, 64>& targets) {
    std::array<std::uint64_t, 64> masks{};
    for (std::size_t square = 0; square < masks.size(); ++square) {
        for (const std::int8_t target : targets[square]) {
            if (target >= 0) masks[square] |= 1ULL << target;
        }
    }
    return masks;
}

constexpr std::array<std::array<std::uint64_t, 8>, 64> make_ray_masks() {
    std::array<std::array<std::uint64_t, 8>, 64> masks{};
    for (std::size_t square = 0; square < masks.size(); ++square) {
        for (std::size_t direction = 0; direction < 8; ++direction) {
            for (const std::int8_t target : RayTargets[square][direction]) {
                if (target < 0) break;
                masks[square][direction] |= 1ULL << target;
            }
        }
    }
    return masks;
}

constexpr std::array<std::array<std::uint64_t, 64>, 2> make_pawn_attackers() {
    std::array<std::array<std::uint64_t, 64>, 2> masks{};
    for (int square = 0; square < 64; ++square) {
        for (int color_index = 0; color_index < 2; ++color_index) {
            const Color color = static_cast<Color>(color_index);
            const int step = color == White ? -8 : 8;
            for (const int delta : {step - 1, step + 1}) {
                const int from = square + delta;
                if (on_board(from) && abs_int(file_of(from) - file_of(square)) == 1) {
                    masks[static_cast<std::size_t>(color)][static_cast<std::size_t>(square)] |=
                        1ULL << from;
                }
            }
        }
    }
    return masks;
}

constexpr auto KnightMasks = make_jump_masks(KnightTargets);
constexpr auto KingMasks = make_jump_masks(KingTargets);
constexpr auto RayMasks = make_ray_masks();
constexpr auto PawnAttackers = make_pawn_attackers();

bool same_color(Piece a, Piece b) {
    return a != Empty && b != Empty && (is_white(a) == is_white(b));
}

Piece char_to_piece(char c) {
    constexpr std::string_view chars = " PNBRQKpnbrqk";
    const auto position = chars.find(c);
    return position == std::string_view::npos ? Empty : static_cast<Piece>(position);
}

char piece_to_char(Piece piece) {
    constexpr std::array<char, 13> chars{' ', 'P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k'};
    return chars[static_cast<std::size_t>(piece)];
}

std::uint64_t mix(std::uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27U)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31U);
}

std::uint64_t piece_key(int square, Piece piece) {
    return mix(1 + static_cast<std::uint64_t>(square) * 13U + static_cast<std::uint64_t>(piece));
}

bool square_attacked_on(const std::array<Piece, 64>& squares, int square, Color by) {
    const Piece pawn = by == White ? WP : BP;
    const int pawn_step = by == White ? -8 : 8;
    for (int delta : {pawn_step - 1, pawn_step + 1}) {
        const int from = square + delta;
        if (on_board(from) && std::abs(file_of(from) - file_of(square)) == 1 &&
            squares[static_cast<std::size_t>(from)] == pawn) return true;
    }
    const Piece knight = by == White ? WN : BN;
    for (const std::int8_t from : KnightTargets[static_cast<std::size_t>(square)]) {
        if (from >= 0 && squares[static_cast<std::size_t>(from)] == knight) return true;
    }
    const Piece king = by == White ? WK : BK;
    for (const std::int8_t from : KingTargets[static_cast<std::size_t>(square)]) {
        if (from >= 0 && squares[static_cast<std::size_t>(from)] == king) return true;
    }
    auto ray = [&](int direction_index, Piece bishop_or_rook) {
        for (const std::int8_t next : RayTargets[static_cast<std::size_t>(square)]
                                                 [static_cast<std::size_t>(direction_index)]) {
            if (next < 0) break;
            const Piece piece = squares[static_cast<std::size_t>(next)];
            if (piece != Empty) {
                const Piece queen = by == White ? WQ : BQ;
                return piece == bishop_or_rook || piece == queen;
            }
        }
        return false;
    };
    const Piece bishop = by == White ? WB : BB;
    const Piece rook = by == White ? WR : BR;
    return ray(0, bishop) || ray(1, bishop) || ray(2, bishop) || ray(3, bishop) ||
           ray(4, rook) || ray(5, rook) || ray(6, rook) || ray(7, rook);
}

bool attacks_target(const std::array<Piece, 64>& squares, int from, int target, Piece piece) {
    const int df = file_of(target) - file_of(from);
    const int dr = rank_of(target) - rank_of(from);
    const int type = piece_type(piece);
    if (type == 1) return is_white(piece) ? dr == 1 && std::abs(df) == 1
                                          : dr == -1 && std::abs(df) == 1;
    if (type == 2) return (std::abs(df) == 1 && std::abs(dr) == 2) ||
                          (std::abs(df) == 2 && std::abs(dr) == 1);
    if (type == 6) return std::max(std::abs(df), std::abs(dr)) == 1;
    const bool diagonal = std::abs(df) == std::abs(dr) && df != 0;
    const bool straight = (df == 0) != (dr == 0);
    if ((type == 3 && !diagonal) || (type == 4 && !straight) ||
        (type == 5 && !diagonal && !straight)) return false;
    const int file_step = (df > 0) - (df < 0);
    const int rank_step = (dr > 0) - (dr < 0);
    int file = file_of(from) + file_step;
    int rank = rank_of(from) + rank_step;
    while (file != file_of(target) || rank != rank_of(target)) {
        if (squares[static_cast<std::size_t>(rank * 8 + file)] != Empty) return false;
        file += file_step;
        rank += rank_step;
    }
    return true;
}

int least_attacker(std::array<Piece, 64>& squares,
                   const std::array<std::uint64_t, 13>& bitboards, int target, Color side) {
    for (int type = 1; type <= 6; ++type) {
        const Piece piece = static_cast<Piece>((side == White ? 0 : 6) + type);
        std::uint64_t candidates = bitboards[static_cast<std::size_t>(piece)];
        while (candidates != 0) {
            const int square = static_cast<int>(std::countr_zero(candidates));
            candidates &= candidates - 1;
            if (!attacks_target(squares, square, target, piece)) continue;
            // SEE must not treat an absolutely pinned piece, or a king moving
            // into check, as a legal recapturer. Probe only the local mailbox;
            // the bitboards are unchanged until an attacker is selected.
            const std::uint64_t kings = bitboards[side == White ? WK : BK];
            if (kings == 0) return -1;
            const int king = type == 6 ? target : static_cast<int>(std::countr_zero(kings));
            const Piece captured = squares[static_cast<std::size_t>(target)];
            squares[static_cast<std::size_t>(square)] = Empty;
            squares[static_cast<std::size_t>(target)] = piece;
            const bool legal = !square_attacked_on(squares, king, opposite(side));
            squares[static_cast<std::size_t>(square)] = piece;
            squares[static_cast<std::size_t>(target)] = captured;
            if (legal) return square;
        }
    }
    return -1;
}

} // namespace

Board::Board() {
    (void)set_fen(StandardStartFen);
}

bool Board::set_fen(std::string_view fen_text, std::string* error) {
    std::istringstream input{std::string(fen_text)};
    std::string placement;
    std::string side;
    std::string castling;
    std::string ep;
    int halfmove = 0;
    int fullmove = 1;
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
    if (std::abs(file_of(king_squares[White]) - file_of(king_squares[Black])) <= 1 &&
        std::abs(rank_of(king_squares[White]) - rank_of(king_squares[Black])) <= 1) {
        if (error != nullptr) *error = "kings may not be adjacent";
        return false;
    }
    const Color parsed_side = side == "w" ? White : Black;
    const Color side_just_moved = opposite(parsed_side);
    if (square_attacked_on(parsed, king_squares[side_just_moved], parsed_side)) {
        if (error != nullptr) *error = "side that moved left its king in check";
        return false;
    }
    for (const Color color : {White, Black}) {
        const int offset = color == White ? 0 : 6;
        const int pawns = piece_counts[static_cast<std::size_t>(WP + offset)];
        int total = 0;
        for (int type = 1; type <= 6; ++type) {
            total += piece_counts[static_cast<std::size_t>(type + offset)];
        }
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

    squares_ = parsed;
    king_squares_ = {king_squares[White], king_squares[Black]};
    bitboards_ = {};
    occupied_ = {};
    for (int square = 0; square < 64; ++square) {
        const Piece piece = squares_[static_cast<std::size_t>(square)];
        if (piece != Empty) {
            const std::uint64_t bit = 1ULL << square;
            bitboards_[static_cast<std::size_t>(piece)] |= bit;
            occupied_[static_cast<std::size_t>(is_white(piece) ? White : Black)] |= bit;
        }
    }
    side_ = side == "w" ? White : Black;
    castling_ = rights;
    ep_square_ = static_cast<std::int8_t>(ep_square);
    halfmove_ = static_cast<std::uint16_t>(std::min(halfmove, 65535));
    fullmove_ = static_cast<std::uint16_t>(std::min(fullmove, 65535));
    key_ = compute_key();
    repetition_context_ = mix(key_);
    pawn_key_ = 0;
    for (int square = 0; square < 64; ++square) {
        const Piece piece = squares_[static_cast<std::size_t>(square)];
        if (piece == WP || piece == BP) pawn_key_ ^= piece_key(square, piece);
    }
    key_history_.clear();
    key_history_.push_back(key_);
    return true;
}

std::uint64_t Board::transposition_history_key() const {
    // Future repetition adjudication depends on occurrence counts in the known
    // reversible legal history, not merely the current position. Addition makes
    // this an order-independent multiset fingerprint. Irreversible moves reset it.
    return key_ ^ std::rotl(repetition_context_, 23);
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

void Board::add_pawn_moves(MoveList& moves, int square, bool captures_only) const {
    const Piece pawn = squares_[static_cast<std::size_t>(square)];
    const bool white = pawn == WP;
    const int direction = white ? 8 : -8;
    const int start_rank = white ? 1 : 6;
    const int promotion_rank = white ? 6 : 1;
    const std::array<std::uint8_t, 4> promotions{5, 4, 3, 2};
    auto add = [&](int to, std::uint8_t flags) {
        if (rank_of(square) == promotion_rank) {
            for (std::uint8_t promotion : promotions) {
                moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(to), promotion,
                                     static_cast<std::uint8_t>(flags | Promotion)});
            }
        } else {
            moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(to), 0, flags});
        }
    };

    const int one = square + direction;
    if ((!captures_only || rank_of(square) == promotion_rank) && on_board(one) && squares_[static_cast<std::size_t>(one)] == Empty) {
        add(one, Quiet);
        const int two = one + direction;
        if (!captures_only && rank_of(square) == start_rank && squares_[static_cast<std::size_t>(two)] == Empty) {
            moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(two), 0, DoublePush});
        }
    }
    for (int delta : {direction - 1, direction + 1}) {
        const int to = square + delta;
        if (!on_board(to) || std::abs(file_of(to) - file_of(square)) != 1) continue;
        const Piece target = squares_[static_cast<std::size_t>(to)];
        if (target != Empty && !same_color(pawn, target)) add(to, Capture);
        if (to == ep_square_) add(to, static_cast<std::uint8_t>(Capture | EnPassant));
    }
}

void Board::add_slider_moves(MoveList& moves, int square, int first_direction,
                             int count, bool captures_only) const {
    const Piece piece = squares_[static_cast<std::size_t>(square)];
    for (int i = 0; i < count; ++i) {
        const auto& ray = RayTargets[static_cast<std::size_t>(square)]
                                    [static_cast<std::size_t>(first_direction + i)];
        for (const std::int8_t target_square : ray) {
            if (target_square < 0) break;
            const int to = target_square;
            const Piece target = squares_[static_cast<std::size_t>(to)];
            if (target == Empty) {
                if (!captures_only) moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(to), 0, Quiet});
            } else {
                if (!same_color(piece, target)) moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(to), 0, Capture});
                break;
            }
        }
    }
}

MoveList Board::pseudo_legal_moves(bool captures_only) const {
    MoveList moves;
    moves.reserve(captures_only ? 32U : 64U);

    std::uint64_t pieces_to_move = occupied_[static_cast<std::size_t>(side_)];
    while (pieces_to_move != 0) {
        const int square = static_cast<int>(std::countr_zero(pieces_to_move));
        pieces_to_move &= pieces_to_move - 1;
        const Piece piece = squares_[static_cast<std::size_t>(square)];
        const int type = piece_type(piece);
        if (type == 1) {
            add_pawn_moves(moves, square, captures_only);
        } else if (type == 3) {
            add_slider_moves(moves, square, 0, 4, captures_only);
        } else if (type == 4) {
            add_slider_moves(moves, square, 4, 4, captures_only);
        } else if (type == 5) {
            add_slider_moves(moves, square, 0, 8, captures_only);
        } else {
            const auto& targets = type == 2 ? KnightTargets[static_cast<std::size_t>(square)]
                                            : KingTargets[static_cast<std::size_t>(square)];
            for (const std::int8_t target_square : targets) {
                if (target_square < 0) continue;
                const int to = target_square;
                const Piece target = squares_[static_cast<std::size_t>(to)];
                if (target == Empty) {
                    if (!captures_only) moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(to), 0, Quiet});
                } else if (!same_color(piece, target)) {
                    moves.push_back(Move{static_cast<std::uint8_t>(square), static_cast<std::uint8_t>(to), 0, Capture});
                }
            }
            if (type == 6 && !captures_only && !in_check(side_)) {
                const Color enemy = opposite(side_);
                if (side_ == White && square == 4) {
                    if ((castling_ & WhiteKingSide) != 0U && squares_[5] == Empty && squares_[6] == Empty && squares_[7] == WR &&
                        !square_attacked(5, enemy) && !square_attacked(6, enemy))
                        moves.push_back(Move{4, 6, 0, KingCastle});
                    if ((castling_ & WhiteQueenSide) != 0U && squares_[3] == Empty && squares_[2] == Empty && squares_[1] == Empty && squares_[0] == WR &&
                        !square_attacked(3, enemy) && !square_attacked(2, enemy))
                        moves.push_back(Move{4, 2, 0, QueenCastle});
                } else if (side_ == Black && square == 60) {
                    if ((castling_ & BlackKingSide) != 0U && squares_[61] == Empty && squares_[62] == Empty && squares_[63] == BR &&
                        !square_attacked(61, enemy) && !square_attacked(62, enemy))
                        moves.push_back(Move{60, 62, 0, KingCastle});
                    if ((castling_ & BlackQueenSide) != 0U && squares_[59] == Empty && squares_[58] == Empty && squares_[57] == Empty && squares_[56] == BR &&
                        !square_attacked(59, enemy) && !square_attacked(58, enemy))
                        moves.push_back(Move{60, 58, 0, QueenCastle});
                }
            }
        }
    }
    return moves;
}

bool Board::square_attacked_with_occupancy(int square, Color by, std::uint64_t occupancy,
                                             std::uint64_t removed_attackers) const {
    const std::uint64_t available = ~removed_attackers;
    const Piece pawn = by == White ? WP : BP;
    if ((PawnAttackers[static_cast<std::size_t>(by)][static_cast<std::size_t>(square)] &
         bitboards_[static_cast<std::size_t>(pawn)] & available) != 0) return true;

    const Piece knight = by == White ? WN : BN;
    if ((KnightMasks[static_cast<std::size_t>(square)] &
         bitboards_[static_cast<std::size_t>(knight)] & available) != 0) return true;

    const Piece king = by == White ? WK : BK;
    if ((KingMasks[static_cast<std::size_t>(square)] &
         bitboards_[static_cast<std::size_t>(king)] & available) != 0) return true;

    const std::uint64_t bishops_queens =
        (bitboards_[static_cast<std::size_t>(by == White ? WB : BB)] |
         bitboards_[static_cast<std::size_t>(by == White ? WQ : BQ)]) & available;
    const std::uint64_t rooks_queens =
        (bitboards_[static_cast<std::size_t>(by == White ? WR : BR)] |
         bitboards_[static_cast<std::size_t>(by == White ? WQ : BQ)]) & available;

    for (int direction = 0; direction < 8; ++direction) {
        std::uint64_t blockers = RayMasks[static_cast<std::size_t>(square)]
                                        [static_cast<std::size_t>(direction)] & occupancy;
        if (blockers == 0) continue;
        const int blocker_square = RayDirections[static_cast<std::size_t>(direction)] > 0
            ? static_cast<int>(std::countr_zero(blockers))
            : 63 - static_cast<int>(std::countl_zero(blockers));
        const std::uint64_t blocker = 1ULL << blocker_square;
        if (direction < 4) {
            if ((blocker & bishops_queens) != 0) return true;
        } else if ((blocker & rooks_queens) != 0) {
            return true;
        }
    }
    return false;
}

bool Board::square_attacked(int square, Color by) const {
    return square_attacked_with_occupancy(square, by, occupied_[White] | occupied_[Black]);
}

int Board::king_square(Color color) const {
    return king_squares_[static_cast<std::size_t>(color)];
}

bool Board::in_check(Color color) const {
    const int square = king_square(color);
    return square >= 0 && square_attacked(square, opposite(color));
}

bool Board::make_move(const Move& move, Undo& undo) {
    const Piece moving = squares_[move.from];
    undo = Undo{squares_[move.to], castling_, ep_square_, halfmove_, fullmove_, key_, pawn_key_,
                repetition_context_};
    const bool old_ep_hashed = ep_square_ >= 0 && has_legal_en_passant_capture();
    key_ ^= piece_key(move.from, moving);
    if (undo.captured != Empty) key_ ^= piece_key(move.to, undo.captured);
    if (piece_type(moving) == 1) pawn_key_ ^= piece_key(move.from, moving);
    if (undo.captured == WP || undo.captured == BP) pawn_key_ ^= piece_key(move.to, undo.captured);
    bitboards_[static_cast<std::size_t>(moving)] &= ~(1ULL << move.from);
    if (undo.captured != Empty) bitboards_[static_cast<std::size_t>(undo.captured)] &= ~(1ULL << move.to);
    occupied_[static_cast<std::size_t>(side_)] &= ~(1ULL << move.from);
    if (undo.captured != Empty) occupied_[static_cast<std::size_t>(opposite(side_))] &= ~(1ULL << move.to);
    occupied_[static_cast<std::size_t>(side_)] |= 1ULL << move.to;
    squares_[move.from] = Empty;
    squares_[move.to] = moving;
    if (piece_type(moving) == 6) king_squares_[static_cast<std::size_t>(side_)] = move.to;
    bitboards_[static_cast<std::size_t>(moving)] |= 1ULL << move.to;
    if ((move.flags & EnPassant) != 0U) {
        const int captured_square = side_ == White ? static_cast<int>(move.to) - 8 : static_cast<int>(move.to) + 8;
        undo.captured = squares_[static_cast<std::size_t>(captured_square)];
        if (undo.captured != Empty) key_ ^= piece_key(captured_square, undo.captured);
        if (undo.captured == WP || undo.captured == BP) pawn_key_ ^= piece_key(captured_square, undo.captured);
        if (undo.captured != Empty) {
            bitboards_[static_cast<std::size_t>(undo.captured)] &= ~(1ULL << captured_square);
            occupied_[static_cast<std::size_t>(opposite(side_))] &= ~(1ULL << captured_square);
        }
        squares_[static_cast<std::size_t>(captured_square)] = Empty;
    }
    if ((move.flags & Promotion) != 0U) {
        const Piece promoted = static_cast<Piece>((side_ == White ? 0 : 6) + move.promotion);
        bitboards_[static_cast<std::size_t>(moving)] &= ~(1ULL << move.to);
        bitboards_[static_cast<std::size_t>(promoted)] |= 1ULL << move.to;
        squares_[move.to] = promoted;
    } else if (piece_type(moving) == 1) {
        pawn_key_ ^= piece_key(move.to, moving);
    }
    key_ ^= piece_key(move.to, squares_[move.to]);
    if ((move.flags & KingCastle) != 0U) {
        const int rook_from = side_ == White ? 7 : 63;
        const int rook_to = side_ == White ? 5 : 61;
        key_ ^= piece_key(rook_from, squares_[static_cast<std::size_t>(rook_from)]);
        key_ ^= piece_key(rook_to, squares_[static_cast<std::size_t>(rook_from)]);
        squares_[static_cast<std::size_t>(rook_to)] = squares_[static_cast<std::size_t>(rook_from)];
        const Piece rook = squares_[static_cast<std::size_t>(rook_from)];
        bitboards_[static_cast<std::size_t>(rook)] &= ~(1ULL << rook_from);
        bitboards_[static_cast<std::size_t>(rook)] |= 1ULL << rook_to;
        occupied_[static_cast<std::size_t>(side_)] &= ~(1ULL << rook_from);
        occupied_[static_cast<std::size_t>(side_)] |= 1ULL << rook_to;
        squares_[static_cast<std::size_t>(rook_from)] = Empty;
    } else if ((move.flags & QueenCastle) != 0U) {
        const int rook_from = side_ == White ? 0 : 56;
        const int rook_to = side_ == White ? 3 : 59;
        key_ ^= piece_key(rook_from, squares_[static_cast<std::size_t>(rook_from)]);
        key_ ^= piece_key(rook_to, squares_[static_cast<std::size_t>(rook_from)]);
        squares_[static_cast<std::size_t>(rook_to)] = squares_[static_cast<std::size_t>(rook_from)];
        const Piece rook = squares_[static_cast<std::size_t>(rook_from)];
        bitboards_[static_cast<std::size_t>(rook)] &= ~(1ULL << rook_from);
        bitboards_[static_cast<std::size_t>(rook)] |= 1ULL << rook_to;
        occupied_[static_cast<std::size_t>(side_)] &= ~(1ULL << rook_from);
        occupied_[static_cast<std::size_t>(side_)] |= 1ULL << rook_to;
        squares_[static_cast<std::size_t>(rook_from)] = Empty;
    }

    key_ ^= mix(900 + castling_);
    if (moving == WK) castling_ &= static_cast<std::uint8_t>(~(WhiteKingSide | WhiteQueenSide));
    if (moving == BK) castling_ &= static_cast<std::uint8_t>(~(BlackKingSide | BlackQueenSide));
    if (move.from == 0 || move.to == 0) castling_ &= static_cast<std::uint8_t>(~WhiteQueenSide);
    if (move.from == 7 || move.to == 7) castling_ &= static_cast<std::uint8_t>(~WhiteKingSide);
    if (move.from == 56 || move.to == 56) castling_ &= static_cast<std::uint8_t>(~BlackQueenSide);
    if (move.from == 63 || move.to == 63) castling_ &= static_cast<std::uint8_t>(~BlackKingSide);
    key_ ^= mix(900 + castling_);
    if (old_ep_hashed) key_ ^= mix(1000 + static_cast<std::uint64_t>(file_of(ep_square_)));
    ep_square_ = (move.flags & DoublePush) != 0U ? static_cast<std::int8_t>((move.from + move.to) / 2) : -1;
    halfmove_ = (piece_type(moving) == 1 || undo.captured != Empty)
        ? 0 : static_cast<std::uint16_t>(std::min<int>(halfmove_ + 1, 65535));
    if (side_ == Black) fullmove_ = static_cast<std::uint16_t>(std::min<int>(fullmove_ + 1, 65535));
    side_ = opposite(side_);
    key_ ^= mix(1100);
    if (ep_square_ >= 0 && has_legal_en_passant_capture()) {
        key_ ^= mix(1000 + static_cast<std::uint64_t>(file_of(ep_square_)));
    }
    const bool irreversible = piece_type(moving) == 1 || undo.captured != Empty ||
                              castling_ != undo.castling;
    if (irreversible) repetition_context_ = 0;
    repetition_context_ += mix(key_);
    key_history_.push_back(key_);
    return true;
}

void Board::unmake_move(const Move& move, const Undo& undo) {
    key_history_.pop_back();
    side_ = opposite(side_);
    fullmove_ = undo.fullmove;
    const Piece moving = squares_[move.to];
    const Piece original = (move.flags & Promotion) != 0U ? (side_ == White ? WP : BP) : moving;
    occupied_[static_cast<std::size_t>(side_)] &= ~(1ULL << move.to);
    occupied_[static_cast<std::size_t>(side_)] |= 1ULL << move.from;
    bitboards_[static_cast<std::size_t>(moving)] &= ~(1ULL << move.to);
    bitboards_[static_cast<std::size_t>(original)] |= 1ULL << move.from;
    squares_[move.from] = original;
    if (piece_type(original) == 6) king_squares_[static_cast<std::size_t>(side_)] = move.from;
    squares_[move.to] = undo.captured;
    if (undo.captured != Empty && (move.flags & EnPassant) == 0U) {
        bitboards_[static_cast<std::size_t>(undo.captured)] |= 1ULL << move.to;
        occupied_[static_cast<std::size_t>(opposite(side_))] |= 1ULL << move.to;
    }
    if ((move.flags & EnPassant) != 0U) {
        squares_[move.to] = Empty;
        const int captured_square = side_ == White ? static_cast<int>(move.to) - 8 : static_cast<int>(move.to) + 8;
        squares_[static_cast<std::size_t>(captured_square)] = undo.captured;
        if (undo.captured != Empty) {
            bitboards_[static_cast<std::size_t>(undo.captured)] |= 1ULL << captured_square;
            occupied_[static_cast<std::size_t>(opposite(side_))] |= 1ULL << captured_square;
        }
    }
    if ((move.flags & KingCastle) != 0U) {
        const int rook_from = side_ == White ? 7 : 63;
        const int rook_to = side_ == White ? 5 : 61;
        squares_[static_cast<std::size_t>(rook_from)] = squares_[static_cast<std::size_t>(rook_to)];
        const Piece rook = squares_[static_cast<std::size_t>(rook_to)];
        bitboards_[static_cast<std::size_t>(rook)] &= ~(1ULL << rook_to);
        bitboards_[static_cast<std::size_t>(rook)] |= 1ULL << rook_from;
        occupied_[static_cast<std::size_t>(side_)] &= ~(1ULL << rook_to);
        occupied_[static_cast<std::size_t>(side_)] |= 1ULL << rook_from;
        squares_[static_cast<std::size_t>(rook_to)] = Empty;
    } else if ((move.flags & QueenCastle) != 0U) {
        const int rook_from = side_ == White ? 0 : 56;
        const int rook_to = side_ == White ? 3 : 59;
        squares_[static_cast<std::size_t>(rook_from)] = squares_[static_cast<std::size_t>(rook_to)];
        const Piece rook = squares_[static_cast<std::size_t>(rook_to)];
        bitboards_[static_cast<std::size_t>(rook)] &= ~(1ULL << rook_to);
        bitboards_[static_cast<std::size_t>(rook)] |= 1ULL << rook_from;
        occupied_[static_cast<std::size_t>(side_)] &= ~(1ULL << rook_to);
        occupied_[static_cast<std::size_t>(side_)] |= 1ULL << rook_from;
        squares_[static_cast<std::size_t>(rook_to)] = Empty;
    }
    castling_ = undo.castling;
    ep_square_ = undo.ep_square;
    halfmove_ = undo.halfmove;
    key_ = undo.key;
    pawn_key_ = undo.pawn_key;
    repetition_context_ = undo.repetition_context;
}

void Board::make_null_move(NullUndo& undo) {
    undo = NullUndo{ep_square_, key_};
    if (ep_square_ >= 0 && has_legal_en_passant_capture()) {
        key_ ^= mix(1000 + static_cast<std::uint64_t>(file_of(ep_square_)));
    }
    ep_square_ = -1;
    side_ = opposite(side_);
    key_ ^= mix(1100);
}

void Board::unmake_null_move(const NullUndo& undo) {
    side_ = opposite(side_);
    ep_square_ = undo.ep_square;
    key_ = undo.key;
}

MoveList Board::legal_moves(bool captures_only) {
    MoveList moves = pseudo_legal_moves(captures_only);
    std::size_t write = 0;
    for (const Move move : moves) {
        if (is_legal_after(move)) moves[write++] = move;
    }
    moves.resize(write);
    return moves;
}

bool Board::is_legal_after(const Move& move) const {
    const Color moving_side = side_;
    const Piece moving = squares_[move.from];
    std::uint64_t occupancy = occupied_[White] | occupied_[Black];
    const std::uint64_t from_bit = 1ULL << move.from;
    const std::uint64_t to_bit = 1ULL << move.to;
    occupancy &= ~from_bit;

    int captured_square = static_cast<int>(move.to);
    if ((move.flags & EnPassant) != 0U) {
        captured_square = moving_side == White ? static_cast<int>(move.to) - 8
                                               : static_cast<int>(move.to) + 8;
    }
    std::uint64_t removed_attackers = 0;
    if (move.is_capture()) {
        const std::uint64_t captured_bit = 1ULL << captured_square;
        occupancy &= ~captured_bit;
        removed_attackers = captured_bit;
    }
    occupancy |= to_bit;

    if ((move.flags & KingCastle) != 0U || (move.flags & QueenCastle) != 0U) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = moving_side == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = moving_side == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        occupancy &= ~(1ULL << rook_from);
        occupancy |= 1ULL << rook_to;
    }

    const int king = piece_type(moving) == 6
        ? static_cast<int>(move.to)
        : king_squares_[static_cast<std::size_t>(moving_side)];
    return king < 0 || !square_attacked_with_occupancy(king, opposite(moving_side),
                                                       occupancy, removed_attackers);
}

bool Board::has_legal_move() {
    for (const Move move : pseudo_legal_moves()) {
        if (is_legal_after(move)) return true;
    }
    return false;
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
    if ((move.flags & Promotion) != 0U) {
        constexpr std::array<char, 7> promotion_chars{' ', ' ', 'n', 'b', 'r', 'q', ' '};
        text += promotion_chars[move.promotion];
    }
    return text;
}

std::uint64_t Board::perft(int depth) {
    if (depth <= 0) return 1;
    const auto moves = legal_moves();
    if (depth == 1) return moves.size();
    std::uint64_t nodes = 0;
    for (const Move move : moves) {
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

bool Board::is_insufficient_material() const {
    constexpr std::uint64_t DarkSquares = 0xAA55AA55AA55AA55ULL;
    const std::uint64_t pawns_rooks_queens = bitboards_[WP] | bitboards_[BP] | bitboards_[WR] |
                                             bitboards_[BR] | bitboards_[WQ] | bitboards_[BQ];
    if (pawns_rooks_queens != 0) return false;
    const std::uint64_t knights = bitboards_[WN] | bitboards_[BN];
    const std::uint64_t bishops = bitboards_[WB] | bitboards_[BB];
    const int minor_count = std::popcount(knights | bishops);
    if (minor_count <= 1) return true;
    return knights == 0 && ((bishops & DarkSquares) == 0 || (bishops & ~DarkSquares) == 0);
}

int Board::static_exchange(const Move& move) const {
    if (!move.is_capture() && (move.flags & Promotion) == 0U) return 0;
    std::array<Piece, 64> position = squares_;
    std::array<std::uint64_t, 13> position_bits = bitboards_;
    Piece moving = position[move.from];
    Piece captured = position[move.to];
    if ((move.flags & EnPassant) != 0U) {
        const int captured_square = side_ == White ? static_cast<int>(move.to) - 8
                                                   : static_cast<int>(move.to) + 8;
        captured = position[static_cast<std::size_t>(captured_square)];
        position[static_cast<std::size_t>(captured_square)] = Empty;
        position_bits[static_cast<std::size_t>(captured)] &= ~(1ULL << captured_square);
    }
    std::array<int, 32> gain{};
    gain[0] = SeeValue[static_cast<std::size_t>(piece_type(captured))];
    if ((move.flags & Promotion) != 0U) {
        gain[0] += SeeValue[move.promotion] - SeeValue[1];
        moving = static_cast<Piece>((side_ == White ? 0 : 6) + move.promotion);
    }
    position[move.from] = Empty;
    position_bits[static_cast<std::size_t>(squares_[move.from])] &= ~(1ULL << move.from);
    if (position[move.to] != Empty) {
        position_bits[static_cast<std::size_t>(position[move.to])] &= ~(1ULL << move.to);
    }
    position[move.to] = moving;
    position_bits[static_cast<std::size_t>(moving)] |= 1ULL << move.to;
    int captured_value = SeeValue[static_cast<std::size_t>(piece_type(moving))];
    Color side = opposite(side_);
    int depth = 0;
    while (depth + 1 < static_cast<int>(gain.size())) {
        const int from = least_attacker(position, position_bits, move.to, side);
        if (from < 0) break;
        const Piece source_attacker = position[static_cast<std::size_t>(from)];
        Piece attacker = source_attacker;
        int promotion_gain = 0;
        const int target_rank = rank_of(move.to);
        if (piece_type(attacker) == 1 && (target_rank == 0 || target_rank == 7)) {
            promotion_gain = SeeValue[5] - SeeValue[1];
            attacker = side == White ? WQ : BQ;
        }
        ++depth;
        gain[static_cast<std::size_t>(depth)] = captured_value + promotion_gain -
                                                gain[static_cast<std::size_t>(depth - 1)];
        position[static_cast<std::size_t>(from)] = Empty;
        const Piece original_attacker = position[move.to];
        position_bits[static_cast<std::size_t>(original_attacker)] &= ~(1ULL << move.to);
        position_bits[static_cast<std::size_t>(source_attacker)] &= ~(1ULL << from);
        position[move.to] = attacker;
        position_bits[static_cast<std::size_t>(attacker)] |= 1ULL << move.to;
        captured_value = SeeValue[static_cast<std::size_t>(piece_type(attacker))];
        side = opposite(side);
    }
    while (depth > 0) {
        gain[static_cast<std::size_t>(depth - 1)] =
            -std::max(-gain[static_cast<std::size_t>(depth - 1)], gain[static_cast<std::size_t>(depth)]);
        --depth;
    }
    return gain[0];
}

bool Board::has_legal_en_passant_capture() const {
    if (ep_square_ < 0) return false;
    const int target = ep_square_;
    const Piece pawn = side_ == White ? WP : BP;
    const int captured_square = side_ == White ? target - 8 : target + 8;
    const std::array<int, 2> candidates = side_ == White
        ? std::array<int, 2>{target - 9, target - 7}
        : std::array<int, 2>{target + 7, target + 9};
    const int king = king_squares_[static_cast<std::size_t>(side_)];
    if (king < 0) return false;
    const std::uint64_t base_occupancy = occupied_[White] | occupied_[Black];
    const std::uint64_t captured_bit = 1ULL << captured_square;
    for (const int from : candidates) {
        if (!on_board(from) || abs_int(file_of(from) - file_of(target)) != 1 ||
            squares_[static_cast<std::size_t>(from)] != pawn) {
            continue;
        }
        std::uint64_t occupancy = base_occupancy;
        occupancy &= ~(1ULL << from);
        occupancy &= ~captured_bit;
        occupancy |= 1ULL << target;
        if (!square_attacked_with_occupancy(king, opposite(side_), occupancy, captured_bit)) return true;
    }
    return false;
}

std::uint64_t Board::compute_key() const {
    std::uint64_t key = 0;
    for (std::size_t square = 0; square < squares_.size(); ++square) {
        if (squares_[square] != Empty) key ^= piece_key(static_cast<int>(square), squares_[square]);
    }
    key ^= mix(900 + castling_);
    if (has_legal_en_passant_capture()) {
        key ^= mix(1000 + static_cast<std::uint64_t>(file_of(ep_square_)));
    }
    if (side_ == Black) key ^= mix(1100);
    return key;
}

} // namespace forge
