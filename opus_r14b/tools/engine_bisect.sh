#!/usr/bin/env bash
# engine_bisect.sh GOOD BAD OUT [--depth 13] [--test "CMD"] - Opus R14-B: which commit first changed the engine's
# bench? Binary search over `git rev-list --first-parent GOOD..BAD` (no worktree, no checkout: every candidate is a
# fresh `git archive` export, so nothing in the repository changes).
# Default test: build the candidate with the lock recipe (engine_fresh_check.sh's build, CPUs 2-3, BelowNormal) and
# run `bench DEPTH` (Threads 1, Hash 16, OwnBook false); "same" = the node count of GOOD, "changed" = another count,
# "skip" = the build or the bench failed (the search then tries a neighbour). GOOD and BAD are tested first: BAD must
# differ from GOOD, else there is nothing to find (exit 1).
# --test "CMD": any predicate instead of the engine build; {sha} and {dir} are replaced by the commit and a new folder
# for it; exit 0 = same as GOOD, 1 = changed, 125 = skip (git bisect's convention), anything else stops the search.
# OUT must not exist; OUT/bisect.log keeps every step. Exit 0 = first changed commit found (printed last), 1 = none,
# 2 = usage, 3 = every candidate in the remaining range was skipped. One build ~15 s and bench d11 ~2 s on a free
# core (2026-11-02).
set -u
here=$(cd "$(dirname "$0")" && pwd)
repo=${REPO:-$(git -C "$here" rev-parse --show-toplevel 2>/dev/null || echo /d/grok-pc-data/dwqww)}  # REPO: another repo
good=${1:-}; bad=${2:-}; out=${3:-}
[ -n "$good" ] && [ -n "$bad" ] && [ -n "$out" ] || { sed -n 2,13p "$0"; exit 2; }
shift 3
depth=13; test_cmd=""
while [ $# -gt 0 ]; do
  case "$1" in
    --depth) depth=${2:?}; shift 2 ;;
    --test) test_cmd=${2:?}; shift 2 ;;
    *) echo "engine_bisect: unknown option $1"; exit 2 ;;
  esac
done
[ -e "$out" ] && { echo "engine_bisect: $out exists (write fresh, named folders)"; exit 2; }
g=$(git -C "$repo" rev-parse --verify -q "$good^{commit}") || { echo "engine_bisect: unknown ref $good"; exit 2; }
b=$(git -C "$repo" rev-parse --verify -q "$bad^{commit}") || { echo "engine_bisect: unknown ref $bad"; exit 2; }
git -C "$repo" merge-base --is-ancestor "$g" "$b" || { echo "engine_bisect: $good is not an ancestor of $bad"; exit 2; }
mapfile -t cand < <(git -C "$repo" rev-list --first-parent --reverse "$g..$b")
[ ${#cand[@]} -gt 0 ] || { echo "engine_bisect: no commits between $good and $bad"; exit 2; }
mkdir -p "$out" || exit 2
log=$out/bisect.log
say() { echo "$*" | tee -a "$log"; }
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
ref_nodes=""

bench_nodes() {  # bench_nodes SHA DIR -> prints the node count, or nothing when the build / bench failed
  local sha=$1 dir=$2
  mkdir -p "$dir/src" || return
  git -C "$repo" -c core.autocrlf=false archive "$sha" src include 2>/dev/null | tar -x -C "$dir/src" 2>/dev/null || return
  [ -d "$dir/src/src" ] || return
  local units args gpp=/c/msys64/ucrt64/bin/g++.exe
  units=$(cd "$dir/src" && ls src/*.cpp | sort | tr '\n' ' ')
  args="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude $units -o ../forge.exe"
  ( cd "$dir/src" && PATH="/c/msys64/ucrt64/bin:$PATH" powershell -NoProfile -ExecutionPolicy Bypass \
      -File "$(cygpath -w "$here/lowrun.ps1")" -Mask 0xC -Priority BelowNormal -Exe "$(cygpath -w "$gpp")" \
      -ArgLine "$args" -Out "$(cygpath -w "$dir/build.out")" -Err "$(cygpath -w "$dir/build.err")" ) || return
  [ -f "$dir/forge.exe" ] || return
  printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench %s\nquit\n' \
    "$depth" > "$dir/bench.in"
  powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$here/lowrun.ps1")" -Mask 0xC -Priority BelowNormal \
    -Exe "$(cygpath -w "$dir/forge.exe")" -In "$(cygpath -w "$dir/bench.in")" -Out "$(cygpath -w "$dir/bench.out")" \
    -Err "$(cygpath -w "$dir/bench.err")" || return
  tr -d '\r' < "$dir/bench.out" | sed -n "s/.*bench depth $depth nodes \([0-9][0-9]*\).*/\1/p" | tail -1
}

verdict() {  # verdict SHA LABEL -> same / changed / skip / stop:<rc>
  local sha=$1 dir="$out/$2_${1:0:8}" rc n
  if [ -n "$test_cmd" ]; then
    local c=${test_cmd//\{sha\}/$sha}; c=${c//\{dir\}/$dir}
    mkdir -p "$dir"; bash -c "$c" > "$dir/test.out" 2>&1; rc=$?
    case $rc in 0) echo same ;; 1) echo changed ;; 125) echo skip ;; *) echo "stop:$rc" ;; esac
    return
  fi
  n=$(bench_nodes "$sha" "$dir")
  if [ -z "$n" ]; then echo skip
  elif [ -z "$ref_nodes" ]; then ref_nodes=$n; echo "same"   # the first call is GOOD itself
  elif [ "$n" = "$ref_nodes" ]; then echo same
  else echo changed
  fi
  echo "$n" > "$dir/nodes.txt"
}

say "engine_bisect $(date '+%F %T'): good $good ($g), bad $bad ($b), ${#cand[@]} commits, depth $depth${test_cmd:+, test: $test_cmd}"
v=$(verdict "$g" good)
if [ -z "$test_cmd" ]; then ref_nodes=$(cat "$out/good_${g:0:8}/nodes.txt" 2>/dev/null); fi
say "good $g: $v${ref_nodes:+ (bench $depth nodes $ref_nodes)}"
[ "$v" = same ] || { say "engine_bisect: GOOD itself is not usable ($v)"; exit 2; }
v=$(verdict "$b" bad)
say "bad $b: $v$( [ -z "$test_cmd" ] && echo " (nodes $(cat "$out/bad_${b:0:8}/nodes.txt" 2>/dev/null))")"
case $v in
  changed) ;;
  same) say "RESULT: $bad does not differ from $good - nothing to find"; exit 1 ;;
  *) say "engine_bisect: BAD is not usable ($v)"; exit 2 ;;
esac
lo=-1; hi=$(( ${#cand[@]} - 1 )); declare -A skipped=()
while [ $(( hi - lo )) -gt 1 ]; do
  mid=$(( (lo + hi) / 2 )); pick=""
  for (( d = 0; d < hi - lo; d++ )); do  # the candidate nearest to the middle that was not skipped
    for i in $(( mid + d )) $(( mid - d )); do
      if [ $i -gt $lo ] && [ $i -lt $hi ] && [ -z "${skipped[$i]:-}" ]; then pick=$i; break 2; fi
    done
  done
  if [ -z "$pick" ]; then
    left=""; for (( i = lo + 1; i < hi; i++ )); do left="$left ${cand[$i]:0:12}"; done
    say "RESULT: the first change is one of the skipped commits (build or bench failed):$left - or ${cand[$hi]:0:12}, the first tested one that changed"
    exit 3
  fi
  sha=${cand[$pick]}
  v=$(verdict "$sha" "c$(printf '%03d' "$pick")")
  say "candidate $pick/${#cand[@]} $sha $(git -C "$repo" log -1 --format='%s' "$sha" | cut -c1-60): $v"
  case $v in
    same) lo=$pick ;;
    changed) hi=$pick ;;
    skip) skipped[$pick]=1 ;;
    *) say "engine_bisect: the test stopped the search ($v)"; exit 2 ;;
  esac
done
first=${cand[$hi]}
say "RESULT: first changed commit $first ($(git -C "$repo" log -1 --format='%cd %s' --date=format:'%F %H:%M' "$first" | cut -c1-90))"
exit 0
