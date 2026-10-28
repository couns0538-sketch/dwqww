#!/usr/bin/env bash
# R3-1 self-play: finish the final-head matrix (330237f3) after the agent's hand-back. Git Bash on the PC.
#   bash opus_r3/R3-1_selfplay/finish_final.sh status    runners / checkers alive?, finished configs, last log lines
#   bash opus_r3/R3-1_selfplay/finish_final.sh resume    restart runner A and B for the configs without a complete
#                                                        summary (refuses while any runner or checker of this head
#                                                        is alive: two checkers must never write the same config)
#   bash opus_r3/R3-1_selfplay/finish_final.sh collect   MATRIX.md + matrix_summary.json for all 36 configs, copy the
#                                                        small evidence into logs/final_330237f3, FILES.txt and
#                                                        SHA256SUMS (finish_report.sh); prints the git commands
# Never kills or deletes anything. Every process at nice 19.
set -euo pipefail
HEAD=330237f3
W=/f/opus_scratch/worktrees/opus_r3_selfplay
JOB=$W/opus_r3/R3-1_selfplay
S=/f/opus_scratch/r3/selfplay
R=$S/runs/$HEAD
H=F:/opus_scratch/r3/selfplay/harness/final_$HEAD
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
EPD=F:/opus_scratch/worktrees/opus_r3_selfplay/tools/openings/forge-10000.epd
COMMON="--engines F:/opus_scratch/r3/selfplay/engines/$HEAD --nets F:/opus_scratch/r3/selfplay/nets --out F:/opus_scratch/r3/selfplay/runs/$HEAD --git-head $HEAD --configs $H/configs_final.json --epd $EPD"

alive() {   # number of python processes running run_matrix.py / opus_selfplay_check.py on this head
  powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and (\$_.CommandLine -like '*run_matrix.py*' -or \$_.CommandLine -like '*opus_selfplay_check.py*') -and \$_.CommandLine -like '*final_$HEAD*' }).Count" | tr -d '\r'
}
done_list() {   # configs with a complete summary (500 games)
  $PY -I -B - "$(cygpath -w $R)" <<'EOF'
import glob, json, os, sys
for p in sorted(glob.glob(os.path.join(sys.argv[1], "*.summary.json"))):
    s = json.load(open(p))
    if s.get("games") == s.get("games_requested"):
        print(f"{s['config']:28s} games {s['games']} plies {s['plies']} errors {s['errors']} watchdog {s.get('watchdog_answers')}")
EOF
}

case ${1:-status} in
  status)
    echo "alive runner/checker processes for $HEAD: $(alive)"
    echo "configs complete: $(done_list | wc -l) of 36"; done_list
    for r in A B; do echo "== matrix_$r.log (last 3)"; tail -n 3 $R/matrix_$r.log | cut -c1-160; done ;;
  resume)
    n=$(alive)
    if [ "$n" != "0" ]; then echo "refused: $n runner/checker processes of $HEAD are alive (let them finish)"; exit 1; fi
    for r in A B; do
      nohup nice -n 19 $PY -I -B $H/run_matrix.py $COMMON --runner $r --log-name matrix_$r.log \
        >> $S/logs/matrix_${HEAD}_$r.console.log 2>&1 &
      echo "runner $r started (pid $!); it skips configs that already have a complete summary"
    done ;;
  collect)
    nice -n 19 $PY -I -B $JOB/run_matrix.py $COMMON --report-only || true   # exit 1 while configs are missing
    J=$JOB/logs/final_$HEAD
    mkdir -p $J/summaries $J/preflight
    cp $R/MATRIX.md $R/matrix_summary.json $R/matrix_A.log $R/matrix_B.log $J/
    cp $R/*.summary.json $J/summaries/
    cp $R/*.preflight.json $J/preflight/
    for f in $(find $J -type f); do sed -i 's/\r$//' "$f"; done
    cd $W
    bash /f/opus_scratch/tools/finish_report.sh opus_r3/R3-1_selfplay FILES.txt
    for f in $(cd opus_r3/R3-1_selfplay && find logs/final_$HEAD -type f | sort); do
      grep -q "^$f |" opus_r3/R3-1_selfplay/FILES.txt || echo "$f | 0 | - | evidence log" >> opus_r3/R3-1_selfplay/FILES.txt
    done
    bash /f/opus_scratch/tools/finish_report.sh opus_r3/R3-1_selfplay FILES.txt
    (cd opus_r3/R3-1_selfplay && sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS OK")
    echo "next (in $W): git add opus_r3/R3-1_selfplay && git commit -m '[R3-1 selfplay] Final matrix 330237f3 ... [skip ci]' && git push -q -u origin opus-r3-selfplay && git ls-remote origin refs/heads/opus-r3-selfplay" ;;
  *) echo "usage: finish_final.sh status|resume|collect"; exit 2 ;;
esac
