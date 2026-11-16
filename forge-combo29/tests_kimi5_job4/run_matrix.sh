#!/bin/bash
# kimi5 job 4 run matrix. Every step appends to stamps.txt first. Run from this folder.
# Order honors the job's minute-40 priority: Part 4's first three columns at d16 early.
set -u
cd "$(dirname "$0")"
BASE=/home/ubuntu/builds/base/forge
TUN=/home/ubuntu/builds/tun/forge
CTR=/home/ubuntu/builds/ctr/forge
FENS=first200.fens
ST=stamps.txt

run() { # engine config depth tag-engine-name
  echo "$(date -u +%FT%TZ) run $2 d$3 on $4" >> $ST
  python3 k5_j4.py "$1" $FENS "$2" "$3" fresh 200
  mv "k5_j4_$2_d$3_fresh.json" "k5_j4_$2_d$3_fresh_$4.json"
  mv "k5_j4_$2_d$3_fresh_input.log" "k5_j4_$2_d$3_fresh_$4_input.log"
}

# K5 part 1: the four names in the exe's own uci list
echo "$(date -u +%FT%TZ) uci list tun" >> $ST
printf 'uci\nquit\n' | $TUN > uci_list_tun.txt 2>&1

# K1: tun OFF vs base OFF at d12 ; base OFF d16 (Part 4 denominator + cross-check)
run $BASE off 12 base
run $BASE off 16 base
run $BASE on 12 base   # K2 comparator: BASE build with the switch on
run $TUN off 12 tun
run $TUN off 16 tun
# K2: tun ON defaults vs base ON ; K3: tun k3 vs base OFF
run $TUN on 12 tun
run $TUN k3 12 tun
# K4: each of the four changed alone
run $TUN k4a 12 tun
run $TUN k4b 12 tun
run $TUN k4c 12 tun
run $TUN k4d 12 tun
# Part 4, d16 first three columns first
run $TUN on 16 tun     # both (defaults)
run $TUN shal 16 tun
run $TUN deep 16 tun
run $TUN shal 12 tun
run $TUN deep 12 tun
run $TUN half 16 tun
run $TUN half 12 tun
run $TUN dbl 16 tun
run $TUN dbl 12 tun
run $TUN flat 16 tun
run $TUN flat 12 tun
# Part 3: must-be-nonzero on ONE position first, then proof + counter runs
echo "$(date -u +%FT%TZ) ctr must-be-nonzero 1pos d16" >> $ST
python3 k5_j4.py $CTR $FENS on 16 fresh 1 && mv k5_j4_on_d16_fresh.json k5_j4_on_d16_fresh_1pos_ctr.json && mv k5_j4_on_d16_fresh_input.log k5_j4_on_d16_fresh_1pos_ctr_input.log
run $CTR on 12 ctr     # proof vs tun on d12 AND d12 counters
run $CTR on 16 ctr     # d16 counters
echo "$(date -u +%FT%TZ) matrix done" >> $ST
