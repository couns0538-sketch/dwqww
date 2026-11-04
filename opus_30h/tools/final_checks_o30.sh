#!/usr/bin/env bash
# final_checks_o30.sh [out log] - Opus 30-h job: re-run every quick check of the job's deliverables (about 10 minutes,
# CPUs 0-1 Idle). Prints one PASS / FAIL line per check and a total; exit 0 only if all pass.
#  1 lock exe pins (-Full)                      2 v2 gate exe (kit v2.5) OFF pins (-Full)
#  3 v2 gate exe: lock net as v2 = lock pins    4 SPSA exe (22 options) defaults = lock pins (-Full)
#  5 parity: own reference vs AVX2 / SSE / scalar on the 4 test nets + planted bug
#  6 accumulator walk (random KB4 mirrored net, 500 games)
#  7 scorer control: the lock net as v2 on the S31 subset = 0.014310027 / 0.004572428
#  8 trainer selfcheck (o30_fit.py)             9 MCP forge-o30 self-test
# 10 cleanroom_lint on every patch and on the branch's commit messages since main
# 11 doc_lint on the branch documents          12 D:\o30\nets\INDEX.md: every cited net / exe sha256 matches its file
set -u
W=/d/o30/wt; T=$W/opus_30h/tools; A=$W/opus_30h/a; B=$W/opus_30h/b
# pin this shell first: every check below inherits Idle + CPUs 0-1 (fail closed)
. "$T/idle.sh"; o30_pin_self 0x3 || { echo "final_checks_o30: cannot pin to Idle / CPUs 0-1 (fail closed)" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LOCK='C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe'
V2EXE='D:\o30\w\v2p3_pc1\src_copy\forge_ltopgo_v2p3_pc1.exe'
SPEXE='D:\o30\w\sp1_pc1\src_copy\forge_ltopgo_sp1_pc1.exe'
PINS='d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354'
stamp=$(date +%Y%m%d_%H%M%S); tmp=/d/o30/tmp/final_checks_$stamp; mkdir -p "$tmp"
pass=0; fail=0
check() { local name="$1"; shift; if "$@" > "$tmp/$name.log" 2>&1; then echo "PASS $name"; pass=$((pass+1)); else echo "FAIL $name (log $tmp/$name.log)"; fail=$((fail+1)); fi; }
pc() { powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" "$@"; }
check 01_lock_pins pc -Exe "$LOCK" -Full
check 02_v2exe_off_pins pc -Exe "$V2EXE" -Full
check 03_v2exe_lock_identity pc -Exe "$V2EXE" -Options 'EvalFileV2=D:\o30\nets\lockv2\lock_kbrank4_ob8.nnue2' -Expect "$PINS"
check 04_spsa_exe_pins pc -Exe "$SPEXE" -Full
check 05_parity bash "$A/parity_o30.sh" "$tmp/parity" /c/o13/p4/fens10k.txt /d/o30/harness/h1 /d/o30/nets/lockv2/rand_kbrank4m_ob8_s2.nnue2 \
  /d/o30/nets/lockv2/rand_kbrank4_ob8_s1.nnue2 /d/o30/nets/lockv2/rand_kbone_ob8_s3.nnue2 /d/o30/nets/lockv2/lock_kbone_ob8.nnue2
walk() { /d/o30/harness/h1/v2_eval_avx2.exe --walk 'D:\o30\nets\lockv2\rand_kbrank4m_ob8_s2.nnue2' 99 500 300; }
check 06_walk walk
scorer() {
  local out; out=$(/d/o30/tools_bin/o30_score_v3.exe --net 'D:\o30\nets\lockv2\lock_kbone_ob1.nnue2' \
    --pos 'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos' --hce 'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.hce' --mate-cut 40000)
  echo "$out"; echo "$out" | grep -q '"mse_b1.0": 0.004572428, "mse_b0.6": 0.014310027'
}
check 07_scorer_control scorer
check 08_trainer_selfcheck "$PY" -I -B "$A/o30_fit.py" selfcheck --kb-map rank4 --ob 8
check 09_mcp_selftest "$PY" -I -B "$W/opus_30h/mcp/test_forge_o30_mcp.py"
lint() {
  "$PY" -I -B "$T/cleanroom_lint.py" --patch "$(cygpath -w "$A/v2port.patch")" --patch "$(cygpath -w "$B/expose22.patch")" \
    --patch "$(cygpath -w "$A/bullet_residual.patch")" --commits main..HEAD --git-dir "$(cygpath -w "$W")"
}
check 10_cleanroom lint
doclint() { "$PY" -I -B "$T/doc_lint.py" $(cd "$W" && git ls-files 'opus_30h/*.md' | sed "s#^#$W/#"); }
check 11_doc_lint doclint
indexsha() {
  [ -f /d/o30/nets/INDEX.md ] || { echo "no INDEX.md yet"; return 0; }
  "$PY" -I -B - <<'EOF'
import hashlib, re, sys
text = open(r'D:\o30\nets\INDEX.md', encoding='utf-8').read()
bad = 0
for m in re.finditer(r'`([A-Z]:\\[^`]+\.(?:nnue2|exe))`[^|]*?(?:\|\s*)?(?:sha256 )?([0-9a-f]{64})', text):
    path, want = m.group(1), m.group(2)
    h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    print(('ok  ' if h == want else 'BAD ') + path)
    bad += h != want
sys.exit(1 if bad else 0)
EOF
}
check 12_index_hashes indexsha
echo "final_checks_o30: $pass PASS, $fail FAIL (logs $tmp)"
[ $fail = 0 ]
