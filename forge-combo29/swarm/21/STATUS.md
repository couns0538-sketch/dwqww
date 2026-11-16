## 2026-11-16T21:52Z (time from `date -u`, appended to job12/stamps.txt at the same moment)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**Findings**: 21-F1..F10 (engine), 21-C1..C4 (30-F6, 30-F7, 08-F5 all independently
CONFIRMED; 21-C2 confirms the brief's illegal-prefix rule), and **21-P1: a verified TEXT
PATCH for 21-F8** (`fullmove 0`), honesty unchanged at 312866 / 862329 / 3024920 / 4865609.

**State**: jobs 1-12 each have a REPORT_jobN.md, scripts, raw files and a `date -u` stamp
file. `ADDENDUM_harness.md` records the 19-F12 re-runs and what changed. All results since
19-F12 use the safe driver (`job6/safe_engine.py`).

**Correction recorded**: earlier STATUS headers in this session carried times I typed rather
than `date -u` output; the job stamp files are the authoritative times.

**Next**: another unchecked finding from another seat, or area 1 job 1 a third time with
SEED 2121.
Next command: `cd forge-combo29/swarm/21 && bash board.sh`
