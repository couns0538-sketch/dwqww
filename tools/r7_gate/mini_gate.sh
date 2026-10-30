#!/usr/bin/env bash
# R7 J4: a scaled-down copy of the PC gate (same fastchess, engine options, tc, book, -repeat pairs) to measure
# games/hour of a flag set. Concurrency 3 = this job's CPU budget; everything (cwd, PGN, log, fastchess config.json)
# stays in <out_dir>. fastchess and the engines run at BelowNormal (children inherit the class).
# usage: mini_gate.sh <out_dir> <engine.exe> <rounds> <srand> <book start> [extra fastchess flags...]
# prints: games, wall seconds, games/hour (from fastchess start to exit), fastchess.exe CPU seconds, log bytes.
set -uo pipefail
OUT=$1; EXE=$2; ROUNDS=$3; SRAND=$4; START=$5; shift 5
FC='C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe'
BOOK='C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn'
mkdir -p "$OUT"
cd "$OUT" || exit 1
W=$(pwd -W)
EXTRA=""
[ $# -gt 0 ] && EXTRA=$(printf "'%s'," "$@" | sed 's/,$//')
cat > run.ps1 << EOF
\$a = @('-engine','name=a','cmd=$EXE','option.Threads=1','option.Hash=16','option.OwnBook=false',
       '-engine','name=b','cmd=$EXE','option.Threads=1','option.Hash=16','option.OwnBook=false',
       '-each','tc=10+0.1','timemargin=1000','proto=uci',
       '-openings','file=$BOOK','format=pgn','order=random','start=$START',
       '-srand','$SRAND','-games','2','-repeat','-rounds','$ROUNDS','-concurrency','3','-recover',
       '-pgnout','file=$W/games.pgn','timeleft=true') + @($EXTRA)
\$sw = [Diagnostics.Stopwatch]::StartNew()
\$p = Start-Process -FilePath '$FC' -ArgumentList \$a -WorkingDirectory '$W' -RedirectStandardOutput '$W/fastchess.out' -RedirectStandardError '$W/fastchess.err' -PassThru -NoNewWindow
try { \$p.PriorityClass = 'BelowNormal' } catch {}
\$p.WaitForExit()
\$cpu = \$p.TotalProcessorTime.TotalSeconds
"wall_s=" + \$sw.Elapsed.TotalSeconds + " fastchess_cpu_s=" + \$cpu + " exit=" + \$p.ExitCode
EOF
res=$(powershell -NoProfile -ExecutionPolicy Bypass -File run.ps1 | tr -d '\r')
games=$(grep -c '^\[Event ' games.pgn 2>/dev/null || echo 0)
wall=$(echo "$res" | sed -n 's/.*wall_s=\([0-9.]*\).*/\1/p')
logb=0
for f in *.log; do [ -f "$f" ] && logb=$((logb + $(stat -c %s "$f"))); done
gph=$(awk -v g="$games" -v w="$wall" 'BEGIN { if (w > 0) printf "%.1f", g * 3600 / w; else print "nan" }')
echo "games=$games $res games_per_hour=$gph log_bytes=$logb" | tee summary.txt
