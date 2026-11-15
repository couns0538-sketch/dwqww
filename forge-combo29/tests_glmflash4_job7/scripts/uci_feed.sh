#!/bin/bash
# Feed fixed UCI lines to one fresh engine process, capture raw output.
# usage: uci_feed.sh <engine_exe> <outfile> <line1> [line2 ...]
exe=$1
out=$2
shift 2
{
  printf '%s\n' uci isready "$@"
  printf '%s\n' quit
} | "$exe" > "$out" 2>&1
