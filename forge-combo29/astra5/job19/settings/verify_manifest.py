from audit import HERE,WORK,MANIFEST,rows,hashlib,re
settings=rows(WORK/'j18sets/sets.txt')
edges=rows(MANIFEST)
assert len(settings)==40 and len(edges)==80
actual={}
for build in ['r15d','kF']:
    output=(WORK/f'j18gate/evidence/{build}/40-uci.txt').read_text()
    actual[build]={name:(int(lo),int(hi)) for name,lo,hi in re.findall(r'^option name (.+?) type spin default -?\d+ min (-?\d+) max (-?\d+)$',output,re.M)}
    assert len(actual[build])==40
skips=[];adjusted=[]
for edge,r in enumerate(edges,1):
    nominal=settings[(edge-1)//2]
    name=nominal['name']
    bound='min' if edge%2 else 'max'
    assert r['name']==name and int(r['edge'])==edge and int(r['index'])==(edge+1)//2 and r['bound']==bound and r['start']==nominal['start']
    for build in actual:assert tuple(int(r[build+'_'+b]) for b in ('min','max'))==actual[build][name]
    target=int(nominal[bound]);lo=max(t[name][0] for t in actual.values());hi=min(t[name][1] for t in actual.values())
    effective=max(lo,min(hi,target))
    assert int(r['value'])==effective and int(r['table_value'])==target
    skip=(effective==int(nominal['start']))
    assert r['status']==('start' if skip else 'play')
    assert int(r['first_game'])==500001+10*(edge-1) and int(r['last_game'])==int(r['first_game'])+4
    if skip:skips.append(f'E{edge:02} {name} {bound}={effective}')
    if effective!=target:adjusted.append(f'E{edge:02} {name} {target}=>{effective}')
text=[f'Frozen manifest SHA-256 {hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}.',f'{len(edges)} numbered edges reproduce the minima/maxima from all 40 frozen job18 settings. The intersected reported UCI bounds of both executable declarations agree. {len(edges)-len(skips)} edges must play and {len(skips)} are start.',f'Start: {", ".join(skips)}.',f'Narrower effective bounds: {len(adjusted)}.']
(HERE/'manifest-check.txt').write_text('\n'.join(text+adjusted)+'\n')
print('\n'.join(text))
