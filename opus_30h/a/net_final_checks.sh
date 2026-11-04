#!/usr/bin/env bash
# net_final_checks.sh <name> <exe> [games=400] [conc=2] [cpus=0,1] - the play-side checks of a packed net
# (D:\o30\nets\<name>\<name>.nnue2 from net_pack.sh), written into that folder:
#   1. smoke_300s.*: smoke2m.py, 300 s of self-play with EvalFileV2 = the net at a real clock (Threads 2, Hash 16):
#      PASS = 0 illegal moves, 0 crashes, 0 hangs, 0 time losses, 0 option errors, empty stderr;
#   2. abba_nps/: abba.py, 6 palindromic pairs of `bench 16`, the lock exe (A) vs <exe> + the net (B), nps metric, on the
#      FIRST CPU of <cpus> (the trees differ: a speed figure for this net, advisory; no identity check);
#   The smoke runs on all CPUs of <cpus> (mask derived from the list), so a training run on another CPU is not touched.
#   3. sanity/: sanity_match.py, <games> games 10+0.1 vs the lock on <conc> CPUs (Threads 1, Hash 16, UHO, -repeat),
#      then gate_summary.py - SANITY ONLY, never an Elo claim.
# Writes FINAL_CHECKS.json. Exit 0 = smoke PASS and fastchess exit 0 (the match result itself is not a pass condition).
set -uo pipefail
name="$1"; exe="$2"; games="${3:-400}"; conc="${4:-2}"; cpus="${5:-0,1}"
A=$(cd "$(dirname "$0")" && pwd); T="$A/../tools"
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
out=/d/o30/nets/$name; N="$out/$name.nnue2"
[ -f "$N" ] || { echo "no packed net $N (run net_pack.sh first)" >&2; exit 2; }
[ -e "$out/FINAL_CHECKS.json" ] && { echo "refusing: $out/FINAL_CHECKS.json exists" >&2; exit 2; }
NW=$(cygpath -w "$N"); NF=$(echo "$NW" | tr '\\' '/'); EW=$(cygpath -w "$exe")
LOCK=/c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe
m=0; for c in ${cpus//,/ }; do m=$((m | (1 << c))); done; MASK=$(printf '0x%X' "$m")
AMASK=$(printf '0x%X' $((1 << ${cpus%%,*})))
echo "cpus $cpus -> smoke mask $MASK, abba mask $AMASK, sanity conc $conc"
fail=0
"$PY" -I -B "$T/smoke2m.py" "$EW" --line "EvalFileV2=$NF" --seconds 300 --threads 2 --hash 16 --mask "$MASK" --idle \
  --out "$(cygpath -w "$out/smoke_300s")" > "$out/smoke_300s.txt" 2>&1 || fail=1
"$PY" -I -B "$T/abba.py" --out "$(cygpath -w "$out/abba_nps")" --a "printf 'bench 16\nquit\n' | $LOCK" \
  --b "printf 'setoption name EvalFileV2 value $NF\nbench 16\nquit\n' | $exe" --pairs 6 --metric 'nps (\d+)' \
  --higher-better --mask "$AMASK" --priority Idle > "$out/abba_nps.txt" 2>&1 || fail=1
"$PY" -I -B "$A/sanity_match.py" --out "$(cygpath -w "$out/sanity")" --cand-exe "$EW" --cand-opt "EvalFileV2=$NF" \
  --games "$games" --conc "$conc" --cpus "$cpus" > "$out/sanity_run.txt" 2>&1 || fail=1
"$PY" -I -B "$T/gate_summary.py" "$(cygpath -w "$out/sanity")" --json "$(cygpath -w "$out/sanity_summary.json")" > "$out/sanity_summary.txt" 2>&1
"$PY" -I -B - "$out" "$fail" <<'EOF'
import json, sys
out, fail = sys.argv[1], sys.argv[2]
def tail(p, n=6):
    try:
        return [l.rstrip() for l in open(p, encoding='utf-8', errors='replace')][-n:]
    except OSError:
        return []
rec = {'smoke_300s': tail(f'{out}/smoke_300s.txt', 4), 'abba_nps': [l for l in tail(f'{out}/abba_nps.txt', 12) if 'geometric' in l or 'median' in l],
       'sanity': tail(f'{out}/sanity_summary.txt', 12), 'sanity_only_never_an_elo_claim': True, 'checks_passed': fail == '0'}
with open(f'{out}/FINAL_CHECKS.json', 'x', newline='\n') as f:
    json.dump(rec, f, indent=1)
print(json.dumps(rec, indent=1))
EOF
exit $fail
