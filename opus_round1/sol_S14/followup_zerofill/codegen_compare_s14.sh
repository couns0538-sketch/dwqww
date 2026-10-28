#!/usr/bin/env bash
# Machine-code comparison of the hot functions of two Forge executables (unstripped), for the S14 follow-up.
# Extended from opus_round1/O3/codegen_compare.sh (branch opus-O3): the same normalisation (addresses,
# immediates and jump targets replaced) and the same function list, plus the Board functions that construct a
# MoveList, plus three counts per function and build: `call ... memset`, 64-byte zmm stores and 32-byte ymm
# stores (vmovdq*/vmovup* with a memory destination).
# usage: codegen_compare_s14.sh <exe_A> <exe_B> [<diff_dir>]
#   GNU objdump/nm on PATH (MSYS2 ucrt64 binutils on Windows, binutils on Linux). Scratch files go to $TMPDIR.
#   With <diff_dir>, the normalised listings and a unified diff per changed function are written there.
set -euo pipefail
A=$1; B=$2; SAVE=${3:-}
TMP=$(mktemp -d)
objdump -d -C --no-show-raw-insn "$A" > "$TMP/a.dis"
objdump -d -C --no-show-raw-insn "$B" > "$TMP/b.dis"
raw() {  # raw <dis> <pattern>: the function's instruction lines, unnormalised
  awk -v pat="$2" 'index($0,"<"pat)>0 && /^[0-9a-f]+ </ {p=1; next} /^[0-9a-f]+ </{p=0} p' "$1" | grep -E '^\s*[0-9a-f]+:' || true
}
norm() {
  sed -E 's/^\s*[0-9a-f]+:\s*//; s/<[^>]*>//g; s/#.*$//; s/0x[0-9a-f]+/IMM/g; s/^(j[a-z]+|call|jmp)\s+[0-9a-f]+/\1 ADDR/; s/\s+/ /g; s/ $//'
}
addr_mod64() {
  local a
  a=$(nm -C "$1" | grep -F " $2" | head -1 | cut -d' ' -f1)
  [ -n "$a" ] && echo $(( 16#$a % 64 )) || echo "?"
}
count() { grep -cE "$2" "$1" || true; }
MEMSET='call\s+[0-9a-f]+ <(__)?memset'
ZMM='vmov(dq[au](8|16|32|64)?|[au]ps|[au]pd)\s+%zmm[0-9]+,[^%]*\('
YMM='vmov(dq[au](8|16|32|64)?|[au]ps|[au]pd)\s+%ymm[0-9]+,[^%]*\('
[ -n "$SAVE" ] && mkdir -p "$SAVE"
printf "%-48s %7s %7s %6s %6s %6s %5s %5s %5s %5s %5s %5s\n" function insns_A insns_B diff mod_A mod_B mset_A mset_B zmm_A zmm_B ymm_A ymm_B
i=0
for f in "forge::Worker::search(forge::Board&" "forge::Worker::qsearch(" "forge::MovePicker::next(" \
         "forge::Worker::static_evaluate(" "forge::TranspositionTable::probe(" "forge::TranspositionTable::store(" \
         "forge::Worker::should_stop(" "forge::Worker::is_draw(" "forge::Worker::corrected_eval(" \
         "forge::Worker::update_correction(" "forge::Worker::quiet_history(" "forge::Worker::capture_history_value(" \
         "forge::Worker::update_quiet_stats(" "forge::Worker::update_capture_stats(" "forge::Worker::update_continuation(" \
         "forge::Worker::record_move(" "forge::Worker::search(forge::Board," "forge::nnue::update(" "forge::nnue::evaluate(" \
         "forge::nnue::refresh(" "forge::Board::make_move(" "forge::Board::unmake_move(" "forge::Board::see_ge(" \
         "forge::Board::has_legal_move(" "forge::Board::perft(" "forge::Board::legal_moves(" \
         "forge::Board::pseudo_legal_moves(" "forge::Board::generate_pseudo_legal(" "forge::Board::is_pseudo_legal("; do
  raw "$TMP/a.dis" "$f" > "$TMP/a.raw"; raw "$TMP/b.dis" "$f" > "$TMP/b.raw"
  norm < "$TMP/a.raw" > "$TMP/a.s"; norm < "$TMP/b.raw" > "$TMP/b.s"
  nd=$(diff "$TMP/a.s" "$TMP/b.s" | grep -c '^[<>]' || true)
  printf "%-48s %7d %7d %6d %6s %6s %5s %5s %5s %5s %5s %5s\n" "$f" "$(wc -l < "$TMP/a.s")" "$(wc -l < "$TMP/b.s")" \
    "$nd" "$(addr_mod64 "$A" "$f")" "$(addr_mod64 "$B" "$f")" \
    "$(count "$TMP/a.raw" "$MEMSET")" "$(count "$TMP/b.raw" "$MEMSET")" \
    "$(count "$TMP/a.raw" "$ZMM")" "$(count "$TMP/b.raw" "$ZMM")" \
    "$(count "$TMP/a.raw" "$YMM")" "$(count "$TMP/b.raw" "$YMM")"
  i=$((i + 1))
  if [ -n "$SAVE" ] && [ "$nd" -gt 0 ]; then
    name=$(printf "%02d_%s" "$i" "$(echo "$f" | tr -c 'A-Za-z0-9_\n' '_')")
    diff -u "$TMP/a.s" "$TMP/b.s" > "$SAVE/$name.diff" || true
  fi
done
