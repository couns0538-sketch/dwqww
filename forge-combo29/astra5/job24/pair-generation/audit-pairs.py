"""Independently rederive all 80 plus/minus vectors and parse the four job 24 pins."""
import argparse
import hashlib
import random
import re
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_settings(path):
    data = path.read_bytes()
    git_hash = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
    require(git_hash == '77ab64b2cc9be317351a27bf0fd67761f6d91c81',
            f'job 18 settings diverge from git blob: {git_hash}')
    lines = data.decode('ascii').splitlines()
    require(lines[0].split()[:5] == ['name','start','min','max','step'], 'settings header')
    settings = [(v[0], *map(int,v[1:5])) for line in lines[1:] if (v := line.split())]
    require(len(settings) == len(set(s[0] for s in settings)) == 40, 'settings count/uniqueness')
    return settings


def supplied_pins(job):
    text = job.read_text()
    pins = {(int(j),s):list(map(int,vector.split()))
            for j,s,vector in re.findall(r'^P(1|80)([+-])\s*=\s*((?:-?\d+[ \t\r\n]*)+)', text, re.M)}
    require(set(pins) == {(j,s) for j in (1,80) for s in '+-'} and all(len(vec)==40 for vec in pins.values()),
            'four 40-element known vectors required')
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('definitions', type=Path)
    parser.add_argument('job', type=Path)
    parser.add_argument('generated', type=Path)
    a = parser.parse_args()
    defs,pins = source_settings(a.definitions),supplied_pins(a.job)
    content = a.generated.read_bytes()
    rows = [line.split('\t') for line in content.decode('ascii').splitlines()]
    head = rows.pop(0)
    require(len(head)==81 and len(rows)==80, 'expected 81 columns and 80 data rows')
    headers = ['j'] + [f'{side}_{setting[0]}' for side in ('plus','minus') for setting in defs]
    require(head == headers, 'setting headers must name every plus field, then every minus field, in order')
    clipped = 0
    for j,row in enumerate(rows,1):
        require(len(row)==81 and row[0]==str(j), f'bad row for j={j}')
        rng=random.Random(240000+j)
        actual={'+':list(map(int,row[1:41])), '-':list(map(int,row[41:]))}
        expected={'+':[],'-':[]}
        for name,start,low,high,step in defs:
            # randrange(2) uses 2-bit draws and rejects 2 and 3.
            bit = rng.getrandbits(2)
            while bit > 1:
                bit = rng.getrandbits(2)
            plus = start + (-step,step)[bit]
            minus = 2*start - plus
            for side,raw in (('+',plus),('-',minus)):
                value=min(high,max(low,raw))
                clipped += value != raw
                expected[side].append(value)
        for side in '+-':
            for ix,(want,got) in enumerate(zip(expected[side],actual[side],strict=True)):
                require(want == got, f'j={j} {side} {defs[ix][0]} expected {want} generated {got}')
            if (j,side) in pins:
                require(actual[side] == pins[j,side], f'P{j}{side} differs from supplied vector')
                print(f'P{j}{side}: 40/40 match supplied vector')
    print(f'Pinned job 18 settings blob: 77ab64b2cc9be317351a27bf0fd67761f6d91c81')
    print(f'All 80 pairs: 6,400/6,400 values match independent recomputation; {clipped} values clipped.')
    print(f'pairsets.tsv sha256: {hashlib.sha256(content).hexdigest()}')


if __name__ == '__main__':
    main()
