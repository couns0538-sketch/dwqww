#!/usr/bin/env bash
# queue_runner2.sh <guard log to wait for> [cutoff HH:MM] - Opus 30-h job, GPU window 2: queue_runner.sh with the
# independent review's fix W2-02 (a run refused at start no longer burns the plan). Runs the plan in
# C:\o30g\gpu\plan2.txt one run at a time; the plan is re-read before every run (edit the PLAN, never this script):
#   <name> <kb map> <superbatches> <seed> <lr> <init dir (Windows path, warm start)>     ('#' lines = comments)
# Per line: the fields are validated (6 fields, a known king map, integer superbatches / seed, a numeric lr, an init
# dir with optimiser_state); no start while an npt-like python process runs (npt_busy.py; wait 5 min and re-check).
# The run is marked in plan2.done only once its guard log shows "start trainer"; then its checkpoint watcher
# (gpu_ckpt_watch2.sh, WATCH_MASK 0x38, WATCH_MAX_MIN 240) starts. A run refused at start (guard exit 78, bat abort)
# is logged in plan2.refused and retried after 5 min; after 3 refusals it goes to plan2.skipped. An invalid line goes
# to plan2.skipped at once. No run starts after the cutoff (default 18:40). Idle, CPUs 3-5 (0x38).
# Before a retry the refused attempt's <run> folder / .out / .guard.log / .runner.txt move aside as <file>.refused<N>
# (bug hunt 2026-11-04: the bat refuses existing ones with exit 4, so retries 2 and 3 could never start; no refusal
# happened in the live window - plan2.refused stayed empty).
# Test hooks (as queue_runner.sh): RUNNER_ROOT (default /c/o30g/gpu), RUNNER_PLAN (default <root>/plan2.txt; .done /
# .skipped / .refused next to it), RUNNER_CMD (a stub instead of the .bat, called with the plan fields; no npt check),
# RUNNER_NO_WATCH=1 (no watcher), RUNNER_RETRY_SLEEP (default 300).
# RUNNER_GPU_MASK (default 0x38 = CPUs 3-5): the CPU mask of the runner, the guard + trainer and the watcher (window 3
# of 2026-11-04 ran on 0x60 = CPUs 5-6, beside sanity matches on CPUs 0-4).
set -u
A=/d/o30/wt/opus_30h/a; G="${RUNNER_ROOT:-/c/o30g/gpu}"; P="${RUNNER_PLAN:-$G/plan2.txt}"
DONE="${P%.txt}.done"; SKIP="${P%.txt}.skipped"; REF="${P%.txt}.refused"; RETRY="${RUNNER_RETRY_SLEEP:-300}"
GM="${RUNNER_GPU_MASK:-0x38}"
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
CUTOFF="${2:-18:40}"
. "$A/../tools/idle.sh"
O30_MASK="$GM" o30_pin_self "$GM" || { echo "queue_runner2: cannot pin to Idle / $GM (fail closed)"; exit 78; }
until grep -q ' end: ' "$1" 2>/dev/null; do sleep 15; done
[ -n "${RUNNER_CMD:-}" ] || sleep 20
echo "$(date '+%F %T') previous run ended ($1); plan $P, cutoff $CUTOFF"
touch "$DONE" "$SKIP" "$REF"
while true; do
    line=""
    while read -r l; do
        case "$l" in ''|'#'*) continue ;; esac
        n=${l%% *}
        if ! grep -qx "$n" "$DONE" && ! grep -qx "$n" "$SKIP"; then line="$l"; break; fi
    done < "$P"
    [ -z "$line" ] && { echo "$(date '+%F %T') plan has no open run: queue ends"; break; }
    if [ "$(date +%H%M)" -ge "$(echo "$CUTOFF" | tr -d ':')" ]; then
        echo "$(date '+%F %T') cutoff $CUTOFF reached: '$line' not started; queue ends"; break
    fi
    read -r name kb sb seed lr init extra <<< "$line"
    why=""
    [ -n "${init:-}" ] && [ -z "${extra:-}" ] || why="needs exactly 6 fields"
    case "$kb" in one|rank4|rank4x2|rank4x4|rank4x8) ;; *) why="${why:+$why; }unknown king map '$kb'" ;; esac
    [[ "$sb" =~ ^[0-9]+$ && "$seed" =~ ^[0-9]+$ ]] || why="${why:+$why; }superbatches / seed not integers"
    [[ "$lr" =~ ^[0-9.eE+-]+$ ]] || why="${why:+$why; }lr not a number"
    [ -n "${init:-}" ] && [ -f "$(cygpath -u "$init")/optimiser_state/weights.bin" ] || why="${why:+$why; }no $init/optimiser_state/weights.bin"
    if [ -n "$why" ]; then
        echo "$name" >> "$SKIP"; echo "$(date '+%F %T') SKIP invalid plan line '$line': $why"; continue
    fi
    busy=0; [ -n "${RUNNER_CMD:-}" ] || busy=$("$PY" -I -B D:/o30/gpu/npt_busy.py)
    if [ "$busy" != "0" ]; then
        echo "$(date '+%F %T') npt-like process present ($busy): $name waits 5 min"; sleep 300; continue
    fi
    echo "$(date '+%F %T') starting $name: kb $kb sb $sb seed $seed lr $lr init $init"
    if [ -n "${RUNNER_CMD:-}" ]; then
        "$RUNNER_CMD" "$name" "$kb" "$sb" "$seed" "$lr" "$init" > "$G/$name.runner.txt" 2>&1 &
    else
        GUARD_MASK="$GM" BULLET_EXE='D:\o30\target_rocm4\release\forge-v2-bullet.exe' O30_INIT_DIR="$init" O30_CLIP=7.99 \
            O30_DECAY=0 cmd //d //c 'D:\o30\wt\opus_30h\a\gpu_run_o30c.bat' "$name" "$kb" 0 256 "$sb" 1024 2 "$seed" "$lr" 0.4 8 \
            > "$G/$name.runner.txt" 2>&1 &
    fi
    bpid=$!
    while kill -0 "$bpid" 2>/dev/null && ! grep -q 'start trainer' "$G/$name.guard.log" 2>/dev/null; do sleep 5; done
    started=0
    if grep -q 'start trainer' "$G/$name.guard.log" 2>/dev/null; then
        started=1
        echo "$name" >> "$DONE"
        [ -n "${RUNNER_NO_WATCH:-}" ] || ( WATCH_ROOT=$G WATCH_MASK="$GM" WATCH_MAX_MIN=240 bash "$A/gpu_ckpt_watch2.sh" "$name" "$kb" > "$G/${name}_watch.log" 2>&1 & )
    fi
    wait "$bpid"; rc=$?
    echo "$(date '+%F %T') $name exit $rc (started $started)"
    if [ "$started" = 0 ]; then
        echo "$name $(date '+%F %T') rc $rc" >> "$REF"
        if [ "$(grep -c "^$name " "$REF")" -ge 3 ]; then
            echo "$name" >> "$SKIP"; echo "$(date '+%F %T') $name refused 3 times: skipped"
        else
            k=$(grep -c "^$name " "$REF")
            for f in "$G/$name" "$G/$name.out" "$G/$name.guard.log" "$G/$name.runner.txt"; do [ -e "$f" ] && mv "$f" "$f.refused$k"; done
            echo "$(date '+%F %T') $name refused at start: its files moved aside (.refused$k); retry in $RETRY s"; sleep "$RETRY"
        fi
    fi
    [ -n "${RUNNER_CMD:-}" ] || sleep 15
done
