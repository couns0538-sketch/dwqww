#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : runs the four honesty checks, one fresh process per line,
# saves raw output, writes .meta beside each output.
set -u
EXE="$1"; OUT="$2"
mkdir -p "$OUT"
sha256sum "$EXE" | awk '{print $1}' > "$OUT/exe.sha256"
{
  echo "exe: $(readlink -f "$EXE")"
  echo "sha256: $(cat "$OUT/exe.sha256")"
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/meta.txt"
# id name and every option line sent (no options sent for the honesty lines)
printf 'uci\nisready\nquit\n' | "$EXE" > "$OUT/uci_answer.txt" 2>&1
grep '^id name' "$OUT/uci_answer.txt" >> "$OUT/meta.txt"
echo "options_sent: none (engine defaults; setoption lines: none)" >> "$OUT/meta.txt"

run_one () {
  name="$1"; cmd="$2"; want="$3"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/$name.raw.txt" 2>&1
  got=$(grep -oE 'nodes [0-9]+' "$OUT/$name.raw.txt" | tail -1 | awk '{print $2}')
  printf '%-12s command=%-14s want=%-9s got=%-9s %s\n' "$name" "$cmd" "$want" "$got" \
    "$([ "$got" = "$want" ] && echo OK || echo MISMATCH)" | tee -a "$OUT/honesty_table.txt"
}

run_one bench11 "bench 11" 312866
run_one bench13 "bench 13" 862329
run_one bench16 "bench 16" 3024920
run_one perft5  "go perft 5" 4865609
