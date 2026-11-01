# IDEA_SOURCE - R13 P4 (v2-feature nets with bullet)
- bullet: jw1912/bullet, MIT, commit da426a49 (the PC's F:\bullet_hip\src checkout); used through its public API only.
  The sfbinpack loader inside bullet_lib reads Stockfish binpack data (format idea from Stockfish, GPL): used as an offline
  data reader inside the training tool, never in the engine.
- Feature definitions: Forge's own (forge/nnue_v2.hpp: C5 output buckets, O6 threats, O7 pawn pairs, by Opus); the Rust
  input type re-implements those definitions (own code, no engine code from elsewhere).
- tools: forge_nnue_v2.py is the crew's own (unchanged copy); export_v2.py, eval_ref.py, v2_eval.cpp are own code.
- Status: UNPROVEN. No net, no Elo claim.
