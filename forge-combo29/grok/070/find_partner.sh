#!/usr/bin/env bash
# Print the partner seat: next same-idea seat after us that has a branch.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
idea=$(( (10#$S - 1) % 50 + 1 ))
seats=()
for add in 0 50 100; do
  n=$(printf '%03d' $((idea + add)))
  seats+=("$n")
done
echo "idea $idea seats ${seats[*]}"
have=()
for n in "${seats[@]}"; do
  if git ls-remote --heads origin "refs/heads/for-fable-and-opus/grok-$n" | grep -q .; then
    echo "has $n"
    have+=("$n")
  else
    echo "missing $n"
  fi
done
partner=none
seen=0
for n in "${seats[@]}"; do
  if [ "$seen" -eq 1 ]; then
    for h in "${have[@]}"; do
      if [ "$h" = "$n" ]; then partner=$n; break; fi
    done
    [ "$partner" != none ] && break
  fi
  [ "$n" = "$S" ] && seen=1
done
if [ "$partner" = none ]; then
  for n in "${seats[@]}"; do
    [ "$n" = "$S" ] && break
    for h in "${have[@]}"; do
      if [ "$h" = "$n" ]; then partner=$n; break; fi
    done
    [ "$partner" != none ] && break
  done
fi
echo "PARTNER $partner"
