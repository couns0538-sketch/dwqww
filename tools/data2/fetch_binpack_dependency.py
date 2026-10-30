"""Fetch explicitly opted-in GPL-3.0 external binpack tooling dependencies.
IDEA_SOURCE: QA licence review of full upstream notices; original fetch wrapper.
Headers and the compiled adapter must remain outside every repository.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, urllib.request


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', required=True, type=pathlib.Path)
    ap.add_argument('--accept-gpl3', action='store_true', help='Explicitly accept external GPL-3.0 tooling; never vendored into Forge')
    ap.add_argument('--manifest', type=pathlib.Path, default=pathlib.Path(__file__).with_name('binpack_dependency_manifest.json'))
    a=ap.parse_args()
    if not a.accept_gpl3:
        ap.error('external GPL-3.0 tooling requires --accept-gpl3; default bulletformat needs none')
    a.out = a.out.resolve()
    if any((p / '.git').exists() for p in (a.out, *a.out.parents)):
        ap.error('GPL-3.0 dependencies and compiled adapter must stay outside every repository')
    spec=json.loads(a.manifest.read_text())
    if spec.get('effective_tool_license') != 'GPL-3.0' or spec.get('enabled_by_default') is not False:
        raise ValueError('dependency manifest must disclose optional GPL-3.0 tooling')
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
        # Exact SHA pins cover ALL notices, including embedded GPL provenance.
        if name == 'nodchip.h' and b'which is released under GPL v3 license' not in data:
            raise ValueError('expected embedded GPL notice missing')
        with (a.out/name).open('xb') as f:f.write(data)
    with (a.out/'FETCHED.json').open('x') as f:json.dump(spec,f,indent=2);f.write('\n')
    print('PASS: exact GPL-3.0 external tooling dependency closure fetched; not engine code')

if __name__=='__main__':main()
