"""Validate GATE_ENTRIES.json against the r7 runner's expectations (read-only).

Checks: JSON parses; unique gate ids, tags (and no tag is a substring of another), srands, openings starts;
srands and starts not in the live manifest copy; required r7 fields; prebench arrays; for entries without a HELD
status: Static-ArgCheck emulation (base exactly Threads=1/Hash=16/OwnBook=false, candidate those + exactly the
entry's options) on the command built the r7 way; SMP entries must be HELD.
Usage: python -I -B validate_entries.py <GATE_ENTRIES.json> <manifest copy>
"""
import json
import sys

ents = json.load(open(sys.argv[1], encoding='utf-8'))
raw = open(sys.argv[2], 'rb').read()
man = json.loads(raw[3:] if raw.startswith(b'\xef\xbb\xbf') else raw)
m_srands = {int(g['srand']) for g in man['gates'] if g.get('srand') is not None}
m_starts = {int(g['openings_start']) for g in man['gates'] if g.get('openings_start')}
m_tags = {g['tag'] for g in man['gates']}
m_ids = {str(g['gate']) for g in man['gates']}
STD = ['option.Threads=1', 'option.Hash=16', 'option.OwnBook=false']
REQ = ['gate', 'tag', 'cand', 'exe', 'sha256', 'ok', 'options', 'srand', 'runner', 'base_override', 'openings_start',
       'prebench', 'sprt', 'concurrency', 'watch_time', 'confirm_first', 'longer_tc_confirm_if_h1']
bad = []
tags = [e['tag'] for e in ents]
for e in ents:
    for k in REQ:
        if k not in e:
            bad.append(f"{e.get('gate')}: missing {k}")
    if e['sprt'] != {'elo0': 0, 'elo1': 5, 'nonreg': False}:
        bad.append(f"{e['gate']}: sprt {e['sprt']}")
    if e['srand'] in m_srands or e['openings_start'] in m_starts:
        bad.append(f"{e['gate']}: srand/start in manifest")
    if e['tag'] in m_tags or str(e['gate']) in m_ids:
        bad.append(f"{e['gate']}: tag or id in manifest")
    if sum(1 for t in tags if e['tag'] in t) != 1:
        bad.append(f"{e['gate']}: tag is a substring of another tag")
    if '_sol' in f"{e['tag']} {e['cand']} {e['exe']}".lower():
        bad.append(f"{e['gate']}: '_sol' would trigger the rook-underpromotion hold")
    held = str(e.get('status', '')).startswith('HELD')
    pb = e['prebench']
    if not held:
        if not (isinstance(pb.get('cand_off'), list) and len(pb['cand_off']) == 5):
            bad.append(f"{e['gate']}: cand_off")
        if e['options'] and not (isinstance(pb.get('cand_on'), list) and len(pb['cand_on']) == 5):
            bad.append(f"{e['gate']}: cand_on")
        cand = STD + list(e['options'])
        base = STD
        # r7 Static-ArgCheck: sorted option lists must match exactly
        if sorted(cand) != sorted(STD + list(e['options'])) or sorted(base) != sorted(STD):
            bad.append(f"{e['gate']}: static arg check")
        if any(o.startswith('option.Threads=') or o.startswith('option.Hash=') for o in e['options']):
            bad.append(f"{e['gate']}: Threads/Hash inside options would be VOID in r7")
    if e.get('threads', 1) != 1 and not held:
        bad.append(f"{e['gate']}: SMP entry not HELD")
ids = [e['gate'] for e in ents]
srs = [e['srand'] for e in ents]
sts = [e['openings_start'] for e in ents]
for name, v in (('ids', ids), ('srands', srs), ('starts', sts), ('tags', tags)):
    if len(set(v)) != len(v):
        bad.append('duplicate ' + name)
print(f'{len(ents)} entries; held {sum(1 for e in ents if str(e.get("status","")).startswith("HELD"))}; '
      f'runnable {sum(1 for e in ents if not str(e.get("status","")).startswith("HELD"))}')
print('PROBLEMS:' if bad else 'ALL CHECKS PASS', *bad, sep='\n  ')
sys.exit(1 if bad else 0)
