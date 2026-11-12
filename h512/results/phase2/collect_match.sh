#!/usr/bin/env bash
# collect_match.sh <match folder name under _work/match> <short id> - JOB E phase 2: evidence of one finished match.
# Writes into h512/results/phase2/<short id>/: match_result.json (recomputed from the PGN by h512/tools/match_elo.py),
# RUN_INFO.txt, match.log.gz, pgn.md5, time_losses.txt (games lost on time in the log, and every suspension of the
# match process by the owner's resource guard between the match's start and end, read from the guard's log).
set -u
name="$1"; id="$2"
D=/d/forge_jobs_20261111/h512E
M="$D/_work/match/$name"; O="$D/h512/results/${3:-phase2}/$id"   # optional third argument: results folder (default phase2)
GL='/c/Users/Administrator/grok-pc/forge_push/autonomy7_20261107/resource_guard.log'
grep -q "^finished" "$M/RUN_INFO.txt" || { echo "match not finished"; exit 2; }
mkdir -p "$O"
python "$D/h512/tools/match_elo.py" --pgn "$M/games.pgn" --cand cand --out "$O/match_result.json" > /dev/null
cp "$M/RUN_INFO.txt" "$O/RUN_INFO.txt"
gzip -c "$M/match.log" > "$O/match.log.gz"
( cd "$M" && md5sum games.pgn ) > "$O/pgn.md5"
start=$(sed -n 's/^started \([0-9-]*\) \([0-9:]*\)$/\1T\2/p' "$M/RUN_INFO.txt")
end=$(sed -n 's/^finished \([0-9-]*\) \([0-9:]*\) .*$/\1T\2/p' "$M/RUN_INFO.txt")
{
  echo "# games lost on time (from match.log)"
  grep -a "loses on time" "$M/match.log" || echo "none"
  echo "# other abnormal endings (disconnect, illegal move, stall)"
  grep -a -i -E "disconnect|illegal|stall|crash" "$M/match.log" | grep -a "Finished game" || echo "none"
  echo "# resource guard: suspensions of a gate process between $start and $end"
  awk -v s="$start" -v e="$end" '/SUSPENDED|RESUMED/ && / gate/ { t = substr($1, 1, 19); if (t >= s && t <= e) print }' "$GL" 2>/dev/null | grep . || echo "none"
} > "$O/time_losses.txt"
python - "$O/match_result.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"games {d['games']} W {d['W']} D {d['D']} L {d['L']} pairs {d['pairs']} penta {d['pentanomial_0_to_2']}")
print(f"Elo {d['elo']:+.2f}  95% [{d['elo_95_low']:+.2f}, {d['elo_95_high']:+.2f}]  LOS {d['los']:.4f}  score {d['pair_score']:.5f}")
print("abnormal:", d["abnormal_terminations"], "unfinished:", d["unfinished_games"])
if "without_pairs_with_abnormal_games" in d:
    w = d["without_pairs_with_abnormal_games"]
    print(f"without {w['pairs_removed']} affected pairs: Elo {w['elo']:+.2f} [{w['elo_95_low']:+.2f}, {w['elo_95_high']:+.2f}]")
EOF
cat "$O/time_losses.txt" | head -30
