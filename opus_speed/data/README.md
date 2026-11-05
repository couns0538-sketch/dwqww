# Data files of the speed job

| file | md5 | lines | what | use |
|---|---|---|---|---|
| fens_12k_v2.txt | e7dbf2c8151188c03ef52054557a531e | 12,000 | six-field FENs (side to move, castling, ep, clocks), LF; copy of `F:\opus_scratch\r10\parity\fens_12k_v2.txt`; same positions as the branch file `opus_r10/parity/fens_12k.txt` of opus-r10-halfka / opus-r12-pgo-net (that one is CRLF, md5 23f4d1dd) | bit-exact L3 (default), the w12k PGO workload |
| fens_12k.txt | 078b6c2ef2785cad94200fe844163d5a | 12,000 | PLACEMENT-ONLY lines (no side to move), copy of the scratch file `F:\opus_scratch\r10\parity\fens_12k.txt` (a parity-tool input) | NOT for engine runs: the lock answers each line with `info string invalid FEN: FEN must contain six fields` and keeps its old position. Kept only as the record of the 09:0x mistake; `ConvertTo-OspdFen` would complete it to white to move, no castling |
| game_positions_300.tsv | c00eb127e7992d173360c078e43ad0e8 | 302 | `#` provenance lines (source PGN `gate_stB_lmrcapvictim1_vs_AL1.pgn` md5 f25a04e2, 30 games of 1071, 10 per game, min ply 16, seed 20261105) + game index, ply, six-field FEN | the wmix PGO workload |
| extreme_fens.tsv | 987a0dfbe839af93bf52189c16740a9c | 22 | 6 `#` header lines + 16 tab-separated rows (id, set, FEN, why, source, expect): set A = 10 positions the lock accepts (the patch review's 218-move and mass-promotion positions, a high-capture node built here, an illegal e.p. under a rank pin, perft positions 3 / 4 / 5 with their published perft 3 counts, stalemate, checkmate, bare kings), set R = 6 FENs illegal in normal play that the lock rejects (expected `invalid FEN` reason per row) | `tools/patchrev_qa.py extreme` (follow-up test 1e) |

Earlier jobs' "12k exe identity" results (R12 / R13 `r12_fens12k.py`) used the branch file with six fields: they are
valid (the R12 e19 output has 11,999 distinct rows of 12,000). Only this job's first L3 runs (before ~09:30) used the
placement-only copy; those results were withdrawn.
