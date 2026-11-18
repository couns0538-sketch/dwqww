#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job21
fixture=forge-combo29/sol3/job19/positions.txt
engine=/workspace/work/sol3-job4/build_0/forge
net=/workspace/work/sol3-job4-net/net768.fnn3
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 21 prediction'
rg -Fxq 'exit_code 0' "$job/stage0/gate.txt"
rg -Fq 'K1 known-answer parser passed' "$job/stamps.txt"
g1="$job/g1"
mkdir -p "$g1/games"
batch=0
first=''
last=''
flush() {
  if ((batch == 0)); then return; fi
  git add -- "$job"
  git commit -m "sol3 job 21 G1 checkpoint whole games $first to $last"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  batch=0
  first=''
  last=''
}
for game in {41..140}; do
  remaining=$((cutoff - $(date -u +%s)))
  if ((remaining <= 0)); then break; fi
  printf -v label '%03d' "$game"
  out="$g1/games/$label"
  code=0
  PYTHONPATH=/workspace/work/sol3-replay/python timeout --kill-after=2s "$remaining" \
    python3 -B "$job/g1_game.py" --engine "$engine" --net "$net" --fixture "$fixture" \
      --game "$game" --output "$out" > "$g1/games/$label.driver.stdout.txt" \
      2> "$g1/games/$label.driver.stderr.txt" || code=$?
  if ((code != 0)); then
    mkdir -p "$g1/incomplete"
    for path in "$out" "$g1/games/$label.driver.stdout.txt" "$g1/games/$label.driver.stderr.txt"; do
      if [[ -e "$path" ]]; then mv "$path" "$g1/incomplete/"; fi
    done
    printf '%s G1 game %s incomplete, exit %s, omitted from whole-game census\n' "$(date -u +%FT%TZ)" "$game" "$code" >> "$job/stamps.txt"
    if ((batch > 0)); then
      flush
    else
      git add -- "$job"
      git commit -m "sol3 job 21 retain incomplete game $game evidence"
      bash /workspace/work/sol3-job3/push-checkpoint.sh
    fi
    cat "$g1/incomplete/$label.driver.stderr.txt"
    break
  fi
  if [[ ! -f "$g1/rows.tsv" ]]; then head -1 "$out/rows.tsv" > "$g1/rows.tsv"; fi
  test "$(head -1 "$out/rows.tsv")" = "$(head -1 "$g1/rows.tsv")"
  tail -n +2 "$out/rows.tsv" >> "$g1/rows.tsv"
  plies=$(($(wc -l < "$out/rows.tsv") - 1))
  printf '%s G1 game %s complete with %s legal plies and recorded rows\n' "$(date -u +%FT%TZ)" "$game" "$plies" >> "$job/stamps.txt"
  if ((batch == 0)); then first=$game; fi
  last=$game
  batch=$((batch+1))
  if ((game == 41 || game % 10 == 0)); then flush; fi
done
flush
