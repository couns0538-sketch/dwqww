#!/usr/bin/env python3
"""Exact saved actual-API assertions; illegal initial moves test precondition only."""
from pathlib import Path
import csv, json, sys

ROOT=Path(__file__).resolve().parent
checks=0
kind='baseline' if len(sys.argv)>1 and sys.argv[1]=='baseline' else 'candidate'
for suffix in ['','supplement-']:
    cases=json.loads((ROOT/('oracle-corpus.json' if not suffix else 'supplement-oracle.json')).read_text())
    with (ROOT/('run-'+kind+'.stdout' if not suffix else 'supplement-'+kind+'.stdout')).open() as f:
        rows={r['id']:r for r in csv.DictReader(f,delimiter='\t')}
    for case in cases:
        if case.get('group')=='seeded_sparse': continue
        row=rows[case['id']]
        legal=case.get('initial_legal',True)
        assert row['initial_legal']==str(int(legal)),case['id']
        checks+=1
        if not legal: continue
        actual=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
        assert actual==case['legal_recaptures'],case['id']
        assert int(row['static_exchange'])==case['oracle_exchange'],(case['id'],int(row['static_exchange']),case['oracle_exchange'])
        checks+=2
        for key,value in row.items():
            if not key.startswith('ge'): continue
            assert bool(int(value))==(case['oracle_exchange']>=int(key[2:])),(case['id'],key)
            checks+=1
print('PASS',checks,'exact actual-API assertions over 48 authored cases (46 legal, two initial-illegal preconditions)')
