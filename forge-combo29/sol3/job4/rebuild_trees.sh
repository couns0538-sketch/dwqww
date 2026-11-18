#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job4
prev=/workspace/work/sol3-job3

apply() {
  local dir=$1 patch_file=$2
  local log="$root/stage0/patch_$(basename "$patch_file")"
  date -u '+%Y-%m-%dT%H:%M:%SZ patch -p1 -F0' > "$log"
  sha256sum "$patch_file" >> "$log"
  LC_ALL=C patch -d "$dir" -p1 -F0 --batch --forward -i "$patch_file" >> "$log" 2>&1
  if rg -qi 'offset|fuzz|FAILED|reject|Skipping|Reversed' "$log"; then exit 21; fi
}

for patch in pc_r15 a_speed_pc20_v3 e1_legal_check_evasions; do
  apply "$root/r15d" "$prev/patches/$patch.patch.txt"
done
(cd "$root/r15d" && sha256sum -c "$prev/r15d.expected.sha256") > "$root/stage0/r15d.sha256check.txt"
test "$(rg -c ': OK$' "$root/stage0/r15d.sha256check.txt")" -eq 29
cp -a "$root/r15d/." "$root/tree_10/"
while read -r digest filename; do
  test "$(sha256sum "$prev/stack/$filename" | awk '{print $1}')" = "$digest"
  apply "$root/tree_10" "$prev/stack/$filename"
done < "$prev/stack.expected.sha256"
cp -a "$root/tree_10/." "$root/tree_11/"
apply "$root/tree_11" "$root/11_stop_hot.patch.txt"
for arm in 0 10 11; do
  tree="$root/tree_$arm"
  if [ "$arm" = 0 ]; then tree="$root/r15d"; fi
  (cd "$tree" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$root/stage0/source_$arm.sha256.txt"
  bash "$prev/build_one.sh" "$tree" "$root/build_$arm" "$root/stage0/build_$arm.txt"
done
sha256sum "$root/build_0/forge" "$root/build_10/forge" "$root/build_11/forge" | tee "$root/stage0/executables_sha256.txt"
printf '%s  %s\n' bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 "$root/build_0/forge" 55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae "$root/build_10/forge" | sha256sum -c | tee "$root/stage0/executable_known_answer.txt"
