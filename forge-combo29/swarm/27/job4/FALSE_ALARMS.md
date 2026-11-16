# FALSE ALARMS of mine, on the record (nothing here is an engine fault)

Date: 2026-11-16T21:39:01Z

## 1. 'DrawJitter refuses every value, even its own default 0'
My shell line was:
  set -- $opt; printf "...setoption name %s value %s..." "$1" "$2"
with opt='Move Overhead 10' the word-splitting shifted arguments, so the engine really did
receive a malformed command. Re-tested from a file:

```
$ ./forge < /tmp/dj/v4.uci      # setoption name DrawJitter value 4
(no refusal line - accepted)
```

DrawJitter 0/1/4/8 are all accepted; there is no fault. The reported max 8 comes from
DrawJitterMax = 8 (include/forge/search.hpp:83) and apply_spin(0, forge::DrawJitterMax, ...)
is correct.

## 2. 'Move Overhead is an unknown option'
Same cause: an unquoted `cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && D="forge-combo29/swarm/$S" && mkdir -p "$D/job4" && { echo "# FALSE ALARMS of mine, on the record (nothing here is an engine fault)"; echo; echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo; echo "## 1. 'DrawJitter refuses every value, even its own default 0'"; echo "My shell line was:"; echo '  set -- $opt; printf "...setoption name %s value %s..." "$1" "$2"'; echo "with opt='Move Overhead 10' the word-splitting shifted arguments, so the engine really did"; echo "receive a malformed command. Re-tested from a file:"; echo; echo '```'; echo '$ ./forge < /tmp/dj/v4.uci      # setoption name DrawJitter value 4'; echo '(no refusal line - accepted)'; echo '```'; echo; echo "DrawJitter 0/1/4/8 are all accepted; there is no fault. The reported max 8 comes from"; echo "DrawJitterMax = 8 (include/forge/search.hpp:83) and apply_spin(0, forge::DrawJitterMax, ...)"; echo "is correct."; echo; echo "## 2. 'Move Overhead is an unknown option'"; echo "Same cause: an unquoted \`$1\` split 'Move' from 'Overhead'. From a file, both"; echo "\`setoption name Move Overhead value 10\` and \`setoption name Book Depth value 30\` are accepted"; echo "with no refusal line (multi-word option names work because the parser accumulates name"; echo "tokens until the word \`value\`)."; echo; echo "## Lesson applied"; echo "Every option test from now on is a .uci file fed to stdin, never a shell \`printf\` with"; echo "unquoted expansions, and a test must first be shown able to produce its refusal line."; echo; echo "## 3. (earlier, already recorded) perft vs python-chess '0 of 12' - python-chess has no Board.perft."; } > "$D/job4/FALSE_ALARMS.md" && cat "$D/job4/FALSE_ALARMS.md" | head -12` split 'Move' from 'Overhead'. From a file, both
`setoption name Move Overhead value 10` and `setoption name Book Depth value 30` are accepted
with no refusal line (multi-word option names work because the parser accumulates name
tokens until the word `value`).

## Lesson applied
Every option test from now on is a .uci file fed to stdin, never a shell `printf` with
unquoted expansions, and a test must first be shown able to produce its refusal line.

## 3. (earlier, already recorded) perft vs python-chess '0 of 12' - python-chess has no Board.perft.
