#!/usr/bin/env bash
# test_fix.sh <fix dir> - original and repaired tablebase download scripts against a local fake mirror (file://).
# Everything happens under <fix dir>/sandbox, which is created fresh; nothing is fetched from the network.
set -u
F=$1
SB="$F/${2:-sandbox}"
if [ -e "$SB" ]; then echo "sandbox exists already: $SB"; exit 2; fi
mkdir -p "$SB/mirror"
for n in KQvK.rtbw KRvK.rtbz KPvKP.rtbw; do printf 'fake table %s\n' "$n" > "$SB/mirror/$n"; done
printf 'escaped\n' > "$SB/mirror/x.rtbw"
# the mirror's list has the form "<md5>  <name>" (two spaces); md5sum on Windows prints "<md5> *<name>"
( cd "$SB/mirror" && md5sum KQvK.rtbw KRvK.rtbz KPvKP.rtbw | awk '{ n = $2; if (substr(n, 1, 1) == "*") n = substr(n, 2); print $1 "  " n }' > checksum.md5 )
URL="file:///$(cygpath -m "$SB/mirror")"
echo "mirror: $URL"
pass=0; failn=0
check() { if eval "$2"; then echo "  PASS $1"; pass=$((pass+1)); else echo "  FAIL $1"; failn=$((failn+1)); fi; }

echo "== 1. clean list, repaired ci_fetch_tables.sh (C1)"
SYZYGY_MIRROR="$URL" bash "$F/scripts/C1_ci_fetch_tables.sh" "$SB/t1/dest"; rc=$?
check "exit 0" "[ $rc -eq 0 ]"
check "3 tables present" "[ \$(ls '$SB/t1/dest' | grep -c 'rtb[wz]\$') -eq 3 ]"
check "same bytes as the mirror" "cmp -s '$SB/mirror/KQvK.rtbw' '$SB/t1/dest/KQvK.rtbw'"

echo "== 2. clean list, ORIGINAL ci_fetch_tables.sh (same result expected)"
SYZYGY_MIRROR="$URL" bash "$F/orig/C1_ci_fetch_tables.sh" "$SB/t2/dest"; rc=$?
check "exit 0" "[ $rc -eq 0 ]"
check "identical folder to the repaired run" "diff -r '$SB/t1/dest' '$SB/t2/dest' > /dev/null"

# a tampered list: one extra line whose name climbs out of the destination folder
mkdir -p "$SB/t3/dest" "$SB/t4/dest"
{ cat "$SB/mirror/checksum.md5"; echo "$(md5sum "$SB/mirror/x.rtbw" | cut -d' ' -f1)  ../x.rtbw"; } > "$SB/tampered.md5"
cp "$SB/tampered.md5" "$SB/t3/dest/checksum.md5"; cp "$SB/tampered.md5" "$SB/t4/dest/checksum.md5"
cp "$SB/mirror/x.rtbw" "$SB/mirror/../x.rtbw.src" 2>/dev/null
echo "== 3. tampered list, ORIGINAL ci_fetch_tables.sh (shows the defect)"
( cd "$SB/mirror" && mkdir -p ../mirror_up && cp x.rtbw ../x.rtbw )   # what the mirror would serve for ../x.rtbw
SYZYGY_MIRROR="$URL" bash "$F/orig/C1_ci_fetch_tables.sh" "$SB/t3/dest"; rc=$?
check "original wrote outside its folder ($SB/t3/x.rtbw)" "[ -f '$SB/t3/x.rtbw' ]"

echo "== 4. tampered list, repaired ci_fetch_tables.sh"
SYZYGY_MIRROR="$URL" bash "$F/scripts/C1_ci_fetch_tables.sh" "$SB/t4/dest"; rc=$?
check "exit 1" "[ $rc -eq 1 ]"
check "nothing written outside ($SB/t4/x.rtbw absent)" "[ ! -e '$SB/t4/x.rtbw' ]"
check "no table fetched at all" "[ \$(ls '$SB/t4/dest' | grep -c 'rtb[wz]') -eq 0 ]"

echo "== 5. clean list, repaired ci_fetch_tables.sh (p6 variant: wants 70 files, the fake mirror has 3)"
SYZYGY_MIRROR="$URL" bash "$F/scripts/p6_ci_fetch_tables.sh" "$SB/t5/dest"; rc=$?
check "3 tables fetched, then its own 70-file check fails (exit 1)" "[ $rc -eq 1 ] && [ \$(ls '$SB/t5/dest' | grep -c 'rtb[wz]\$') -eq 3 ]"
mkdir -p "$SB/t5b/dest"; cp "$SB/tampered.md5" "$SB/t5b/dest/checksum.md5"
SYZYGY_MIRROR="$URL" bash "$F/scripts/p6_ci_fetch_tables.sh" "$SB/t5b/dest"; rc=$?
check "p6 tampered: exit 1, nothing outside, nothing fetched" "[ $rc -eq 1 ] && [ ! -e '$SB/t5b/x.rtbw' ] && [ \$(ls '$SB/t5b/dest' | grep -c 'rtb[wz]') -eq 0 ]"

echo "== 6. download_tb.sh: clean list, repaired and original"
MIRROR="$URL" bash "$F/scripts/C1_download_tb.sh" "$SB/t6/dest" "$SB/mirror/checksum.md5" | tail -n 1; rc=${PIPESTATUS[0]}
check "repaired: 3 files" "[ \$(ls '$SB/t6/dest' | grep -c 'rtb[wz]\$') -eq 3 ]"
MIRROR="$URL" bash "$F/orig/C1_download_tb.sh" "$SB/t7/dest" "$SB/mirror/checksum.md5" | tail -n 1
check "original gives the identical folder" "diff -r '$SB/t6/dest' '$SB/t7/dest' > /dev/null"

echo "== 7. download_tb.sh: tampered list"
MIRROR="$URL" bash "$F/orig/C1_download_tb.sh" "$SB/t8/dest" "$SB/tampered.md5" | tail -n 1
check "original wrote outside its folder ($SB/t8/x.rtbw)" "[ -f '$SB/t8/x.rtbw' ]"
MIRROR="$URL" bash "$F/scripts/C1_download_tb.sh" "$SB/t9/dest" "$SB/tampered.md5"; rc=$?
check "repaired: exit 1" "[ $rc -eq 1 ]"
check "repaired: nothing written, destination not even created" "[ ! -e '$SB/t9' ]"

echo "== 8. other malformed lines are refused by the repaired scripts"
n=0
for badline in "0123  KQvK.rtbw" "$(printf '%032d' 0)  /etc/passwd" "$(printf '%032d' 0)  KQvK.rtbw; rm -rf x" "$(printf '%032d' 0)  a/KQvK.rtbw" "$(printf '%032d' 0)  KQvK.exe" "$(printf '%032d' 0)  *KQvK.rtbw"; do
  n=$((n+1)); mkdir -p "$SB/t10_$n/dest"; { cat "$SB/mirror/checksum.md5"; echo "$badline"; } > "$SB/t10_$n/dest/checksum.md5"
  SYZYGY_MIRROR="$URL" bash "$F/scripts/C1_ci_fetch_tables.sh" "$SB/t10_$n/dest" > /dev/null; rc=$?
  check "refused: [$badline]" "[ $rc -eq 1 ] && [ \$(ls '$SB/t10_$n/dest' | grep -c 'rtb[wz]') -eq 0 ]"
done
echo "RESULT pass=$pass fail=$failn"
