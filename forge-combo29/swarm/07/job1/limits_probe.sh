#!/usr/bin/env bash
# limits_probe.sh EXE OUTDIR : one engine process per case; each case is a committed .in file.
# Every case: uci, Hash 16, Threads 1, isready, ucinewgame, isready, <lines>, isready, quit.
set -u
EXE="$1"; OUT="$2"; mkdir -p "$OUT"; : > "$OUT/summary.txt"
CASES="$OUT/cases"
mkdir -p "$CASES"
run() {
  name="$1"; shift
  {
    echo uci; echo "setoption name Hash value 16"; echo "setoption name Threads value 1"; echo isready
    echo ucinewgame; echo isready
    for line in "$@"; do echo "$line"; echo isready; done
    echo quit
  } > "$CASES/$name.in"
  timeout 300 "$EXE" < "$CASES/$name.in" > "$CASES/$name.out" 2> "$CASES/$name.err"
  rc=$?
  san=$(grep -cE 'AddressSanitizer|runtime error|LeakSanitizer' "$CASES/$name.err" || true)
  bm=$(grep -c '^bestmove' "$CASES/$name.out" || true)
  inf_bad=$(grep -cE 'info string (invalid|unknown|illegal)' "$CASES/$name.out" || true)
  printf '%-26s rc=%-3s sanitizer=%-2s bestmove=%-2s infostrings=%s\n' "$name" "$rc" "$san" "$bm" "$inf_bad" | tee -a "$OUT/summary.txt"
  if [ "$san" != 0 ]; then echo "  --- sanitizer output: $CASES/$name.err ---" | tee -a "$OUT/summary.txt"; fi
}
P="position startpos"
run depth0              "$P" "go depth 0"
run depth_huge          "$P" "go depth 999999"
run nodes0              "$P" "go nodes 0"
run nodes_max           "$P" "go nodes 18446744073709551615"
run nodes_overflow      "$P" "go nodes 99999999999999999999999999"
run movetime0           "$P" "go movetime 0"
run movetime_neg        "$P" "go movetime -5"
run movetime_huge       "$P" "go movetime 9223372036854775807"
run mate0               "$P" "go mate 0"
run mate2               "$P" "go mate 2"
run wtime0              "$P" "go wtime 0 btime 0"
run wtime1              "$P" "go wtime 1 btime 1"
run wtime_noval         "$P" "go wtime"
run movestogo0          "$P" "go wtime 1000 btime 1000 movestogo 0"
run movestogo_huge      "$P" "go wtime 1000 btime 1000 movestogo 2147483647"
run movestogo_neg       "$P" "go wtime 1000 btime 1000 movestogo -3"
run searchmoves_none    "$P" "go depth 4 searchmoves"
run searchmoves_one     "$P" "go depth 4 searchmoves e2e4"
run searchmoves_all     "$P" "go depth 3 searchmoves a2a3 a2a4 b1a3 b1c3 b2b3 b2b4 c2c3 c2c4 d2d3 d2d4 e2e3 e2e4 f2f3 f2f4 g1f3 g1h3 g2g3 g2g4 h2h3 h2h4"
run searchmoves_illegal "$P" "go depth 4 searchmoves e2e5"
run softnodes0          "$P" "go softnodes 0"
run softnodes100        "$P" "go softnodes 100"
run infinite_stop       "$P" "go infinite" "stop"
run ponder_quit         "$P" "go ponder depth 5" "quit"
run depth_and_mate      "$P" "go depth 6 mate 1"
run multipv0            "setoption name MultiPV value 0" "$P" "go depth 4"
run multipv8            "setoption name MultiPV value 8" "$P" "go depth 5"
run multipv8_mate       "setoption name MultiPV value 8" "$P" "position fen 7k/5KQ1/8/8/8/8/8/8 w - - 0 1" "go depth 4"
run multipv8_1move      "setoption name MultiPV value 8" "$P" "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1" "go depth 4"
run stalemate_root      "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1" "go depth 5"
run mate_root           "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1" "go depth 5"
run no_legal_moves_d1   "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1" "go depth 1"
run restricted_empty    "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1" "go depth 3 searchmoves a1a2"
run halfmove99          "position fen 8/8/8/4k3/8/8/4K3/R7 w - - 99 80" "go depth 10"
run halfmove100         "position fen 8/8/8/4k3/8/8/4K3/R7 w - - 100 80" "go depth 6"
run repeated_threefold  "$P moves e2e4 e7e5 e1e2 e8e7 e2e1 e7e8 e1e2 e8e7 e2e1 e7e8" "go depth 8"
run fifty_clock_wrap    "position fen 8/8/8/4k3/8/8/4K3/R7 w - - 65535 1" "go depth 6"
run mate_distance_deep  "position fen 8/8/8/8/8/8/8/K6k w - - 0 1" "go depth 64"
run depth64_start       "$P" "go depth 64 nodes 200000"
