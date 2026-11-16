#!/usr/bin/env bash
# run_mate_roots.sh EXE OUTDIR : job 3 — checkmated and stalemated roots.
#
# 10 checkmated roots and 10 stalemated roots, each with `go depth 5`, `go nodes 100` and
# `go movetime 50`. For every run we keep the exact answer lines, count sanitizer output, and record
# whether the bestmove is `0000` (the expected answer on a terminal position).
# Writes sanitizer_count.txt so a plant can prove this runner can SEE a sanitizer line.
set -u
EXE="$1"; OUTDIR="$2"
mkdir -p "$OUTDIR"
: > "$OUTDIR/all_raw.txt"
: > "$OUTDIR/sanitizer_lines.txt"
: > "$OUTDIR/summary.tsv"

# A sanitizer line looks like: "==12345==ERROR: AddressSanitizer: ..." or "runtime error: ...".
scan() { grep -E 'ERROR: (Address|Memory|Thread)Sanitizer|runtime error:|SUMMARY: (Address|Undefined)' "$1" || true; }

for kind in mate stale; do
  case "$kind" in
    mate)  FENS=(
      "7k/5KQ1/8/8/8/8/8/8 b - - 0 1"
      "6k1/6Q1/6K1/8/8/8/8/8 b - - 0 1"
      "8/8/8/8/8/5k2/7q/6K1 w - - 0 1"
      "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1"
      "R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"
      "2r3k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"
      "6rk/6pp/8/8/8/8/8/K6R b - - 0 1"
      "3r2k1/5ppp/8/8/8/8/6PP/3R2K1 w - - 0 1"
      "1k6/1P6/1K6/8/8/8/8/8 b - - 0 1"
      "7k/8/6KQ/8/8/8/8/8 b - - 0 1"
    ) ;;
    stale) FENS=(
      "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
      "k7/P7/K7/8/8/8/8/8 b - - 0 1"
      "5k2/5P2/5K2/8/8/8/8/8 b - - 0 1"
      "8/8/8/8/8/1k6/8/K1q5 w - - 0 1"
      "8/8/8/8/8/8/1k6/KQ6 w - - 0 1"
      "8/8/8/8/8/6k1/6P1/6K1 w - - 0 1"
      "1k6/8/1K6/8/8/8/8/6q1 w - - 0 1"
      "8/8/8/8/8/2k5/8/1K1q4 w - - 0 1"
      "8/8/8/8/8/8/2k5/K2b4 w - - 0 1"
      "8/8/8/8/8/5k2/5p2/5K2 w - - 0 1"
    ) ;;
  esac
  idx=0
  for fen in "${FENS[@]}"; do
    idx=$((idx+1))
    for go in "go depth 5" "go nodes 100" "go movetime 50"; do
      tag="${kind}_${idx}_$(echo "$go" | tr ' ' '_')"
      raw="$OUTDIR/$tag.txt"
      {
        printf 'uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\n%s\n' "$fen" "$go"
        sleep 2
        printf 'quit\n'
      } | timeout 60 bash -c "$EXE" > "$raw" 2>&1
      # keep every answer line
      { echo "=== $tag | $fen | $go ==="; grep -E '^(info|bestmove|readyok|id )' "$raw" || echo "(no answer lines)"; } >> "$OUTDIR/all_raw.txt"
      scan "$raw" >> "$OUTDIR/sanitizer_lines.txt"
      last=$(grep -E '^info ' "$raw" | tail -1)
      bm=$(grep -E '^bestmove' "$raw" | tail -1)
      printf '%s\t%s\t%s\t%s\n' "$tag" "$fen" "$go" "${bm:-NO-BESTMOVE}" >> "$OUTDIR/summary.tsv"
    done
  done
done

# The count this runner reports. The plant checks it is > 0 when fed a fake that emits a sanitizer line.
wc -l < "$OUTDIR/sanitizer_lines.txt" | tr -d ' ' > "$OUTDIR/sanitizer_count.txt"
echo "sanitizer lines counted: $(cat "$OUTDIR/sanitizer_count.txt")"
echo "runs: $(wc -l < "$OUTDIR/summary.tsv")"
