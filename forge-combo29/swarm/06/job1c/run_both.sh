#!/usr/bin/env bash
# job 1 third run: the same 3,853 pairs on BOTH builds. Threads is never above 1 here.
set -u
cd "$(dirname "$0")"
echo "=== base build, S14 ==="
python3 harness_mirror.py /home/ubuntu/bld/release/forge GR_853_621.fens out_base_GR.txt meta_base_GR.txt
python3 harness_mirror.py /home/ubuntu/bld/release/forge Rbig_621.fens   out_base_Rbig.txt meta_base_Rbig.txt
echo "=== PC build, PC20 ==="
python3 ../pc/pc20_rerun.py eval /tmp/bld/pc/forge GR_853_621.fens out_pc_GR.jsonl meta_pc_GR.txt 0 PC20
python3 ../pc/pc20_rerun.py eval /tmp/bld/pc/forge Rbig_621.fens   out_pc_Rbig.jsonl meta_pc_Rbig.txt 0 PC20
echo "=== controls (planted: FEN i vs FEN i+1) on both builds ==="
head -100 G_353.fens > G_100.fens
python3 control_self.py shift /home/ubuntu/bld/release/forge G_100.fens ctrl_base_shift.txt meta_ctrl_base_shift.txt
