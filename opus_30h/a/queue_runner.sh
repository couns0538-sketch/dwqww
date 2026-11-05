#!/usr/bin/env bash
# queue_runner.sh <guard log to wait for> [cutoff HH:MM] - Opus 30-h job, GPU window 2: runs the GPU plan one run at a
# time. The plan is C:\o30g\gpu\plan.txt, re-read before every run (edit the plan, never this script, while it runs):
#   <name> <kb map> <superbatches> <seed> <lr> <init dir (Windows path, warm start)>     ('#' lines = comments)
# A run whose name is in plan.done is skipped. Owner's fix list 2026-11-04 item 1: the name goes into plan.done only
# after the run exits 0; exit 78 (the guard refused to start: npt-like process, stale sensor feed, mask) waits
# RUNNER_RETRY_SLEEP seconds (default 300) and retries the same line WITHOUT marking it; any other exit code goes to
# plan.failed (with the code) and the next line follows, so one refusal can no longer burn the plan.
# Per run: its checkpoint watcher (gpu_ckpt_watch2.sh, WATCH_MASK 0x38) starts in the background, then gpu_run_o30c.bat
# under the guard (exe D:\o30\target_rocm4, O30_CLIP 7.99, O30_DECAY 0, wdl 0.4, 1024 batches per superbatch, 2 loader
# threads, GUARD_MASK 0x38). No run starts after the cutoff (default 18:40). Idle, CPUs 3-5.
# Since 15:19 the live queue is a/queue_runner2.sh (review fix W2-02, plan2.txt); this file was fixed afterwards.
# Test hooks: RUNNER_ROOT (default /c/o30g/gpu), RUNNER_PLAN (default <root>/plan.txt), RUNNER_CMD (a stub run instead of
# the .bat, called with the plan fields), RUNNER_NO_WATCH=1 (no watcher), RUNNER_RETRY_SLEEP.
set -u
A=/d/o30/wt/opus_30h/a; G="${RUNNER_ROOT:-/c/o30g/gpu}"; P="${RUNNER_PLAN:-$G/plan.txt}"
DONE="${P%.txt}.done"; FAILED="${P%.txt}.failed"; RETRY="${RUNNER_RETRY_SLEEP:-300}"
CUTOFF="${2:-18:40}"
. "$A/../tools/idle.sh"
o30_pin_self 0x38 || { echo "queue_runner: cannot pin to Idle / CPUs 3-5 (fail closed)"; exit 78; }
until grep -q ' end: ' "$1" 2>/dev/null; do sleep 15; done
[ -n "${RUNNER_CMD:-}" ] || sleep 20
echo "$(date '+%F %T') previous run ended ($1); plan $P, cutoff $CUTOFF"
while true; do
    line=""
    while read -r l; do
        case "$l" in ''|'#'*) continue ;; esac
        n=${l%% *}
        if ! grep -qx "$n" "$DONE" 2>/dev/null && ! grep -q "^$n " "$FAILED" 2>/dev/null; then line="$l"; break; fi
    done < "$P"
    [ -z "$line" ] && { echo "$(date '+%F %T') plan has no open run: queue ends"; break; }
    if [ "$(date +%H%M)" -ge "$(echo "$CUTOFF" | tr -d ':')" ]; then
        echo "$(date '+%F %T') cutoff $CUTOFF reached: '$line' not started; queue ends"; break
    fi
    read -r name kb sb seed lr init <<< "$line"
    echo "$(date '+%F %T') starting $name: kb $kb sb $sb seed $seed lr $lr init $init"
    if [ -z "${RUNNER_NO_WATCH:-}" ] && [ ! -e "$G/${name}_watch.log" ]; then
        ( WATCH_ROOT=$G WATCH_MASK=0x38 WATCH_MAX_MIN=240 bash "$A/gpu_ckpt_watch2.sh" "$name" "$kb" > "$G/${name}_watch.log" 2>&1 & )
    fi
    if [ -n "${RUNNER_CMD:-}" ]; then
        "$RUNNER_CMD" "$name" "$kb" "$sb" "$seed" "$lr" "$init"
    else
        GUARD_MASK=0x38 BULLET_EXE='D:\o30\target_rocm4\release\forge-v2-bullet.exe' O30_INIT_DIR="$init" O30_CLIP=7.99 \
            O30_DECAY=0 cmd //d //c 'D:\o30\wt\opus_30h\a\gpu_run_o30c.bat' "$name" "$kb" 0 256 "$sb" 1024 2 "$seed" "$lr" 0.4 8
    fi
    rc=$?
    echo "$(date '+%F %T') $name exit $rc"
    if [ "$rc" = 0 ]; then
        echo "$name" >> "$DONE"
    elif [ "$rc" = 78 ]; then
        echo "$(date '+%F %T') $name refused at start (exit 78): not marked; retry in $RETRY s"
        sleep "$RETRY"
        continue
    else
        echo "$name rc $rc $(date '+%F %T')" >> "$FAILED"
        echo "$(date '+%F %T') $name failed (exit $rc): recorded in $FAILED, next line"
    fi
    [ -n "${RUNNER_CMD:-}" ] || sleep 15
done
