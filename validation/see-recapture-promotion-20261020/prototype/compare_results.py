#!/usr/bin/env python3
"""Evaluate future actual API outputs against immutable source16/oracle evidence."""
from pathlib import Path
import csv, json, sys

ROOT=Path(__file__).resolve().parent
THRESHOLDS=json.loads((ROOT/'inputs/fixed-thresholds.json').read_text())
EXPECTED=json.loads((ROOT/'inputs/expected326.json').read_text())

def evaluate(reference_path,candidate_path,output_path):
    reference_text=Path(reference_path).read_text()
    candidate_text=Path(candidate_path).read_text()
    reference={r['id']:r for r in csv.DictReader(reference_text.splitlines(),delimiter='\t')}
    candidate={r['id']:r for r in csv.DictReader(candidate_text.splitlines(),delimiter='\t')}
    golden={r['id']:r for r in csv.DictReader((ROOT/'inputs/source16-golden326.stdout').read_text().splitlines(),delimiter='\t')}
    ref_lines={line.split('\t',1)[0]:line for line in reference_text.splitlines()[1:]}
    cand_lines={line.split('\t',1)[0]:line for line in candidate_text.splitlines()[1:]}
    ids={c['id'] for c in EXPECTED}
    failures=[]
    if set(reference)!=ids or set(candidate)!=ids:failures.append(['protocol','case IDs/count'])
    reference_oracle_bad=[];candidate_oracle_bad=[];non_guard_rows=0
    adjacent_answers=0
    for case in EXPECTED:
        name=case['id']
        if name not in reference or name not in candidate:continue
        ref=reference[name];cand=candidate[name]
        if any(ref.get(k)!=v for k,v in golden[name].items()):
            failures.append([name,'source16 reference differs from frozen 20-threshold output'])
        for label,row in [('reference',ref),('candidate',cand)]:
            if bool(int(row['initial_legal']))!=case['initial_legal']:
                failures.append([name,label,'initial legality'])
            if bool(int(row['promotion_guard']))!=case['promotion_guard']:
                failures.append([name,label,'guard classification'])
            if case['initial_legal']:
                recaptures=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
                if recaptures!=case['legal_recaptures']:
                    failures.append([name,label,'legal first recaptures'])
        if not case['promotion_guard']:
            non_guard_rows+=1
            if ref_lines[name]!=cand_lines[name]:
                failures.append([name,'non-guard full API row differs'])
        if not case['initial_legal']:
            # SEE is not an initial-move legality validator. Preserve these
            # pseudo-legal controls through ordinary-path byte parity only.
            continue
        expected=case['oracle_exchange']
        for label,row,bad in [('reference',ref,reference_oracle_bad),('candidate',cand,candidate_oracle_bad)]:
            wrong=[t for t in THRESHOLDS if bool(int(row['ge'+str(t)]))!=(expected>=t)]
            if int(row['static_exchange'])!=max(-2000,min(2000,expected)) or wrong:
                bad.append({'id':name,'oracle_exchange':expected,
                            'actual_exchange':int(row['static_exchange']),'bad_thresholds':wrong})
        if case['new_research_case']:
            brackets=dict(pair.split(':') for pair in cand['adjacent_thresholds'].split(','))
            if set(brackets)!={str(expected+d) for d in [-1,0,1]}:
                failures.append([name,'adjacent bracket set'])
            for delta in [-1,0,1]:
                threshold=expected+delta;adjacent_answers+=1
                if brackets.get(str(threshold))!=str(int(expected>=threshold)):
                    failures.append([name,'adjacent threshold',threshold])
    failures.extend([c['id'],'candidate oracle disagreement'] for c in candidate_oracle_bad)
    record={'status':'PASS_BOUNDED_ORACLE_AND_ORDINARY_PARITY' if not failures else 'FAILED_PRESERVE_ATTEMPT',
            'cases':len(EXPECTED),'legal_cases':sum(c['initial_legal'] for c in EXPECTED),
            'initial_illegal_cases_excluded_from_oracle':sum(not c['initial_legal'] for c in EXPECTED),
            'non_guard_rows_byte_compared':non_guard_rows,
            'guard_rows':len(EXPECTED)-non_guard_rows,'new_adjacent_answers':adjacent_answers,
            'reference_oracle_mismatches':reference_oracle_bad,
            'candidate_oracle_mismatches':candidate_oracle_bad,'failures':failures,
            'performance_claim':None,'strength_claim':None}
    Path(output_path).write_text(json.dumps(record,indent=2)+'\n')
    return record

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('reference.stdout candidate.stdout result.json')
    result=evaluate(*sys.argv[1:])
    print(json.dumps({k:result[k] for k in ['status','non_guard_rows_byte_compared','guard_rows','new_adjacent_answers','failures']}))
    raise SystemExit(bool(result['failures']))
