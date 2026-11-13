// Legality probe for Board move generation, is_legal / gives_check, and make/unmake.
// Build against include/ and src/board.cpp + src/bitboard.cpp. Reads commands on stdin.
// Each command ends with a line "END". FAIL lines are invariant breaks.

#include "forge/board.hpp"

#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

int g_command_fails = 0;
int g_total_fails = 0;

void fail(const std::string& message) {
    std::cout << "FAIL " << message << '\n';
    ++g_command_fails;
    ++g_total_fails;
}

void end_command() {
    std::cout << "SUMMARY fails " << g_command_fails << "\nEND\n";
    std::cout.flush();
    g_command_fails = 0;
}

std::string hex64(std::uint64_t value) {
    std::ostringstream out;
    out << std::hex << value;
    return out.str();
}

std::string move_id(const forge::Move& move) {
    return forge::Board::move_to_uci(move) + " f" + std::to_string(move.flags) + " p" +
           std::to_string(move.promotion);
}

std::string square_list(forge::Bitboard bits) {
    std::string text;
    while (bits != 0) {
        const int square = forge::pop_lsb(bits);
        if (!text.empty()) text += ',';
        text += static_cast<char>('a' + forge::file_of(square));
        text += static_cast<char>('1' + forge::rank_of(square));
    }
    if (text.empty()) text = '-';
    return text;
}

struct Snapshot {
    std::string fen;
    std::uint64_t key = 0;
    std::uint64_t pawn_key = 0;
    forge::Bitboard checkers = 0;
    int ep = -1;
    int castling = 0;
    int half = 0;
    int full = 0;
    std::size_t history = 0;
    bool in_check = false;
    std::string signature;
};

std::string signature_of(forge::Board& board) {
    std::string text;
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move move : legal) {
        text += forge::Board::move_to_uci(move);
        text += board.gives_check(move) ? '+' : '.';
        text += ';';
    }
    text += board.has_legal_move() ? 'H' : 'h';
    text += board.in_check() ? 'C' : 'c';
    return text;
}

Snapshot take_snapshot(forge::Board& board) {
    Snapshot snap;
    snap.fen = board.fen();
    snap.key = board.key();
    snap.pawn_key = board.pawn_key();
    snap.checkers = board.checkers();
    snap.ep = board.ep_square();
    snap.castling = board.castling_rights();
    snap.half = board.halfmove_clock();
    snap.full = board.fullmove_number();
    snap.history = board.history_size();
    snap.in_check = board.in_check();
    snap.signature = signature_of(board);
    return snap;
}

bool same_snapshot(const Snapshot& snap, forge::Board& board, const std::string& ctx) {
    bool ok = true;
    if (board.fen() != snap.fen) {
        fail(ctx + " fen " + board.fen() + " != " + snap.fen);
        ok = false;
    }
    if (board.key() != snap.key) {
        fail(ctx + " key");
        ok = false;
    }
    if (board.pawn_key() != snap.pawn_key) {
        fail(ctx + " pawn key");
        ok = false;
    }
    if (board.checkers() != snap.checkers) {
        fail(ctx + " checkers");
        ok = false;
    }
    if (board.ep_square() != snap.ep || board.castling_rights() != snap.castling ||
        board.halfmove_clock() != snap.half || board.fullmove_number() != snap.full ||
        board.history_size() != snap.history || board.in_check() != snap.in_check) {
        fail(ctx + " counters");
        ok = false;
    }
    if (signature_of(board) != snap.signature) {
        fail(ctx + " legal/gives_check signature changed");
        ok = false;
    }
    return ok;
}

// Mailbox, bitboards, kings, checkers, castling geometry, ep geometry.
void check_structure(const forge::Board& board, const std::string& ctx, bool require_opponent_safe) {
    forge::Bitboard seen[13] = {};
    forge::Bitboard occ[2] = {};
    int kings[2] = {-1, -1};
    int king_count[2] = {};
    for (int square = 0; square < 64; ++square) {
        const forge::Piece piece = board.piece_at(square);
        if (piece == forge::Empty) continue;
        if (piece < forge::WP || piece > forge::BK) {
            fail(ctx + " piece value");
            return;
        }
        seen[piece] |= forge::square_bb(square);
        const forge::Color color = forge::color_of(piece);
        occ[color] |= forge::square_bb(square);
        if (forge::piece_type(piece) == forge::King) {
            kings[color] = square;
            ++king_count[color];
        }
    }
    for (int piece = forge::WP; piece <= forge::BK; ++piece) {
        if (board.pieces(static_cast<forge::Piece>(piece)) != seen[piece]) {
            fail(ctx + " bitboard " + std::to_string(piece));
        }
    }
    if (board.occupied(forge::White) != occ[0] || board.occupied(forge::Black) != occ[1]) {
        fail(ctx + " occupied");
    }
    if (king_count[0] != 1 || king_count[1] != 1 || board.king_square(forge::White) != kings[0] ||
        board.king_square(forge::Black) != kings[1]) {
        fail(ctx + " king squares");
        return;
    }
    const forge::Color side = board.side_to_move();
    const forge::Bitboard checkers =
        board.attackers_to(board.king_square(side)) & board.occupied(forge::opposite(side));
    if (checkers != board.checkers()) fail(ctx + " checkers mismatch");
    if ((checkers != 0) != board.in_check() || board.in_check() != board.in_check(side)) {
        fail(ctx + " in_check mismatch");
    }
    if (require_opponent_safe && board.in_check(forge::opposite(side))) {
        fail(ctx + " opponent king in check");
    }
    const unsigned rights = board.castling_rights();
    if ((rights & 1U) != 0U && (board.piece_at(4) != forge::WK || board.piece_at(7) != forge::WR)) {
        fail(ctx + " white kingside rights without king and rook");
    }
    if ((rights & 2U) != 0U && (board.piece_at(4) != forge::WK || board.piece_at(0) != forge::WR)) {
        fail(ctx + " white queenside rights without king and rook");
    }
    if ((rights & 4U) != 0U && (board.piece_at(60) != forge::BK || board.piece_at(63) != forge::BR)) {
        fail(ctx + " black kingside rights without king and rook");
    }
    if ((rights & 8U) != 0U && (board.piece_at(60) != forge::BK || board.piece_at(56) != forge::BR)) {
        fail(ctx + " black queenside rights without king and rook");
    }
    const int ep = board.ep_square();
    if (ep >= 0) {
        const int pawn_square = side == forge::White ? ep - 8 : ep + 8;
        const int origin = side == forge::White ? ep + 8 : ep - 8;
        const forge::Piece expected = side == forge::White ? forge::BP : forge::WP;
        const int rank = forge::rank_of(ep);
        if (pawn_square < 0 || pawn_square > 63 || origin < 0 || origin > 63 ||
            board.piece_at(ep) != forge::Empty || board.piece_at(origin) != forge::Empty ||
            board.piece_at(pawn_square) != expected || (side == forge::White && rank != 5) ||
            (side == forge::Black && rank != 2)) {
            fail(ctx + " ep geometry");
        }
    }
}

bool contains_move(const forge::MoveList& moves, const forge::Move& needle) {
    for (const forge::Move move : moves) {
        if (move.from == needle.from && move.to == needle.to && move.promotion == needle.promotion &&
            move.flags == needle.flags) {
            return true;
        }
    }
    return false;
}

void check_partitions(const forge::Board& board, const std::string& ctx) {
    const forge::MoveList all = board.pseudo_legal_moves(false);
    const forge::MoveList captures = board.pseudo_legal_moves(true);
    std::unordered_map<std::string, int> ids;
    for (const forge::Move move : all) {
        const std::string id = move_id(move);
        if (++ids[id] > 1) fail(ctx + " duplicate pseudo " + id);
        const bool material = move.is_capture() || move.is_promotion();
        if (material != contains_move(captures, move)) {
            fail(ctx + (material ? " missing from captures " : " quiet in captures ") + id);
        }
        if (!board.is_pseudo_legal(move)) fail(ctx + " generated not pseudo-legal " + id);
    }
    for (const forge::Move move : captures) {
        if (!contains_move(all, move)) fail(ctx + " capture not in full list " + move_id(move));
    }
#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
    forge::MoveList quiets;
    board.generate_pseudo_legal(quiets, forge::Board::GenMode::Quiets);
    if (quiets.size() + captures.size() != all.size()) {
        fail(ctx + " quiets+captures size " + std::to_string(quiets.size() + captures.size()) + " != " +
             std::to_string(all.size()));
    }
    for (const forge::Move move : quiets) {
        if (move.is_capture() || move.is_promotion()) fail(ctx + " material in quiets " + move_id(move));
        if (!contains_move(all, move)) fail(ctx + " quiet not in full list " + move_id(move));
        if (contains_move(captures, move)) fail(ctx + " quiet also capture " + move_id(move));
    }
#endif
}

void check_ep_key(forge::Board& board, const std::string& ctx) {
    if (board.ep_square() < 0) return;
    std::istringstream input(board.fen());
    std::string placement;
    std::string side;
    std::string castling;
    std::string ep;
    std::string half;
    std::string full;
    if (!(input >> placement >> side >> castling >> ep >> half >> full)) {
        fail(ctx + " fen fields");
        return;
    }
    if (ep == "-") return;
    const std::string stripped =
        placement + " " + side + " " + castling + " - " + half + " " + full;
    forge::Board other;
    std::string error;
    if (!other.set_fen(stripped, &error)) {
        fail(ctx + " stripped ep fen rejected: " + error);
        return;
    }
    bool legal_ep = false;
    for (const forge::Move move : board.legal_moves()) {
        if ((move.flags & forge::EnPassant) != 0U) legal_ep = true;
    }
    if (legal_ep && other.key() == board.key()) fail(ctx + " legal ep missing from key");
    if (!legal_ep && other.key() != board.key()) fail(ctx + " illegal ep present in key");
}

void check_against_fresh(forge::Board& board, const std::string& ctx) {
    forge::Board fresh;
    std::string error;
    if (!fresh.set_fen(board.fen(), &error)) {
        fail(ctx + " fresh fen rejected: " + error);
        return;
    }
    if (fresh.fen() != board.fen()) fail(ctx + " fen round trip " + fresh.fen());
    if (fresh.key() != board.key()) fail(ctx + " key != recomputed");
    if (fresh.pawn_key() != board.pawn_key()) fail(ctx + " pawn key != recomputed");
    if (fresh.checkers() != board.checkers()) fail(ctx + " checkers != recomputed");
    if (signature_of(fresh) != signature_of(board)) fail(ctx + " signature != fresh board");
}

void scan_pseudo(forge::Board& board, const std::string& ctx) {
    const forge::MoveList generated = board.pseudo_legal_moves(false);
    constexpr std::uint8_t flags[] = {
        forge::Quiet,
        forge::Capture,
        forge::DoublePush,
        forge::KingCastle,
        forge::QueenCastle,
        forge::EnPassant,
        forge::Promotion,
        static_cast<std::uint8_t>(forge::Capture | forge::Promotion),
        static_cast<std::uint8_t>(forge::Capture | forge::EnPassant),
        static_cast<std::uint8_t>(forge::DoublePush | forge::Promotion),
        static_cast<std::uint8_t>(forge::KingCastle | forge::QueenCastle),
        static_cast<std::uint8_t>(forge::Capture | forge::EnPassant | forge::Promotion),
        static_cast<std::uint8_t>(forge::EnPassant | forge::Promotion),
        static_cast<std::uint8_t>(forge::DoublePush | forge::Capture)};
    constexpr int promos[] = {0, forge::Knight, forge::Bishop, forge::Rook, forge::Queen, forge::Pawn, forge::King};
    for (int from = 0; from < 64; ++from) {
        for (int to = 0; to < 64; ++to) {
            for (const int promo : promos) {
                for (const std::uint8_t flag : flags) {
                    const forge::Move move{static_cast<std::uint8_t>(from), static_cast<std::uint8_t>(to),
                                           static_cast<std::uint8_t>(promo), flag};
                    if (!board.is_pseudo_legal(move)) continue;
                    if (!contains_move(generated, move)) {
                        fail(ctx + " is_pseudo_legal not generated " + move_id(move));
                    }
                }
            }
        }
    }
}

void audit(forge::Board& board, bool scan) {
    const std::string ctx = board.fen();
    check_structure(board, ctx, true);
    check_partitions(board, ctx);
    check_ep_key(board, ctx);
    check_against_fresh(board, ctx);
    const bool mate = !board.has_legal_move() && board.in_check();
    const bool stale = !board.has_legal_move() && !board.in_check();
    if (board.has_legal_move() == board.legal_moves().empty()) {
        fail(ctx + " has_legal_move disagrees with legal_moves");
    }
    std::cout << "S check " << (board.in_check() ? 1 : 0) << " has " << (board.has_legal_move() ? 1 : 0)
              << " mate " << (mate ? 1 : 0) << " stale " << (stale ? 1 : 0) << " castle "
              << static_cast<int>(board.castling_rights()) << " ep " << board.ep_square() << " half "
              << board.halfmove_clock() << " full " << board.fullmove_number() << " key " << hex64(board.key())
              << " pawn " << hex64(board.pawn_key()) << " checkers " << square_list(board.checkers()) << " hist "
              << board.history_size() << "\nFEN " << board.fen() << '\n';

    const Snapshot snap = take_snapshot(board);
    const forge::MoveList pseudo = board.pseudo_legal_moves(false);
    const forge::MoveList legal = board.legal_moves();
    for (const forge::Move move : legal) {
        if (!contains_move(pseudo, move)) fail(ctx + " legal not pseudo " + move_id(move));
        if (!board.is_legal(move)) fail(ctx + " legal list move fails is_legal " + move_id(move));
    }
    for (const forge::Move move : pseudo) {
        const bool legal_move = board.is_legal(move);
        if (legal_move != contains_move(legal, move)) {
            fail(ctx + " is_legal disagrees with legal list " + move_id(move));
        }
        const std::string before = board.fen();
        const bool gives = board.gives_check(move);
        if (board.fen() != before) fail(ctx + " gives_check mutated " + move_id(move));
#if FORGE_SPD_PREFETCH_EARLY
        std::uint64_t predicted = 0;
        const bool early = board.key_after(move, predicted);
#else
        const bool early = false;
        const std::uint64_t predicted = 0;
#endif
        forge::Undo undo;
        (void)board.make_move(move, undo);
        check_structure(board, ctx + " after " + move_id(move), legal_move);
        if (legal_move) {
            if (gives != board.in_check()) {
                fail(ctx + " gives_check " + std::to_string(gives) + " in_check " +
                     std::to_string(board.in_check()) + " " + move_id(move));
            }
            if (board.in_check(forge::opposite(board.side_to_move()))) {
                fail(ctx + " legal move left own king in check " + move_id(move));
            }
            check_against_fresh(board, ctx + " after " + move_id(move));
            if (early && predicted != board.key()) fail(ctx + " key_after " + move_id(move));
        }
        std::cout << "M " << forge::Board::move_to_uci(move) << " legal " << (legal_move ? 1 : 0) << " gives "
                  << (gives ? 1 : 0) << " flags " << static_cast<int>(move.flags) << " promo "
                  << static_cast<int>(move.promotion) << " child " << board.fen() << '\n';
        board.unmake_move(move, undo);
        same_snapshot(snap, board, ctx + " unmake " + move_id(move));
    }

    if (!board.in_check()) {
        forge::NullUndo undo;
        board.make_null_move(undo);
        check_structure(board, ctx + " null", true);
        if (board.in_check()) fail(ctx + " null move produced check");
        if (board.ep_square() != -1) fail(ctx + " null move kept ep");
        check_against_fresh(board, ctx + " null");
        std::cout << "N " << board.fen() << '\n';
        board.unmake_null_move(undo);
        same_snapshot(snap, board, ctx + " unmake null");
    } else {
        std::cout << "N -\n";
    }
    if (scan) scan_pseudo(board, ctx);
}

struct WalkStep {
    bool null_move = false;
    forge::Move move{};
    forge::Undo undo{};
    forge::NullUndo null_undo{};
};

void walk(forge::Board& board, int plies, std::uint32_t seed) {
    const Snapshot root = take_snapshot(board);
    std::mt19937 rng(seed);
    std::vector<WalkStep> steps;
    steps.reserve(static_cast<std::size_t>(plies));
    for (int ply = 0; ply < plies; ++ply) {
        check_structure(board, "walk " + std::to_string(ply), true);
        check_against_fresh(board, "walk " + std::to_string(ply));
        if (!board.in_check() && (rng() % 7U) == 0U) {
            WalkStep step;
            step.null_move = true;
            board.make_null_move(step.null_undo);
            check_structure(board, "walk null", true);
            steps.push_back(step);
            continue;
        }
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) break;
        WalkStep step;
        step.move = legal[static_cast<std::size_t>(rng() % legal.size())];
        const bool gives = board.gives_check(step.move);
        (void)board.make_move(step.move, step.undo);
        if (gives != board.in_check()) {
            fail("walk gives_check " + forge::Board::move_to_uci(step.move));
        }
        check_structure(board, "walk after " + forge::Board::move_to_uci(step.move), true);
        check_against_fresh(board, "walk after " + forge::Board::move_to_uci(step.move));
        steps.push_back(step);
    }
    for (std::size_t i = steps.size(); i-- > 0;) {
        if (steps[i].null_move) board.unmake_null_move(steps[i].null_undo);
        else board.unmake_move(steps[i].move, steps[i].undo);
    }
    same_snapshot(root, board, "walk root");
    std::cout << "WALK plies " << steps.size() << " seed " << seed << '\n';
}

struct PerftCase {
    const char* name;
    const char* fen;
    int depth;
    std::uint64_t nodes;
};

void expect_perft(const PerftCase& test) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(test.fen, &error)) {
        fail(std::string(test.name) + " fen rejected: " + error);
        std::cout << "PERFT " << test.name << " depth " << test.depth << " nodes 0 expected " << test.nodes
                  << " ok 0\n";
        return;
    }
    const std::uint64_t nodes = board.perft(test.depth);
    const bool ok = nodes == test.nodes;
    if (!ok) {
        fail(std::string(test.name) + " perft " + std::to_string(nodes) + " != " + std::to_string(test.nodes));
    }
    std::cout << "PERFT " << test.name << " depth " << test.depth << " nodes " << nodes << " expected " << test.nodes
              << " ok " << (ok ? 1 : 0) << '\n';
}

void selftest() {
    constexpr PerftCase kCases[] = {
        {"start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1, 20},
        {"start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 2, 400},
        {"start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 3, 8902},
        {"start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4, 197281},
        {"start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 5, 4865609},
        {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 1, 48},
        {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 2, 2039},
        {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862},
        {"kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4, 4085603},
        {"pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 1, 14},
        {"pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 2, 191},
        {"pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 3, 2812},
        {"pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238},
        {"pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674624},
        {"pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 1, 6},
        {"pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 2, 264},
        {"pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 3, 9467},
        {"pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 4, 422333},
        {"pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 1, 44},
        {"pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 2, 1486},
        {"pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62379},
        {"pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 4, 2103487},
        {"pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 1, 46},
        {"pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 2, 2079},
        {"pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3, 89890},
        {"promo", "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 1, 24},
        {"promo", "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 2, 496},
        {"promo", "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 3, 9483},
        {"promo", "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 4, 182838},
    };
    for (const PerftCase& test : kCases) expect_perft(test);

    constexpr const char* kAudit[] = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    };
    for (const char* fen : kAudit) {
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) {
            fail(std::string("selftest reject ") + error);
            continue;
        }
        audit(board, true);
        walk(board, 200, 0x4f3e91c2U);
    }
    forge::Board start;
    walk(start, 1500, 0x82b6a11dU);
}

forge::Board g_board;
bool g_have_board = false;

void handle(const std::string& line) {
    std::istringstream input(line);
    std::string command;
    if (!(input >> command)) {
        end_command();
        return;
    }
    if (command == "fen") {
        std::string fen;
        std::getline(input, fen);
        if (!fen.empty() && fen[0] == ' ') fen.erase(fen.begin());
        std::string error;
        forge::Board candidate;
        if (!candidate.set_fen(fen, &error)) {
            std::cout << "REJECT " << error << '\n';
        } else {
            g_board = std::move(candidate);
            g_have_board = true;
            std::cout << "ACCEPT " << g_board.fen() << '\n';
        }
    } else if (command == "audit" || command == "scan") {
        if (!g_have_board) fail("no board");
        else audit(g_board, command == "scan");
    } else if (command == "perft") {
        int depth = 0;
        if (!g_have_board || !(input >> depth) || depth < 0 || depth > 8) fail("perft usage");
        else {
            const std::uint64_t nodes = g_board.perft(depth);
            std::cout << "NODES " << nodes << '\n';
        }
    } else if (command == "walk") {
        int plies = 0;
        unsigned seed = 1;
        if (!g_have_board || !(input >> plies >> seed) || plies < 0 || plies > 20000) fail("walk usage");
        else walk(g_board, plies, seed);
    } else if (command == "selftest") {
        selftest();
    } else if (command == "quit") {
        std::cout << "TOTAL fails " << g_total_fails << "\nEND\n";
        std::cout.flush();
        std::exit(g_total_fails == 0 ? 0 : 1);
    } else {
        fail("unknown command " + command);
    }
    end_command();
}

} // namespace

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "selftest") {
        selftest();
        end_command();
        std::cout << "TOTAL fails " << g_total_fails << '\n';
        return g_total_fails == 0 ? 0 : 1;
    }
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        handle(line);
    }
    return g_total_fails == 0 ? 0 : 1;
}
