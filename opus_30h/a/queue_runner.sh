#!/usr/bin/env bash
# queue_runner.sh <guard log to wait for> [cutoff HH:MM] - Opus 30-h job, GPU window 2: runs the GPU plan one run at a
# time. The plan is C:\o30g\gpu\plan.txt, re-read before every run (edit the plan, never this script, while it runs):
#   <name> <kb map> <superbatches> <seed> <lr> <init dir (Windows path, warm start)>     ('#' lines = comments)
# A run whose name is in C:\o30g\gpu\plan.done is skipped (the runner writes the name there when it starts the run).
# Per run: its checkpoint watcher (gpu_ckpt_watch.sh, WATCH_ROOT=C:\o30g\gpu, CPUs 3-5) starts in the background, then
# gpu_run_o30c.bat under the guard (exe D:\o30\target_rocm4, O30_CLIP 7.99, O30_DECAY 0, wdl 0.4, 1024 batches per
# superbatch, 2 loader threads, GUARD_MASK 0x38). No run starts after the cutoff (default 18:40, so the last run ends
# inside the owner's window); no run starts while an npt-like process runs (the guard refuses too). Idle, CPUs 3-5.
set -u
A=/d/o30/wt/opus_30h/a; G=/c/o30g/gpu; P=$G/plan.txt; DONE=$G/plan.done
CUTOFF="${2:-18:40}"
. "$A/../tools/idle.sh"
o30_pin_self 0x38 || { echo "queue_runner: cannot pin to Idle / CPUs 3-5 (fail closed)"; exit 78; }
until grep -q ' end: ' "$1" 2>/dev/null; do sleep 15; done
sleep 20
echo "$(date '+%F %T') previous run ended ($1); plan $P, cutoff $CUTOFF"
while true; do
    line=""
    while read -r l; do
        case "$l" in ''|'#'*) continue ;; esac
        n=${l%% *}
        if ! grep -qx "$n" "$DONE" 2>/dev/null; then line="$l"; break; fi
    done < "$P"
    [ -z "$line" ] && { echo "$(date '+%F %T') plan has no open run: queue ends"; break; }
    if [ "$(date +%H%M)" -ge "$(echo "$CUTOFF" | tr -d ':')" ]; then
        echo "$(date '+%F %T') cutoff $CUTOFF reached: '$line' not started; queue ends"; break
    fi
    read -r name kb sb seed lr init <<< "$line"
    echo "$name" >> "$DONE"
    echo "$(date '+%F %T') starting $name: kb $kb sb $sb seed $seed lr $lr init $init"
    ( WATCH_ROOT=$G WATCH_MASK=0x38 bash "$A/gpu_ckpt_watch.sh" "$name" "$kb" > "$G/${name}_watch.log" 2>&1 & )
    GUARD_MASK=0x38 BULLET_EXE='D:\o30\target_rocm4\release\forge-v2-bullet.exe' O30_INIT_DIR="$init" O30_CLIP=7.99 \
        O30_DECAY=0 cmd //d //c 'D:\o30\wt\opus_30h\a\gpu_run_o30c.bat' "$name" "$kb" 0 256 "$sb" 1024 2 "$seed" "$lr" 0.4 8
    echo "$(date '+%F %T') $name exit $?"
    sleep 15
done
