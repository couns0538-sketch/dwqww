#!/usr/bin/env bash
# Fable 2026-11-23, W5 (a) of FINAL_PLAN_2311.md with N16 (the profile is part of the test): build ONE variant of
# the engine on Linux with GCC, profile-guided, and stop at the first thing that is not as known.
#
#   build_forge.sh <variant> <source folder (src/, include/)> <net.fnn3> <workloads folder> <known folder> <new work folder>
#   variant: v4 | avx2_pext | avx2_nobmi2 | scalar_verify          (what each needs: cpu_check.sh)
#   env: CXX (g++)  JOBS (4)  PY (python3)  STEP_S (3600: seconds one step of a run may take)
#        LTO (none | full)   CPUINFO (a flag file for the rehearsal)
#        PLANT (none | missing_profile | other_source): the two faults that MUST make this build fail
#
# The steps, each with its stop:
#   1  the processor can run the variant (cpu_check.sh); the work folder is new
#   2  the source is copied into the work folder and its hash list equals <known>/SOURCE.sha256
#   3  pass 1: every unit compiled with counters (-fprofile-generate), linked
#   4  the profile run: <workloads>/profile.uci (the frozen net, the loop's whole option list, bench 11/13/16 and
#      the self-play games as the loop plays them); what the engine answered must EQUAL <known>/profile.json,
#      which was taken from the PC's own program: the same benches, the same games row for row
#   5  counter files exist and none is empty; their hash list is kept (the profile's digest)
#   6  pass 2: every unit compiled with the profile at the SAME object paths; a missing profile or one that does
#      not fit the source is a compiler ERROR (-Werror=missing-profile -Werror=coverage-mismatch), never a warning
#   7  the finished program: <workloads>/verify.uci must equal <known>/verify.json (the three reference numbers,
#      12 perft counts, the net's checksum, eval and benches with the loop's settings) and startup.uci must equal
#      <known>/startup.json (the live searcher after the option list)
#   8  BUILD_NOTE.txt: compiler, flags, digests of source and profile, the program's sha256
# The numbers a build must print carry their settings: the known files are made by tools/make_workloads.py and
# tools/check_run.py on the PC from the live config; nothing is typed here.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PKG="$(dirname "$HERE")"
[ $# -eq 6 ] || { sed -n '2,12p' "$0"; exit 2; }
V="$1"; SRC="$2"; NET="$3"; WL="$4"; KN="$5"; WORK="$6"
CXX="${CXX:-g++}"; JOBS="${JOBS:-4}"; PY="${PY:-python3}"; STEP_S="${STEP_S:-3600}"
LTO="${LTO:-none}"; PLANT="${PLANT:-none}"
say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$WORK/build.log"; }
stop() { echo "[$(date +%H:%M:%S)] STOP: $*" | tee -a "$WORK/build.log" 2>/dev/null || echo "STOP: $*"; exit 1; }

COMMON="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 \
-DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_MATE_ALPHA_GUARD=1 \
-DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -pthread"
case "$V" in
  v4)            ARCH="-march=x86-64-v4 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1" ;;
  avx2_pext)     ARCH="-march=x86-64-v3 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=0" ;;
  avx2_nobmi2)   ARCH="-march=x86-64-v2 -mavx2 -mno-bmi2 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0" ;;
  scalar_verify) ARCH="-march=x86-64 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -DFORGE_NNUE_V3_VERIFY=1" ;;
  *) echo "STOP: unknown variant '$V'"; exit 2 ;;
esac
case "$LTO" in none) LTOC=""; LTOL="" ;; full) LTOC="-flto"; LTOL="-flto=$JOBS" ;; *) echo "STOP: LTO=$LTO"; exit 2 ;; esac
case "$PLANT" in none|missing_profile|other_source) ;; *) echo "STOP: PLANT=$PLANT"; exit 2 ;; esac

# ---- 1 ---------------------------------------------------------------------------------------------------------
[ ! -e "$WORK" ] || { echo "STOP: the work folder $WORK exists (every build gets a new one)"; exit 2; }
for f in "$SRC/src" "$SRC/include" "$NET" "$WL/profile.uci" "$WL/verify.uci" "$WL/startup.uci" \
         "$KN/profile.json" "$KN/verify.json" "$KN/startup.json" "$KN/SOURCE.sha256"; do
  [ -e "$f" ] || { echo "STOP: missing $f"; exit 2; }
done
command -v "$CXX" > /dev/null || { echo "STOP: no compiler '$CXX' on this machine"; exit 2; }
command -v "$PY" > /dev/null || { echo "STOP: no '$PY' on this machine"; exit 2; }
mkdir -p "$WORK"
WORK="$(cd "$WORK" && pwd)"                      # absolute: the counter files are named by full object paths
mkdir -p "$WORK/source" "$WORK/obj" "$WORK/prof" "$WORK/bin" "$WORK/tmp" "$WORK/logs"
export TMPDIR="$WORK/tmp"                        # the compiler's temporary files stay in the work folder too
say "variant $V, compiler $("$CXX" --version | head -n 1), LTO $LTO, plant $PLANT, jobs $JOBS"
bash "$HERE/cpu_check.sh" "$V" ${CPUINFO:+"$CPUINFO"} | tee -a "$WORK/build.log" || stop "the processor check refused the variant"

# ---- 2 ---------------------------------------------------------------------------------------------------------
S="$WORK/source"
cp -r "$SRC/src" "$SRC/include" "$S/"
"$PY" "$PKG/tools/hash_tree.py" "$S" - src include == "$KN/SOURCE.sha256" | tee -a "$WORK/build.log" \
  || stop "the source is not the known source"
"$PY" "$PKG/tools/hash_tree.py" "$S" "$WORK/SOURCE.sha256" src include >> "$WORK/build.log"
UNITS="$(cd "$S/src" && ls *.cpp | sed 's/\.cpp$//')"
NUNITS="$(echo "$UNITS" | wc -w)"

compile_all() {   # $1 = name of the pass, $2 = its extra flags; every unit to the SAME object path in both passes
  local pass="$1" extra="$2" fail=0 pids=() u p
  rm -f "$WORK"/obj/*.o
  for u in $UNITS; do
    ( "$CXX" $COMMON $ARCH $LTOC $extra -I"$S/include" -c "$S/src/$u.cpp" -o "$WORK/obj/$u.o" \
        > "$WORK/logs/${pass}_$u.log" 2>&1 ) &
    pids+=($!)
    if [ "${#pids[@]}" -ge "$JOBS" ]; then wait "${pids[0]}" || fail=1; pids=("${pids[@]:1}"); fi
  done
  for p in "${pids[@]}"; do wait "$p" || fail=1; done
  return $fail
}
link_all() {      # $1 = extra flags, $2 = output, $3 = log
  local objs="" u
  for u in $UNITS; do objs="$objs $WORK/obj/$u.o"; done
  "$CXX" $COMMON $ARCH $LTOC $LTOL $1 $objs -o "$2" > "$3" 2>&1
}
first_error() { grep -h -m 3 -E "error|Error" "$WORK"/logs/"$1"_*.log 2>/dev/null | cut -c1-300 | tee -a "$WORK/build.log" || true; }

# ---- 3 ---------------------------------------------------------------------------------------------------------
GEN="-fprofile-generate=$WORK/prof -fprofile-update=atomic"
say "pass 1: $NUNITS units with counters"
compile_all gen "$GEN" || { first_error gen; stop "pass 1 did not compile"; }
link_all "$GEN" "$WORK/bin/forge_gen" "$WORK/logs/gen_link.log" || { first_error gen; stop "pass 1 did not link"; }

# ---- 4 ---------------------------------------------------------------------------------------------------------
say "the profile run (the loop's options, benches and self-play games)"
"$PY" "$PKG/tools/drive.py" "$WORK/bin/forge_gen" "$WL/profile.uci" "$NET" "$WORK/profile_run.txt" "$STEP_S" \
  | tee -a "$WORK/build.log" \
  || stop "the profile run did not end cleanly"
"$PY" "$PKG/tools/check_run.py" "$WORK/profile_run.txt" known "$KN/profile.json" | tee -a "$WORK/build.log" \
  || stop "the profile run is not the known work: this profile is not used"

# ---- 5 ---------------------------------------------------------------------------------------------------------
NG="$(find "$WORK/prof" -type f -name '*.gcda' | wc -l)"
NE="$(find "$WORK/prof" -type f -name '*.gcda' -size 0 | wc -l)"
say "counter files: $NG for $NUNITS units, $NE empty"
[ "$NG" -ge 1 ] && [ "$NE" -eq 0 ] || stop "no counter file, or an empty one"
"$PY" "$PKG/tools/hash_tree.py" "$WORK" "$WORK/PROFILE.sha256" prof >> "$WORK/build.log"
if [ "$PLANT" = "missing_profile" ]; then
  F="$(find "$WORK/prof" -type f -name '*search.gcda' | head -n 1)"
  [ -n "$F" ] || stop "plant: no counter file of search.cpp to take away"
  rm -f "$F"; say "PLANTED: the counter file of search.cpp is taken away; pass 2 must fail"
fi
if [ "$PLANT" = "other_source" ]; then
  { echo "// planted line: the profile below was taken from another source"; cat "$S/src/search.cpp"; } > "$WORK/tmp/search.cpp"
  mv -f "$WORK/tmp/search.cpp" "$S/src/search.cpp"
  say "PLANTED: one line added at the top of search.cpp after the profile run; pass 2 must fail"
fi

# ---- 6 ---------------------------------------------------------------------------------------------------------
USE="-fprofile-use=$WORK/prof -Werror=missing-profile -Werror=coverage-mismatch"
say "pass 2: $NUNITS units with the profile"
compile_all use "$USE" || { first_error use; stop "pass 2 did not compile (a profile that is missing or does not fit is an error)"; }
link_all "$USE" "$WORK/bin/forge" "$WORK/logs/use_link.log" || { first_error use; stop "pass 2 did not link"; }
[ "$PLANT" = "none" ] || stop "a planted fault was NOT caught: pass 2 went through with PLANT=$PLANT"
if grep -l -E "warning: .*(profile|coverage)" "$WORK"/logs/use_*.log > "$WORK/tmp/profile_warnings.txt" 2>/dev/null; then
  cut -c1-200 "$WORK/tmp/profile_warnings.txt" | tee -a "$WORK/build.log"
  stop "pass 2 wrote a profile warning (see the logs named above): the profile was not used as it is"
fi

# ---- 7 ---------------------------------------------------------------------------------------------------------
for w in verify startup; do
  "$PY" "$PKG/tools/drive.py" "$WORK/bin/forge" "$WL/$w.uci" "$NET" "$WORK/${w}_run.txt" "$STEP_S" | tee -a "$WORK/build.log" \
    || stop "the $w run did not end cleanly"
  "$PY" "$PKG/tools/check_run.py" "$WORK/${w}_run.txt" known "$KN/$w.json" | tee -a "$WORK/build.log" \
    || stop "the finished program does not give the known answers of $w"
done

# ---- 8 ---------------------------------------------------------------------------------------------------------
{
  echo "built:    $(date '+%Y-%m-%d %H:%M:%S') on $(uname -sr), $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //')"
  echo "variant:  $V     LTO: $LTO"
  echo "compiler: $("$CXX" --version | head -n 1)"
  echo "flags:    $COMMON $ARCH $LTOC"
  echo "pass 1:   $GEN"
  echo "pass 2:   $USE"
  echo "source:   $(tail -n 1 "$WORK/SOURCE.sha256")   ($(( $(wc -l < "$WORK/SOURCE.sha256") - 1 )) files, equal to the known list)"
  echo "profile:  $(tail -n 1 "$WORK/PROFILE.sha256")   ($NG counter files; the run equal to the known answers of profile.json)"
  echo "program:  sha256 $(sha256sum "$WORK/bin/forge" | cut -d' ' -f1)   $(stat -c %s "$WORK/bin/forge") bytes"
  echo "checks:   verify.json and startup.json equal"
} > "$WORK/BUILD_NOTE.txt"
cat "$WORK/BUILD_NOTE.txt" >> "$WORK/build.log"
say "BUILT $WORK/bin/forge"
