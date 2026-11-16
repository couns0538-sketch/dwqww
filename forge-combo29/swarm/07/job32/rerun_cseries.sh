#!/usr/bin/env bash
# rerun_cseries.sh -- re-runs this seat's board-level checks against the PC r15 tree.
#
# Why: every check below was written against the BASE tree (6b98f217). The PC build changes search
# extensively, so any of them could plausibly have been broken there. Each is compiled against the
# PC tree's OWN src/ and include/, so the code under test is the PC engine's, not a mix.
#
# Every program carries its own positive control (a planted fault in a scratch copy), run in the
# same script, so a zero from the real build means something. See job32/CONTROLS.txt for the control
# runs recorded in this job.
set -u
PC=/agent/repos/pcbase/forge-combo29
OUT=/agent/repos/dwqww/forge-combo29/swarm/07/job32
DEFS='-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_KING_LINES=1 -DFORGE_MATE_ALPHA_GUARD=1 -DNDEBUG'
INC="-I$PC/include"

echo "=== 1. key_after vs make_move (PC tree) ==="
g++-13 -std=c++20 -O2 -march=x86-64-v4 $DEFS $INC \
    /agent/repos/dwqww/forge-combo29/swarm/07/job6/key_after_test.cpp \
    $PC/src/board.cpp $PC/src/bitboard.cpp -o /tmp/pc_keytest 2>&1 | head -5
/tmp/pc_keytest 200 701 | tee "$OUT/key_after_pc.txt"

echo "=== 2. board probes: castling / ep / king across null (PC tree) ==="
g++-13 -std=c++20 -O2 -march=x86-64-v4 $DEFS $INC \
    /agent/repos/dwqww/forge-combo29/swarm/07/job6/board_probes.cpp \
    $PC/src/board.cpp $PC/src/bitboard.cpp -o /tmp/pc_boardprobes 2>&1 | head -5
/tmp/pc_boardprobes | tee "$OUT/board_probes_pc.txt"

echo "=== 3. fast legality path vs brute force (PC tree) ==="
g++-13 -std=c++20 -O2 -march=x86-64-v4 $DEFS $INC \
    /agent/repos/dwqww/forge-combo29/swarm/07/job13/is_legal_probe.cpp \
    $PC/src/board.cpp $PC/src/bitboard.cpp -o /tmp/pc_islegal 2>&1 | head -5
/tmp/pc_islegal 40 701 | tee "$OUT/is_legal_pc.txt"

echo "=== 4. gives_check vs make+in_check (PC tree) ==="
g++-13 -std=c++20 -O2 -march=x86-64-v4 $DEFS $INC \
    /agent/repos/dwqww/forge-combo29/swarm/07/job14/gives_check_probe.cpp \
    $PC/src/board.cpp $PC/src/bitboard.cpp -o /tmp/pc_gcprobe 2>&1 | head -5
/tmp/pc_gcprobe 40 701 | tee "$OUT/gives_check_pc.txt"

echo "=== 5. has_legal_move vs python-chess (PC tree) ==="
g++-13 -std=c++20 -O2 -march=x86-64-v4 $DEFS $INC \
    /agent/repos/dwqww/forge-combo29/swarm/07/job8/legal_move_probe.cpp \
    $PC/src/board.cpp $PC/src/bitboard.cpp -o /tmp/pc_legalprobe 2>&1 | head -5
cd /agent/repos/dwqww/forge-combo29/swarm/07/job32 && \
  timeout 600 python3 -u ../job8/check_legal_move.py /tmp/pc_legalprobe 2>&1 | tee "$OUT/has_legal_move_pc.txt"

echo "=== 6. repetition vs python-chess (PC tree) ==="
g++-13 -std=c++20 -O2 -march=x86-64-v4 $DEFS $INC \
    /agent/repos/dwqww/forge-combo29/swarm/07/job7/repetition_probe.cpp \
    $PC/src/board.cpp $PC/src/bitboard.cpp -o /tmp/pc_repprobe 2>&1 | head -5
cd /agent/repos/dwqww/forge-combo29/swarm/07/job32 && \
  timeout 600 python3 -u ../job7/check_repetition.py /tmp/pc_repprobe 2>&1 | tee "$OUT/repetition_pc.txt"

echo "=== 7. perft vs python-chess on the 14 special positions (PC exe) ==="
cd /agent/repos/dwqww/forge-combo29/swarm/07/job32 && \
  timeout 900 python3 -u ../job4/perft_board.py "$PC/build-pc/forge" perft_pc 2>&1 | tee "$OUT/perft_pc.txt"
