| case | FEN (fullmove 0) | Forge answer | Forge perft 1 | python-chess accepts | python legal moves | FEN with fullmove 1 | Forge perft 1 then |
|---|---|---|---|---|---|---|---|
| king_and_rook | `4k3/8/8/8/8/8/8/4K2R w K - 0 0` | info string invalid FEN: invalid FEN fields | 20 | True (0) | 15 | `4k3/8/8/8/8/8/8/4K2R w K - 0 1` | 15 |
| ruy_lopez_mid | `r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 0` | info string invalid FEN: invalid FEN fields | 20 | True (0) | 30 | `r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 1` | 30 |
| startpos_fullmove0 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0` | info string invalid FEN: invalid FEN fields | 20 | True (0) | 20 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1` | 20 |
