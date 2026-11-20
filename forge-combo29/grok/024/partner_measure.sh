#!/usr/bin/env bash
# Independent check of seat 074's patch. Uses this seat's search_set.py, not theirs.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/tmp/forge-partner/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F 'id name ' '/^id name /{print substr($0,9); exit}')
run_one() {
  local name="$1" cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$D/${name}.txt"
  cat > "$D/${name}.meta" << META
exe=$EXE
sha256=$SHA
id_name=$IDNAME
options_sent=
command=$cmd
META
}
run_one partner_honesty_bench11 "bench 11"
run_one partner_honesty_bench13 "bench 13"
run_one partner_honesty_bench16 "bench 16"
run_one partner_honesty_perft5 "go perft 5"
python3 "$D/search_set.py" "$EXE" "$D/O.fens" 12 "$D/partner_off_O" \
  "setoption name IdeaS32 value false" "setoption name IdeaS32_OwedSlack value 0"
python3 "$D/search_set.py" "$EXE" "$D/O.fens" 12 "$D/partner_on_O" \
  "setoption name IdeaS32 value true" "setoption name IdeaS32_OwedSlack value 0"
