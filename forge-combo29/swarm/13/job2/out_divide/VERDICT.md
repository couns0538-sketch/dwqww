# divide check, perft 2, engine vs python-chess, 494 positions

engine produced 494 divide blocks for 494 positions

## move-set comparison
positions differing in root move set or counts: **0 of 494**

## class properties
class-property assertions failed: **2 of 494**
- position 10 (castle_transit_attacked) FEN `rn3b2/pBp2kp1/b2ppnr1/1p3P1Q/2P4P/NP2P2N/PB1P2q1/R3K2R w KQ - 1 15`: class still reports True; no castling in engine moves: False
- position 11 (castle_transit_attacked) FEN `r4b2/pBp2kp1/b1nppnr1/1p3P1Q/2P4P/NPB1P2N/P2P2q1/R3K2R w KQ - 3 16`: class still reports True; no castling in engine moves: False

## positions per class
- castle_transit_attacked: 78
- ep_pseudo_but_illegal: 7
- ep_legal: 83
- castle_rook_path_attacked: 77
- capture_promo_check: 83
- double_check: 83
- pinned_captures_pinner: 83