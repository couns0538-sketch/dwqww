#!/usr/bin/env bash
# perf record on `bench 13` then a flat text report (top symbols), text only, nothing binary committed.
# Note: on this host the kernel-versioned perf is at /usr/lib/linux-tools/6.8.0-149-generic/perf because the
# /usr/bin/perf wrapper cannot find a build for kernel 6.12.113+ (that is why it is called by full path).
# cycles:u is not available to an unprivileged user here (perf_event_paranoid=2 blocks cpu cycles only for
# system-wide, and the software fallback task-clock was chosen by perf itself); the event is printed below.
set -u
EXE="$1"; OUT="${2:-perf_bench13.data}"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n' > /tmp/bin_profile.txt
"$PERF" record -q -e cycles:u -o "$OUT" "$EXE" < /tmp/bin_profile.txt > /dev/null 2>/tmp/perf_err.txt
echo "record exit=$?  perf_err: $(tr '\n' ' ' < /tmp/perf_err.txt)"
"$PERF" report -i "$OUT" --stdio --percent-limit 0.4 --no-children 2>/dev/null | sed -n '1,70p'
