#!/usr/bin/env bash
# Compare immutable lock to a fully frozen reviewed commit, using one build path.
set -euo pipefail
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
revision=${1:?Pass the final frozen reviewed source commit}
out=${2:-/tmp/forge-default-lock-identity}
mkdir -p "$out"
out=$(cd "$out" && pwd)
cxx=$(command -v "${CXX:-g++-14}")
lock=$(git -C "$repo" rev-parse 16833ec)
review=$(git -C "$repo" rev-parse "$revision")
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude)
{
  "$cxx" --version
  printf 'compiler_sha256: '; sha256sum "$cxx"
  printf 'lock_commit: %s\nreview_commit: %s\n' "$lock" "$review"
  printf 'build_command: '; printf '%q ' "$cxx" "${flags[@]}" 'src/*.cpp' -o ../engine; printf '\n'
} > "$out/material_cache_lock_identity_provenance.txt"
for label in lock reviewed; do
  revision=$lock
  [[ $label == reviewed ]] && revision=$review
  # Dedicated scratch directory only; all builds reuse exactly this path.
  rm -rf "$out/source"
  mkdir "$out/source"
  git -C "$repo" archive "$revision" | tar -x -C "$out/source"
  (cd "$out/source/forge-combo29"; "$cxx" "${flags[@]}" src/*.cpp -o ../engine)
  cp "$out/source/engine" "$out/$label"
  nm -C -S "$out/$label" > "$out/$label.symbols.txt"
  readelf -n "$out/$label" > "$out/$label.notes.txt"
done
sha256sum "$out/lock" "$out/reviewed" > "$out/material_cache_lock_identity_hashes.txt"
if cmp "$out/lock" "$out/reviewed"; then
  echo 'PASS: default-off reviewed binary is byte-identical to immutable lock'
else
  echo 'FAIL: default-off reviewed binary differs from immutable lock'
  diff -u "$out/lock.symbols.txt" "$out/reviewed.symbols.txt" > "$out/symbols.diff" || true
  diff -u "$out/lock.notes.txt" "$out/reviewed.notes.txt" > "$out/notes.diff" || true
  exit 1
fi
