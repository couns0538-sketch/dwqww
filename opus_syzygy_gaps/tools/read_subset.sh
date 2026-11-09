#!/usr/bin/env bash
# read_subset.sh <exe tag> <exe name> <kind> <rows> <depth> <label> <options> - one read-side run on the first <rows> rows of out/exp/read/rows_<kind>.tsv, with an exe mutants_read_side.sh already built (out/exe/tbr_<exe tag>_<exe name>.exe). No build, so it can run beside that script. Files: out/exp/read/sub_<...>.out and .err, one line in out/exp/read/SUMMARY_sub.txt with the wrong counts per site (null_raw left out: it is a raw return, not a returned claim).
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
R=$J/out/exp/read; RW="$W\\out\\exp\\read"
tag=$1; exe=$2; kind=$3; rows=$4; depth=$5; label=$6; opts=$7
sub=rows_${kind}_s$rows.tsv
[ -e "$R/$sub" ] || head -n "$rows" "$R/rows_$kind.tsv" > "$R/$sub"
n=sub_${tag}_${exe}_${kind}_${rows}_d${depth}_$label
export TB_CLAIMS_WARM=2
s=$(date +%s)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$W\\out\\exe\\tbr_${tag}_$exe.exe" -ArgLine "D:\\syzygy345 $RW\\$sub 4 $depth 0 0 $opts" -OutFile "$RW\\$n.out" -ErrFile "$RW\\$n.err"
rc=$?
e=$(date +%s)
sites=$(grep -E '^site ' "$R/$n.out" | grep -v 'site null_raw')
totals=$(echo "$sites" | awk '{w += $6; v += $4} END {print "events", v, "wrong", w}')
bad=$(echo "$sites" | awk '$6 != 0 {printf "%s %s/%s; ", $2, $6, $4}')
line="$n exit $rc seconds $((e - s)): $totals | $bad$(grep -E '^roots ' "$R/$n.out" | cut -c1-70)"
echo "$line" >> "$R/SUMMARY_sub.txt"
echo "$line" | cut -c1-220
