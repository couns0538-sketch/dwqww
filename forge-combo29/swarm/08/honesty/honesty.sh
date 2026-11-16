#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : runs the four honesty checks, one fresh process each, raw output saved.
set -u
EXE="$1"; OUT="$2"
mkdir -p "$OUT"
echo "$EXE" > "$OUT/exe_path.txt"
sha256sum "$EXE" | tee "$OUT/exe_sha256.txt"
{ printf 'uci\nisready\nquit\n'; } | "$EXE" > "$OUT/uci_raw.txt" 2>&1
grep -m1 -E '^id name' "$OUT/uci_raw.txt" > "$OUT/id_name.txt"
for b in 11 13 16; do
  { printf 'uci\nisready\nucinewgame\nisready\nbench %s\nquit\n' "$b"; } | "$EXE" > "$OUT/bench_${b}_raw.txt" 2>&1
  grep -E 'nodes' "$OUT/bench_${b}_raw.txt" | tail -1 > "$OUT/bench_${b}_last.txt"
done
{ printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo perft 5\nquit\n'; } | "$EXE" > "$OUT/perft5_raw.txt" 2>&1
grep -E '^Nodes searched|^nodes' "$OUT/perft5_raw.txt" | tail -1 > "$OUT/perft5_last.txt"
{
  echo "exe $EXE"
  echo "sha256 $(cut -d' ' -f1 "$OUT/exe_sha256.txt")"
  echo "id $(cat "$OUT/id_name.txt")"
  echo "options sent: uci, isready, ucinewgame, isready, bench N | position startpos + go perft 5"
} > "$OUT/.meta"
echo "--- summary ---"
for b in 11 13 16; do echo "bench $b: $(cat "$OUT/bench_${b}_last.txt")"; done
echo "perft 5: $(cat "$OUT/perft5_last.txt")"
