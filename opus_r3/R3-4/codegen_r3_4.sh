#!/usr/bin/env bash
# R3-4: machine code of every search instance before / after turning the null-move margin literals
# (beta - 24 * depth + 180) into tunables. Extends opus_round1/sol_S29/codegen_compare.sh with the eight
# alphabeta.inc instances, both qsearch instances and the root search.
# For each function: start address, size, instruction count, and the number of differing instructions
#   - "norm": addresses, immediates and jump targets normalised (layout-independent shape), and
#   - "raw":  only the instruction addresses removed (immediates and RIP-relative targets kept).
# Then the raw diff of the default Worker::search (the AL1 s198 function).
# usage: codegen_r3_4.sh <exe_A (before)> <exe_B (after)> <out_dir>   (GNU objdump/nm, e.g. MSYS2 ucrt64)
set -euo pipefail
A=$1; B=$2; OUT=$3
mkdir -p "$OUT"
objdump -d -C --no-show-raw-insn "$A" > "$OUT/a.dis"
objdump -d -C --no-show-raw-insn "$B" > "$OUT/b.dis"
nm -C -S "$A" > "$OUT/a.nm"
nm -C -S "$B" > "$OUT/b.nm"
raw() {  # function body without instruction addresses
  awk -v pat="$2" 'index($0,"<"pat)>0 && /^[0-9a-f]+ </ {p=1; next} /^[0-9a-f]+ </{p=0} p' "$1" |
    sed -E 's/^\s*[0-9a-f]+:\s*//; s/\s+/ /g; s/ $//' | grep -v '^$' || true
}
norm() {  # as codegen_compare.sh: addresses, immediates and symbol names normalised
  awk -v pat="$2" 'index($0,"<"pat)>0 && /^[0-9a-f]+ </ {p=1; next} /^[0-9a-f]+ </{p=0} p' "$1" |
    sed -E 's/^\s*[0-9a-f]+:\s*//; s/<[^>]*>//g; s/#.*$//; s/0x[0-9a-f]+/IMM/g; s/^(j[a-z]+|call|jmp)\s+[0-9a-f]+/\1 ADDR/; s/\s+/ /g; s/ $//' |
    grep -v '^$' || true
}
sym() {  # "address size" of the first symbol whose demangled name starts with $2
  grep -F " $2" "$1" | head -1 | awk '{print $1, $2}'
}
printf "%-36s %-26s %-26s %7s %7s %5s %5s\n" function "addr/size A" "addr/size B" insns_A insns_B norm raw
for f in "forge::Worker::search(forge::Board&" "forge::Worker::search_corr_margins(" "forge::Worker::search_corr_ext(" \
         "forge::Worker::search_cm_ce(" "forge::Worker::search_cuckoo_body(" "forge::Worker::search_cm_cu_body(" \
         "forge::Worker::search_ce_cu_body(" "forge::Worker::search_cm_ce_cu_body(" "forge::Worker::qsearch(" \
         "forge::Worker::qsearch_cuckoo_body(" "forge::Worker::search(forge::Board," "forge::MovePicker::next(" \
         "forge::Worker::static_evaluate(" "forge::Board::see_ge(" "forge::nnue::update(" "forge::nnue::evaluate("; do
  raw "$OUT/a.dis" "$f" > "$OUT/a.raw"; raw "$OUT/b.dis" "$f" > "$OUT/b.raw"
  norm "$OUT/a.dis" "$f" > "$OUT/a.norm"; norm "$OUT/b.dis" "$f" > "$OUT/b.norm"
  sa=$(sym "$OUT/a.nm" "$f"); sb=$(sym "$OUT/b.nm" "$f")
  printf "%-36s %-26s %-26s %7d %7d %5d %5d\n" "${f%%(*}" "${sa:-?}" "${sb:-?}" "$(wc -l < "$OUT/a.raw")" "$(wc -l < "$OUT/b.raw")" \
    "$(diff "$OUT/a.norm" "$OUT/b.norm" | grep -c '^[<>]' || true)" "$(diff "$OUT/a.raw" "$OUT/b.raw" | grep -c '^[<>]' || true)"
done
echo
echo "== raw diff of the default forge::Worker::search (A '<', B '>'):"
raw "$OUT/a.dis" "forge::Worker::search(forge::Board&" > "$OUT/search_a.raw"
raw "$OUT/b.dis" "forge::Worker::search(forge::Board&" > "$OUT/search_b.raw"
diff "$OUT/search_a.raw" "$OUT/search_b.raw" || true
echo
echo "== globals of the null-move margin in B:"
grep -E "tune::NullMoveMargin(Depth|Base)" "$OUT/b.nm" || true
