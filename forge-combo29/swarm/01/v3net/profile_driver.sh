#!/usr/bin/env bash
# swarm seat 01: the one workload Step 1 profiles — PC20 + the test net, Threads 1, Hash 16, bench 13.
#
# Kept as a script so the profiled workload is exactly the one Step 0 validated, and so the load ORDER cannot
# drift: NNUEArchFile first, NNUEArch second. Reversed, the net silently does not load and the profile would
# describe the built-in net while looking perfectly healthy.
#
# Usage: profile_driver.sh <v3-exe> <testnet.fnn3> <bench depth>
set -euo pipefail
EXE="$1"; NET="$2"; DEPTH="${3:-13}"

{ printf 'uci\n'
  printf 'setoption name Threads value 1\n'
  printf 'setoption name Hash value 16\n'
  # PC20, the settings Step 0's numbers were measured under
  printf 'setoption name LmrQuietBase value 93\n'
  printf 'setoption name LmrQuietDivisor value 205\n'
  printf 'setoption name LmrNoisyBase value 13\n'
  printf 'setoption name LmrNoisyDivisor value 333\n'
  printf 'setoption name LmrHistoryDivisor value 5643\n'
  printf 'setoption name NullMoveBase value 5\n'
  printf 'setoption name LmpBase value 8\n'
  printf 'setoption name HistoryPruneMultiplier value 2220\n'
  printf 'setoption name HistoryBonusQuadratic value 24\n'
  printf 'setoption name HistoryBonusLinear value 54\n'
  printf 'setoption name HistoryBonusMax value 2212\n'
  printf 'setoption name SingularDepth value 6\n'
  printf 'setoption name IirDepth value 2\n'
  printf 'setoption name NonPawnCorrection value true\n'
  printf 'setoption name CuckooRep value true\n'
  printf 'setoption name HistRework value 2\n'
  printf 'setoption name TtPruneV2 value true\n'
  printf 'setoption name CorrHistV2 value true\n'
  printf 'setoption name MateAlphaGuard value true\n'
  printf 'setoption name OwnBook value false\n'
  # ORDER: file, then boolean
  printf 'setoption name NNUEArchFile value %s\n' "$NET"
  printf 'setoption name NNUEArch value true\n'
  printf 'isready\n'
  printf 'ucinewgame\n'
  printf 'isready\n'
  printf 'bench %s\n' "$DEPTH"
  printf 'quit\n'
} | "$EXE"
