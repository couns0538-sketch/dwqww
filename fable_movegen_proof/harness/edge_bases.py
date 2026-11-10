"""edge_bases.py - the hand-made bases of the job-3 edge suite.

Each LEGAL base is (id, category, predicate, FEN, provenance). The predicate is a list of atoms joined by ';'
that chess_oracle.check_predicate() must find true, so a base cannot carry a label it does not deserve:
  checkers=N, checker=<piece letters of all checkers>, legal=N, legal>=N, has=<uci> (legal), no=<uci> (not legal),
  pseudo=<uci> (generated before the king-safety test), mate, stalemate, gives_check=<uci>, no_check=<uci>,
  discovered=<uci> (after it the king is attacked by a piece other than the one that moved),
  double_after=<uci>, ep_legal, ep_illegal (en passant is generated but not legal), promos=<from><to> (all four),
  castle=K|Q (legal for the side to move), nocastle=K|Q (the right is there, the move is not legal).
edge.py adds the colour mirror of every base and, where there are no castling rights, the file mirror and its
colour mirror, with the predicate mirrored too.

Provenance: J3 = constructed for this job; J2 row n = job 2's tests/targeted_fens.txt; REVIEW = named by the
planning review of job 3; CPW = Chess Programming Wiki "Perft Results" (position 2 is "kiwipete" by Peter McKenzie);
QA = Engine QA's perft_extra_v3 positions.
"""
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

LEGAL = [
    # ---- single checks by each kind of piece, with the ways out
    ("chk_knight_only_king_moves", "check_knight", "checkers=1;checker=N;nocastle=K;nocastle=Q", "4k3/8/8/8/8/3n4/3P1P2/R3K2R w KQ - 0 1", "J2 row 17"),
    ("chk_knight_three_captures", "check_knight", "checkers=1;checker=N;has=c2d3;has=d2d3;has=e2d3", "4k3/8/8/8/2b5/3n4/2PQB3/R3K2R w KQ - 0 1", "J3"),
    ("chk_knight_many_pieces_near", "check_knight", "checkers=1;checker=N;has=e2f3;has=g2f3;has=g1f3;no=d1d2", "4k3/8/8/8/8/5n2/4PPPP/RN1QKBNR w KQ - 0 1", "REVIEW"),
    ("chk_pawn", "check_pawn", "checkers=1;checker=P;has=c2d3;has=e2d3", "4k3/8/8/8/8/3p4/2P1K3/8 w - - 0 1", "J2 row 18"),
    ("chk_bishop_blocks", "check_slider", "checkers=1;checker=B;has=b1c3;has=b1d2;has=f2d2", "4k3/8/8/8/1b6/8/5R2/RN2K3 w - - 0 1", "J3"),
    ("chk_rook_file_blocks", "check_slider", "checkers=1;checker=R;has=d2e3;has=f2e4", "4r1k1/8/8/8/8/8/3B1N2/R3K3 w - - 0 1", "J3"),
    ("chk_queen_diagonal", "check_slider", "checkers=1;checker=Q;has=g2g3;has=h1h4;nocastle=K", "6k1/8/8/8/7q/8/6P1/4K2R w K - 0 1", "J3"),
    ("chk_far_bishop_double_push_block", "check_slider", "checkers=1;checker=B;has=b2b4;has=c2c3;no=c2c4;no=b2b3", "4k3/8/8/b7/8/8/1PP5/4K3 w - - 0 1", "REVIEW"),
    ("chk_contact_queen", "check_slider", "checkers=1;checker=Q;has=e1e2;legal=1", "4k3/8/8/8/8/8/4q3/4K2R w K - 0 1", "J3"),
    # ---- double checks: suffered and given
    ("dbl_rook_knight", "double_check", "checkers=2;checker=NR;no=g2f3", "4k3/8/8/8/8/5n2/6B1/r3K3 w - - 0 1", "J2 row 8"),
    ("dbl_bishop_rook", "double_check", "checkers=2;checker=BR", "4k3/8/8/8/1b6/8/8/r3K3 w - - 0 1", "J3"),
    ("dbl_queen_knight", "double_check", "checkers=2;checker=NQ;nocastle=K", "4k3/8/8/8/8/3n4/8/q3K2R w K - 0 1", "J3"),
    ("dbl_given_by_knight", "double_check_given", "double_after=e4d6;double_after=e4f6;discovered=e4c3", "4k3/8/8/8/4N3/8/8/4R1K1 w - - 0 1", "J2 row 11"),
    ("dbl_given_by_bishop", "double_check_given", "double_after=e4c6;double_after=e4g6;discovered=e4d3", "4k3/8/8/8/4B3/8/8/4Q1K1 w - - 0 1", "J2 row 16"),
    ("dbl_given_by_rook", "double_check_given", "discovered=d4d1;double_after=d4d8;double_after=d4h4", "7k/8/8/8/3R4/8/8/B5K1 w - - 0 1", "J3"),
    # ---- discovered checks
    ("disc_king_moves", "discovered_check", "discovered=d1d2;discovered=d1c2;no_check=d1c1;no_check=d1e1", "8/8/8/8/8/8/8/R2K3k w - - 0 1", "J2 row 1"),
    ("disc_pawn_stays_on_file", "discovered_check", "no_check=e4e5", "4k3/8/8/8/4P3/8/8/4R1K1 w - - 0 1", "J2 row 2"),
    ("disc_pawn_leaves_diagonal", "discovered_check", "discovered=c3c4", "7k/8/8/8/8/2P5/8/B5K1 w - - 0 1", "J2 row 3"),
    ("disc_bishop_along_own_king_line", "discovered_check", "discovered=e3f2;discovered=e3d4;discovered=e3a7", "4k3/8/8/8/8/4B3/8/4R1K1 w - - 0 1", "J2 row 24"),
    ("disc_pawn_capture_leaves_file", "discovered_check", "discovered=e4d5;no_check=e4e5", "4k3/8/8/3p4/4P3/8/8/4R1K1 w - - 0 1", "J3"),
    ("disc_double_push_stays", "discovered_check", "no_check=e2e4;no_check=e2e3", "4k3/8/8/8/8/8/4P3/4R1K1 w - - 0 1", "REVIEW"),
    ("chk_capture_removes_blocker_queen", "check_by_capture", "gives_check=e2e7", "4k3/4r3/8/8/8/8/4Q3/4RK2 w - - 0 1", "J2 row 14"),
    ("chk_capture_removes_blocker_rook", "check_by_capture", "gives_check=e4e7;no_check=e4e6", "4k3/4p3/8/8/4R3/8/8/4K3 w - - 0 1", "J2 row 15"),
    ("chk_double_push_gives_check", "pawn_push_check", "gives_check=d2d4;no_check=d2d3", "8/8/8/2k5/8/8/3P4/4K3 w - - 0 1", "REVIEW"),
    ("chk_single_push_gives_check", "pawn_push_check", "gives_check=d2d3", "8/8/8/8/2k5/8/3P4/4K3 w - - 0 1", "J3"),
    ("evasion_block_gives_check", "evasion_gives_check", "checkers=1;gives_check=g3e4", "4r3/8/3k4/8/8/6N1/8/4K3 w - - 0 1", "REVIEW"),
    ("evasion_capture_gives_check", "evasion_gives_check", "checkers=1;gives_check=c3e4", "8/8/5k2/8/4r3/2N5/8/4K3 w - - 0 1", "REVIEW"),
    # ---- pinned defenders that cannot answer the check
    ("pin_queen_cannot_capture_checker", "pinned_evasion", "checkers=1;pseudo=e2d3;no=e2d3", "4r2k/8/8/8/8/3n4/4Q3/4K3 w - - 0 1", "J2 row 6"),
    ("pin_rook_cannot_block", "pinned_evasion", "checkers=1;pseudo=e2d2;no=e2d2", "4r2k/8/8/8/1b6/8/4R3/4K3 w - - 0 1", "J2 row 7"),
    ("pin_knight_cannot_interpose", "pinned_evasion", "checkers=1;pseudo=c3e2;no=c3e2;no=c3e4;has=h2e2", "4r1k1/8/8/b7/8/2N5/7R/4K3 w - - 0 1", "J2 row 19"),
    ("pin_bishop_by_other_slider", "pinned_evasion", "checkers=1;checker=N;pseudo=d2e3;no=d2e3", "3r3k/8/8/8/8/4n3/3B4/3K4 w - - 0 1", "J3"),
    ("pin_pawn_cannot_capture_checker", "pinned_evasion", "checkers=1;checker=Q;pseudo=c2d3;no=c2d3", "6k1/8/8/8/b7/3q4/2P5/3K4 w - - 0 1", "J3"),
    # ---- en passant
    ("ep_removes_checker", "ep_removes_checker", "checkers=1;checker=P;has=e4d3;ep_legal", "8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1", "J2 row 5"),
    ("ep_or_piece_takes_checker", "ep_removes_checker", "checkers=1;has=e4d3;has=b5d4;has=c5d4", "8/8/8/1nk5/3Pp3/8/8/4K3 b - d3 0 1", "REVIEW"),
    ("ep_illegal_rank_pin", "ep_illegal_rank_pin", "ep_illegal;pseudo=e5d6;no=e5d6;checkers=0", "8/8/8/K2pP2r/8/8/8/7k w - d6 0 1", "J3"),
    ("ep_illegal_diagonal_pin", "ep_illegal_diagonal_pin", "ep_illegal;pseudo=e5d6;no=e5d6;no=e5e6;checkers=0", "8/6b1/8/3pP3/8/2K5/8/7k w - d6 0 1", "J3"),
    ("ep_legal_along_pin_diagonal", "ep_pinned_but_legal", "ep_legal;has=e5d6;no=e5e6;checkers=0", "1b6/8/8/3pP3/8/8/7K/k7 w - d6 0 1", "J3"),
    ("ep_discovered_check_bishop", "ep_discovered_check", "ep_legal;discovered=e5d6", "7k/8/8/3pP3/8/8/8/B5K1 w - d6 0 1", "J2 row 13"),
    ("ep_discovered_check_rank", "ep_discovered_check", "ep_legal;discovered=e5d6", "8/8/8/k2pP2R/8/8/8/6K1 w - d6 0 1", "J2 row 23"),
    ("ep_direct_check", "ep_gives_check", "ep_legal;gives_check=e5d6", "8/2k5/8/3pP3/8/8/8/4K3 w - d6 0 1", "J3"),
    ("ep_two_capturers", "ep_legal", "has=c5d6;has=e5d6", "4k3/8/8/2PpP3/8/8/8/4K3 w - d6 0 1", "J3"),
    ("ep_square_without_capturer", "ep_square_only", "legal=5;checkers=0", "4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1", "J3"),
    ("ep_does_not_answer_check", "ep_in_check", "checkers=1;pseudo=e5d6;no=e5d6", "4k3/8/8/3pP3/8/8/8/r3K3 w - d6 0 1", "J3"),
    # ---- promotions and underpromotions
    ("promo_push_all_four", "promotion_push", "promos=a7a8;no_check=a7a8q", "8/P6k/8/8/8/8/8/K7 w - - 0 1", "J3"),
    ("promo_capture_both_sides", "promotion_capture", "promos=c7b8;promos=c7d8;promos=c7c8", "1n1n3k/2P5/8/8/8/8/8/K7 w - - 0 1", "J3"),
    ("promo_check_queen_rook", "promotion_gives_check", "gives_check=b7b8q;gives_check=b7b8r;no_check=b7b8b;no_check=b7b8n", "3k4/1P6/8/8/8/8/8/4K3 w - - 0 1", "J2 row 4"),
    ("promo_check_knight_only", "underpromotion_check", "gives_check=f7f8n;no_check=f7f8q;no_check=f7f8r;no_check=f7f8b", "8/5P1k/8/8/8/8/8/K7 w - - 0 1", "J3"),
    ("promo_check_bishop_queen", "underpromotion_check", "gives_check=c7c8b;gives_check=c7c8q;no_check=c7c8r;no_check=c7c8n", "8/2P5/k7/8/8/8/8/7K w - - 0 1", "J3"),
    ("promo_check_through_vacated_file", "promotion_gives_check", "gives_check=b7b8q;gives_check=b7b8r;no_check=b7b8n;no_check=b7b8b", "8/1P6/8/8/8/1k6/8/7K w - - 0 1", "REVIEW"),
    ("promo_discovered_check", "promotion_discovered_check", "discovered=d7d8q;discovered=d7d8n", "8/R2P3k/8/8/8/8/8/K7 w - - 0 1", "J3"),
    ("promo_captures_checker", "promotion_in_check", "checkers=1;promos=e7d8;promos=e7e8", "3r3K/4P3/8/8/8/8/8/k7 w - - 0 1", "REVIEW"),
    ("promo_blocks_check", "promotion_in_check", "checkers=1;promos=e7e8", "r6K/4P3/8/8/8/8/8/k7 w - - 0 1", "REVIEW"),
    ("promo_illegal_pinned", "promotion_illegal", "pseudo=d7d8q;no=d7d8q;no=d7d8n;checkers=0", "8/r2P3K/8/8/8/8/8/k7 w - - 0 1", "J3"),
    ("promo_black_both_edges", "promotion_capture", "promos=b2a1;promos=b2c1;promos=b2b1;promos=g2f1;promos=g2h1;promos=g2g1", "4k3/8/8/8/8/8/1p4p1/R1N1KB1R b - - 0 1", "J2 row 21"),
    ("promo_many_pawns", "promotion_capture", "promos=b7a8;promos=b7c8;promos=b7b8;has=d5c6", "r1b1k1nr/pP3p1p/8/2pPp3/1p2P1p1/8/P1P2PpP/R1B1K1NR w KQkq c6 0 1", "J2 row 20"),
    ("promo_edge_single_target", "promotion_capture", "promos=b7a8;promos=g7h8;promos=b7b8;promos=g7g8", "n6n/1P4P1/8/8/8/8/8/k3K3 w - - 0 1", "REVIEW"),
    # ---- castling
    ("castle_both_legal", "castling_legal", "castle=K;castle=Q", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_through_attack_kingside", "castling_through_attack", "nocastle=K;castle=Q;checkers=0", "r3k2r/8/b7/8/8/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_into_attack_kingside", "castling_into_attack", "nocastle=K;castle=Q;checkers=0", "r3k2r/8/1b6/8/8/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_out_of_check", "castling_out_of_check", "checkers=1;nocastle=K;nocastle=Q", "r3k2r/8/8/8/1b6/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_through_attack_queenside", "castling_through_attack", "nocastle=Q;castle=K;checkers=0", "r3k2r/8/8/8/6b1/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_into_attack_queenside", "castling_into_attack", "nocastle=Q;castle=K;checkers=0", "r3k2r/8/7b/8/8/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_b1_attacked_still_legal", "castling_legal", "castle=Q;castle=K;checkers=0", "r3k2r/7b/8/8/8/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_rook_attacked_still_legal", "castling_legal", "castle=K;castle=Q;checkers=0", "r3k2r/1b6/8/8/8/8/8/R3K2R w KQkq - 0 1", "J3"),
    ("castle_blocked_own_pieces", "castling_blocked", "nocastle=K;nocastle=Q;checkers=0", "r3k2r/8/8/8/8/8/8/RN2KB1R w KQkq - 0 1", "J3"),
    ("castle_blocked_enemy_pieces", "castling_blocked", "nocastle=K;nocastle=Q;checkers=0", "r3k2r/8/8/8/8/8/8/R2nK1nR w KQkq - 0 1", "J3"),
    ("castle_gives_check_queenside", "castling_gives_check", "castle=Q;gives_check=e1c1", "3k4/8/8/8/8/8/8/R3K3 w Q - 0 1", "J2 row 12"),
    ("castle_gives_check_kingside", "castling_gives_check", "castle=K;gives_check=e1g1", "5k2/8/8/8/8/8/8/4K2R w K - 0 1", "QA"),
    ("castle_one_right_only", "castling_legal", "castle=K;no=e1c1", "r3k2r/8/8/8/8/8/8/R3K2R w Kq - 0 1", "J3"),
    ("castle_in_check_with_rights", "castling_out_of_check", "checkers=1;nocastle=K;nocastle=Q", "r3k2r/8/8/8/8/4R3/8/R3K2R b KQkq - 0 1", "QA"),
    # ---- highest known move counts and the standard perft positions
    ("max_moves_218_a", "high_move_count", "legal=218", "R6R/3Q4/1Q4Q1/4Q3/2Q4Q/Q4Q2/pp1Q4/kBNN1KB1 w - - 0 1", "known 218-move position (Petrovic, 1964)"),
    ("max_moves_218_b", "high_move_count", "legal=218", "3Q4/1Q4Q1/4Q3/2Q4R/Q4Q2/3Q4/1Q4Rp/1K1BBNNk w - - 0 1", "known 218-move position"),
    ("std_startpos", "standard_perft", "legal=20", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "CPW position 1"),
    ("std_kiwipete", "standard_perft", "legal=48", KIWI, "CPW position 2"),
    ("std_position3", "standard_perft", "legal=14", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "CPW position 3"),
    ("std_position4", "standard_perft", "legal=6;checkers=1", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", "CPW position 4"),
    ("std_position5", "standard_perft", "legal=44", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", "CPW position 5"),
    ("std_position6", "standard_perft", "legal=46", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", "CPW position 6"),
    # ---- stalemate and checkmate
    ("stalemate_queen", "stalemate", "stalemate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "J3"),
    ("stalemate_pinned_pawn_diagonal", "stalemate", "stalemate;pseudo=g2g3;no=g2g3", "k7/8/8/3b4/8/4b3/6P1/5n1K w - - 0 1", "J2 row 10"),
    ("stalemate_pinned_pawn_rank", "stalemate", "stalemate;pseudo=c5c6;no=c5c6", "8/1k1b4/8/K1P4r/8/3n4/8/8 w - - 0 1", "REVIEW"),
    ("stalemate_blocked_pawns", "stalemate", "stalemate", "8/8/8/8/p7/P1k5/2p5/2K5 w - - 0 1", "J3"),
    ("mate_back_rank", "checkmate", "mate;checker=R", "3R2k1/5ppp/8/8/8/8/8/6K1 b - - 0 1", "J3"),
    ("mate_free_pawn_push", "checkmate", "mate;checker=R", "6k1/8/8/8/8/8/P4PPP/3r2K1 w - - 0 1", "J2 row 9"),
    ("mate_smothered", "checkmate", "mate;checker=N", "6rk/5Npp/8/8/8/8/8/6K1 b - - 0 1", "J3"),
    ("mate_protected_contact_queen", "checkmate", "mate;checker=Q", "4k3/8/8/8/2b5/8/4q3/4K2R w K - 0 1", "J3"),
    # ---- rows aimed at one candidate each
    ("pcm_edge_single_target_white", "pawn_capture_edge", "has=b4a5;has=g4h5;has=a4b5;has=h4g5", "4k3/8/8/np4pn/PP4PP/8/8/4K3 w - - 0 1", "REVIEW"),
    ("pcm_edge_single_target_black", "pawn_capture_edge", "has=a5b4;has=b5a4;has=g5h4;has=h5g4", "4k3/8/8/pp4pp/NP4PN/8/8/4K3 b - - 0 1", "REVIEW"),
    ("pcm_interleaved_capturers", "pawn_capture_order", "has=b4c5;has=d4c5;has=d4e5;has=f4e5;has=f4g5;has=h4g5;has=a2a3", "4k3/8/8/2p1p1p1/1P1P1P1P/8/P7/4K3 w - - 0 1", "J3"),
    ("kpc_kings_open_files", "king_pawn_structure", "legal>=5;checkers=0", "4k3/pp3ppp/8/8/8/8/PP3PPP/4K3 w - - 0 1", "J2 row 22"),
    ("kpc_castled_shelters", "king_pawn_structure", "legal>=5;checkers=0", "6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 0 1", "J3"),
    ("kpc_opposite_wings", "king_pawn_structure", "legal>=5;checkers=0", "2k5/ppp5/8/8/8/8/5PPP/6K1 w - - 0 1", "J3"),
    ("kpc_no_pawns", "king_pawn_structure", "legal>=10;checkers=0", "4k3/8/8/8/8/8/8/4K2R w - - 0 1", "J3"),
    ("kpc_pawn_storm", "king_pawn_structure", "legal>=5;checkers=0", "6k1/5p1p/6p1/8/5PPP/8/8/6K1 w - - 0 1", "J3"),
    ("kpc_edge_kings", "king_pawn_structure", "legal>=3;checkers=0", "k7/p7/8/8/8/8/7P/7K w - - 0 1", "J3"),
    ("wnp_lowest_push_pinned", "has_legal_move_witness", "no=b2b3;has=h2h3;checkers=0", "7k/8/8/8/3b4/8/1P5P/K7 w - - 0 1", "REVIEW"),
    ("wnp_file_pinned_push_legal", "has_legal_move_witness", "has=e2e3;has=e2e4;checkers=0", "4r2k/8/8/8/8/8/4P3/4K3 w - - 0 1", "REVIEW"),
    ("wnp_free_push_available", "has_legal_move_witness", "has=a2a3;no=g2g3;checkers=0", "k7/8/8/3b4/8/8/P5P1/7K w - - 0 1", "REVIEW"),
]

# Rejected by set_fen: (id, category, expected part of the engine's error text, FEN, provenance)
REJECTED = [
    ("rej_adjacent_kings_file", "invalid_adjacent_kings", "kings may not be adjacent", "8/8/8/8/8/8/4k3/4K3 w - - 0 1", "J3"),
    ("rej_adjacent_kings_diagonal", "invalid_adjacent_kings", "kings may not be adjacent", "8/8/8/8/8/5k2/4K3/8 b - - 0 1", "J3"),
    ("rej_side_not_to_move_in_check", "invalid_opponent_in_check", "side that moved left its king in check", "4k3/8/8/8/8/8/4R3/4K3 w - - 0 1", "J3"),
    ("rej_white_pawn_on_rank_8", "invalid_pawn_rank", "pawn on promotion rank", "P3k3/8/8/8/8/8/8/4K3 w - - 0 1", "J3"),
    ("rej_black_pawn_on_rank_1", "invalid_pawn_rank", "pawn on promotion rank", "4k3/8/8/8/8/8/8/p3K3 w - - 0 1", "J3"),
    ("rej_missing_black_king", "invalid_kings", "invalid FEN fields", "8/8/8/8/8/8/8/4K3 w - - 0 1", "J3"),
    ("rej_two_white_kings", "invalid_kings", "invalid FEN fields", "4k3/8/8/8/8/8/8/3KK3 w - - 0 1", "J3"),
    ("rej_nine_pawns", "invalid_inventory", "impossible piece inventory", "4k3/8/8/8/8/P7/PPPPPPPP/4K3 w - - 0 1", "J3"),
    ("rej_three_queens_eight_pawns", "invalid_inventory", "impossible piece inventory", "4k3/8/8/8/8/QQQ5/PPPPPPPP/4K3 w - - 0 1", "J3"),
    ("rej_castling_right_without_rook", "invalid_castling", "castling right without king and rook", "4k3/8/8/8/8/8/8/4K3 w K - 0 1", "J3"),
    ("rej_castling_right_king_off_e1", "invalid_castling", "castling right without king and rook", "4k3/8/8/8/8/8/8/3K3R w K - 0 1", "J3"),
    ("rej_ep_no_pawn_in_front", "invalid_en_passant", "inconsistent en-passant square", "4k3/8/8/8/8/8/8/4K3 w - e6 0 1", "J3"),
    ("rej_ep_wrong_rank_for_side", "invalid_en_passant", "inconsistent en-passant square", "4k3/8/8/8/4P3/8/8/4K3 w - e3 0 1", "J3"),
    ("rej_ep_start_square_occupied", "invalid_en_passant", "inconsistent en-passant square", "4k3/3p4/8/3p4/8/8/8/4K3 w - d6 0 1", "J3"),
    ("rej_five_fields", "invalid_syntax", "FEN must contain six fields", "4k3/8/8/8/8/8/8/4K3 w - - 0", "J3"),
    ("rej_seven_ranks", "invalid_syntax", "invalid FEN", "4k3/8/8/8/8/8/4K3 w - - 0 1", "J3"),
    ("rej_unknown_piece_letter", "invalid_syntax", "invalid FEN placement", "4k3/8/8/8/8/8/8/4K2X w - - 0 1", "J3"),
]

# Accepted by set_fen but not reachable in a legal game: (id, category, what makes it unreachable, FEN, provenance)
UNREACHABLE = [
    ("unr_triple_check", "unreachable_triple_check", "three pieces give check at once", "4r1k1/8/8/8/1b6/5n2/8/4K3 w - - 0 1", "J3"),
    ("unr_two_knights_check", "unreachable_double_knight_check", "two knights give check at once", "4k3/8/8/8/8/3n1n2/8/4K3 w - - 0 1", "J3"),
    ("unr_ep_uncovers_second_line", "unreachable_ep_in_check", "in check on the rank while the en-passant pawn shields a diagonal: the last move cannot have been the double push",
     "8/8/2K4r/3pP3/8/8/6b1/k7 w - d6 0 1", "REVIEW"),
    ("unr_four_pawns_on_a_file", "unreachable_pawn_structure", "four white a-pawns with all sixteen black men on the board",
     "rnbqkbnr/pppppppp/8/P7/P7/P7/P7/RNBQKBNR w KQkq - 0 1", "J3"),
]
