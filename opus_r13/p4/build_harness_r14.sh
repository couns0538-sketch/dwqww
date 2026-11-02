#!/usr/bin/env bash
# R14 A4: v2_eval parity harness builds for H = 768 / 1024 / 1536 (AVX2 x86-64-v3 + SSE x86-64-v2), same flags as the
# R13 H256 builds (C:/o13/p4/run_p4_parity.sh). Source: D:/o14a/p4/r3_h = the R3 tree copy C:/o13/p4/r3 without
# src/nnue_weights.inc (the embedded H256 default net static-asserts H = 256; without it FORGE_HAS_NNUE = 0, and the
# nnue::v2 loader / features / output code is the same source). Outputs D:/o14a/p4.
# (The copy that ran, D:/o14a/p4/build_harness_h2.sh, had a sed-mangled line-3 comment; its commands are these.)
set -u
export PATH=/c/msys64/ucrt64/bin:$PATH
P4=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p4/opus_r13/p4
cd /d/o14a/p4/r3_h || exit 2
SRCS="src/bitboard.cpp src/board.cpp src/book.cpp src/datagen.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/profile.cpp src/search.cpp"
date '+start %F %T'
for H in 768 1024 1536; do
  for v in avx2:x86-64-v3 sse:x86-64-v2; do
    IFS=: read tag march <<< "$v"
    out=/d/o14a/p4/v2_eval_${tag}_h$H.exe; log=/d/o14a/p4/build_v2_eval_${tag}_h${H}_noembed.log
    if [ -e "$out" ]; then echo "exists: $out - skip"; continue; fi
    g++ -std=c++20 -O2 -DNDEBUG -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=$H -march=$march -static -Iinclude \
      $P4/v2_eval.cpp $SRCS -o $out > $log 2>&1
    echo "build $tag H$H exit $? warnings $(grep -c 'warning:' $log) sha256 $(sha256sum $out 2>/dev/null | cut -c1-16)"
  done
  echo "sse H$H ymm/zmm instructions: $(objdump -d /d/o14a/p4/v2_eval_sse_h$H.exe 2>/dev/null | grep -cE 'ymm|zmm')"
done
date '+end %F %T'
