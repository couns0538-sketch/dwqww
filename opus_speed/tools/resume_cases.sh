#!/usr/bin/env bash
# resume_cases.sh - prove that bitexact_check.ps1 -ResumeFrom cannot lie (own code, runner audit 2026-11-06).
# usage: bash opus_speed/tools/resume_cases.sh [<base dir>]      (default D:/opus_5h/runner_audit)
# Each case copies a REAL prior run (bitexact.log + cand/sig_*.json, the originals are only read) into
# <base>/priors/<case>/, applies ONE edit, then runs the shipped runner with -ResumeFrom and -SkipSan (no engine search,
# no sanitizer build: only sha256 / md5 / log checks). A row counts as the expected REJECT only when the runner exits
# non-zero AND prints the expected guard text; an ACCEPT needs exit 0 and "VERDICT BIT-EXACT".
# Output: <base>/results.tsv (case, expected, got, exit, reason_ok, last line) and <base>/runs/<case>/ (never reused).
set -u
BASE="${1:-D:/opus_5h/runner_audit}"
RUNNER='F:\ospd\wt\opus_speed\tools\bitexact_check.ps1'
LOCK='C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_trial_w6.exe'   # 4181a589
OLDLOCK='C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe'     # fd3a5190
CAND='F:/ospd/cut_nott_lmr/pack/forge_cut_nott_lmr_gate_dcdec9a7.exe'                      # dcdec9a7
OTHER='F:/ospd/tt_cut_node/pack/forge_tt_cut_node_gate_8151e220.exe'                       # 8151e220
PON=/d/oleft2/cnl/fens12k_on      # default (net on) full 12k prior, ref lock, cand dcdec9a7
POFF=/d/oleft2/cnl/fens12k_off    # -FenOptions UseNNUE=false full 12k prior, same exes
FENS=/f/ospd/wt/opus_speed/data/fens_12k_v2.txt
B=$(echo "$BASE" | sed 's#^\([A-Za-z]\):#/\L\1#')
mkdir -p "$B/priors" "$B/runs" || exit 2
[ -e "$B/results.tsv" ] && { echo "resume_cases: $B/results.tsv exists (never overwritten)"; exit 2; }
printf 'case\texpected\tgot\texit\treason_ok\tlast_line\n' > "$B/results.tsv"
[ -f "$B/fens_other.txt" ] || head -n 2000 "$FENS" > "$B/fens_other.txt"

mk() {   # <case> <source prior>: copy log + signature json
  local d="$B/priors/$1"
  [ -e "$d" ] && { echo "resume_cases: $d exists"; exit 2; }
  mkdir -p "$d/cand" && cp "$2/bitexact.log" "$d/" && cp "$2"/cand/sig_*.json "$d/cand/" || exit 2
}
run() {  # <case> <prior dir or ''> <expected REJECT|ACCEPT> <expected text> [runner args...]
  local c="$1" p="$2" exp="$3" txt="$4"; shift 4
  local out="$BASE/runs/$c" pr=() o rc got ok last
  [ -n "$p" ] && pr=(-ResumeFrom "$p")
  o=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$RUNNER" -Out "$out" "${pr[@]}" -SkipSan "$@" 2>&1); rc=$?
  printf '%s\n' "$o" > "$B/runs/$c.console.txt"
  got=REJECT; [ $rc -eq 0 ] && got=ACCEPT
  ok=no; printf '%s' "$o" | grep -qF -- "$txt" && ok=yes
  last=$(printf '%s\n' "$o" | grep -E '^(ERROR|VERDICT)' | tail -1 | tr '\t' ' ' | cut -c1-220)
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$c" "$exp" "$got" "$rc" "$ok" "$last" >> "$B/results.tsv"
  echo "$c: expected $exp, got $got (exit $rc), reason_ok $ok"
}
P="$BASE/priors"
# controls (ACCEPT)
run K1_on_default "${PON/\/d\//D:/}" ACCEPT 'VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs)' -Cand "$CAND" -Ref "$LOCK"
run K2_off_usennue "${POFF/\/d\//D:/}" ACCEPT 'VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs)' -Cand "$CAND" -Ref "$LOCK" -FenOptions UseNNUE=false
mk K3_cut_after_L3 "$PON"; sed -i '/^L3 FENs /q' "$B/priors/K3_cut_after_L3/bitexact.log"
run K3_cut_after_L3 "$P/K3_cut_after_L3" ACCEPT 'VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs)' -Cand "$CAND" -Ref "$LOCK"
# a: options
run A1_off_prior_no_opts "${POFF/\/d\//D:/}" REJECT 'prior L3 used FenOptions but this run has none' -Cand "$CAND" -Ref "$LOCK"
run A2_on_prior_usennue_false "${PON/\/d\//D:/}" REJECT 'resume: FenOptions mismatch' -Cand "$CAND" -Ref "$LOCK" -FenOptions UseNNUE=false
run A3_off_prior_other_opt "${POFF/\/d\//D:/}" REJECT 'resume: FenOptions mismatch' -Cand "$CAND" -Ref "$LOCK" -FenOptions Hash=64
# b: binaries
run B1_other_cand "${PON/\/d\//D:/}" REJECT 'is not for this ref + cand (sha256 mismatch)' -Cand "$OTHER" -Ref "$LOCK"
run B2_other_ref "${PON/\/d\//D:/}" REJECT 'is not for this ref + cand (sha256 mismatch)' -Cand "$CAND" -Ref "$OLDLOCK"
mk B3_sig_json_other_sha "$PON"; sed -i 's/dcdec9a7d71aec370cba9516ed75183f2ee433f71f6024ebdfa4e23c8a56a0c4/8151e220000000000000000000000000000000000000000000000000000000ff/' "$B/priors/B3_sig_json_other_sha"/cand/sig_*.json
run B3_sig_json_other_sha "$P/B3_sig_json_other_sha" REJECT 'belongs to another exe' -Cand "$CAND" -Ref "$LOCK"
# c: FEN set
run C1_other_fen_file "${PON/\/d\//D:/}" REJECT 'is for another FEN file or depth' -Cand "$CAND" -Ref "$LOCK" -Fens "$BASE/fens_other.txt"
run C2_other_depth "${PON/\/d\//D:/}" REJECT 'is for another FEN file or depth' -Cand "$CAND" -Ref "$LOCK" -FenDepth 11
mk C3_l3_md5_edited "$PON"; sed -i 's/(md5 e7dbf2c8;/(md5 00000000;/' "$B/priors/C3_l3_md5_edited/bitexact.log"
run C3_l3_md5_edited "$P/C3_l3_md5_edited" REJECT 'is for another FEN file or depth' -Cand "$CAND" -Ref "$LOCK"
# d: truncated / corrupt
mk D1_cut_in_L1 "$PON"; awk '/^L1 /{n++} n>5{exit} {print}' "$PON/bitexact.log" > "$B/priors/D1_cut_in_L1/bitexact.log"
run D1_cut_in_L1 "$P/D1_cut_in_L1" REJECT 'lacks a complete L1-L3 PASS set' -Cand "$CAND" -Ref "$LOCK"
mk D2_cut_before_L3 "$PON"; sed -i '/^L3 /,$d' "$B/priors/D2_cut_before_L3/bitexact.log"
run D2_cut_before_L3 "$P/D2_cut_before_L3" REJECT 'lacks a complete L1-L3 PASS set' -Cand "$CAND" -Ref "$LOCK"
mk D3_l3_zero "$PON"; sed -i 's#depth 13:12000 / 12000 identical#depth 13:0 / 12000 identical#' "$B/priors/D3_l3_zero/bitexact.log"
run D3_l3_zero "$P/D3_l3_zero" REJECT 'cannot parse L3 identical counts' -Cand "$CAND" -Ref "$LOCK"
mk D4_l3_garbled "$PON"; sed -i 's#depth 13:12000 / 12000 identical#depth 13:twelve-k / 12000 identical#' "$B/priors/D4_l3_garbled/bitexact.log"
run D4_l3_garbled "$P/D4_l3_garbled" REJECT 'cannot parse L3 identical counts' -Cand "$CAND" -Ref "$LOCK"
mk D5_l3_total_zero "$PON"; sed -i 's#depth 13:12000 / 12000 identical#depth 13:12000 / 0 identical#' "$B/priors/D5_l3_total_zero/bitexact.log"
run D5_l3_total_zero "$P/D5_l3_total_zero" REJECT 'cannot parse L3 identical counts' -Cand "$CAND" -Ref "$LOCK"
mk D6_extra_fail_line "$PON"; sed -i '/^L2 perft 5 kiwipete/a L1 bench d11 net on             ref 312866       cand 312867       pin 312866  FAIL' "$B/priors/D6_extra_fail_line/bitexact.log"
run D6_extra_fail_line "$P/D6_extra_fail_line" REJECT 'lacks a complete L1-L3 PASS set' -Cand "$CAND" -Ref "$LOCK"
mkdir -p "$B/priors/D7_no_log/cand" && cp "$PON"/cand/sig_*.json "$B/priors/D7_no_log/cand/"
run D7_no_log "$P/D7_no_log" REJECT 'resume: no ' -Cand "$CAND" -Ref "$LOCK"
mkdir -p "$B/priors/D8_no_sig_json/cand" && cp "$PON/bitexact.log" "$B/priors/D8_no_sig_json/"
run D8_no_sig_json "$P/D8_no_sig_json" REJECT 'ERROR: ' -Cand "$CAND" -Ref "$LOCK"
# extra probes (recorded only; no guard is added for them)
mk X1_l3_k_lt_n_pass "$PON"; sed -i 's#depth 13:12000 / 12000 identical#depth 13:11999 / 12000 identical#' "$B/priors/X1_l3_k_lt_n_pass/bitexact.log"
run X1_l3_k_lt_n_pass "$P/X1_l3_k_lt_n_pass" REJECT 'resume: ' -Cand "$CAND" -Ref "$LOCK"
run X2_chained_resume "$BASE/runs/K1_on_default" REJECT 'lacks a complete L1-L3 PASS set' -Cand "$CAND" -Ref "$LOCK"
echo "results: $B/results.tsv"
