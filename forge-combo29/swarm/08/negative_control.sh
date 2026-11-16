#!/usr/bin/env bash
# negative_control.sh — proves the hardened checks FAIL LOUDLY when the reader cannot see a number.
# Seat 19's measurement-integrity warning: a check that prints "CONFIRMS" from a NaN / empty parse is worse
# than no check. This runs each hardened script against a FAKE engine that prints no eval/depth line and
# requires a non-zero exit with a CONTROL... message.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"
OUT=negative_control.txt
: > "$OUT"

echo "## negative control: /bin/cat as a fake engine that answers readyok/uciok but never prints a number" >> "$OUT"
echo >> "$OUT"
echo '```' >> "$OUT"

# a fake engine: echoes the commands it needs to, prints readyok/uciok, never an eval line
cat > /tmp/fake_engine.sh <<'FAKE'
#!/usr/bin/env bash
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name FAKE"; echo "uciok";;
    isready) echo "readyok";;
    eval) : ;;
    go*) echo "bestmove a2a3";;
    quit) exit 0;;
  esac
done
FAKE
chmod +x /tmp/fake_engine.sh

head -3 job1/G100.fens > /tmp/nc_fens.txt 2>/dev/null || head -3 job1/set_G.epd | cut -d' ' -f1-6 > /tmp/nc_fens.txt

echo "### check_s06f4.py against the fake engine (must abort, not confirm)" | tee -a "$OUT"
set +e
timeout 120 python3 check_s06f4.py /tmp/fake_engine.sh /tmp/nc_fens.txt /tmp/nc_out.txt >> "$OUT" 2>&1
RC=$?
set -e
echo "exit code: $RC" | tee -a "$OUT"
if [ "$RC" -eq 0 ]; then
  echo "*** THE HARDENED CHECK PASSED ON A FAKE ENGINE — IT IS STILL VACUOUS ***" | tee -a "$OUT"
else
  echo "OK: non-zero exit, the check refused to report" | tee -a "$OUT"
fi
grep -E "CONTROL|RESULT FAILED|no eval line" "$OUT" | head -3 | tee -a "$OUT"
echo '```' >> "$OUT"
cat "$OUT"
