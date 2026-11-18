#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job3
job=forge-combo29/sol3/job3
cutoff=$(date -u -d 2026-11-18T10:12:14Z +%s)
test "$(git symbolic-ref --short HEAD)" = for-fable-and-opus/sol3-work
mkdir -p "$root/arms"

checkpoint() {
  local arm=$1 status=$2 source=$3 evidence=$4
  cp "$evidence/"*.txt "$job/"
  if [ "$arm" = 0 ]; then
    cp "$root/run_stack.sh" "$job/run_stack.sh"
    cp "$root/stack.expected.sha256" "$job/stack.expected.sha256.txt"
  elif [ "$arm" = P ]; then
    cp "$evidence/plant.diff" "$job/plant.diff"
  fi
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 3 $arm $source build/identity disposition $status" >> "$job/stamps.txt"
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "sol3 job 3 step 3 arm $arm $source"
  bash "$root/push-checkpoint.sh"
  printf 'Recorded %s %s at %s (%s)\n' "$arm" "$source" "$(git rev-parse --short HEAD)" "$status"
}

measure() {
  local arm=$1 tree=$2 label=$3 evidence=$4
  local build="$root/build_$arm" status=0 remaining
  remaining=$((cutoff - $(date -u +%s)))
  if (( remaining <= 0 )); then
    printf 'Budget cutoff reached before building arm %s\n' "$arm" | tee "$evidence/run_$arm.txt"
    checkpoint "$arm" 'budget-cutoff' "$label" "$evidence"
    return 1
  fi
  if [ "$arm" != 0 ]; then
    timeout --kill-after=5s "$remaining" bash "$root/build_one.sh" "$tree" "$build" "$evidence/build_$arm.txt" || status=$?
  fi
  if [ "$status" -ne 0 ]; then
    printf 'Build failed exit %s\n' "$status" > "$evidence/run_$arm.txt"
    checkpoint "$arm" "build-exited-$status" "$label" "$evidence"
    return "$status"
  fi
  remaining=$((cutoff - $(date -u +%s)))
  if (( remaining <= 0 )); then
    printf 'Budget cutoff reached before searching arm %s\n' "$arm" > "$evidence/run_$arm.txt"
    checkpoint "$arm" 'budget-cutoff' "$label" "$evidence"
    return 1
  fi
  {
    date -u '+%Y-%m-%dT%H:%M:%SZ Identity started'
    printf 'python3 %q %q %q %q %q\n' "$root/identity.py" "$build/forge" "$job/positions.txt" "$evidence" "$arm"
    timeout --kill-after=5s "$remaining" python3 "$root/identity.py" "$build/forge" "$job/positions.txt" "$evidence" "$arm" || status=$?
    date -u "+%Y-%m-%dT%H:%M:%SZ Identity ended exit $status"
  } > "$evidence/run_$arm.txt" 2> "$evidence/run_$arm.stderr.txt"
  checkpoint "$arm" "identity-exited-$status" "$label" "$evidence"
  return "$status"
}

apply_piece() {
  local tree=$1 patch_file=$2 log=$3 status=0
  date -u '+%Y-%m-%dT%H:%M:%SZ Applying patch -p1 -F0' > "$log"
  sha256sum "$patch_file" >> "$log"
  LC_ALL=C patch -d "$tree" -p1 -F0 --batch --forward -i "$patch_file" >> "$log" 2>&1 || status=$?
  printf 'patch_exit %s\n' "$status" >> "$log"
  if [ "$status" -eq 0 ] && ! rg -qi 'offset|fuzz|FAILED|reject|Skipping|Reversed' "$log"; then
    printf 'patch_result CLEAN\n' >> "$log"
  else
    printf 'patch_result EXCEPTION\n' >> "$log"
    while IFS= read -r -d '' rejected; do
      printf '\nRejected hunk from %s\n' "${rejected#"$tree"/}" >> "$log"
      cat "$rejected" >> "$log"
    done < <(find "$tree" -type f -name '*.rej' -print0)
  fi
}

mkdir "$root/arms/0"
printf 'patch_result BASELINE\n' > "$root/arms/0/patch_0.txt"
measure 0 "$root/r15d" r15d "$root/arms/0"
previous="$root/r15d"
k=0
while read -r digest filename; do
  k=$((k+1))
  tree="$root/tree_$k"
  evidence="$root/arms/$k"
  mkdir "$tree" "$evidence"
  cp -a "$previous/." "$tree/"
  test "$(sha256sum "$root/stack/$filename" | awk '{print $1}')" = "$digest"
  apply_piece "$tree" "$root/stack/$filename" "$evidence/patch_$k.txt"
  (cd "$tree" && find . -type f ! -name '*.orig' ! -name '*.rej' -print0 | sort -z | xargs -0 sha256sum) > "$evidence/source_$k.sha256.txt"
  measure "$k" "$tree" "${filename%.patch.txt}" "$evidence"
  previous="$tree"
done < "$root/stack.expected.sha256"
test "$k" -eq 10
plant_tree="$root/tree_P"
evidence="$root/arms/P"
mkdir "$plant_tree" "$evidence"
cp -a "$previous/." "$plant_tree/"
python3 - "$previous/src/board.cpp" "$evidence/plant.diff" <<'PY'
import difflib
from pathlib import Path
import sys

board = Path(sys.argv[1]).read_text()
search_start = board.index('bool Board::key_after(')
search_end = board.index('\n}', search_start)
fragment = board[search_start:search_end]
old = 'next ^= Z.castling[castling_] ^ Z.castling[castling] ^ Z.side;'
new = 'next ^= Z.castling[castling_] ^ Z.castling[castling];'
assert fragment.count(old) == 1
planted = board[:search_start] + fragment.replace(old, new) + board[search_end:]
patch = difflib.unified_diff(board.splitlines(keepends=True), planted.splitlines(keepends=True),
                             fromfile='a/src/board.cpp', tofile='b/src/board.cpp')
Path(sys.argv[2]).write_text(''.join(patch))
PY
apply_piece "$plant_tree" "$evidence/plant.diff" "$evidence/patch_P.txt"
rg -x 'patch_result CLEAN' "$evidence/patch_P.txt"
(cd "$plant_tree" && find . -type f ! -name '*.orig' ! -name '*.rej' -print0 | sort -z | xargs -0 sha256sum) > "$evidence/source_P.sha256.txt"
measure P "$plant_tree" planted-key-fault "$evidence"
