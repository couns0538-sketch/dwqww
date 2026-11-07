# KING_LINES on trial_w6 - qualification pack (speed switch, expected BIT-EXACT; NOT a lock)

- **Branch:** `opus-king-lines-20261106`, cut from opus-speed f17a83b5.
- **Engine parent:** the live lock trial_w6, `F:\ospd\src\trial_w6`, sha256 4181A589...6FB0 with its six lock switches.
- **Builds and outputs:** `D:\opus_5h\king_lines\`.
- **Switch:** `FORGE_SPD_KING_LINES`, compile time, default 0, in include/forge/board.hpp. There is no UCI option.
  - It caches pins, discoverers and check squares for is_legal / gives_check.
  - It adds about 80 B per Undo / NullUndo.
- **Source:** the committed, reviewed KING_LINES-only patch `opus_speed/patches/b4_king_lines_after_w8.patch` (md5
  d680f9bf) applied to a trial_w6 copy.
  - This works because trial_w6 and trial_w8 have the same board.hpp / board.cpp. trial_w8 only adds nnue / search
    switches.
  - The result equals `F:\ospd\src\trial_w9` in both files, and lock + `patches/trial_w9.patch` (8bf44bab) = that tree.
  - Saved as `king_lines_after_w6.patch` (md5 70d69d8a); apply-proof gives an identical tree.
- **Builds:** `tools/port_controls.sh` makes `kl_id` (the six lock flips, KING_LINES 0) and `kl_gate` (the six +
  KING_LINES 1). Both are built with lp_v1 -Twice.

The results are in STATUS.md (steps 1-4).
