#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job4
previous=/workspace/work/sol3-job3
job=forge-combo29/sol3/job4
positions=forge-combo29/sol3/job3/positions.txt
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T10:10:12Z +%s)
test "$(git symbolic-ref --short HEAD)" = for-fable-and-opus/sol3-work
mkdir "$root/cells"

save() {
  local subject=$1
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "$subject"
  bash "$previous/push-checkpoint.sh"
  printf '%s %s\n' "$(git rev-parse --short HEAD)" "$subject"
}

run_cell() {
  local arm=$1 cell=$2
  local out="$root/cells/${arm}_${cell}" status=0 remaining
  local args=("$root/build_$arm/forge" "$positions" "$out" "$arm" "$cell")
  if [[ "$cell" = N* ]]; then args+=(--net "$net"); fi
  mkdir "$out"
  remaining=$((cutoff - $(date -u +%s)))
  {
    date -u '+%Y-%m-%dT%H:%M:%SZ Cell started'
    printf 'python3 %q' "$job/identity.py"
    printf ' %q' "${args[@]}"
    printf '\n'
    if (( remaining > 0 )); then
      timeout --kill-after=5s "$remaining" python3 "$job/identity.py" "${args[@]}" || status=$?
    else
      status=124
      printf 'Clock cutoff reached before starting cell\n'
    fi
    date -u "+%Y-%m-%dT%H:%M:%SZ Cell ended exit $status"
  } > "$out/run_${arm}_${cell}.txt" 2> "$out/run_${arm}_${cell}.stderr.txt"
  cp "$out/"*.txt "$job/"
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 3 $arm/$cell finished, exit $status" >> "$job/stamps.txt"
  save "sol3 job 4 step 3 checkpoint $arm $cell"
  return "$status"
}

cp "$root/run_matrix.sh" "$job/run_matrix.sh"
for arm in 10 11; do
  for cell in B2 B3 N2 N3 ND; do
    run_cell "$arm" "$cell"
  done
done

plant_dir="$root/control"
mkdir "$root/tree_P" "$plant_dir"
cp -a "$root/tree_11/." "$root/tree_P/"
python3 - "$root/tree_11/include/forge/search.hpp" "$plant_dir/plant.diff" <<'PY'
import difflib
from pathlib import Path
import sys

header = Path(sys.argv[1]).read_text()
start = header.index('bool check_node_or_periodic_stop()')
end = header.index('\n    }', start)
fragment = header[start:end]
old = 'local_nodes_ < node_limit_'
new = 'local_nodes_ <= node_limit_'
assert fragment.count(old) == 1
planted = header[:start] + fragment.replace(old, new) + header[end:]
Path(sys.argv[2]).write_text(''.join(difflib.unified_diff(header.splitlines(keepends=True),
    planted.splitlines(keepends=True), fromfile='a/include/forge/search.hpp', tofile='b/include/forge/search.hpp')))
PY
status=0
LC_ALL=C patch -d "$root/tree_P" -p1 -F0 --batch --forward -i "$plant_dir/plant.diff" > "$plant_dir/patch_P.txt" 2>&1 || status=$?
if rg -qi 'offset|fuzz|FAILED|reject|Skipping|Reversed' "$plant_dir/patch_P.txt"; then status=21; fi
printf 'patch_exit %s\n' "$status" >> "$plant_dir/patch_P.txt"
remaining=$((cutoff - $(date -u +%s)))
if [ "$status" -eq 0 ] && (( remaining > 0 )); then
  timeout --kill-after=5s "$remaining" bash "$previous/build_one.sh" "$root/tree_P" "$root/build_P" "$plant_dir/build_P.txt" || status=$?
else
  if [ "$status" -eq 0 ]; then status=124; fi
fi
cp "$plant_dir/"*.txt "$plant_dir/plant.diff" "$job/"
date -u "+%Y-%m-%dT%H:%M:%SZ Step 3 planted control patch and build exited $status" >> "$job/stamps.txt"
save 'sol3 job 4 step 3 preserve exact planted control and build'
test "$status" -eq 0
for cell in B2 B3 N2 N3 ND; do
  run_cell P "$cell"
done
