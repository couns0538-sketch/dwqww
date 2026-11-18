#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job5
job=forge-combo29/sol3/job5
recipe=/workspace/work/sol3-job5-assert-prep
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T10:32:59Z +%s)
remaining=$((cutoff - $(date -u +%s)))
test "$remaining" -gt 0
status=0
timeout --kill-after=5s "$remaining" bash "$recipe/build_asserting_k11.sh" "$root/k11_assert" > "$root/assertion_build.output.txt" 2>&1 || status=$?
cp "$recipe/build_asserting_k11.sh" "$recipe/no-ndebug.diff" "$root/run_asserting_check.sh" "$job/"
cp "$root/assertion_build.output.txt" "$job/"
if [ "$status" -eq 0 ]; then
  python3 - "$root/k11_assert/build/compile_commands.json" <<'PY' > "$job/assertion_compile_guard.txt" || status=$?
import json
from pathlib import Path
import sys
commands = json.loads(Path(sys.argv[1]).read_text())
assert commands
print(commands[0]['command'])
print('Compile commands:', len(commands))
print('Commands with NDEBUG:', sum('NDEBUG' in command['command'] for command in commands))
assert all('NDEBUG' not in command['command'] for command in commands)
PY
fi
date -u "+%Y-%m-%dT%H:%M:%SZ Step 5 asserting k11 scratch build and compile guard exited $status" >> "$job/stamps.txt"
git add --sparse -- "$job/"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm 'sol3 job 5 step 5 checkpoint asserting release build'
bash /workspace/work/sol3-job3/push-checkpoint.sh
test "$status" -eq 0
exe="$root/k11_assert/build/forge"
args=(--engine "$exe" --net "$net" --games 60 --softnodes 2000 --random-plies 8 --max-plies 300 --seed 20261117 --json)
{
  printf 'strace -f -e trace=write,writev -e trace-fds=2 -s 2048 -o %q python3 -B %q' "$root/assertion_stderr_syscalls.txt" "$job/selfplay_driver.py"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$exe" "$net" "$job/selfplay_driver.py"
  printf 'uci\nquit\n' | "$exe" | sed -n '/^id name /p'
  date -u +%FT%TZ
} > "$root/assertion_run.meta"
remaining=$((cutoff - $(date -u +%s)))
if (( remaining > 0 )); then
  timeout --kill-after=5s "$remaining" strace -f -e trace=write,writev -e trace-fds=2 -s 2048 -o "$root/assertion_stderr_syscalls.txt" python3 -B "$job/selfplay_driver.py" "${args[@]}" > "$root/assertion_original.json" 2> "$root/assertion_original.stderr.txt" || status=$?
else
  status=124
fi
if rg -q 'Assertion' "$root/assertion_original.stderr.txt" "$root/assertion_stderr_syscalls.txt"; then status=22; fi
printf 'exit_code %s\n' "$status" >> "$root/assertion_run.meta"
cp "$root/assertion_run.meta" "$root/assertion_original.json" "$root/assertion_original.stderr.txt" "$root/assertion_stderr_syscalls.txt" "$job/"
date -u "+%Y-%m-%dT%H:%M:%SZ Step 5 asserting k11 whole-game workload with unchanged original driver exited $status" >> "$job/stamps.txt"
git add --sparse -- "$job/"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm 'sol3 job 5 step 5 preserve asserting workload and stderr'
bash /workspace/work/sol3-job3/push-checkpoint.sh
cat "$job/assertion_original.json" "$job/assertion_original.stderr.txt" "$job/assertion_stderr_syscalls.txt"
test "$status" -eq 0
