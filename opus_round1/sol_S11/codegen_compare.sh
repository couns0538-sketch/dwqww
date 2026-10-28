#!/usr/bin/env bash
# Compare the machine code of the hot search/eval functions of two Forge executables (unstripped).
# For each function: instruction counts, number of differing instructions after normalising
# addresses, immediates and jump targets, and the function's start address mod 64 in both builds.
# usage: codegen_compare.sh <exe_A> <exe_B>      (needs GNU objdump/nm, e.g. MSYS2 ucrt64 binutils)
set -euo pipefail
A=$1; B=$2
TMP=$(mktemp -d)
objdump -d -C --no-show-raw-insn "$A" > "$TMP/a.dis"
objdump -d -C --no-show-raw-insn "$B" > "$TMP/b.dis"
body() {
  awk -v pat="$2" 'index($0,"<"pat)>0 && /^[0-9a-f]+ </ {p=1; next} /^[0-9a-f]+ </{p=0} p' "$1" |
    sed -E 's/^\s*[0-9a-f]+:\s*//; s/<[^>]*>//g; s/#.*$//; s/0x[0-9a-f]+/IMM/g; s/^(j[a-z]+|call|jmp)\s+[0-9a-f]+/\1 ADDR/; s/\s+/ /g; s/ $//'
}
addr_mod64() {
  local a
  a=$(nm -C "$1" | grep -F " $2" | head -1 | cut -d' ' -f1)
  [ -n "$a" ] && echo $(( 16#$a % 64 )) || echo "?"
}
printf "%-48s %8s %8s %9s %8s %8s\n" function insns_A insns_B differing mod64_A mod64_B
for f in "forge::Worker::search(forge::Board&" "forge::Worker::qsearch(" "forge::MovePicker::next(" \
         "forge::Worker::static_evaluate(" "forge::TranspositionTable::probe(" "forge::TranspositionTable::store(" \
         "forge::Worker::should_stop(" "forge::Worker::is_draw(" "forge::Worker::corrected_eval(" \
         "forge::Worker::update_correction(" "forge::Worker::quiet_history(" "forge::Worker::capture_history_value(" \
         "forge::Worker::update_quiet_stats(" "forge::Worker::update_capture_stats(" "forge::Worker::update_continuation(" \
         "forge::Worker::record_move(" "forge::Worker::search(forge::Board," "forge::nnue::update(" "forge::nnue::evaluate(" \
         "forge::nnue::refresh(" "forge::Board::make_move(" "forge::Board::unmake_move(" "forge::Board::see_ge("; do
  body "$TMP/a.dis" "$f" > "$TMP/a.s"; body "$TMP/b.dis" "$f" > "$TMP/b.s"
  printf "%-48s %8d %8d %9d %8s %8s\n" "$f" "$(wc -l < "$TMP/a.s")" "$(wc -l < "$TMP/b.s")" \
    "$(diff "$TMP/a.s" "$TMP/b.s" | grep -c '^[<>]' || true)" "$(addr_mod64 "$A" "$f")" "$(addr_mod64 "$B" "$f")"
done
