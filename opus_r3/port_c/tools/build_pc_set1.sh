#!/usr/bin/env bash
# R3 port C, PC recipe builds set 1 (one g++ at a time, nice 19): final head default / O2, base O2 reference.
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
W=/f/opus_scratch/worktrees/opus_r3_port_c
B=/f/opus_scratch/build/r3_port_c
L=/f/opus_scratch/r3/port_c/logs
nice -n 19 bash $T/build_pc.sh "$W" $B/final_default.exe > $L/build_final_default.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/final_o2.exe -DFORGE_NNUE_O2=1 > $L/build_final_o2.log 2>&1
nice -n 19 bash $T/build_pc.sh /f/opus_scratch/r3/port_c/base_src $B/base_2432670b_o2.exe -DFORGE_NNUE_O2=1 > $L/build_base_2432670b_o2.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/final_int16.exe -DFORGE_NNUE_INT16=1 > $L/build_final_int16.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/final_int16_o2.exe -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_O2=1 > $L/build_final_int16_o2.log 2>&1
{
  echo "# cmp -l (byte offset, differing values) of PC-recipe exes; 4 bytes = PE timestamp (137-138) + checksum (217-218)"
  echo "## final_default.exe vs base_2432670b.exe"; cmp -l $B/base_2432670b.exe $B/final_default.exe; echo "differing bytes: $(cmp -l $B/base_2432670b.exe $B/final_default.exe | wc -l)"
  echo "## final_o2.exe vs base_2432670b_o2.exe"; cmp -l $B/base_2432670b_o2.exe $B/final_o2.exe; echo "differing bytes: $(cmp -l $B/base_2432670b_o2.exe $B/final_o2.exe | wc -l)"
  ls -l $B/base_2432670b.exe $B/final_default.exe $B/base_2432670b_o2.exe $B/final_o2.exe $B/final_int16.exe $B/final_int16_o2.exe
} > $L/byte_identity_default_and_o2.log 2>&1
cat $L/build_final_default.log $L/build_final_o2.log $L/build_base_2432670b_o2.log $L/build_final_int16.log $L/build_final_int16_o2.log
cat $L/byte_identity_default_and_o2.log
