#!/usr/bin/env bash
# fallback.sh — can a search return an UNSEARCHED move (the first legal move, a2a3-family)?
#
# Criterion, stated before the run: a reply is UNSEARCHED when the process printed NO `info depth` line
# before its `bestmove` (the code path is search.cpp "an unfinished ply still falls back to the first legal
# move" / "if (result.best_move.is_none()) result.best_move = root_candidates.front();").
# The first legal move of the position is taken from the engine's own `go perft 1` first line, not guessed.
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
echo "exe=$EXE"
echo "sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
echo "id name: $(printf 'uci\nquit\n' | "$EXE" 2>/dev/null | grep -m1 '^id name')"
echo "nproc=$(nproc)"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
echo
echo "position under test: $FEN"
echo "its first legal move per the engine: $( { echo "position fen $FEN"; echo 'go perft 1'; echo quit; } | "$EXE" 2>/dev/null | head -1 | cut -d: -f1)"
echo
printf '%-34s %-8s %-9s %-14s %s\n' "go line" "runs" "unsearch" "bestmoves" "verdict"
for go in "go depth 6" "go movetime 1" "go movetime 2" "go movetime 5" "go movetime 10" \
          "go wtime 10 btime 10" "go wtime 30 btime 30" "go wtime 100 btime 100" \
          "go nodes 1" "go nodes 10" "go nodes 100"; do
  uns=0; n=0; bms=""
  for i in $(seq 1 20); do
    f="$OUT/case_$(echo "$go" | tr ' ' '_')_$i.out.txt"
    { echo uci; echo isready; echo ucinewgame; echo isready
      echo "position fen $FEN"; echo "$go"; sleep 2; echo quit; } > "${f%.out.txt}.stdin.txt"
    timeout 60 "$EXE" < "${f%.out.txt}.stdin.txt" > "$f" 2>&1
    bm=$(grep '^bestmove' "$f" | tail -1 | awk '{print $2}')
    nd=$(grep -c '^info depth' "$f")
    n=$((n+1))
    [ -z "$bm" ] && bm="<none>"
    bms="$bms $bm"
    # unsearched = bestmove present but no info depth line at all
    if [ "$nd" -eq 0 ] && [ "$bm" != "<none>" ]; then uns=$((uns+1)); fi
  done
  uniqbms=$(echo $bms | tr ' ' '\n' | sort -u | tr '\n' ',' | sed 's/,$//')
  if [ "$uns" -gt 0 ]; then v="UNSEARCHED MOVES RETURNED"; else v="ok (searched)"; fi
  printf '%-34s %-8s %-9s %-14s %s\n' "$go" "$n" "$uns" "$uniqbms" "$v"
done
