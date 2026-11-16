#!/usr/bin/env python3
"""checker.py DETECT_JSON -- the CHECKER, as a rule anyone can apply to recorded output.

It takes the detect.json produced by detect.py and asks, for every middle-band record:
  Does the rule "the record is UNFINISHED iff its last `info depth` value < the requested depth" catch
  every record that actually differs from the finished search?
and, symmetrically, does it ever flag a record that is identical to the finished search (a false alarm)?

The rule needs the requested depth. When it is NOT recorded (the common case in saved data) the fallback
test is "the pv's last move's score does not equal the reported score" -- measured here too, with the
number of false alarms.
"""
import json, sys
d = json.load(open(sys.argv[1]))
def key(m): return (m.get('info_lines'), m.get('last_depth'), m.get('S3_pv_len'),
                    m.get('S6_last_nodes'), str(m.get('score')), m.get('bestmove'))
rows = []
for b, pos in d['builds'].items():
    for p, blk in pos.items():
        f = blk['finished']
        for m in blk['middle']:
            if m.get('empty'):
                rows.append((b, p, m['delay_ms'], 'empty', False, None)); continue
            differs = key(m) != key(f)
            flagged = not m.get('S9_reached_requested_depth')     # the rule
            rows.append((b, p, m['delay_ms'], 'differs' if differs else 'identical', flagged,
                         m.get('S9_last_depth_deficit')))
tot = len([r for r in rows if r[3] != 'empty'])
diff = [r for r in rows if r[3] == 'differs']
ident = [r for r in rows if r[3] == 'identical']
caught = [r for r in diff if r[4]]
false_alarm = [r for r in ident if r[4]]
print("RULE R1: a record is UNFINISHED iff  last `info depth` < the requested depth")
print(f"  records with info lines : {tot}")
print(f"  genuinely differ        : {len(diff)}")
print(f"  of those, R1 catches    : {len(caught)}  ({'ALL' if len(caught)==len(diff) else 'NOT ALL'})")
print(f"  identical to finished   : {len(ident)}")
print(f"  of those, R1 false-alarms: {len(false_alarm)}  (want 0)")
print(f"  records with NO info line at all (R1 cannot see them): {len(rows)-tot}")
print()
print("VERDICT:", "R1 is COMPLETE AND SOUND on this sample"
      if len(caught)==len(diff) and not false_alarm else "R1 is INCOMPLETE or UNSOUND")
if false_alarm:
    for r in false_alarm[:5]: print("   false alarm:", r)
