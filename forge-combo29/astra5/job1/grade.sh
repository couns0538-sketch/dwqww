set -eu
jobdir=forge-combo29/astra5/job1
python3 "$jobdir/analyze.py" pair "$jobdir/rows" G --bounds .9304 .9306
python3 "$jobdir/analyze.py" pair "$jobdir/rows" G --sd20 --bounds 1.0150 1.1500
python3 "$jobdir/analyze.py" pair "$jobdir/rows" O --bounds .9701 .9703
python3 "$jobdir/analyze.py" pair "$jobdir/rows" O --sd20 --bounds 1.0100 1.1400
