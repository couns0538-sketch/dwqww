#!/usr/bin/env python3
"""t3_inspect.py - print the layout of a samply (Firefox Profiler processed) profile: libs, threads, table columns."""
import gzip
import json
import sys

p = sys.argv[1]
with gzip.open(p, 'rt', encoding='utf-8') as f:
    d = json.load(f)
print('top keys', list(d.keys()))
print('meta keys', list(d.get('meta', {}).keys())[:30])
libs = d.get('libs', [])
print('libs', len(libs))
for lib in libs[:400]:
    n = lib.get('name', '')
    if 'forge' in n.lower():
        print('  lib', json.dumps(lib)[:400])
shared = d.get('shared', {})
print('shared keys', list(shared.keys()))
threads = d.get('threads', [])
print('threads', len(threads))
for i, t in enumerate(threads):
    pn = t.get('processName', '')
    if 'forge' in pn.lower():
        s = t.get('samples', {})
        print(i, 'thread', t.get('name'), 'process', pn, 'pid', t.get('pid'), 'tid', t.get('tid'), 'samples', s.get('length'))
        print('   thread keys', list(t.keys()))
        for k in ('samples', 'stackTable', 'frameTable', 'funcTable', 'resourceTable', 'nativeSymbols'):
            v = t.get(k)
            if isinstance(v, dict):
                print('   ', k, 'cols', list(v.keys()), 'len', v.get('length'))
        ft = t.get('funcTable', {})
        strings = t.get('stringArray') or t.get('stringTable') or shared.get('stringArray')
        names = ft.get('name', [])[:8]
        print('    first func names', [strings[n] if isinstance(n, int) and strings else n for n in names])
