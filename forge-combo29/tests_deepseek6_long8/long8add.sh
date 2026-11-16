#!/usr/bin/env bash
# long8add.sh -- the remaining long-8 moved values, one setting per line.
set -u
D=/agent/repos/base/forge-combo29/tests_deepseek6_long8
S14=$(cat "$D/s14.txt")
mkdir -p "$D/runs"
run() { # $1 = tag, $2 = exe, $3 = set file, $4 = options
  local tag="$1" exe="$2" setf="$3" opts="$4"
  if [ -s "$D/runs/$tag.rows" ]; then echo "skip $tag (exists)"; return 0; fi
  echo "--- $tag $(date -u) ---"
  python3 "$D/sanrun.py" --exe "$exe" --set "$setf" \
      --out "$D/runs/$tag.rows" --raw "/tmp/$tag.rawlog" \
      --opts "$opts" --depth 10
  python3 "$D/sancount.py" "$D/runs/$tag.rows"
  rm -f "/tmp/$tag.rawlog"
}

SA=/agent/repos/work/l8/build-SoundArms/forge
SS=/agent/repos/work/l8/build-SoundSteps/forge
NL=/agent/repos/work/l8/build-NodeLiterals/forge

for setname in O G; do
  if [ "$setname" = O ]; then setf="$D/first200.fens"; else setf="$D/set_G.epd"; fi
  run "SoundArms_${setname}_ic1"  "$SA" "$setf" "$S14;SoundInCheckArm=1"
  run "SoundArms_${setname}_ma1"  "$SA" "$setf" "$S14;SoundMateAlphaArm=1"
  run "SoundSteps_${setname}_mask8" "$SS" "$setf" "$S14;SoundPvArm=1;SoundStepMask=8"
  run "SoundSteps_${setname}_mask1" "$SS" "$setf" "$S14;SoundPvArm=1;SoundStepMask=1"
  run "SoundSteps_${setname}_rc"  "$SS" "$setf" "$S14;SoundRegretCount=true"
  run "SoundSteps_${setname}_rp"  "$SS" "$setf" "$S14;SoundRegretProbe=true"
  run "NodeLiterals_${setname}_nss48"  "$NL" "$setf" "$S14;NullStaticSlope=48"
  run "NodeLiterals_${setname}_nerm0"  "$NL" "$setf" "$S14;NullEvalRedMax=0"
  run "NodeLiterals_${setname}_nvd1"   "$NL" "$setf" "$S14;NullVerifyDepth=1"
  run "NodeLiterals_${setname}_pci0"   "$NL" "$setf" "$S14;ProbcutImproving=0"
  run "NodeLiterals_${setname}_pcr6"   "$NL" "$setf" "$S14;ProbcutReduction=6"
  run "NodeLiterals_${setname}_pts1"   "$NL" "$setf" "$S14;ProbcutTtSlack=1"
  run "NodeLiterals_${setname}_psr1"   "$NL" "$setf" "$S14;ProbcutStoreReduction=1"
done
echo "ADDENDUM DONE $(date -u)"
