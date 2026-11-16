#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : fresh engine process per line, raw output saved
set -u
EXE="$1"; OUT="$2"
mkdir -p "$OUT"
run() {
  local name="$1"; shift
  { printf 'uci\nisready\nucinewgame\n'
    printf '%s\n' "$@"
    printf 'quit\n'
  } > "$OUT/$name.in"
  timeout 600 "$EXE" < "$OUT/$name.in" > "$OUT/$name.out" 2> "$OUT/$name.err"
  echo "exit $? $name"
}
run bench11 "bench 11"
run bench13 "bench 13"
run bench16 "bench 16"
run perft5 "go perft 5"
for f in bench11 bench13 bench16 perft5; do
  echo "== $f"
  grep -E "^Nodes searched|Nodes:" "$OUT/$f.out" | tail -2
  echo "-- err:"; tail -2 "$OUT/$f.err"
done
sha256sum "$EXE"
{ echo "exe: $EXE"; sha256sum "$EXE"; echo "id name:"; grep -m1 "id name" "$OUT/bench11.out"
  echo "options/commands sent: uci, isready, ucinewgame, then the go/bench line from each .in, then quit"; } > "$OUT/honesty.meta"
cat "$OUT/honesty.meta"
