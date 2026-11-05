#!/usr/bin/env bash
# final_checks_o30.sh [out log] - Opus 30-h job: re-run every quick check of the job's deliverables (about 10 minutes,
# Idle on O30_MASK, default 0x3 = CPUs 0-1). Prints one PASS / FAIL line per check and a total; exit 0 only if all pass.
#  1 lock exe pins (-Full)                      2 v2 gate exe (kit v2.5) OFF pins (-Full)
#  3 v2 gate exe: lock net as v2 = lock pins    4 SPSA exe (22 options) defaults = lock pins (-Full)
#  5 parity: own reference vs AVX2 / SSE / scalar on the 4 test nets + planted bug
#  6 accumulator walk (random KB4 mirrored net, 500 games)
#  7 scorer control: the lock net as v2 on the S31 subset = 0.014310027 / 0.004572428
#  8 trainer selfcheck (o30_fit.py)             9 MCP forge-o30 self-test
# 10 cleanroom_lint on every patch and on the branch's commit messages since main
# 11 doc_lint on the branch documents          12 INDEX.md: net sha256 + md5 and exe sha256 of every net section
# 13 every Windows / branch path the documents cite exists   14 loader fuzz: 18 damaged files refused, fallback
# 15 every hash the documents cite matches a file / commit / hand-checked entry (tools/hash_allow_o30.txt)
# 16 the multi-file patch scripts are all-or-nothing (test_patch_atomic.py)
# 17 / 18 v2 gate exe: the lock net written as KB16 / KB32 = lock pins (the GPU-window-2 layouts)
# 19 soup and layout-expansion tools on synthetic checkpoints (a/test_soup_tools.py)
set -u
W=/d/o30/wt; T=$W/opus_30h/tools; A=$W/opus_30h/a; B=$W/opus_30h/b
# pin this shell first: every check below inherits Idle + the mask (O30_MASK, default 0x3 = CPUs 0-1; fail closed)
[ -n "${O30_MASK:-}" ] || { echo "final_checks_o30: set O30_MASK (no default; review W2-05)" >&2; exit 78; }
MASK="$O30_MASK"
. "$T/idle.sh"; o30_pin_self "$MASK" || { echo "final_checks_o30: cannot pin to Idle / $MASK (fail closed)" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LOCK='C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe'
V2EXE='D:\o30\w\v2p4_pc1\src_copy\forge_ltopgo_v2p4_pc1.exe'   # the gate exe with the root fix (v2p3 = before it)
SPEXE='D:\o30\w\sp1_pc1\src_copy\forge_ltopgo_sp1_pc1.exe'
PINS='d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354'
stamp=$(date +%Y%m%d_%H%M%S); tmp=/d/o30/tmp/final_checks_$stamp; mkdir -p "$tmp"
pass=0; fail=0
check() { local name="$1"; shift; if "$@" > "$tmp/$name.log" 2>&1; then echo "PASS $name"; pass=$((pass+1)); else echo "FAIL $name (log $tmp/$name.log)"; fail=$((fail+1)); fi; }
pc() { powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Mask "$MASK" "$@"; }   # pin_check pins itself to 0x3 without -Mask
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
lint() {   # must scan the branch's commits (a range that matches nothing would print CLEAN for nothing)
  local out extra=() p
  for p in "$B"/o30tuned_*.patch; do [ -f "$p" ] && extra+=(--patch "$(cygpath -w "$p")"); done   # the O30Tuned patch(es)
  out=$("$PY" -I -B "$T/cleanroom_lint.py" --patch "$(cygpath -w "$A/v2port.patch")" --patch "$(cygpath -w "$B/expose22.patch")" \
    --patch "$(cygpath -w "$A/bullet_residual.patch")" "${extra[@]}" --commits main..HEAD --git-dir "$(cygpath -w "$W")") || { echo "$out"; return 1; }
  echo "$out"; echo "$out" | grep -qE '^cleanroom_lint: CLEAN .*: [1-9][0-9]* scanned\)$'
}
check 10_cleanroom lint
doclint() { "$PY" -I -B "$T/doc_lint.py" $(cd "$W" && git ls-files 'opus_30h/*.md' | sed "s#^#$W/#"); }
check 11_doc_lint doclint
# 12: every net section of INDEX.md - net sha256 + md5 and the gate exe's sha256 (index_check_o30.py; the regex used
#     here until 2026-11-03 20:4x matched the exe rows only and never compared a net hash)
indexsha() { "$PY" -I -B "$T/index_check_o30.py" 'D:\o30\nets\INDEX.md'; }
check 12_index_hashes indexsha
# 13: every Windows / branch path the documents cite exists (WINDOW.md is written only if the GPU is released)
paths() {
  (cd "$W/opus_30h" && "$PY" -I -B "$T/path_sweep.py" FINAL_REPORT.md TOOLS.md STATUS.md a/RESULTS.md b/RESULTS.md \
    b/README.md a/DATA.md a/GPU_PATH.md kit25/README.md CR_FIXLIST_20261104_REPORT.md /d/o30/nets/INDEX.md --allow 'D:\o30\WINDOW.md')
}
check 13_paths paths
# 14: the v2 loader refuses 18 kinds of damaged files with their reason and falls back to the compiled-in net
fuzz() { "$PY" -I -B "$A/loader_fuzz_o30.py" "$V2EXE" 'D:\o30\nets\lockv2\rand_kbrank4m_ob8_s2.nnue2' "$(cygpath -w "$tmp/fuzz")" --mask "$MASK"; }
check 14_loader_fuzz fuzz
# 15: every hash the documents cite = a file hashed here, a commit of the branch, or a hand-checked entry with its
#     reason in tools/hash_allow_o30.txt (input shard hashes, external commits, superseded versions, FNV checksums)
hashes() {
  local f files=()
  for f in /d/o30/nets /d/o30/w/v2p1_pc1/src_copy/forge_ltopgo_v2p1_pc1.exe /d/o30/w/v2p2_pc1/src_copy/forge_ltopgo_v2p2_pc1.exe \
           /d/o30/w/v2p3_pc1/src_copy/forge_ltopgo_v2p3_pc1.exe /d/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe /d/o30/w/sp1_pc1/src_copy/forge_ltopgo_sp1_pc1.exe /d/o30/plain/v2root_1/forge_plain.exe /d/o30/plain/v2root_verify/forge_plain.exe \
           /d/o30/plain/v2port_1/forge_plain.exe /d/o30/plain/spsa_1/forge_plain.exe /d/o30/plain/tunedtest_1/forge_plain.exe \
           /d/o30/plain/v2port_verify/forge_plain.exe /d/o30/target_mock/release/forge-v2-bullet.exe \
           /d/o30/target_rocm/release/forge-v2-bullet.exe /d/o30/tools_bin /d/o30/kit25 /d/o30/repos/base/src/nnue_weights.inc \
           /c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe "$W/opus_30h/a" "$W/opus_30h/b" \
           /d/o30/data/AUDIT.json /d/o30/w/*tuned*_pc1/src_copy/*.exe /d/o30/target_rocm2/release/forge-v2-bullet.exe \
           /d/o30/target_rocm3/release/forge-v2-bullet.exe /d/o30/target_rocm4/release/forge-v2-bullet.exe \
           /d/o30/checks_gpu /d/o30/control/lockkb4_v2p4 /d/o30/spsa/report_184pairs /d/o30/spsa/stc8_main/params.csv /d/a14/FINAL_REPORT.md \
           /c/a14x/cr_fixlist_20261104_from_owner.txt /c/a14x/cr_fixlist2_20261104_from_owner.txt /d/o30/review_w2_independent; do
    [ -e "$f" ] && files+=("$(cygpath -w "$f")")
  done
  (cd "$W" && "$PY" -I -B "$T/hash_sweep.py" --docs $(git ls-files 'opus_30h/*.md') --files "${files[@]}" \
    --repo "$(cygpath -w "$W")" --allow "$(cygpath -w "$T/hash_allow_o30.txt")")
}
check 15_doc_hashes hashes
# 16: the multi-file patch scripts change all their files or none (Code Review 2026-11-04 on o30_v2int16.py)
check 16_patch_atomic "$PY" -I -B "$A/test_patch_atomic.py"
check 17_kb16_identity pc -Exe "$V2EXE" -Options 'EvalFileV2=D:/o30/nets/lockv2/lock_kbrank4x4_ob8.nnue2' -Expect "$PINS"
check 18_kb32_identity pc -Exe "$V2EXE" -Options 'EvalFileV2=D:/o30/nets/lockv2/lock_kbrank4x8_ob8.nnue2' -Expect "$PINS"
check 19_soup_tools "$PY" -I -B "$A/test_soup_tools.py"
echo "final_checks_o30: $pass PASS, $fail FAIL (logs $tmp)"
[ $fail = 0 ]
