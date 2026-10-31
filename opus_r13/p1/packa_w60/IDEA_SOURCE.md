# IDEA_SOURCE - packa port (R13 P1, items packa_w50 / packa_w60)
- Port: Opus R13, mechanical application of `D:\grok-pc-data\opus30h_inputs\packa.patch` (sha256 909d9bfb7258be73…)
  onto the lock tree d4f4312 with `patch -p1 -F0` (no fuzz, no offset); its CMakeLists.txt hunk is dropped (no CMake in
  the lock tree). No new code, ideas or constants. Gate values 50 / 60 are the crew's own g43 / g34 values.
- Idea sources of packa itself (from the crew's packae2r IDEA_SOURCE.md, unchanged): P1 non-pawn correction history -
  Caissa (correction history) and Stockfish (several correction tables), public technique, own code; P3 pawn-keyed quiet
  history - Stockfish's pawn history (idea only); P7 correction-magnitude LMR (LmrCorrThreshold, default 0, not in the gate
  lines) - Stockfish PR #5727 idea (GPL-3, idea only). No code, comments, tables or tuned constants from any engine.
- Status: UNPROVEN. No Elo or speed claim.
