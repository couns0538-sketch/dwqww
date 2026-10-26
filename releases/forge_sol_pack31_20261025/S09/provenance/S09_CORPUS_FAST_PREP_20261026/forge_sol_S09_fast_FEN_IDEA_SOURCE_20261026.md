# S09 FEN-only corpus fallback idea sources, 2026-10-26

This is a FEN-output adaptation of our own original native oracle, not imported
engine code or tuned constants. Original dependency:
`tools/nnue_million_oracle.cpp`, SHA256
`ea4593539d4d23744b0cc7fb5cf1c21eb9a8385fb6b7cf534f8d55c5e7e6f93e`.
Its ten Starts, Seed and LCG block are byte-identical. The same Forge legal-move
API enumerates all legal first moves, then deterministic walks of at most192
plies. NNUE observations are omitted; board.fen() supplies complete six-field
FENs. The new code keeps first occurrences by textual first-four-field FEN,
without implementing a FEN parser. A finite explicit attempt bound fails closed.

The1024-position dry runs are capacity diagnostics only. They do not establish
a completed1M-position corpus, NNUE parity, engine speed or playing strength.
Python-chess validates every dry FEN independently using its existing installed
API; its source is not copied. Original inputs, closed reference archive and
all dry output bytes are retained unchanged.
