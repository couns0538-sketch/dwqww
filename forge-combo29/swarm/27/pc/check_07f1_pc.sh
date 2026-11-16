#!/usr/bin/env bash
# check_07f1_pc.sh <exe> [settings: PC20|S14|none]
# Reproduces seat 07's 07-F1 (`searchmoves` with no legal root move answers a 0-node "score cp 0" and
# bestmove 0000) and, crucially, runs the CONTROL through the same harness: a restriction that DOES name
# a legal move must show a real search. Without the control, "nodes 0" could just as well be a harness
# artefact as an engine behaviour.
#
# Threads 1 always (swarm rule). Every go is awaited until bestmove; stdin is never closed mid-search.
set -u
EXE=$(readlink -f "${1:?exe}")
SETTINGS="${2:-PC20}"
HERE=$(dirname "$(readlink -f "$0")")
PACED="$HERE/../job2/paced_session.py"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

S14='setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true'
PC20X='setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false'

block() {
  printf 'setoption name Hash value 16\nsetoption name Threads value 1\n'
  case "$SETTINGS" in
    S14|PC20) printf '%s\n' "$S14" ;;
  esac
  case "$SETTINGS" in
    PC20) printf '%s\n' "$PC20X" ;;
  esac
  [ "$SETTINGS" = "none" ] || true
}

run_case() { # run_case <label> <position-line> <go-line>
  local label="$1" pos="$2" go="$3"
  {
    printf 'uci\nisready\n'; block; printf 'isready\nucinewgame\nisready\n'
    printf '%s\nisready\n%s\n' "$pos" "$go"
  } > "$TMP/$label.uci"
  python3 "$PACED" "$EXE" "$TMP/$label.uci" "$TMP/$label" 120 > /dev/null 2>&1
  echo "== $label"
  echo "   $pos"
  echo "   $go"
  grep -E '^info depth|^bestmove' "$TMP/$label.out.txt" | tail -2 | sed 's/^/     /'
  cp "$TMP/$label.out.txt" "./check_07F1_${label}.raw.txt" 2>/dev/null || true
}

echo "exe      : $EXE"
echo "sha256   : $(sha256sum "$EXE" | awk '{print $1}')"
echo "settings : $SETTINGS   threads: 1"
echo
run_case "no_legal_root_move" "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1" "go depth 3 searchmoves a1a2"
run_case "empty_list"         "position startpos"                        "go depth 4 searchmoves"
echo
echo "-- CONTROL: a restriction that names a legal move must show a real search --"
run_case "control_legal"      "position startpos"                        "go depth 6 searchmoves e2e4"

echo
echo "Read it as: the two defect cases show 'score cp 0 nodes 0' with an empty pv and bestmove 0000;"
echo "the control shows a node count and a pv. If the control ALSO showed nodes 0, the harness would be"
echo "broken and the defect cases would prove nothing."
