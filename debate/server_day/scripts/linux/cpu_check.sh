#!/usr/bin/env bash
# Fable 2026-11-23, W5 (a) of FINAL_PLAN_2311.md: refuse a build variant the processor cannot run.
#   cpu_check.sh <variant> [cpuinfo file = /proc/cpuinfo]
# Exit 0 = every flag the variant needs is in the processor's flag list; exit 1 = refused, the missing flags are
# named; exit 2 = wrong call. The second argument exists for the rehearsal (a flag list with one flag taken out).
# The lists are what the compiler is allowed to use under each variant's -march line (see build_forge.sh):
#   v4            x86-64-v4 (AVX-512 F, BW, CD, DQ, VL) and BMI2 for the slider tables
#   avx2_pext     x86-64-v3 (AVX2, BMI1, BMI2, FMA, F16C, LZCNT, MOVBE)
#   avx2_nobmi2   x86-64-v2 with AVX2, without BMI2
#   scalar_verify plain x86-64 (the checking build; every processor runs it)
set -euo pipefail
V="${1:-}"
INFO="${2:-/proc/cpuinfo}"
V2="cx16 lahf_lm popcnt pni sse4_1 sse4_2 ssse3"
V3="$V2 avx avx2 bmi1 bmi2 f16c fma abm movbe xsave"
case "$V" in
  v4)            NEED="$V3 avx512f avx512bw avx512cd avx512dq avx512vl" ;;
  avx2_pext)     NEED="$V3" ;;
  avx2_nobmi2)   NEED="$V2 avx avx2" ;;
  scalar_verify) NEED="" ;;
  *) echo "cpu_check: unknown variant '$V' (v4, avx2_pext, avx2_nobmi2, scalar_verify)"; exit 2 ;;
esac
[ -r "$INFO" ] || { echo "cpu_check: cannot read $INFO"; exit 2; }
FLAGS=" $(grep -m1 '^flags' "$INFO" | cut -d: -f2) "
[ "$FLAGS" != "  " ] || { echo "cpu_check: no flags line in $INFO"; exit 2; }
MISSING=""
for f in $NEED; do
  case "$FLAGS" in *" $f "*) ;; *) MISSING="$MISSING $f" ;; esac
done
if [ -n "$MISSING" ]; then
  echo "cpu_check: REFUSED: this processor cannot run the variant $V; missing:$MISSING"
  exit 1
fi
echo "cpu_check: ok: the processor has every flag the variant $V needs"
