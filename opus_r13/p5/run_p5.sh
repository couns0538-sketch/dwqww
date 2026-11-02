#!/usr/bin/env bash
# R13 P5: build Astra's forge_data_probe against the lock source (git d4f4312), then the sharded relabel job (1 worker).
set -uo pipefail
export PATH=/c/msys64/ucrt64/bin:$PATH
P5=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p5/opus_r13/p5
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
mkdir -p /c/o13/p5/lock && cd /c/o13/p5/lock
[ -e src/search.cpp ] || git -C /d/grok-pc-data/dwqww -c core.autocrlf=false archive d4f43124dde1d1e37de90e18930e374f32ea7ffa src include | tar -x
[ -e /c/o13/p5/forge_data_probe.exe ] || nice -n 10 g++ -O3 -DNDEBUG -std=gnu++20 -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -DFORGE_NNUE_HIDDEN=256 -static -Iinclude $P5/forge_data_probe.cpp src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp \
  src/eval_params.cpp src/nnue.cpp src/search.cpp -o /c/o13/p5/forge_data_probe.exe > /c/o13/p5/build_probe.log 2>&1
echo "probe build exit $? warnings $(grep -c 'warning:' /c/o13/p5/build_probe.log) sha256 $(sha256sum /c/o13/p5/forge_data_probe.exe | cut -c1-16)"
cd $P5 && "$PY" -I -B relabel_job.py run --pos D:/grok-pc-data/r11_nnue/astra/forge_filtered.pos --allow-reconstructed \
  --probe C:/o13/p5/forge_data_probe.exe --job C:/o13/p5/job1 --run-id r13p5-20261101-a --shard-size 20000 --nodes 20000 \
  --workers 1 --mask 0x8 --until "$1"
echo "relabel exit $?"
"$PY" -I -B relabel_job.py status C:/o13/p5/job1
