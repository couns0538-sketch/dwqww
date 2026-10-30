"""Fetch the five explicitly MIT binpack headers; never vendor GPL code.
IDEA_SOURCE: pinned per-file licenses in upstream nnue-pytorch; original wrapper.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, urllib.request


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', required=True, type=pathlib.Path)
    ap.add_argument('--manifest', type=pathlib.Path, default=pathlib.Path(__file__).with_name('binpack_dependency_manifest.json'))
    a=ap.parse_args(); spec=json.loads(a.manifest.read_text())
    if spec['repository']!='official-stockfish/nnue-pytorch' or spec['commit']!='ec2ead9feeb5677b828536fc53000d1379a1d207':
        raise ValueError('unexpected dependency manifest origin')
    expected={'arithmetic.h','binpack.h','chess.h','nodchip.h','training_data_entry.h'}
    if set(spec['files'])!=expected: raise ValueError('unexpected dependency closure')
    a.out.mkdir(parents=True, exist_ok=False)
    for name,meta in spec['files'].items():
        url=f"https://raw.githubusercontent.com/{spec['repository']}/{spec['commit']}/data_loader/cpp/lib/{name}"
        with urllib.request.urlopen(url,timeout=60) as r: data=r.read(300000)
        if len(data)!=meta['bytes'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:
            raise ValueError(f'upstream identity mismatch: {name}')
        if b'Permission is hereby granted, free of charge,' not in data[:2000]:
            raise ValueError(f'MIT header missing: {name}')
        with (a.out/name).open('xb') as f:f.write(data)
    with (a.out/'FETCHED.json').open('x') as f:json.dump(spec,f,indent=2);f.write('\n')
    print('PASS: exact five-file MIT dependency closure fetched')

if __name__=='__main__':main()
