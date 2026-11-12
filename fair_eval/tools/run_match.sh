#!/usr/bin/env bash
# run_match.sh <name> <out root> <games> <candidate exe> <"option.N=V ..." or ""> [extra fastchess args...]
# JOB D follow-up (own code, 2026-11-11). A fixed-length match of one candidate against the original lock exe, run
# by this job's own processes. It is NOT the crew gate and never touches the gate queue; nothing here is a lock claim.
#
# Settings (the earlier jobs' sanity-match layout, shorter clock): fastchess, Threads 1, Hash 16, OwnBook false,
# book UHO_Lichess_4852_v1.epd in random order with a fixed seed, every opening played with both colours
# (-games 2 -repeat), tc from MATCH_TC (default 6+0.06), timemargin 1000 ms, MATCH_CONC games at once (default 12
# of the 16 logical CPUs), -recover. Output: <out root>/<name>/{match.log, games.pgn, RUN_INFO.txt}.
# Since 2026-11-12 the opponent can be changed for net-against-net comparisons: MATCH_BASE (exe, default the
# original lock exe), MATCH_BASE_OPTS ("option.N=V ...", default none), MATCH_BASE_NAME (PGN name, default lock).
set -u
name="$1"; root="$2"; games="$3"; cand="$4"; opts="$5"; shift 5
FC='/c/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe'
BOOK='C:/Users/Administrator/grok-pc/coder-fuzz/UHO_Lichess_4852_v1.epd'
here="$(cd "$(dirname "$0")" && pwd)"
lock="${MATCH_BASE:-$here/../../forge-combo29/windows/forge_clang_combo29_trial_w6.exe}"
bopts="${MATCH_BASE_OPTS:-}"; bname="${MATCH_BASE_NAME:-lock}"
tc="${MATCH_TC:-6+0.06}"; conc="${MATCH_CONC:-12}"; seed="${MATCH_SEED:-20261111}"
out="$root/$name"
[ -e "$out" ] && { echo "refusing: $out exists"; exit 2; }
mkdir -p "$out"
{
  echo "name $name"; echo "started $(date '+%F %T')"; echo "games $games tc $tc concurrency $conc seed $seed"
  echo "candidate $(cygpath -w "$cand") md5 $(md5sum "$cand" | cut -c1-32) options: $opts"
  echo "base $(cygpath -w "$lock") md5 $(md5sum "$lock" | cut -c1-32) name $bname options: $bopts"
  echo "book $BOOK"; echo "extra: $*"
} > "$out/RUN_INFO.txt"
# shellcheck disable=SC2086
"$FC" -engine "cmd=$(cygpath -w "$cand")" name=cand $opts -engine "cmd=$(cygpath -w "$lock")" "name=$bname" $bopts \
  -each "tc=$tc" timemargin=1000 proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false \
  -openings "file=$BOOK" format=epd order=random -srand "$seed" \
  -games 2 -repeat -rounds $((games / 2)) -concurrency "$conc" -recover \
  -pgnout "file=$(cygpath -w "$out/games.pgn")" "$@" > "$out/match.log" 2>&1
rc=$?
echo "finished $(date '+%F %T') fastchess exit $rc" >> "$out/RUN_INFO.txt"
grep -a -E "^Results of|^Elo:|^LOS:|^Games:|^Ptnml|^LLR|^Elo  |nElo|time|disconnect|illegal" "$out/match.log" | tail -12
exit $rc
