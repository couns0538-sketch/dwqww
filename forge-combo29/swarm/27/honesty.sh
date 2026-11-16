#!/usr/bin/env bash
# honesty.sh <exe> <outdir> : runs the four honesty numbers, one fresh process per line, saves raw output
# and a .meta beside it. Also records exe path started + sha256 + id name.
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
EXE_ABS=$(readlink -f "$EXE")
SHA=$(sha256sum "$EXE_ABS" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE_ABS" 2>/dev/null | grep -m1 '^id name' || true)

meta() {
  {
    echo "exe_started: $EXE_ABS"
    echo "sha256: $SHA"
    echo "id_name: $IDNAME"
    echo "what: $2"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$1"
}

for d in 11 13 16; do
  printf 'uci\nisready\nucinewgame\nposition startpos\nbench %s\nquit\n' "$d" > "$OUT/bench$d.in"
  "$EXE_ABS" < "$OUT/bench$d.in" > "$OUT/bench$d.raw.txt" 2> "$OUT/bench$d.stderr.txt"
  rc=$?
  meta "$OUT/bench$d.meta" "input $OUT/bench$d.in exit $rc"
  echo "== bench $d rc=$rc"
  grep -E 'nodes' "$OUT/bench$d.raw.txt" | tail -2
done

printf 'uci\nisready\nucinewgame\nposition startpos\ngo perft 5\nquit\n' > "$OUT/perft5.in"
"$EXE_ABS" < "$OUT/perft5.in" > "$OUT/perft5.raw.txt" 2> "$OUT/perft5.stderr.txt"
rc=$?
meta "$OUT/perft5.meta" "input $OUT/perft5.in exit $rc"
echo "== perft 5 rc=$rc"
grep -E '^nodes' "$OUT/perft5.raw.txt" | tail -2

echo "id_name: $IDNAME"
