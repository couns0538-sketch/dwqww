#!/usr/bin/env bash
# run_match_nodes.sh <name> <out root> <games> <candidate exe> <"option.N=V ..." or ""> [extra fastchess args...]
# JOB E phase 2 (own code, 2026-11-11). Same layout as Job D's fair_eval/tools/run_match.sh, with one difference:
# no clock. Both engines search a fixed number of nodes per move (MATCH_NODES, required), so the result does not
# depend on speed, machine load or a suspended match process. Not the crew gate; nothing here is a lock claim.
#
# Settings: fastchess, Threads 1, Hash 16, OwnBook false, book UHO_Lichess_4852_v1.epd in random order with a fixed
# seed (MATCH_SEED), every opening with both colours (-games 2 -repeat), MATCH_CONC games at once (default 12),
# -recover, no adjudication. Output: <out root>/<name>/{match.log, games.pgn, RUN_INFO.txt}.
set -u
name="$1"; root="$2"; games="$3"; cand="$4"; opts="$5"; shift 5
FC='/c/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe'
BOOK='C:/Users/Administrator/grok-pc/coder-fuzz/UHO_Lichess_4852_v1.epd'
here="$(cd "$(dirname "$0")" && pwd)"
lock="$here/../../forge-combo29/windows/forge_clang_combo29_trial_w6.exe"
nodes="${MATCH_NODES:?set MATCH_NODES}"; conc="${MATCH_CONC:-12}"; seed="${MATCH_SEED:-20261111}"
out="$root/$name"
[ -e "$out" ] && { echo "refusing: $out exists"; exit 2; }
mkdir -p "$out"
{
  echo "name $name"; echo "started $(date '+%F %T')"; echo "games $games nodes per move $nodes (no clock) concurrency $conc seed $seed"
  echo "candidate $(cygpath -w "$cand") md5 $(md5sum "$cand" | cut -c1-32) options: $opts"
  echo "base $(cygpath -w "$lock") md5 $(md5sum "$lock" | cut -c1-32)"
  echo "book $BOOK"; echo "extra: $*"
} > "$out/RUN_INFO.txt"
cd "$out" || exit 2          # fastchess writes its autosave file (config.json) into the current folder
# shellcheck disable=SC2086
"$FC" -engine "cmd=$(cygpath -w "$cand")" name=cand $opts -engine "cmd=$(cygpath -w "$lock")" name=lock \
  -each "nodes=$nodes" proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false \
  -openings "file=$BOOK" format=epd order=random -srand "$seed" \
  -games 2 -repeat -rounds $((games / 2)) -concurrency "$conc" -recover \
  -pgnout "file=$(cygpath -w "$out/games.pgn")" nodes=true "$@" > "$out/match.log" 2>&1
rc=$?
echo "finished $(date '+%F %T') fastchess exit $rc" >> "$out/RUN_INFO.txt"
grep -a -E "^Results of|^Elo:|^LOS:|^Games:|^Ptnml|^LLR|^Elo  |nElo|time|disconnect|illegal" "$out/match.log" | tail -12
exit $rc
