#!/usr/bin/env python3
"""Original exporter/oracle for the exact AL1 768->256x2 SCReLU residual net.

The lock embeds a C++ .inc, not a loadable .nnue. Both feature accumulation and
16-lane output reduction below explicitly reproduce float32 operation order.
All exports require a bound manifest; all outputs use exclusive creation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

import numpy as np
import export_forge as common

ARCH='Forge-AL1-768x256x2-SCReLU-residual-v1'
SHAPES={'ftw':[256,768],'ftb':[256,1],'outw':[1,512],'outb':[1,1]}
NAMES={'ftw':'NnueW1','ftb':'NnueB1','outw':'NnueW2','outb':'NnueB2'}


def write_checkpoint(out: Path,tensors: dict,provenance: str,description: str='Forge original lock-format smoke') -> dict:
    """Write a manifest and x64 Bullet-format floats; caller supplies provenance.

Physical arrays: ftw[768,256], ftb[256], outw[2,256], outb scalar or[1].
Writing this interchange layout does NOT mean Bullet performed the training.
"""
    if set(tensors)!=set(SHAPES):raise ValueError('exactly four tensor roles required')
    payload=bytearray();manifest={'schema':1,'architecture':ARCH,'usize_bytes':8,'hidden':256,'residual':True,
        'bullet_commit':common.BULLET_COMMIT,'description':description,'provenance':provenance,'tensors':{}}
    physical={'ftw':(768,256),'ftb':(256,),'outw':(2,256),'outb':(1,)}
    for role in SHAPES:
        arr=np.asarray(tensors[role],dtype='<f4')
        if role=='outb' and arr.shape==():arr=arr.reshape(1)
        if arr.shape!=physical[role] or not np.all(np.isfinite(arr)):raise ValueError('wrong/nonfinite '+role+' tensor')
        payload.extend(role.encode()+b'\n'+struct.pack('<Q',arr.size)+arr.tobytes(order='C'))
        manifest['tensors'][role]={'id':role,'shape':SHAPES[role],'layout':'column_major','scale':4096,'rounding':'nearest_ties_away'}
    manifest['checkpoint_sha256']=hashlib.sha256(payload).hexdigest()
    out.mkdir(parents=True,exist_ok=False)
    common.write_new(out/'weights.bin',payload)
    common.write_new(out/'manifest.json',(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
    return manifest


def load_quantized(checkpoint: Path,manifest: Path) -> dict[str,np.ndarray]:
    m=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(m,dict):raise ValueError('manifest must be JSON object')
    if m.get('schema')!=1 or m.get('architecture')!=ARCH or m.get('usize_bytes')!=8 or m.get('hidden')!=256 or m.get('residual') is not True:
        raise ValueError('requires explicit AL1 residual256/x64 checkpoint contract')
    if m.get('bullet_commit')!=common.BULLET_COMMIT:raise ValueError('unreviewed Bullet revision')
    if m.get('checkpoint_sha256')!=common.sha256(checkpoint):raise ValueError('checkpoint SHA256 mismatch')
    specs=m.get('tensors',{})
    if not isinstance(specs,dict) or set(specs)!=set(SHAPES) or any(not isinstance(x,dict) for x in specs.values()):raise ValueError('exactly four tensor specs required')
    raw=common.read_checkpoint(checkpoint,m['checkpoint_sha256']);result={};used=[]
    for role,shape in SHAPES.items():
        spec=specs[role];name=spec.get('id')
        if name not in raw or name in used or spec.get('shape')!=shape or spec.get('layout')!='column_major' or spec.get('scale')!=4096:
            raise ValueError('tensor contract mismatch '+role)
        if raw[name].size!=int(np.prod(shape)):raise ValueError('wrong tensor size '+role)
        used.append(name);result[role]=common.quantize(raw[name],4096,spec.get('rounding'),'<i2')
    if set(used)!=set(raw):raise ValueError('unexpected checkpoint tensors')
    return result


def render_include(q: dict[str,np.ndarray]) -> bytes:
    lines=['// Original Forge AL1 exporter; generated int16 storage, float32 inference.','#include <cstdint>',
           '#define FORGE_NNUE_RESIDUAL 1',
           'static_assert(forge::nnue::InputCount == 768 && forge::nnue::HiddenSize == 256, "NNUE shape mismatch");',
           'static_assert(forge::nnue::WeightScale == 4096.0F && forge::nnue::OutputScale == 4096.0F, "NNUE quantization mismatch");',
           'static_assert(forge::nnue::SigmoidK == 2.25F, "NNUE output scale mismatch");']
    for role in ('ftw','ftb','outw'):
        arr=q[role].reshape(-1)
        lines.append(f'static const std::int16_t {NAMES[role]}[{len(arr)}] = {{')
        for start in range(0,len(arr),24):lines.append('  '+', '.join(str(int(v)) for v in arr[start:start+24])+',')
        lines.append('};')
    lines.append(f'static const std::int16_t NnueB2 = {int(q["outb"].reshape(-1)[0])};')
    return ('\n'.join(lines)+'\n').encode('ascii')


def parse_include(path: Path) -> dict[str,np.ndarray]:
    if path.stat().st_size>8*1024*1024:raise ValueError('include exceeds size bound')
    text=path.read_text(encoding='ascii')
    if not re.search(r'^#define\s+FORGE_NNUE_RESIDUAL\s+1\s*$',text,re.M):raise ValueError('not a residual include')
    result={}
    for role,name in NAMES.items():
        if role=='outb':
            matches=re.findall(r'\bNnueB2\s*=\s*(-?\d+)\s*;',text)
            if len(matches)!=1:raise ValueError('unique NnueB2 required')
            values=[int(matches[0])]
        else:
            matches=re.findall(r'\b'+name+r'\s*\[\s*(\d+)\s*\]\s*=\s*\{([^}]*)\}\s*;',text,re.S)
            if len(matches)!=1:raise ValueError('unique '+name+' required')
            count,body=matches[0]
            if re.search(r'[^\d\s,+-]',body):raise ValueError('unexpected include syntax')
            values=[int(v.strip()) for v in body.split(',') if v.strip()]
            if int(count)!=len(values):raise ValueError('declared size mismatch')
        if len(values)!=int(np.prod(SHAPES[role])) or any(v < -32768 or v > 32767 for v in values):raise ValueError('size/range mismatch '+name)
        result[role]=np.array(values,dtype='<i2')
    return result


def evaluate(q: dict[str,np.ndarray],fen: str) -> tuple[int,int]:
    board,side=common.parse_fen(fen)
    weights=q['ftw'].astype(np.float32).reshape((768,256))/np.float32(4096)
    bias=q['ftb'].astype(np.float32)/np.float32(4096)
    output=q['outw'].astype(np.float32).reshape((2,256))/np.float32(4096)
    acts=[]
    for perspective in (side,1-side):
        acc=bias.copy()
        for color,piece,square in sorted(board,key=lambda item:item[2]):
            index=((int(color!=perspective)*6+piece)*64)+(square^(56 if perspective else 0))
            np.add(acc,weights[index],out=acc)
        acts.append(np.clip(acc,np.float32(0),np.float32(1)))
    lanes=np.zeros(16,dtype=np.float32)
    for h in range(0,256,16):
        a=acts[0][h:h+16];b=acts[1][h:h+16]
        aa=np.multiply(np.multiply(a,a),output[0,h:h+16])
        bb=np.multiply(np.multiply(b,b),output[1,h:h+16])
        np.add(lanes,np.add(aa,bb),out=lanes)
    result=np.float32(q['outb'][0])/np.float32(4096)
    for lane in lanes:result=np.float32(result+lane)
    cp=np.float32(np.float32(result*np.float32(400))/np.float32(2.25))
    value=int(np.clip(cp,np.float32(-30000),np.float32(30000)))
    bits=struct.unpack('<I',struct.pack('<f',float(result)))[0]
    return value,bits


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    for command in ('export','reference'):
        s=sub.add_parser(command);s.add_argument('--checkpoint',type=Path,required=True);s.add_argument('--manifest',type=Path,required=True);s.add_argument('--out',type=Path,required=True)
        if command=='reference':s.add_argument('--fens',type=Path,required=True)
    s=sub.add_parser('include-fixture');s.add_argument('--include',dest='include_file',type=Path,required=True);s.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.cmd=='include-fixture':
            q=parse_include(a.include_file)
            t={'ftw':q['ftw'].astype(np.float32).reshape((768,256))/np.float32(4096),'ftb':q['ftb'].astype(np.float32)/np.float32(4096),'outw':q['outw'].astype(np.float32).reshape((2,256))/np.float32(4096),'outb':q['outb'].astype(np.float32)/np.float32(4096)}
            m=write_checkpoint(a.out,t,'SYNTHETIC interchange from existing include; not Bullet-trained')
            print(json.dumps({'status':'SYNTHETIC_CHECKPOINT_NOT_BULLET_TRAINED','checkpoint_sha256':m['checkpoint_sha256']}));return 0
        q=load_quantized(a.checkpoint,a.manifest)
        if a.cmd=='export':
            content=render_include(q);common.write_new(a.out,content)
            print(json.dumps({'status':'EXPORTED_EMBEDDED_INCLUDE_NOT_RUNTIME_NNUE','bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}));return 0
        n=0
        with a.fens.open(encoding='utf-8') as f,a.out.open('x',encoding='ascii',newline='\n') as out:
            for line in f:
                fen=line.split('|',1)[0].strip()
                if not fen:raise ValueError('blank FEN row')
                cp,bits=evaluate(q,fen);out.write(f'{cp} {bits}\n');n+=1
        if n==0:raise ValueError('empty parity set')
        print(json.dumps({'status':'REFERENCE','positions':n,'columns':['residual_cp','float32_output_bits'],'output_sha256':common.sha256(a.out)}));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print('ERROR: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
