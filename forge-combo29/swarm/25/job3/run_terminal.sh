#!/usr/bin/env bash
# run_terminal.sh EXE OUTDIR : job 3, corrected — 10 verified checkmate + 10 verified stalemate roots,
# each with `go depth 5`, `go nodes 100`, `go movetime 50`. FENs come from *_roots.fens, which
# make_terminal_fens.py wrote only after python-chess confirmed each one is terminal.
set -u
EXE="$1"; OUTDIR="$2"; JOB="/agent/repos/dwqww/forge-combo29/swarm/25/job3"
mkdir -p "$OUTDIR"
: > "$OUTDIR/all_raw.txt"; : > "$OUTDIR/sanitizer_lines.txt"; : > "$OUTDIR/summary.tsv"
scan() { grep -E 'ERROR: (Address|Memory|Thread)Sanitizer|runtime error:|SUMMARY: (Address|Undefined)' "$1" || true; }

for kind in mate stale; do
  idx=0
  while IFS= read -r fen; do
    [ -z "$fen" ] && continue
    idx=$((idx+1))
    for go in "go depth 5" "go nodes 100" "go movetime 50"; do
      tag="${kind}_${idx}_$(echo "$go" | tr ' ' '_')"
      raw="$OUTDIR/$tag.txt"
      {
        printf 'uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\n%s\n' "$fen" "$go"
        sleep 2
        printf 'quit\n'
      } | timeout 90 bash -c "$EXE" > "$raw" 2>&1
      { echo "=== $tag | $fen | $go ==="; grep -E '^(info|bestmove)' "$raw" || echo "(no answer lines)"; } >> "$OUTDIR/all_raw.txt"
      scan "$raw" >> "$OUTDIR/sanitizer_lines.txt"
      bm=$(grep -E '^bestmove' "$raw" | tail -1)
      printf '%s\t%s\t%s\t%s\n' "$tag" "$fen" "$go" "${bm:-NO-BESTMOVE}" >> "$OUTDIR/summary.tsv"
    done
  done < "$JOB/${kind}_roots.fens"
done
wc -l < "$OUTDIR/sanitizer_lines.txt" | tr -d ' ' > "$OUTDIR/sanitizer_count.txt"
echo "sanitizer lines: $(cat "$OUTDIR/sanitizer_count.txt") | runs: $(wc -l < "$OUTDIR/summary.tsv")"
