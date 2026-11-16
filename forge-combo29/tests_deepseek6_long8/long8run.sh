#!/usr/bin/env bash
# long8run.sh -- all the long-8 sanitizer runs, one setting per line.
set -u
D=/agent/repos/base/forge-combo29/tests_deepseek6_long8
S14=$(cat "$D/s14.txt")
mkdir -p "$D/runs"
run() { # $1 = tag, $2 = exe, $3 = set file, $4 = options, $5 = depth
  local tag="$1" exe="$2" setf="$3" opts="$4" depth="${5:-10}"
  if [ -s "$D/runs/$tag.rows" ]; then echo "skip $tag (exists)"; return 0; fi
  echo "--- $tag $(date -u) ---"
  python3 "$D/sanrun.py" --exe "$exe" --set "$setf" \
      --out "$D/runs/$tag.rows" --raw "$D/runs/$tag.rawlog" \
      --opts "$opts" --depth "$depth"
  python3 "$D/sancount.py" "$D/runs/$tag.rows"
}

for spec in \
  "LmrGiveCheck:/agent/repos/work/l8/build-LmrGiveCheck/forge::LmrGiveCheck=0" \
  "LmrCutNode:/agent/repos/work/l8/build-LmrCutNode/forge::LmrCutNode=0" \
  "LmrTtPv:/agent/repos/work/l8/build-LmrTtPv/forge::LmrTtPv=0" \
  "SoundArms:/agent/repos/work/l8/build-SoundArms/forge::SoundPvArm=1" \
  "SoundSteps:/agent/repos/work/l8/build-SoundSteps/forge::SoundPvArm=1;SoundStepMask=0" \
  "NodeLiterals:/agent/repos/work/l8/build-NodeLiterals/forge::NullStaticBase=360" \
  "IirNoRoot:/agent/repos/work/l8/build-IirNoRoot/forge::IirRootExclude=1" ; do
  name="${spec%%:*}"; rest="${spec#*:}"
  exe="${rest%%:*}"; moved="${rest#*:}"; moved="${moved#:}"
  for setname in O G; do
    if [ "$setname" = O ]; then setf="$D/first200.fens"; else setf="$D/set_G.epd"; fi
    # defaults
    run "${name}_${setname}_def" "$exe" "$setf" "$S14" 10
    # moved
    run "${name}_${setname}_mov" "$exe" "$setf" "$S14;$moved" 10
  done
done
echo "ALL DONE $(date -u)"
