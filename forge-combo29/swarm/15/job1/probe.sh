#!/usr/bin/env bash
# probe.sh FEN DEPTH : S14, Threads 1, Hash 16, one position, prints LAST info + bestmove
set -u
FEN="$1"; D="$2"; EXE="${3:-$HOME/builds/rel/forge}"
{ echo uci
  echo "setoption name Threads value 1"; echo "setoption name Hash value 16"
  echo "setoption name LmrQuietBase value 93"; echo "setoption name LmrQuietDivisor value 205"
  echo "setoption name LmrNoisyBase value 13"; echo "setoption name LmrNoisyDivisor value 333"
  echo "setoption name LmrHistoryDivisor value 5643"; echo "setoption name NullMoveBase value 5"
  echo "setoption name LmpBase value 8"; echo "setoption name HistoryPruneMultiplier value 2220"
  echo "setoption name HistoryBonusQuadratic value 24"; echo "setoption name HistoryBonusLinear value 54"
  echo "setoption name HistoryBonusMax value 2212"; echo "setoption name SingularDepth value 6"
  echo "setoption name IirDepth value 2"; echo "setoption name NonPawnCorrection value true"
  echo isready; echo ucinewgame; echo isready; echo "position fen $FEN"; echo isready
  echo "go depth $D"; sleep "${4:-8}"; echo quit; } | "$EXE" 2>&1 | grep -E "score mate|score cp .* pv |^bestmove" | tail -2
