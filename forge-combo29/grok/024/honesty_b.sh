#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
EXE=/tmp/forge-base/forge
OUTDIR="$(cd "$(dirname "$0")" && pwd)"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F 'id name ' '/^id name /{print substr($0,9); exit}')
printf 'uci\nquit\n' | "$EXE" > "$OUTDIR/honesty_b_uci.txt"
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$OUTDIR/${name}.txt"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  cat > "$OUTDIR/${name}.meta" << EOF
exe=$EXE
sha256=$SHA
id_name=$IDNAME
options_sent=
command=$cmd
EOF
  echo "WROTE $raw"
}
run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"
echo "IDNAME=$IDNAME"
echo "SHA=$SHA"
grep -E 'nodes ' "$OUTDIR"/honesty_b_bench11.txt "$OUTDIR"/honesty_b_bench13.txt "$OUTDIR"/honesty_b_bench16.txt "$OUTDIR"/honesty_b_perft5.txt
