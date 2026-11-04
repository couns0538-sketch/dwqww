#!/usr/bin/env bash
# parity_o30.sh <work dir (new)> <fens.txt> <harness dir with v2_eval_{avx2,sse,scalar}.exe> <net.nnue2> [<net> ...]
# Per net: independent float32 reference (o30_v2ref.py) vs the engine's own loader / features / output kernel in the
# AVX2, SSE and scalar builds of the port, on every FEN. PASS = every FEN exact on all three builds, no ERR, same line
# counts, at least one nonzero eval. Then a planted-bug run (--mutate) on the first net must FAIL (the comparison can
# fail). Exit 0 only if every net passes and the planted bug is caught.
set -uo pipefail
. "$(cd "$(dirname "$0")" && pwd)/../tools/idle.sh"; o30_pin_self 0x3 || { echo "cannot pin to Idle / CPUs 0-1 (fail closed)" >&2; exit 78; }
W="$1"; FENS="$2"; H="$3"; shift 3
A=$(cd "$(dirname "$0")" && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
[ -e "$W" ] && { echo "refusing: $W exists" >&2; exit 2; }
mkdir -p "$W"
compare() {  # compare <ref> <tag> -> prints one line per build, returns 0 if all exact
  "$PY" -I -B - "$W" "$1" "$2" <<'EOF'
import sys
w, ref_path, tag = sys.argv[1], sys.argv[2], sys.argv[3]
ref = [l.strip() for l in open(ref_path)]
failed = False
for build in ('avx2', 'sse', 'scalar'):
    eng = [l.strip() for l in open(f'{w}/eng_{build}_{tag}.txt')]
    if len(eng) != len(ref) or not ref:
        print(f'{tag} {build}: FAIL line counts {len(eng)} vs {len(ref)}'); failed = True; continue
    errs = sum(1 for a, b in zip(ref, eng) if a == 'ERR' or b == 'ERR')
    pairs = [(int(a), int(b)) for a, b in zip(ref, eng) if a != 'ERR' and b != 'ERR']
    exact = sum(a == b for a, b in pairs)
    worst = max((abs(a - b) for a, b in pairs), default=0)
    nonzero = sum(b != 0 for _, b in pairs)
    ok = errs == 0 and exact == len(pairs) and nonzero > 0
    failed |= not ok
    print(f'{tag} {build}: {exact}/{len(pairs)} exact, max |diff| {worst}, nonzero {nonzero}, ERR {errs} -> {"PASS" if ok else "FAIL"}')
sys.exit(1 if failed else 0)
EOF
}
fail=0; first=""
for net in "$@"; do
  tag=$(basename "$net" .nnue2); [ -z "$first" ] && first="$net"
  "$PY" -I -B "$A/o30_v2ref.py" "$(cygpath -w "$net")" "$(cygpath -w "$FENS")" "$(cygpath -w "$W/ref_$tag.txt")" > /dev/null || { echo "$tag: reference failed"; fail=1; continue; }
  for b in avx2 sse scalar; do "$H/v2_eval_$b.exe" "$(cygpath -w "$net")" "$(cygpath -w "$FENS")" > "$W/eng_${b}_$tag.txt" 2> "$W/eng_${b}_$tag.err"; done
  compare "$W/ref_$tag.txt" "$tag" || fail=1
done
tag=$(basename "$first" .nnue2)
"$PY" -I -B "$A/o30_v2ref.py" "$(cygpath -w "$first")" "$(cygpath -w "$FENS")" "$(cygpath -w "$W/ref_mutated.txt")" --mutate > /dev/null
if compare "$W/ref_mutated.txt" "$tag" > "$W/planted_bug.txt"; then echo "planted bug NOT caught: FAIL"; fail=1; else echo "planted bug caught ($(grep -c FAIL "$W/planted_bug.txt") of 3 builds FAIL as required)"; fi
[ $fail = 0 ] && echo "PARITY PASS ($# nets x AVX2 / SSE / scalar)" || echo "PARITY FAIL"
exit $fail
