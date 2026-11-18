#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job12
job=forge-combo29/sol3/job12
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
earliest=$(($(date -u -d "$claim" +%s) + 2700))
test "$(date -u +%s)" -ge "$earliest"
head=$1
[[ "$head" =~ ^[0-9a-f]{40}$ ]]
handoff=1f7159c4fe9ebadf54e40a1c8a2fd5c4efbace69
file=forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt
branch=for-fable-and-opus/carbon2-work
reference=/workspace/work/sol3-job10/tree_13
base=/workspace/work/sol3-job4/r15d
b1="$job/B1"
b2="$job/B2"
mkdir "$b1"
cp "$work/partB_poll.txt" "$b1/"
cp "$work/run_B1_B2.sh" "$b1/"
status=0
git cat-file -e "$head:$file" || status=$?
commit=$head
if ((status == 0)); then
  actual=$(timeout 40s gh api --method GET 'repos/couns0538-sketch/dwqww/commits'         -f "sha=$branch" -f "path=$file" -f per_page=1 --jq '.[0].sha' 2> "$b1/path_history.stderr.txt") || actual=
  if [[ "$actual" =~ ^[0-9a-f]{40}$ ]] &&       timeout 40s git fetch --depth=1 origin "$actual" > "$b1/source_fetch.txt" 2>&1 &&       git cat-file -e "$actual:$file" && cmp -s <(git show "$actual:$file") <(git show "$head:$file"); then
    commit=$actual
  fi
  {
    printf 'Observed carbon2 branch commit %s\n' "$head"
    printf 'Commit used for consolidated patch %s\n' "$commit"
    printf 'Commit owning the currently fetched path bytes from path history %s\n' "${actual:-unavailable}"
    git rev-parse "$commit:$file"
  } > "$b1/source_commit.txt"
  git show "$commit:$file" > "$b1/stack_r15d_to_final.patch.txt" || status=$?
  sha256sum "$b1/stack_r15d_to_final.patch.txt" > "$b1/patch.sha256.txt" || status=$?
fi
if ((status == 0)); then
  git show "$handoff:forge-combo29/soak_all/FABLE_TO_carbon2_17.md" | sed -n '131,159p' > "$b1/r15d.expected.sha256"
  test "$(wc -l < "$b1/r15d.expected.sha256")" -eq 29 || status=$?
  sha256sum "$b1/r15d.expected.sha256" >> "$b1/source_commit.txt"
fi
if ((status == 0)); then
  pinned=$(realpath "$b1/r15d.expected.sha256")
  (cd "$base" && sha256sum --strict -c "$pinned") > "$b1/r15d_check.txt" 2> "$b1/r15d_check.stderr.txt" || status=$?
fi
if ((status == 0)); then
  cp -a "$base" "$work/tree_F"
  patch -d "$work/tree_F" -p1 -F0 --batch --forward < "$b1/stack_r15d_to_final.patch.txt" > "$b1/patch_apply.txt" 2>&1 || status=$?
  if rg -in 'reject|failed|fuzz' "$b1/patch_apply.txt"; then status=1; fi
fi
date -u "+%FT%TZ Part B1 source commit, 29-file r15d pin and consolidated patch exit $status" >> "$job/stamps.txt"
git add --sparse -- "$b1" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 12 checkpoint B1 exact consolidated patch and r15d verification'
bash /workspace/work/sol3-job3/push-checkpoint.sh
for file in source_commit.txt patch.sha256.txt r15d_check.txt patch_apply.txt; do
  if test -f "$b1/$file"; then cat "$b1/$file"; fi
done
test "$status" -eq 0

mkdir "$b2"
compare_source() {
  local options=$1 file=$2 status
  for part in src include CMakeLists.txt; do
    status=0
    diff "$options" "$reference/$part" "$work/tree_F/$part" || status=$?
    if ((status > 1)); then return "$status"; fi
  done > "$b2/$file"
}
compare_source -rq changed_files.txt
compare_source -ru literal_diff.txt
compare_source -ruw ignore_space_diff.txt
cat "$b2/changed_files.txt"
rg -n '^(-{3}|\+{3}|@@)' "$b2/literal_diff.txt" || :
date -u '+%FT%TZ Part B2 captured recursive file and hunk diffs for classification' >> "$job/stamps.txt"
git add --sparse -- "$b2" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 12 checkpoint B2 literal k13 to kF differences'
bash /workspace/work/sol3-job3/push-checkpoint.sh
