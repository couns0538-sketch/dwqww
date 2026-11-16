#!/usr/bin/env bash
# setoption_grammar.sh EXE — proves the setoption name/value grammar defect.
set -u
EXE="$1"
echo "exe: $EXE"
echo
echo "=== 1. 'setoption name UseNNUE false' (value word omitted): accepted SILENTLY, then IGNORED"
printf 'uci\nisready\neval\nquit\n' | "$EXE" | grep 'info string eval' | sed 's/^/  no setoption : /'
printf 'uci\nsetoption name UseNNUE false\nisready\neval\nquit\n' | "$EXE" | grep -E 'info string eval|invalid' | sed 's/^/  no value word: /'
echo
echo "=== 2. the same intent WITH the value word takes effect"
printf 'uci\nsetoption name UseNNUE value false\nisready\neval\nquit\n' | "$EXE" | grep -E 'info string eval|invalid' | sed 's/^/  with value   : /'
echo
echo "=== 3. an unknown option name is ignored with NO line at all (UCI says nothing is required,"
echo "===    but combined with 1 this makes a typo indistinguishable from success)"
printf 'uci\nsetoption name Totally Bogus value 42\nisready\nquit\n' | "$EXE" | grep -E 'invalid|readyok' | sed 's/^/  bogus name   : /'
echo
echo "=== 4. control: a genuinely out-of-range value DOES answer, so the harness can see a line"
printf 'uci\nsetoption name Hash value 0\nisready\nquit\n' | "$EXE" | grep -E 'invalid|readyok' | sed 's/^/  Hash 0       : /'
echo
echo "=== 5. cause: the name loop eats every token up to 'value', so 'false' becomes part of the NAME"
grep -n 'token != "value"' /agent/repos/base/forge-combo29/src/uci.cpp | sed 's/^/  src\/uci.cpp:/'
