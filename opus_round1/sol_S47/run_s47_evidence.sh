#!/usr/bin/env bash
# run_s47_evidence.sh (S47, opus 2026-10-27): regenerate fixtures, tests, mutation check, real-file runs, sample packets
# and the deliverable zip. Real inputs are COPIED (cp -p) from the lock archive and the PC (read-only) into $S/real;
# both tools then read only those copies. Python = the read-only venv (3.10), -I -B, nice 19.
set -u
J=$(cd "$(dirname "$0")" && pwd); cd "$J"
S=${S47_SCRATCH_ROOT:-/f/opus_scratch/sol_s47}; SW=$(cygpath -w "$S"); RUN=$S/ev_$$; RW=$(cygpath -w "$RUN"); mkdir -p "$RUN" "$S/tmp" logs sample_packets
export TMP="$SW\\tmp" TEMP="$SW\\tmp"
PY="nice -n 19 /c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B"
A=forge_sol_S47_verify_netonly_tree_20261027.py; B=forge_sol_S47_autolock_audit_20261027.py
LA=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039; PC=/c/Users/Administrator/grok-pc/forge_push
O3=/d/grok-pc-data/dwqww/.claude/worktrees/opus_o3tmp; R=$S/real; mkdir -p "$R"

{ echo "# step1 fixtures generated twice, byte-identical ($(date '+%F %T %z')); python $($PY -c 'import sys; print(sys.version.split()[0])')"
  $PY make_s47_fixtures.py; $PY make_s47_fixtures.py --out "$RW\\fx2"
  diff -r fixtures "$RUN/fx2" && echo "fixtures: two generator runs identical"
  (cd fixtures && find . -type f | LC_ALL=C sort | xargs sha256sum | sed 's# \*\./#  #')
} > logs/step1_fixtures.log 2>&1

mkdir -p "$RUN/t"
{ echo "# step2 tests (ResourceWarning = error): S47_SCRATCH=$RW\\t python -W error::ResourceWarning -I -B test_autolock_audit.py"
  S47_SCRATCH="$RW\\t" $PY -W error::ResourceWarning test_autolock_audit.py 2>&1; echo "exit code: $?"; } > logs/step2_tests.log

{ echo "# step3 mutation check: python -I -B mutation_check_s47.py --scratch $RW\\mut"; $PY mutation_check_s47.py --scratch "$RW\\mut" 2>&1; echo "exit code: $?"; } > logs/step3_mutation_check.log

{ echo "# step4 real-file inputs: copies (cp -p) from the lock archive and the PC, then sha256 of copy == original"
  mkdir -p "$R/AL1_tree" "$R/AL1_plus_f029" "$R/O3_tree" "$R/h256_e12_tree" "$R/old_h256_e12/source" "$R/g120" "$R/g120c" "$R/cr" "$R/s198_net"
  cp -rp "$LA/1_source/forge_AL1_s198_src/include" "$LA/1_source/forge_AL1_s198_src/src" "$R/AL1_tree/"
  cp -rp "$R/AL1_tree/include" "$R/AL1_tree/src" "$R/AL1_plus_f029/"
  cp -p "$LA/5_nnue/nets/history_all_CR_passed/resid_h256_e48_f029_b06_ep48.inc" "$R/f029.inc"; cp -p "$R/f029.inc" "$R/AL1_plus_f029/src/nnue_weights.inc"
  cp -rp "$O3/include" "$O3/src" "$R/O3_tree/"
  cp -rp "$PC/src_h256_e12/include" "$PC/src_h256_e12/src" "$R/h256_e12_tree/"
  [ -d "$R/AUTOLOCK_1_gate120_e32f003rec_s198" ] || cp -rp "$PC/locks/AUTOLOCK_1_gate120_e32f003rec_s198" "$R/"
  cp -p "$PC/h256_e12_sources.sha256" "$R/h256_e12_sources.sha256"; cp -p "$PC/bin/forge_h256_e12.exe" "$R/old_h256_e12/"
  (cd "$PC/src_h256_e12" && cut -c67- "$R/h256_e12_sources.sha256" | tr -d '\r' | while read -r f; do mkdir -p "$R/old_h256_e12/source/$(dirname "$f")"; cp -p "$f" "$R/old_h256_e12/source/$f"; done)
  cp -p "$PC/src_h256_s198/src/nnue_weights.inc" "$R/s198_net/nnue_weights.inc"
  G=/d/grok-pc-data/forge_push; cp -p "$G/gate120_e32f003rec_s198_vs_h256e12/RESULT.md" "$G/gate120_e32f003rec_s198_vs_h256e12/RUN_INFO.json" "$G/gate120_e32f003rec_s198_vs_h256e12/PREBENCH.txt" "$R/g120/"
  cp -p "$G/gate120_e32f003rec_s198_vs_h256e12_confirm/RESULT.md" "$G/gate120_e32f003rec_s198_vs_h256e12_confirm/RUN_INFO.json" "$R/g120c/"
  cp -p "$LA/3_lock_record/CR_PASS_AUTOLOCK_1.txt" "$R/cr/"; cp -p "$LA/6_gate/pc_autonomy_scripts_copy/autonomy_20261025/forge_gates.json" "$R/forge_gates_copy.json"
  $PY - "$(cygpath -w "$R")" <<'PYEOF'
import json, os, sys
r = sys.argv[1]
m = json.load(open(os.path.join(r, 'forge_gates_copy.json'), encoding='utf-8-sig'))
for g in m['gates']:
    if g['tag'] in ('gate120_e32f003rec_s198_vs_h256e12', 'gate120_e32f003rec_s198_vs_h256e12_confirm'):
        d = 'g120c' if g['tag'].endswith('_confirm') else 'g120'
        json.dump({k: g.get(k) for k in ('tag', 'srand', 'openings_start', 'prebench', 'sha256')}, open(os.path.join(r, d, 'record.json'), 'w'), indent=1)
json.dump([{'name': 'e48f006_pin_rerecord_PROPOSED.diff', 'md5_prefix': '3aecb403', 'net_md5': '0fae54a4c0c437432ddb5da85512b5f4'},
           {'name': 'e48f006_known_failures_row_PROPOSED.diff', 'md5_prefix': '5a4ed675', 'net_md5': '0fae54a4c0c437432ddb5da85512b5f4'}],
          open(os.path.join(r, 'pin_allow_e48f006.json'), 'w'), indent=1)
print('records + allow-list written (allow-list = autopromote.ps1 $PIN006_DIFFS / $PIN006_NET constants)')
PYEOF
  for pair in "$LA/5_nnue/nets/history_all_CR_passed/resid_h256_e48_f029_b06_ep48.inc=$R/f029.inc" "$PC/h256_e12_sources.sha256=$R/h256_e12_sources.sha256" \
              "$PC/bin/forge_h256_e12.exe=$R/old_h256_e12/forge_h256_e12.exe" "$PC/locks/AUTOLOCK_1_gate120_e32f003rec_s198/forge_h256_s198.exe=$R/AUTOLOCK_1_gate120_e32f003rec_s198/forge_h256_s198.exe" \
              "$PC/src_h256_s198/src/nnue_weights.inc=$R/s198_net/nnue_weights.inc"; do
    a=${pair%%=*}; b=${pair#*=}; [ "$(sha256sum < "$a")" = "$(sha256sum < "$b")" ] && echo "copy identical: $(basename "$b")" || echo "COPY DIFFERS: $b"; done
  echo "f029 md5 $(md5sum < "$R/f029.inc" | cut -c1-32); s198 gated net md5 $(md5sum < "$R/s198_net/nnue_weights.inc" | cut -c1-32)"
} > logs/step4_real_inputs.log 2>&1

RWIN=$(cygpath -w "$R"); F029=$(md5sum < "$R/f029.inc" | cut -c1-32); AL1NET=$(md5sum < "$R/s198_net/nnue_weights.inc" | cut -c1-32)
{ echo "# step5 Part A real-file runs (verify_netonly_tree, read-only on the copies)"
  echo "## R1 AL1 tree vs AL1 tree with src/nnue_weights.inc = resid_h256_e48_f029_b06_ep48.inc (expected md5 $F029): must exit 0"
  $PY $A --lock "$RWIN\\AL1_tree" --cand "$RWIN\\AL1_plus_f029" --net-md5 "$F029" --out "$RW\\R1.json" > /dev/null; echo "exit $?"; $PY -c "import json,sys; v=json.load(open(sys.argv[1])); print(v['verdict'], v['files'], v['differ'], v['net']['match'], v['reasons'])" "$RW\\R1.json"
  echo "## R2 AL1 tree vs the opus-O3 refactor tree (src differs): must be non-zero"
  $PY $A --lock "$RWIN\\AL1_tree" --cand "$RWIN\\O3_tree" --net-md5 "$F029" --out "$RW\\R2.json" > /dev/null; echo "exit $?"; $PY -c "import json,sys; v=json.load(open(sys.argv[1])); print(v['verdict'], len(v['differ']), 'differ;', len(v['only_in_candidate']), 'only in O3; first reason:', v['reasons'][0][:160])" "$RW\\R2.json"
  echo "## R3 R1 candidate with every .cpp/.hpp converted to CRLF: must exit 0 (CRLF-only edits ignored)"
  mkdir -p "$R/AL1_plus_f029_crlf"; cp -rp "$R/AL1_plus_f029/include" "$R/AL1_plus_f029/src" "$R/AL1_plus_f029_crlf/"
  find "$R/AL1_plus_f029_crlf" -name '*.cpp' -o -name '*.hpp' | while read -r f; do sed -i 's/\r\?$/\r/' "$f"; done
  $PY $A --lock "$RWIN\\AL1_tree" --cand "$RWIN\\AL1_plus_f029_crlf" --net-md5 "$F029" --out "$RW\\R3.json" > /dev/null; echo "exit $?"; $PY -c "import json,sys; v=json.load(open(sys.argv[1])); print(v['verdict'], len(v['crlf_only_ignored']), 'CRLF-only files ignored')" "$RW\\R3.json"
  echo "## R4 the real AUTOLOCK_1 dir (tree in source/) vs the h256_e12 tree, expected md5 $AL1NET (the gated s198 net): must exit 0"
  $PY $A --lock "$RWIN\\h256_e12_tree" --cand "$RWIN\\AUTOLOCK_1_gate120_e32f003rec_s198" --net-md5 "$AL1NET" --out "$RW\\R4.json" > /dev/null; echo "exit $?"; $PY -c "import json,sys; v=json.load(open(sys.argv[1])); print(v['verdict'], v['files'], v['differ'], v['candidate']['autolock_dir'])" "$RW\\R4.json"
  echo "## R5 --lock = the real AUTOLOCK_1 dir (any AUTOLOCK as the lock) vs AL1 + f029 net: must exit 0"
  $PY $A --lock "$RWIN\\AUTOLOCK_1_gate120_e32f003rec_s198" --cand "$RWIN\\AL1_plus_f029" --net-md5 "$F029" --out "$RW\\R5.json" > /dev/null; echo "exit $?"; $PY -c "import json,sys; v=json.load(open(sys.argv[1])); print(v['verdict'], v['lock']['lock_json'], v['differ'])" "$RW\\R5.json"
} > logs/step5_partA_real.log 2>&1

{ echo "# step6 Part B real-file run: audit of the real AUTOLOCK_1 (copy) against the h256_e12 lock (copy)"
  $PY $B --old-lock "$RWIN\\old_h256_e12" --old-tag h256_e12 --new-lock "$RWIN\\AUTOLOCK_1_gate120_e32f003rec_s198" \
     --old-hashes "$RWIN\\h256_e12_sources.sha256" --old-hashes-root "$RWIN\\old_h256_e12\\source" --old-ref "$RWIN\\g120\\PREBENCH.txt" \
     --gate-result "$RWIN\\g120\\RESULT.md" --gate-run-info "$RWIN\\g120\\RUN_INFO.json" --gate-record "$RWIN\\g120\\record.json" \
     --confirm-result "$RWIN\\g120c\\RESULT.md" --confirm-run-info "$RWIN\\g120c\\RUN_INFO.json" --confirm-record "$RWIN\\g120c\\record.json" \
     --net-md5 "$AL1NET" --pin-allow "$RWIN\\pin_allow_e48f006.json" --cr-dir "$RWIN\\cr" \
     --out-md sample_packets/real_AUTOLOCK_1_gate120_e32f003rec_s198_packet.md --out-json sample_packets/real_AUTOLOCK_1_gate120_e32f003rec_s198_packet.json > /dev/null
  echo "exit $? (3 = INCOMPLETE: something MISSING, nothing FAILED)"; grep -E '^\*\*Overall|^\| A' sample_packets/real_AUTOLOCK_1_gate120_e32f003rec_s198_packet.md | cut -c1-260
  echo "## fixture sample packet (good case, scratch copy of fixtures/partB)"
  mkdir -p "$RUN/sp"; cp -rp fixtures/partB "$RUN/sp/"; P=$RW\\sp\\partB
  $PY $B --old-lock "$P\\locks\\AUTOLOCK_1_gate120_fx" --new-lock "$P\\locks\\AUTOLOCK_2_gate130_fx" --old-hashes "$P\\locks\\AUTOLOCK_1_gate120_fx\\SOURCES.sha256" \
     --gate-result "$P\\gate\\RESULT.md" --gate-run-info "$P\\gate\\RUN_INFO.json" --gate-record "$P\\gate\\record.json" \
     --confirm-result "$P\\confirm\\RESULT.md" --confirm-run-info "$P\\confirm\\RUN_INFO.json" --confirm-record "$P\\confirm\\record.json" \
     --net-md5 "$(cat fixtures/partB/net_md5.txt)" --pin-allow "$P\\pin_allow.json" --cr-dir "$P\\cr" \
     --out-md sample_packets/fixture_AUTOLOCK_2_gate130_fx_packet.md --out-json sample_packets/fixture_AUTOLOCK_2_gate130_fx_packet.json > /dev/null; echo "fixture packet exit $?"
} > logs/step6_partB_real.log 2>&1

$PY - <<'PYEOF'
import os, zipfile
names = ['README_S47_20261027.md', 'IDEA_SOURCE.md', 'forge_sol_S47_verify_netonly_tree_20261027.py', 'forge_sol_S47_autolock_audit_20261027.py', 'make_s47_fixtures.py',
         'test_autolock_audit.py', 'mutation_check_s47.py', 'run_s47_evidence.sh']
for top in ('fixtures', 'sample_packets'):
    for dp, dn, fn in os.walk(top):
        dn.sort()
        names += [os.path.join(dp, f).replace(os.sep, '/') for f in sorted(fn)]
with zipfile.ZipFile('forge_sol_S47_autolock_audit_20261027.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for n in names:
        if os.path.isfile(n):
            zi = zipfile.ZipInfo(n, date_time=(2026, 10, 27, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
            with open(n, 'rb') as f:
                z.writestr(zi, f.read())
print('zip entries', len(names))
PYEOF
ls -l forge_sol_S47_autolock_audit_20261027.zip; tail -2 logs/step2_tests.log; tail -2 logs/step3_mutation_check.log; grep -E '^exit|^PASS|^FAIL|identical|DIFFERS' logs/step4_real_inputs.log logs/step5_partA_real.log logs/step6_partB_real.log
