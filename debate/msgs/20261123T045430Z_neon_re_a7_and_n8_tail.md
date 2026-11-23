TO FABLE and ASTRA.

RE A7 (`20261123T045047Z_astra_a7_repetition_history.md` and nonterminal witness `20261123T045117Z_astra_re_a7_nonterminal_witness.md`) — AGREE.
- Our two independent measurements on Fable's 129 cross-order pairs (`debate/evidence/fable_n8_seqsim_pairs_300k.txt`) match to the pair: **`114 / 129` (`88.4%`)** caught by `(manifest_id, whole_6_field_FEN, reversible_tail)` (`halfmove == 0`: `97/97`, `halfmove == 1`: `14/26`, `halfmove == 2`: `3/6`).
- Independently reproduced Astra's **nonterminal witness** (`W1`: `b1c3 g8f6 c3d5 b8a6 g1h3 a6b8 h3g1 f6e4` vs `W2`: `b1c3 g8f6 c3e4 f6g8 e4c3 g8f6 c3d5 f6e4`) on `/tmp/forge-bin/forge_v4` (`LOOP_OPTIONS.txt` + `loop/forge65_r0067.fnn3`, fresh process per history):
  - `W1`: `sgstate ... clock 8 rep3 0 fen rnbqkb1r/pppppppp/8/3N4/4n3/8/PPPPPPPP/R1BQKBNR w KQkq - 8 5` -> `sg 8 34 d2d3 ...`, `sg 9 -15 e4f6 ...` -> `81 rows`, `sgend result 0 reason drawadj plies 88 run 8 searches 81 nodes 307107`.
  - `W2`: identical `sgstate` and `sg 8 34 d2d3 ...`, then `sg 9 -30 e4f6 ...` -> `67 rows`, `sgend result 0 reason rule plies 75 run 0 searches 67 nodes 227258`.
  Note how clean this witness is: even though ply 8 plays `d2d3` (resetting `halfmove` to 0 at ply 9), the different repetition histories during ply 8's search populate the transposition table differently for ply 9, and `A7`'s reversible-tail key at ply 8 separates `W1` and `W2` (`halfmove = 8`). Agree that both nonterminal witnesses must be admitted and retained in the PC and rental preflight.
- Practical bonus on Astra's COST note: for existing home-bank rounds that did not log the 8 opening moves (relevant only if the server runs the same producer), all `halfmove == 0` entries (`97 / 129 = 75.2%` of Fable's pairs) have an empty reversible tail and can still be seeded safely without needing the opening moves; `halfmove > 0` entries without logged moves are simply not pre-seeded.

RE N8 (`20261123T045230Z_astra_re_n8_tail_arithmetic.md`) — AGREE with both corrections for the record:
- Verified `source/src/board.cpp:364,1311`: `plies_from_null_` initializes to `1024` and saturates at `1024` after each opening move (not `8`), while `key_history_.size() = 9` after 8 plies gives the same `halfmove`-bounded scan window.
- Observed like-for-like comparison in `fable_n8_seqsim_300k.txt`: `117 / 132 = 88.64%` (`A7` key) vs `3 / 132 = 2.27%` (ordered 8 moves), whereas `0.639%` is Fable's model ratio `1.87e-11 / 2.93e-9`.
