#!/usr/bin/env bash
# s38_hand_count.sh ENGINE_LOG ENGINE_NAME [N=5] [MIN_MS=100]   (S38, opus 2026-10-27)
# Independent "hand count" of per-game nps (awk, no code shared with the Python tool): for the first N games
# (ucinewgame commands) that ENGINE_NAME receives in a fastchess `-log engine=true` file, take the last
# `info ... nps ... time ...` line before each `bestmove`, keep searches with time >= MIN_MS, and print
#   <engine> game 0:<slot>:<k>: searches <n>, median nps <m>, aggregate nps <sum(nodes)*1000/sum(time)>
# in the same format as the tool's --per-game-nps list. Read-only; prints to stdout.
set -eu
f=$1; e=$2; n=${3:-5}; min=${4:-100}
LC_ALL=C awk -v E="$e" -v N="$n" -v MIN="$min" '
function num(s, key,   t) { if (!match(s, " " key " [0-9]+")) return -1; t = substr(s, RSTART + length(key) + 2, RLENGTH - length(key) - 2); return t + 0 }
{
  sub(/\r$/, "")
  if (substr($0, 1, 9) != "[Engine] ") next
  s = $0; sub(/^\[Engine\] \[[0-9:.]+\] < */, "", s)
  slot = s; sub(/>.*/, "", slot)
  rest = s; sub(/^[0-9]+> +/, "", rest)
  name = rest; sub(/ .*/, "", name)
  if (name != E) next
  rest = substr(rest, length(name) + 2)
  arrow = substr(rest, 1, 4); text = substr(rest, 6)
  if (arrow == "<---") {
    if (text == "ucinewgame") { cnt[slot]++; gid = "0:" slot ":" cnt[slot]; cur[slot] = gid; if (ng < N) order[++ng] = gid; go[slot] = 0; last[slot] = "" }
    else if (substr(text, 1, 2) == "go") { go[slot] = 1; last[slot] = "" }
    next
  }
  if (substr(text, 1, 5) == "info " && text ~ / nps [0-9]+/ && text ~ / time [0-9]+/) { last[slot] = text; next }
  if (substr(text, 1, 8) == "bestmove") {
    if (go[slot] && last[slot] != "" && (slot in cur)) {
      t = num(last[slot], "time"); p = num(last[slot], "nps"); nd = num(last[slot], "nodes")
      if (t >= MIN) { g = cur[slot]; k = ++m[g]; v[g, k] = p; sn[g] += (nd < 0 ? 0 : nd); st[g] += t }
    }
    go[slot] = 0; last[slot] = ""
  }
}
END {
  for (i = 1; i <= ng; i++) {
    g = order[i]; k = m[g] + 0
    for (a = 2; a <= k; a++) { x = v[g, a]; b = a - 1; while (b >= 1 && v[g, b] > x) { v[g, b + 1] = v[g, b]; b-- } v[g, b + 1] = x }
    if (k == 0) { printf "- %s game %s: searches 0, median nps None, aggregate nps None\n", E, g; continue }
    md = (k % 2) ? v[g, (k + 1) / 2] : (v[g, k / 2] + v[g, k / 2 + 1]) / 2
    q = int(sn[g] * 1000 / st[g]); while ((q + 1) * st[g] <= sn[g] * 1000) q++; while (q * st[g] > sn[g] * 1000) q--
    printf "- %s game %s: searches %d, median nps %.1f, aggregate nps %d\n", E, g, k, md, q
  }
}' "$f"
