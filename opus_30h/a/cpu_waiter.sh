#!/usr/bin/env bash
# cpu_waiter.sh <cpu number> <games> - Opus 30-h job, window 2: waits until no python / fastchess process is pinned to
# exactly that CPU and C:/o30g/gpu/cpu<N>_candidate.txt names a packed net in D:/o30/nets, then plays the sanity match
# (sanity_match.py, the gate exe v2p4 with EvalFileV2=<net> vs the lock exe, 10+0.1, Idle on that CPU) into
# D:\o30\nets\<name>\sanity (or sanity2 when sanity exists). Paths built from variables (no backslash literals).
set -u
cpu="$1"; games="$2"
mask=$(printf '0x%X' $((1 << cpu)))
C=/c/o30g/gpu/cpu${cpu}_candidate.txt
busy() {
    powershell -NoProfile -Command "Get-Process python,fastchess -ErrorAction SilentlyContinue | Where-Object { [int64]\$_.ProcessorAffinity -eq $((1 << cpu)) } | Measure-Object | Select-Object -ExpandProperty Count"
}
until [ -f "$C" ] && [ "$(busy | tr -d '\r')" = "0" ]; do sleep 30; done
read -r name < "$C"
[ -f "/d/o30/nets/$name/$name.nnue2" ] || { echo "no packed net /d/o30/nets/$name/$name.nnue2"; exit 2; }
sub=sanity; [ -e "/d/o30/nets/$name/sanity" ] && sub=sanity2
out=$(cygpath -w "/d/o30/nets/$name/$sub")
net="D:/o30/nets/$name/$name.nnue2"
echo "$(date '+%F %T') CPU $cpu (mask $mask) free, candidate $name: $games games into $out"
cd /d/o30/control || exit 1
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B 'D:\o30\wt\opus_30h\a\sanity_match.py' --out "$out" \
    --cand-exe 'D:\o30\w\v2p4_pc1\src_copy\forge_ltopgo_v2p4_pc1.exe' --cand-opt "EvalFileV2=$net" --games "$games" \
    --conc 1 --cpus "$cpu" > "/d/o30/logs/sanity_${name}_${sub}.out" 2>&1
rc=$?   # bug hunt: taken before $(date) runs - inside the echo, $? read date's status (always 0); same class as fix list 2 item 3
echo "$(date '+%F %T') sanity exit $rc"
