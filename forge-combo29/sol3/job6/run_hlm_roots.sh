#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job6
job=forge-combo29/sol3/job6
probes=/workspace/work/sol3-job6-hlm
root_driver=/workspace/work/sol3-job6-hlm-roots
cutoff=$(date -u -d 2026-11-18T11:02:40Z +%s)
mkdir "$root/stage4a" "$job/root_oracle"
cp "$root_driver/hlm_roots.cpp" "$root_driver/CMakeLists.txt" "$root_driver/build_roots.sh" "$job/root_oracle/"
cp "$root/run_hlm_roots.sh" "$probes/hlm_probe.diff" "$probes/hlm_control.diff" "$job/"
cat "$job/root_positions/"positions-*.txt > "$root/stage4a/replay.commands.txt"
cmp "$root/stage4a/replay.commands.txt" "$root/positions.commands.txt"
sha256sum "$root/stage4a/replay.commands.txt" forge-combo29/sol3/job3/positions.txt > "$job/hlm_4a_fixture_sha256.txt"
status=0
for kind in oracle control; do
  candidate="$root/tree_hlm_$kind"
  mkdir "$candidate"
  cp -a "$root/tree_12/." "$candidate/"
  patchlog="$job/hlm_${kind}.patch.stdout.txt"
  date -u +%FT%TZ > "$patchlog"
  LC_ALL=C patch -d "$candidate" -p1 -F0 --batch --forward -i "$(realpath "$job/hlm_probe.diff")" >> "$patchlog" 2>&1 || status=$?
  if [ "$status" -eq 0 ] && [ "$kind" = control ]; then
    LC_ALL=C patch -d "$candidate" -p1 -F0 --batch --forward -i "$(realpath "$job/hlm_control.diff")" >> "$patchlog" 2>&1 || status=$?
  fi
  if rg -qi 'offset|fuzz|FAILED|reject|Skipping|Reversed' "$patchlog"; then status=21; fi
  remaining=$((cutoff-$(date -u +%s)))
  if [ "$status" -eq 0 ] && ((remaining>0)); then
    timeout --kill-after=5s "$remaining" bash "$job/root_oracle/build_roots.sh" "$candidate" "$root/build_hlm_$kind" > "$job/hlm_${kind}.build.stdout.txt" 2>&1 || status=$?
  elif [ "$status" -eq 0 ]; then status=124; fi
  remaining=$((cutoff-$(date -u +%s)))
  if [ "$status" -eq 0 ] && ((remaining>0)); then
    {
      printf '%q %q %q\n' "$root/build_hlm_$kind/hlm_roots" "$root/stage4a/replay.commands.txt" forge-combo29/sol3/job3/positions.txt
      date -u +%FT%TZ
    } > "$job/hlm_${kind}.command.txt"
    timeout --kill-after=5s "$remaining" "$root/build_hlm_$kind/hlm_roots" "$root/stage4a/replay.commands.txt" forge-combo29/sol3/job3/positions.txt > "$job/hlm_${kind}.stdout.txt" 2> "$job/hlm_${kind}.stderr.txt" || status=$?
  elif [ "$status" -eq 0 ]; then status=124; fi
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 4a $kind patch, compile and root/full-generator replay exited $status" >> "$job/stamps.txt"
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "sol3 job 6 step 4a checkpoint $kind position replay"
  if test -f "$job/hlm_${kind}.stdout.txt"; then cat "$job/hlm_${kind}.stdout.txt"; fi
  test "$status" -eq 0
done
status=0
python3 - "$job" <<'PY' > "$job/hlm_4a.gate.txt" 2> "$job/hlm_4a.gate.stderr.txt" || status=$?
from pathlib import Path
import sys

def groups(path):
    result={}
    for line in path.read_text().splitlines():
        if line.startswith('set=') and ' group=' in line:
            data=dict(field.split('=',1) for field in line.split())
            which=(data.pop('set'),data.pop('group'))
            result[which]={key:int(value) for key,value in data.items()}
    assert len(result)==9,result
    return result
job=Path(sys.argv[1]); a=groups(job/'hlm_oracle.stdout.txt');b=groups(job/'hlm_control.stdout.txt')
for row in a:
    primary,control=a[row],b[row]
    print(row,primary,control)
    assert all(primary[x]==control[x] for x in ('positions','in_check','nomove'))
    assert primary['mismatch']==0
    assert control['mismatch']==primary['nomove']
assert a[('whole_game_roots','all')]['positions']==8612
assert a[('whole_game_roots','all')]['nomove']==41
assert a[('whole_game_roots','in_check')]['nomove']==41
assert a[('whole_game_roots','not_in_check')]['nomove']==0
print('Step 4a gates PASS')
PY
cat "$job/hlm_4a.gate.txt" "$job/hlm_4a.gate.stderr.txt"
date -u "+%Y-%m-%dT%H:%M:%SZ Step 4a full-generator replay and planted-control gates exited $status" >> "$job/stamps.txt"
git add --sparse -- "$job/"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm 'sol3 job 6 step 4a publish full-generator oracle and control gate'
test "$status" -eq 0
