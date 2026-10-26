# S14 prose line-reference correction — 2026-10-26

Two handwritten references in the source-recon Markdown were off. The exact machine-recorded source hashes and line ranges in the recon JSON were already correct.

- `include/forge/board.hpp`: MoveList is lines49–73 (the JSON hashed49–75, also including the following blank and `struct Undo` marker); use49–73 for the class itself.
- `include/forge/board.hpp`: moved_piece is line163, not161.

No source, engine finding, test result or implementation changed. This addendum preserves the initial sealed packet and checksum manifest. The successor v2 checksum manifest includes both the original files and this correction. Native allocation/node/speed/Elo results remain UNVERIFIED.
