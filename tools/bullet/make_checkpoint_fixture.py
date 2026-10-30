#!/usr/bin/env python3
"""Make a synthetic Bullet-format checkpoint from an existing R10 net for tests.

THIS DOES NOT TRAIN AND DOES NOT PROVE BULLET TRAINING COMPATIBILITY. It checks
our checkpoint parser, tensor layout, serializer and integer-reference arithmetic.
Only zero-padded nets whose integer tensors are exactly representable by float32
can round-trip through this deliberately scale=1 fixture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np
import export_forge as ef


def import_fixture(net_path: Path, out: Path, l1: int, l2: int, l3: int) -> dict:
    if not (isinstance(l1,int) and isinstance(l2,int) and isinstance(l3,int) and 64<=l1<=4096 and l1%64==0 and 2<=l2<=64 and l2%2==0 and 2<=l3<=64 and l3%2==0):
        raise ValueError('unsupported R10 dimensions')
    if net_path.stat().st_size>300*1024*1024:
        raise ValueError('net exceeds bounded fixture-import size')
    data=net_path.read_bytes();cursor=0
    def read(dtype,count):
        nonlocal cursor
        n=np.dtype(dtype).itemsize*count
        if cursor+n>len(data):raise ValueError('truncated net')
        result=np.frombuffer(data,dtype=dtype,count=count,offset=cursor).copy();cursor+=n;return result
    version,nethash,descsize=(int(x) for x in read('<u4',3))
    if version!=ef.VERSION or nethash!=(ef.fc_hash(l1,l2,l3)^ef.FEATURE_HASH^(2*l1)):
        raise ValueError('net version/hash does not match specified dimensions')
    if descsize>1024*1024 or cursor+descsize>len(data):raise ValueError('bad description length')
    try:description=data[cursor:cursor+descsize].decode('utf-8')
    except UnicodeDecodeError as exc:raise ValueError('fixture requires UTF-8 description') from exc
    cursor+=descsize
    if int(read('<u4',1)[0])!=(ef.FEATURE_HASH^(2*l1)):raise ValueError('wrong feature hash')
    ftb=read('<i2',l1);ftw=read('i1',ef.FEATURES*l1).reshape((ef.FEATURES,l1))
    tensors={'ftw':ftw,'ftb':ftb}
    for role in ('l1w','l1b','l2w','l2b','l3w','l3b'):tensors[role]=[]
    for stack in range(32):
        if int(read('<u4',1)[0])!=ef.fc_hash(l1,l2,l3):raise ValueError('wrong stack hash')
        for layer,width,inputs in [('l1',l2,l1),('l2',l3,2*l2),('l3',1,2*l2+2*l3)]:
            tensors[layer+'b'].append(read('<i4',width))
            weights=read('i1',width*ef.pad32(inputs)).reshape((width,ef.pad32(inputs)))
            if np.any(weights[:,inputs:]):raise ValueError('nonzero padded weight cannot be preserved by fixture')
            tensors[layer+'w'].append(weights[:,:inputs].copy())
    if cursor!=len(data):raise ValueError('trailing net bytes')
    for role in ('l1w','l1b','l2w','l2b','l3w','l3b'):tensors[role]=np.stack(tensors[role])
    net=ef.Net(l1,l2,l3,description,tensors);ef.validate_bounds(net)
    if ef.serialize(net)!=data:raise ValueError('net decoder/serializer byte identity failed')
    manifest={'schema':1,'architecture':ef.ARCH,'usize_bytes':8,'bullet_commit':ef.BULLET_COMMIT,
              'l1':l1,'l2':l2,'l3':l3,'description':description,'tensors':{},
              'provenance':'SYNTHETIC CHECKPOINT: decoded from existing net, not produced by Bullet training',
              'source_net_sha256':hashlib.sha256(data).hexdigest()}
    payload=bytearray()
    for role,shape in ef.shapes(l1,l2,l3).items():
        a=tensors[role]
        if role=='ftw':a=a.T
        else:a=a.reshape(shape)
        floats=a.astype('<f4')
        if not np.array_equal(floats.astype(np.int64),a.astype(np.int64)):
            raise ValueError('integer tensor not exactly representable by float32 scale=1 fixture')
        payload.extend(role.encode()+b'\n'+struct.pack('<Q',floats.size)+floats.tobytes(order='F'))
        manifest['tensors'][role]={'id':role,'shape':list(shape),'layout':'column_major','scale':1,'rounding':'truncate'}
    manifest['checkpoint_sha256']=hashlib.sha256(payload).hexdigest()
    out.mkdir(parents=True,exist_ok=False)
    ef.write_new(out/'weights.bin',payload)
    ef.write_new(out/'manifest.json',(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
    return {'status':'SYNTHETIC_CHECKPOINT_NOT_BULLET_TRAINED','source_net_sha256':manifest['source_net_sha256'],'checkpoint_sha256':manifest['checkpoint_sha256'],'bytes':len(payload)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--net',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    for name in ('l1','l2','l3'):p.add_argument('--'+name,type=int,required=True)
    a=p.parse_args()
    try:print(json.dumps(import_fixture(a.net,a.out,a.l1,a.l2,a.l3),sort_keys=True));return 0
    except (ValueError,OSError) as e:print('ERROR: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
