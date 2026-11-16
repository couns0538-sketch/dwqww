#!/usr/bin/env bash
# PLANTED CONTROL (not the engine): answers every position with a refusal and perft with 1 node.
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name fake-refuse"; echo uciok ;;
    isready) echo readyok ;;
    position*) echo "info string invalid FEN: planted refusal" ;;
    "go perft"*) echo "nodes 1" ;;
    quit) exit 0 ;;
  esac
done
