#!/usr/bin/env bash
# M1 kernel audit: disassemble the NNUE accumulator functions of a built engine exe and count the vector
# instructions by register width, so the kernel that runs is read from the binary itself.
# usage: [AUDIT_DUMP=<file>] nnue_kernel_audit.sh <exe>...   (AUDIT_DUMP: append each function's disassembly)
# Per exe and per function (forge::nnue::refresh / update / evaluate) it prints:
#   insns    instructions in the function body
#   zmm/ymm  instructions that name a zmm / ymm register (AVX-512 / AVX2 width)
#   vaddps/vsubps zmm|ymm   packed float add/sub by width (the accumulator arithmetic)
#   stores   vector stores (vmovups/vmovaps to memory) - the register-blocked O2 refresh kernel stores each
#            accumulator vector once per block; the portable loop stores it once per column
# plus the whole-exe FMA count (vfmadd/vfmsub/vfnmadd; must be 0).
set -euo pipefail
export PATH=/c/msys64/ucrt64/bin:$PATH
for exe in "$@"; do
  echo "== $(basename "$exe")  sha256 $(sha256sum "$exe" | cut -d' ' -f1)"
  dis=$(mktemp "${TMPDIR:-/tmp}/r5b_audit.XXXXXX")
  objdump -d -C --no-show-raw-insn "$exe" > "$dis"
  for fn in "forge::nnue::refresh(" "forge::nnue::update(" "forge::nnue::evaluate("; do
    # function body = lines after the "<symbol>:" header up to the next blank line
    awk -v f="$fn" 'index($0, "<" f) && /:$/ {on=1; next} on && /^$/ {exit} on {print}' "$dis" > "$dis.fn"
    n=$(wc -l < "$dis.fn")
    z=$(grep -c 'zmm' "$dis.fn" || true)
    y=$(grep -c 'ymm' "$dis.fn" || true)
    az=$(grep -cE 'v(add|sub)ps .*zmm' "$dis.fn" || true)
    ay=$(grep -cE 'v(add|sub)ps .*ymm' "$dis.fn" || true)
    st=$(grep -cE 'vmov(u|a)ps +%[xyz]mm[0-9]+,.*\(' "$dis.fn" || true)
    [ -n "${AUDIT_DUMP:-}" ] && { echo "### $(basename "$exe") ${fn%(}"; cat "$dis.fn"; } >> "$AUDIT_DUMP"
    printf '  %-24s insns %5d  zmm %4d  ymm %4d  vaddps/vsubps zmm %4d ymm %4d  vector stores %4d\n' \
      "${fn%(}" "$n" "$z" "$y" "$az" "$ay" "$st"
  done
  echo "  FMA (vfmadd/vfmsub/vfnmadd) in exe: $(grep -cE 'vfn?m(add|sub)' "$dis" || true)"
done
