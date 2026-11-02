#!/usr/bin/env bash
# parity_v2.sh - R13 P4 feature / export-layout parity for stages a, b, c (own code). Per stage: a seeded random FORGENN2
# net -> (1) Rust feature lists (forge_v2_bullet features) + numpy float32 reference (eval_ref.py) vs (2) the engine's own
# loader, features and output kernel (v2_eval, AVX2 and SSE builds of forge-bundle-int b7c17722) on the same FENs.
# PASS = every FEN exact on both engine builds, no ERR line, same line counts; anything else exits 1 (CR R13: the first
# version only printed and always exited 0).
# PARITY_MUTATE=1 corrupts one reference value (+1 on the first FEN of each stage) before the comparison: the script must
# then exit 1 - the planted-bug check that the comparison can fail.
# usage: parity_v2.sh <work dir> <fens.txt> <forge_v2_bullet.exe> <v2_eval_avx2.exe> <v2_eval_sse.exe>
set -euo pipefail
W="$1"; FENS="$2"; FV2="$3"; AVX2="$4"; SSE="$5"
D=$(cd "$(dirname "$0")" && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
mkdir -p "$W"
for s in a b c; do
  net="$W/rand_$s.nnue2"
  [ -e "$net" ] || "$PY" -I -B "$D/make_random_net.py" "$s" "$(cygpath -w "$net")" --seed $((13450 + $(printf '%d' "'$s") - 96))
  "$FV2" features "$s" "$(cygpath -w "$FENS")" > "$W/feat_$s.txt"
  [ -e "$W/ref_$s.txt" ] || "$PY" -I -B "$D/eval_ref.py" "$(cygpath -w "$net")" "$(cygpath -w "$W/feat_$s.txt")" "$(cygpath -w "$FENS")" "$(cygpath -w "$W/ref_$s.txt")"
  "$AVX2" "$(cygpath -w "$net")" "$(cygpath -w "$FENS")" > "$W/eng_avx2_$s.txt" 2> "$W/eng_avx2_$s.err"
  "$SSE" "$(cygpath -w "$net")" "$(cygpath -w "$FENS")" > "$W/eng_sse_$s.txt" 2> "$W/eng_sse_$s.err"
  "$PY" -I -B - "$W" "$s" "${PARITY_MUTATE:-0}" <<'EOF'
import sys
w, s, mutate = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
ref = [l.strip() for l in open(f'{w}/ref_{s}.txt')]
if mutate:
    ref[0] = str(int(ref[0]) + 1)
failed = False
for path in ('avx2', 'sse'):
    eng = [l.strip() for l in open(f'{w}/eng_{path}_{s}.txt')]
    if len(eng) != len(ref) or not ref:
        print(f'stage {s} {path}: FAIL line counts {len(eng)} vs {len(ref)}')
        failed = True
        continue
    errs = sum(1 for a, b in zip(ref, eng) if a == 'ERR' or b == 'ERR')
    pairs = [(int(a), int(b)) for a, b in zip(ref, eng) if a != 'ERR' and b != 'ERR']
    exact = sum(a == b for a, b in pairs)
    worst = max((abs(a - b) for a, b in pairs), default=0)
    nonzero = sum(b != 0 for _, b in pairs)
    ok = errs == 0 and exact == len(pairs) and nonzero > 0
    failed |= not ok
    print(f'stage {s} {path}: {exact}/{len(pairs)} exact, max |diff| {worst}, nonzero evals {nonzero}, ERR {errs} -> {"PASS" if ok else "FAIL"}')
sys.exit(1 if failed else 0)
EOF
done
echo "PARITY PASS (stages a, b, c; AVX2 + SSE)"
