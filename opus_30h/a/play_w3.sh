#!/usr/bin/env bash
# play_w3.sh <net name> <out sub folder> <games> <cpus e.g. 2,3> <concurrency> <opening seed> - Opus 30-h job, window 3:
# one sanity match of a packed net (gate exe v2p4 with EvalFileV2=<net>, 10+0.1 vs the lock exe, Idle on <cpus>) into
# D:\o30\nets\<name>\<sub> (sanity_match.py refuses an existing folder). A different opening seed than 30 for extra games
# of a net that already played (seed 30 replays the same openings). The exit code is taken before any $(...) (BH-2).
set -u
name="$1"; sub="$2"; games="$3"; cpus="$4"; conc="$5"; seed="$6"
net="D:/o30/nets/$name/$name.nnue2"
[ -f "$net" ] || { echo "no packed net $net"; exit 2; }
out=$(cygpath -w "/d/o30/nets/$name/$sub")
echo "$(date '+%F %T') $name: $games games, CPUs $cpus, conc $conc, seed $seed -> $out"
cd /d/o30/control || exit 1
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B 'D:\o30\wt\opus_30h\a\sanity_match.py' --out "$out" \
    --cand-exe 'D:\o30\w\v2p4_pc1\src_copy\forge_ltopgo_v2p4_pc1.exe' --cand-opt "EvalFileV2=$net" --games "$games" \
    --conc "$conc" --cpus "$cpus" --seed "$seed" > "/d/o30/logs/sanity_${name}_${sub}.out" 2>&1
rc=$?
echo "$(date '+%F %T') sanity exit $rc"
exit $rc
