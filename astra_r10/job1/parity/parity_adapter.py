"""R10 diagnostic build/run adapter. Invoke only through the reviewed safe launcher.

No production candidate is built here. All outputs are new, retained D:/a10 files.
The negative binary changes one embedded NnueW2 int16 coefficient; it is compared
against the GOOD binary's OFF trace, not merely against its own OFF mode.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
sys.path.insert(0,'D:/a10/pydeps')
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lane_guard import check_lane  # CR crfix abcbb9c9

FENS_SHA='c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265'
SOURCE_NET_SHA='a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638'
SOURCE_MANIFEST_SHA='eb0ce6937c9c63be40ac8f8d3c59aada7c0ee4baaa172746d920a4246f5d173a'
COMPONENTS=[{'name':f'lane{i}','encoding':'f32-bits'} for i in range(16)]+[
    {'name':'raw_output','encoding':'f32-bits'}, {'name':'nnue','encoding':'i32-bits'},
    {'name':'hce','encoding':'i32-bits'}, {'name':'combined','encoding':'i32-bits'}]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def new_json(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2); f.write('\n')


def own(path):
    path=Path(path).absolute()
    if '..' in path.parts or not path.is_relative_to(Path('D:/a10')): raise ValueError('path must be under D:/a10 without traversal')
    for parent in [path,*path.parents]:
        if parent.exists() and (parent.is_symlink() or getattr(parent,'is_junction',lambda:False)()):
            raise ValueError('reparse path refused')
    return path


def sources(root):
    return {p.relative_to(root).as_posix():sha(p) for part in ('include','src')
            for p in sorted((root/part).rglob('*')) if p.is_file()}


def unchanged(root,manifest):
    if sources(root)!=manifest: raise ValueError('source changed: '+str(root))


def authoritative_source(root,manifest_path):
    manifest_path=own(manifest_path)
    data=manifest_path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SOURCE_MANIFEST_SHA: raise ValueError('authoritative source manifest hash mismatch')
    raw=json.loads(data.decode('utf-8-sig'))
    expected={key.replace('\\','/'):value for key,value in raw.items()}
    if len(expected)!=len(raw) or sources(root)!=expected: raise ValueError('authoritative source manifest differs from complete source tree')
    return expected,data


def weights(data):
    """Serialize the exact four Forge int16 tensors, with no external decoder."""
    arrays=[]; spans={}; offset=0
    for name,count in [('NnueW1',196608),('NnueB1',256),('NnueW2',512)]:
        pattern=rb'static const std::int16_t '+name.encode()+rb'\['+str(count).encode()+rb'\]\s*=\s*\{([^}]*)\};'
        matches=list(re.finditer(pattern,data))
        if len(matches)!=1: raise ValueError('unexpected embedded array '+name)
        m=matches[0]; body=m.group(1)
        if not re.fullmatch(rb'\s*-?\d+(?:\s*,\s*-?\d+)*\s*,?\s*',body): raise ValueError('array grammar')
        tokens=list(re.finditer(rb'-?\d+',body)); values=[int(t.group()) for t in tokens]
        if len(values)!=count or any(not -32768<=x<=32767 for x in values): raise ValueError('array count/range')
        spans[name]={'offset':offset,'values':values,'tokens':[(m.start(1)+t.start(),m.start(1)+t.end()) for t in tokens]}
        arrays.append(struct.pack('<'+'h'*count,*values)); offset+=count*2
    m=re.search(rb'static const std::int16_t NnueB2\s*=\s*(-?\d+)\s*;',data)
    if not m: raise ValueError('missing NnueB2')
    value=int(m.group(1))
    if not -32768<=value<=32767: raise ValueError('bias range')
    arrays.append(struct.pack('<h',value))
    return b''.join(arrays),spans


def prepare(a):
    root=own(a.out); source=own(a.source); negative=own(a.negative_source)
    fens=own(a.fens); harness=own(Path(__file__).with_name('eval_components.cpp'))
    source_manifest=own(a.source_manifest)
    before,authoritative_bytes=authoritative_source(source,source_manifest)
    if sha(fens)!=FENS_SHA: raise ValueError('authoritative corpus hash mismatch')
    if sha(source/'src/nnue_weights.inc')!=SOURCE_NET_SHA: raise ValueError('embedded source network hash mismatch')
    if not 0<a.seed<2**64 or a.seed==0xA9D1FF: raise ValueError('fresh nonzero uint64 seed required')
    if root.exists() or negative.exists(): raise ValueError('prepared/output directories must be new')
    root.mkdir(); negative.mkdir()
    (root/'authoritative-c1-source.json').write_bytes(authoritative_bytes)
    for part in ('src','include'): shutil.copytree(source/part,negative/part)
    # Preserve the original copied include and create the mutation once. No dataset
    # or .nnue file is overwritten; this is an explicitly disposable source copy.
    path=negative/'src/nnue_weights.inc'; original=path.read_bytes()
    image,spans=weights(original); tensor=spans['NnueW2']; index=0
    old=tensor['values'][index]; new=old+4096
    if new>32767: new=old-4096
    start,end=tensor['tokens'][index]
    changed=original[:start]+str(new).encode('ascii')+original[end:]
    (root/'original_weights.inc').write_bytes(original)
    path.write_bytes(changed)
    negative_image,_=weights(changed)
    offset=tensor['offset']+index*2
    diffs=[i for i,(x,y) in enumerate(zip(image,negative_image)) if x!=y]
    if not diffs or any(not offset<=i<offset+2 for i in diffs): raise ValueError('not a single-weight mutation')
    (root/'network.bin').write_bytes(image); (root/'negative_network.bin').write_bytes(negative_image)
    unchanged(source,before)
    after=sources(negative)
    if [key for key in before if before[key]!=after[key]]!=['src/nnue_weights.inc']:
        raise ValueError('negative source changed more than one file')
    config={'schema':1,'scope':'native-diagnostic-only; UNPROVEN','source':str(source),
            'authoritative_manifest':str(root/'authoritative-c1-source.json'),
            'authoritative_manifest_origin':str(source_manifest),'authoritative_manifest_sha256':SOURCE_MANIFEST_SHA,
            'negative_source':str(negative),'source_files':before,'negative_source_files':after,
            'harness':str(harness),'harness_sha256':sha(harness),'fens':str(fens),'fens_sha256':FENS_SHA,
            'seed':a.seed,'components':COMPONENTS,
            'mutation':{'tensor':'NnueW2','index':index,'old_int16':old,'new_int16':new,
                        'offset':offset,'width':2,'image_encoding':'little-endian-int16 W1,B1,W2,B2',
                        'source_token_start':start,'source_token_end_before':end,
                        'source_token_end_after':start+len(str(new)),
                        'source_before_sha256':sha(root/'original_weights.inc'),'source_after_sha256':sha(path)},
            'network_sha256':sha(root/'network.bin'),'negative_network_sha256':sha(root/'negative_network.bin')}
    new_json(root/'prepared.json',config)
    print('PREPARED',root/'prepared.json')


def load_prepared(path):
    path=own(path); c=json.loads(path.read_text(encoding='utf-8')); root=path.parent
    fens=own(c['fens']); harness=own(c['harness'])
    if sha(fens)!=FENS_SHA or c['fens_sha256']!=FENS_SHA: raise ValueError('corpus drift')
    if sha(harness)!=c['harness_sha256']: raise ValueError('harness drift')
    expected,_=authoritative_source(own(c['source']),own(c['authoritative_manifest']))
    if c['source_files']!=expected or c['authoritative_manifest_sha256']!=SOURCE_MANIFEST_SHA: raise ValueError('authoritative source binding drift')
    unchanged(own(c['source']),c['source_files']); unchanged(own(c['negative_source']),c['negative_source_files'])
    for name,key in [('network.bin','network_sha256'),('negative_network.bin','negative_network_sha256')]:
        if sha(root/name)!=c[key]: raise ValueError('weight image drift')
    return root,c


def compiler_environment(base):
    env=dict(base)
    env['PATH']='C:\\msys64\\ucrt64\\bin;'+env.get('PATH','')
    return env


def invoke(argv,directory,timeout=None,env=None):
    directory.mkdir()
    effective=os.environ if env is None else env
    new_json(directory/'command.json',{'argv':argv,'cwd':str(directory),'threads':1,
             'environment':{key:effective.get(key) for key in ('PATH','TEMP','TMP','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')}})
    start=time.monotonic()
    try:
        with (directory/'stdout.log').open('xb') as out,(directory/'stderr.log').open('xb') as err:
            p=subprocess.run(argv,cwd=directory,stdout=out,stderr=err,stdin=subprocess.DEVNULL,
                             timeout=timeout,shell=False,env=env)
    except subprocess.TimeoutExpired:
        new_json(directory/'exit.json',{'exit_code':None,'timeout':True,'wall_seconds':time.monotonic()-start})
        raise
    new_json(directory/'exit.json',{'exit_code':p.returncode,'wall_seconds':time.monotonic()-start})
    if p.returncode: raise ValueError('native command failed: '+str(directory))


def build(a):
    check_lane()  # CR crfix: Idle/BelowNormal, CPUs 2-3, tmfit lane, foreign pins, 8 GiB RAM
    root,c=load_prepared(a.prepared)
    if not re.fullmatch('[a-zA-Z0-9_-]{1,24}',a.tag): raise ValueError('new bounded build tag required')
    if (root/'builds.json').exists(): raise ValueError('successful build receipt already exists; never overwrite it')
    tool=json.loads(own(a.compiler_config).read_text(encoding='utf-8-sig'))
    compiler=Path(tool['path'])
    if compiler!=Path('C:/msys64/ucrt64/bin/g++.exe'): raise ValueError('only pinned read-only kit compiler approved')
    if tool['sha256'].lower()!='08c11faa4f15a460af8d90a2fd90f658658938c94051bde8babfbecce3304c6c': raise ValueError('compiler identity not approved')
    if not compiler.is_file(): raise ValueError('compiler missing')
    compiler_hash=sha(compiler); exes={}
    if compiler_hash!=tool['sha256'].lower(): raise ValueError('compiler hash mismatch')
    env=compiler_environment(os.environ)
    for label,src in [('good',c['source']),('negative',c['negative_source'])]:
        src=own(src); directory=root/('build-'+label+'-'+a.tag); exe=directory/'eval_components.exe'
        argv=[str(compiler),'-std=c++20','-O3','-DFORGE_NNUE_HIDDEN=256','-DFORGE_NNUE_DIAGNOSTICS',
              '-ffp-contract=off','-fno-fast-math','-march=znver5','-static','-pthread',
              '-I'+str(src/'include'),c['harness']]+[str(src/'src'/f'{unit}.cpp') for unit in
              ('bitboard','board','eval','eval_params','nnue')]+['-o',str(exe)]
        invoke(argv,directory,timeout=1800,env=env)  # CR crfix: bounded compile
        load_prepared(a.prepared)
        if sha(compiler)!=compiler_hash: raise ValueError('compiler drift')
        exes[label]={'path':str(exe),'sha256':sha(exe),'compile_command':argv}
    new_json(root/'builds.json',{'compiler':str(compiler),'compiler_sha256':compiler_hash,
                              'prepared_sha256':sha(a.prepared),'build_tag':a.tag,'binaries':exes})
    print('BUILT diagnostic only',root/'builds.json')


def ref(path,root):
    return {'path':os.path.relpath(path,root).replace('\\','/'),'sha256':sha(path)}


def convert(raw,path,header,lines,seed,mode):
    with raw.open(encoding='utf-8') as src,path.open('x',encoding='utf-8',newline='\n') as dst:
        if src.readline().rstrip('\n')!=f'R10_COMPONENT_TRACE\t1\t{seed}\t{mode}': raise ValueError('native trace header')
        dst.write(json.dumps(header)+'\n'); count=0
        for i,line in enumerate(src):
            parts=line.rstrip('\n').split('\t')
            if i>=len(lines) or len(parts)!=23 or parts[0]!=str(i) or parts[1]!=lines[i]: raise ValueError('native row/order/FEN/components')
            active=int(parts[2]); expected=0 if mode=='OFF' else 1
            if active!=expected: raise ValueError('native activation mismatch')
            if any(not re.fullmatch('[0-9a-f]{8}',x) for x in parts[3:]): raise ValueError('native raw bits malformed')
            dst.write(json.dumps({'row':i,'fen_sha256':hashlib.sha256(lines[i].encode()).hexdigest(),
                                  'eval_bits':parts[3:],'active_evaluations':active})+'\n'); count+=1
        if count!=12000: raise ValueError('native trace length')


def run(a):
    check_lane()  # CR crfix
    root,c=load_prepared(a.prepared); builds=json.loads((root/'builds.json').read_text())
    if builds['prepared_sha256']!=sha(a.prepared): raise ValueError('prepared manifest drift')
    lines=Path(c['fens']).read_text(encoding='utf-8').splitlines()
    options={}
    for mode in ('OFF','ON'):
        path=root/(mode.lower()+'-options.json')
        new_json(path,{'NNUEWideOutput':mode=='ON','NNUE':True,'Threads':1,'evaluation':'residual HCE plus NNUE clamped at MateInMaxPly','playout_seed':c['seed']})
        options[mode]=path
    combined=[]; counters={}
    for label in ('good','negative'):
        binary=builds['binaries'][label]; exe=own(binary['path'])
        if sha(exe)!=binary['sha256']: raise ValueError('binary drift')
        directory=root/('run-'+label)
        invoke([str(exe),c['fens'],str(directory/'off.tsv'),str(directory/'on.tsv'),str(c['seed'])],directory,600)
        if sha(exe)!=binary['sha256']: raise ValueError('binary changed during run')
        native=(directory/'stdout.log').read_text(encoding='utf-8')
        m=re.fullmatch(r'PASS fens=12000 positions=(\d+) moves=(\d+) nulls=(\d+) wide_output_calls=(\d+) seed=(\d+) digest=([0-9a-f]+)\s*',native)
        if not m or int(m[1])!=int(m[4]) or int(m[4])<12000 or int(m[5])!=c['seed']: raise ValueError('native coverage summary invalid')
        counters[label]=int(m[4]); combined.append(label+'\n'+native)
        netkey='network_sha256' if label=='good' else 'negative_network_sha256'
        for mode in ('OFF','ON'):
            header={'schema':1,'kind':'eval-trace','encoding':'components-v1','components':COMPONENTS,
                    'implementation':'scalar' if mode=='OFF' else 'NNUEWideOutput',
                    'binary_sha256':binary['sha256'],'network_sha256':c[netkey],
                    'options_sha256':sha(options[mode]),'fens_sha256':FENS_SHA}
            convert(directory/(mode.lower()+'.tsv'),directory/(mode.lower()+'.jsonl'),header,lines,c['seed'],mode)
    load_prepared(a.prepared)
    (root/'native-summary.log').write_text('\n'.join(combined),encoding='utf-8')
    negative=c['mutation']
    record={'schema':1,'encoding':'components-v1','components':COMPONENTS,'network_storage':'embedded',
            'candidate_path':{'name':'NNUEWideOutput','active_evaluations':counters['good']},
            'fens':ref(Path(c['fens']),root),'scalar_binary':ref(Path(builds['binaries']['good']['path']),root),
            'candidate_binary':ref(Path(builds['binaries']['good']['path']),root),
            'network':ref(root/'network.bin',root),'scalar_options':ref(options['OFF'],root),
            'candidate_options':ref(options['ON'],root),'native_log':ref(root/'native-summary.log',root),
            'scalar_trace':ref(root/'run-good/off.jsonl',root),'candidate_trace':ref(root/'run-good/on.jsonl',root),
            'embedded_provenance':ref(root/'prepared.json',root),'build_provenance':ref(root/'builds.json',root),
            'negative_control':{'network':ref(root/'negative_network.bin',root),'trace':ref(root/'run-negative/on.jsonl',root),
                                'binary':ref(Path(builds['binaries']['negative']['path']),root),
                                'tensor':negative['tensor'],'offset':negative['offset'],'width':negative['width']}}
    new_json(root/'eval-parity.json',record)
    print('RECORDED; checker and native review still required',root/'eval-parity.json')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--threads',required=True,type=int,choices=[1])
    subs=ap.add_subparsers(dest='command',required=True)
    p=subs.add_parser('prepare');p.add_argument('--source',required=True);p.add_argument('--negative-source',required=True)
    p.add_argument('--source-manifest',required=True)
    p.add_argument('--fens',required=True);p.add_argument('--out',required=True);p.add_argument('--seed',required=True,type=int)
    p=subs.add_parser('build');p.add_argument('--prepared',required=True);p.add_argument('--compiler-config',required=True);p.add_argument('--tag',required=True)
    p=subs.add_parser('run');p.add_argument('--prepared',required=True)
    a=ap.parse_args(); {'prepare':prepare,'build':build,'run':run}[a.command](a)


if __name__=='__main__': main()
