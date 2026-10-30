#!/usr/bin/env python3
"""Original Bullet checkpoint exporter and integer oracle for Forge R10 K32H3^.

No generic Bullet network can be converted by renaming tensors. A checked explicit
manifest binds the exact architecture, tensor layout, quantization and source hash.
This tool never trains a network or changes the engine. NumPy is the only dependency.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
from typing import Iterable

import numpy as np

BULLET_COMMIT = 'da426a49b2a4b79a55a87031cd51c89bdf1ff030'
ARCH = 'Forge-R10-K32H3-pairwise-32stack-v1'
FEATURES = 67584
FEATURE_HASH = 0xAB005CEF
VERSION = 0x6A448AFA
ROLES = ('ftw', 'ftb', 'l1w', 'l1b', 'l2w', 'l2b', 'l3w', 'l3b')
MAX_CHECKPOINT = 1200 * 1024 * 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write_new(path: Path, payload: bytes) -> None:
    """Exclusive creation; partial files survive a failed write for diagnosis."""
    with path.open('xb') as f:
        f.write(payload)


def read_checkpoint(path: Path) -> dict[str, np.ndarray]:
    size = path.stat().st_size
    if not 0 < size <= MAX_CHECKPOINT:
        raise ValueError('checkpoint empty or above 1200 MiB parser bound')
    tensors = {}
    with path.open('rb') as f:
        while f.tell() < size:
            name = f.readline(257)
            if not name.endswith(b'\n') or len(name) <= 1 or len(name) > 256:
                raise ValueError('invalid or overlong tensor ID')
            try:
                name = name[:-1].decode('ascii')
            except UnicodeDecodeError as e:
                raise ValueError('tensor ID must be ASCII') from e
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in tensors:
                raise ValueError('invalid or duplicate tensor ID')
            header = f.read(8)
            if len(header) != 8:
                raise ValueError('truncated 64-bit tensor element count')
            n, = struct.unpack('<Q', header)
            if n == 0 or n > (size - f.tell()) // 4:
                raise ValueError('zero or truncated tensor size')
            a = np.frombuffer(f.read(n * 4), dtype='<f4').copy()
            if not np.all(np.isfinite(a)):
                raise ValueError('checkpoint contains nonfinite tensor')
            tensors[name] = a
    if not tensors:
        raise ValueError('empty checkpoint')
    return tensors


def quantize(a: np.ndarray, scale: float, rounding: str, dtype: str) -> np.ndarray:
    if isinstance(scale, bool) or not isinstance(scale, (float, int)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError('positive finite quantization scale required')
    # Bullet converts the stored f32 to f64 before multiplying; preserve that order.
    z = a.astype(np.float64) * scale
    if rounding == 'truncate':
        z = np.trunc(z)
    elif rounding == 'nearest_ties_away':
        z = np.copysign(np.floor(np.abs(z) + .5), z)
    else:
        raise ValueError('unsupported rounding: use truncate or nearest_ties_away')
    limits = np.iinfo(np.dtype(dtype))
    if not np.all(np.isfinite(z)) or np.any(z < limits.min) or np.any(z > limits.max):
        raise ValueError('quantization is nonfinite or overflows ' + dtype)
    return z.astype(dtype)


@dataclass
class Net:
    l1: int
    l2: int
    l3: int
    description: str
    tensors: dict[str, np.ndarray]


def shapes(l1: int, l2: int, l3: int) -> dict[str, tuple[int, int]]:
    return {'ftw': (l1, FEATURES), 'ftb': (l1, 1),
            'l1w': (32*l2, l1), 'l1b': (32*l2, 1),
            'l2w': (32*l3, 2*l2), 'l2b': (32*l3, 1),
            'l3w': (32, 2*l2+2*l3), 'l3b': (32, 1)}


def load_quantized(checkpoint: Path, manifest: Path) -> Net:
    m = json.loads(manifest.read_text(encoding='utf-8'))
    if m.get('schema') != 1 or m.get('architecture') != ARCH or m.get('usize_bytes') != 8:
        raise ValueError('requires explicit Forge R10 architecture and x64 Bullet checkpoint contract')
    if m.get('bullet_commit') != BULLET_COMMIT:
        raise ValueError('unsupported Bullet revision; review checkpoint format before updating pin')
    if m.get('checkpoint_sha256') != sha256(checkpoint):
        raise ValueError('checkpoint SHA256 does not match manifest')
    l1, l2, l3 = (m.get(k) for k in ('l1', 'l2', 'l3'))
    if any(type(x) is not int for x in (l1,l2,l3)):
        raise ValueError('integer dimensions required')
    if not (64 <= l1 <= 4096 and l1 % 64 == 0 and 2 <= l2 <= 64 and l2 % 2 == 0 and 2 <= l3 <= 64 and l3 % 2 == 0):
        raise ValueError('shape outside Forge R10 supported dimensions')
    description = m.get('description', '')
    if not isinstance(description,str) or len(description.encode('utf-8')) > 1024*1024:
        raise ValueError('invalid description')
    spec = m.get('tensors',{})
    if set(spec) != set(ROLES):
        raise ValueError('manifest must name exactly the eight supported tensor roles')
    original = read_checkpoint(checkpoint)
    quantized = {}
    used = []
    for role, shape in shapes(l1,l2,l3).items():
        s = spec[role]
        name = s.get('id')
        if name not in original or s.get('shape') != list(shape) or s.get('layout') != 'column_major':
            raise ValueError('tensor ID/shape/layout contract mismatch for ' + role)
        if name in used or original[name].size != math.prod(shape):
            raise ValueError('duplicate role mapping or tensor size mismatch for ' + role)
        used.append(name)
        dtype = '<i2' if role == 'ftb' else ('i1' if role.endswith('w') else '<i4')
        a = quantize(original[name], s.get('scale'), s.get('rounding'), dtype)
        a = a.reshape(shape,order='F')
        if role == 'ftw':
            quantized[role] = a.T.copy()  # file rows are feature-major
        elif role == 'ftb':
            quantized[role] = a[:,0].copy()
        elif role.endswith('w'):
            quantized[role] = a.reshape((32, shape[0]//32, shape[1])).copy()
        else:
            quantized[role] = a.reshape((32, shape[0]//32)).copy()
    if set(used) != set(original):
        raise ValueError('unexpected checkpoint tensors: architecture/factoriser not accounted for')
    net = Net(l1,l2,l3,description,quantized)
    validate_bounds(net)
    return net


def validate_bounds(net: Net) -> None:
    t = net.tensors
    ft_bound = np.abs(t['ftb'].astype(np.int64)) + 32*np.max(np.abs(t['ftw'].astype(np.int64)),axis=0)
    if np.any(ft_bound > 32767):
        raise ValueError('feature transformer could overflow Forge int16 accumulator')
    for name in ('l1','l2','l3'):
        w = t[name+'w'].astype(np.int64)
        b = t[name+'b'].astype(np.int64)
        bound = np.abs(b) + 127*np.sum(np.abs(w),axis=2)
        if np.any(bound > 2**31-1):
            raise ValueError(name+' affine sum could overflow Forge int32 arithmetic')


def fc_hash(l1: int,l2: int,l3: int) -> int:
    previous = 0xEC42E90D ^ (2*l1)
    for width in (l2,l3,1):
        h = (0xCC03DAE4+width) & 0xffffffff
        h ^= previous >> 1
        h ^= (previous << 31) & 0xffffffff
        if width != 1:
            h = (h+0x538D24C7) & 0xffffffff
        previous = h
    return previous


def pad32(x: int) -> int:
    return (x+31)//32*32


def serialize(net: Net) -> bytes:
    desc = net.description.encode('utf-8')
    h = fc_hash(net.l1,net.l2,net.l3)
    out = bytearray(struct.pack('<III',VERSION,h^FEATURE_HASH^(2*net.l1),len(desc)))
    out.extend(desc)
    out.extend(struct.pack('<I',FEATURE_HASH^(2*net.l1)))
    out.extend(net.tensors['ftb'].astype('<i2').tobytes())
    out.extend(net.tensors['ftw'].astype('i1').tobytes())
    for stack in range(32):
        out.extend(struct.pack('<I',h))
        for layer in ('l1','l2','l3'):
            out.extend(net.tensors[layer+'b'][stack].astype('<i4').tobytes())
            w = net.tensors[layer+'w'][stack]
            padded = np.zeros((w.shape[0],pad32(w.shape[1])),dtype='i1')
            padded[:,:w.shape[1]] = w
            out.extend(padded.tobytes())
    return bytes(out)


def parse_fen(fen: str) -> tuple[list[tuple[int,int,int]],int]:
    fields = fen.strip().split()
    if len(fields)!=6 or fields[1] not in ('w','b'):
        raise ValueError('full six-field FEN required')
    if fields[2]!='-' and (not re.fullmatch(r'K?Q?k?q?', fields[2]) or not fields[2]):
        raise ValueError('invalid castling field')
    if fields[3]!='-' and not re.fullmatch(r'[a-h][36]',fields[3]):
        raise ValueError('invalid en passant field')
    if not fields[4].isdigit() or not fields[5].isdigit() or int(fields[5])<1:
        raise ValueError('invalid FEN clocks')
    rows=fields[0].split('/')
    if len(rows)!=8:
        raise ValueError('FEN must contain eight ranks')
    board=[]
    for rank,text in enumerate(rows):
        file=0
        for c in text:
            if c in '12345678': file+=int(c)
            elif c in 'PNBRQKpnbrqk':
                if file>=8: raise ValueError('rank exceeds eight files')
                board.append((0 if c.isupper() else 1,'pnbrqk'.index(c.lower()),(7-rank)*8+file));file+=1
            else: raise ValueError('invalid FEN piece/run')
        if file!=8: raise ValueError('rank does not span eight files')
    if not 2<=len(board)<=32 or any(sum(c==side and p==5 for c,p,_ in board)!=1 for side in (0,1)):
        raise ValueError('reference requires two kings and at most 32 occupied squares')
    return board,0 if fields[1]=='w' else 1


def feature_indices(board: list[tuple[int,int,int]],side: int) -> list[int]:
    king = next(s for c,p,s in board if c==side and p==5)
    flip = (56 if side else 0) ^ (7 if king%8<4 else 0)
    oriented = king^flip
    king_bucket = (7-oriented//8)*4+(7-oriented%8)
    state=2 if any(c!=side and p==4 for c,p,_ in board) else int(any(p in (3,4) for _,p,_ in board))
    bucket=state*32+king_bucket
    return sorted(bucket*704+min(2*p+int(c!=side),10)*64+(square^flip) for c,p,square in board)


def stack_index(board: list[tuple[int,int,int]],side: int) -> int:
    return ((len(board)-1)//4)*4+2*int(any(c==side and p==4 for c,p,_ in board))+int(any(c!=side and p==4 for c,p,_ in board))


def trunc_div(n: int,d: int) -> int:
    return (-1 if n<0 else 1)*(abs(n)//d)


def forward_trace(net: Net,fen: str) -> tuple[int,int,np.ndarray]:
    board,side=parse_fen(fen);t=net.tensors;acts=[]
    for pov in (side,1-side):
        acc=t['ftb'].astype(np.int64)+np.sum(t['ftw'][feature_indices(board,pov)].astype(np.int64),axis=0)
        clipped=np.clip(acc,0,255);half=net.l1//2
        acts.append((clipped[:half]*clipped[half:])>>9)
    ft=np.concatenate(acts);stack=stack_index(board,side)
    s1=t['l1b'][stack].astype(np.int64)+t['l1w'][stack].astype(np.int64)@ft
    x1=np.concatenate((np.minimum((s1*s1+20)>>21,127),np.clip(s1>>7,0,127)))
    s2=t['l2b'][stack].astype(np.int64)+t['l2w'][stack].astype(np.int64)@x1
    x=np.concatenate((x1,np.minimum((s2*s2+5)>>19,127),np.clip(s2>>6,0,127)))
    s3=int(t['l3b'][stack,0])+int(t['l3w'][stack,0].astype(np.int64)@x)
    total=s3+int(s1[-2])-int(s1[-1])
    return trunc_div(total*19200,32768),stack,x


def evaluate(net: Net,fen: str) -> int:
    return forward_trace(net,fen)[0]


def corrupt_active_weight(net: Net,payload: bytes,fen: str) -> tuple[bytes,dict]:
    before,stack,x=forward_trace(net,fen)
    column=int(np.argmax(x))
    if x[column]==0: raise ValueError('chosen FEN has no active output feature; select another FEN')
    old=int(net.tensors['l3w'][stack,0,column]);new=127 if old<=0 else -128
    header=12+len(net.description.encode('utf-8'))+4+2*net.l1+FEATURES*net.l1
    stackbytes=4+4*net.l2+net.l2*pad32(net.l1)+4*net.l3+net.l3*pad32(2*net.l2)+4+pad32(2*net.l2+2*net.l3)
    offset=header+(stack+1)*stackbytes-pad32(2*net.l2+2*net.l3)+column
    mutated=bytearray(payload)
    if mutated[offset] != old%256: raise ValueError('file weight offset does not match checkpoint')
    mutated[offset]=new%256
    # Include the skip term through an isolated copied tensor, without changing original.
    changed_t={k:v.copy() for k,v in net.tensors.items()}
    changed_t['l3w'][stack,0,column]=new
    after=evaluate(Net(net.l1,net.l2,net.l3,net.description,changed_t),fen)
    if before==after: raise ValueError('selected corruption does not change raw score')
    return bytes(mutated),{'kind':'single_output_weight_byte','stack':stack,'column':column,'byte_offset':offset,'old':old,'new':new,'raw_before':before,'raw_after':after}


def compare_eval_lines(reference: Iterable[str],native: Iterable[str]) -> int:
    left=list(reference);right=list(native)
    if not left or len(left)!=len(right): raise ValueError('empty parity corpus or output line count mismatch')
    for row,(a,b) in enumerate(zip(left,right),1):
        try:
            aa=tuple(map(int,a.split()));bb=tuple(map(int,b.split()))
        except ValueError as e: raise ValueError(f'non-integer parity output at row {row}') from e
        if len(aa)!=2 or len(bb)!=2 or aa!=bb or aa[1]!=trunc_div(aa[0],16):
            raise ValueError(f'parity mismatch row {row}: reference={a.strip()} native={b.strip()}')
    return len(left)


def create_fixture(out: Path,seed: int=19) -> None:
    """NON-TRAINED deterministic fixture, never labelled a Bullet smoke checkpoint."""
    out.mkdir(exist_ok=False,parents=True)
    l1,l2,l3=64,32,32;rng=np.random.default_rng(seed)
    manifest={'schema':1,'architecture':ARCH,'usize_bytes':8,'bullet_commit':BULLET_COMMIT,
              'l1':l1,'l2':l2,'l3':l3,'description':'NON-TRAINED original exporter contract fixture',
              'provenance':'synthetic format fixture; not produced by Bullet training','seed':seed,'tensors':{}}
    with (out/'weights.bin').open('xb') as f:
        for role,shape in shapes(l1,l2,l3).items():
            if role=='ftb': a=rng.integers(80,180,size=shape,dtype=np.int32)
            elif role.endswith('w'): a=rng.integers(-5,6,size=shape,dtype=np.int32)
            else: a=rng.integers(-4096,4097,size=shape,dtype=np.int32)
            f.write(role.encode()+b'\n'+struct.pack('<Q',math.prod(shape)))
            f.write(a.astype('<f4').tobytes(order='F'))
            manifest['tensors'][role]={'id':role,'shape':list(shape),'layout':'column_major','scale':1,'rounding':'truncate'}
    manifest['checkpoint_sha256']=sha256(out/'weights.bin')
    write_new(out/'manifest.json',(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for command in ('export','reference','corrupt'):
        p=sub.add_parser(command);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
        if command!='export':p.add_argument('--fens',type=Path,required=True)
    p=sub.add_parser('fixture');p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,default=19)
    p=sub.add_parser('compare');p.add_argument('--reference',type=Path,required=True);p.add_argument('--native',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=='fixture':
            create_fixture(args.out,args.seed);print(json.dumps({'status':'FIXTURE_ONLY_NOT_TRAINED','out':str(args.out)}));return 0
        if args.command=='compare':
            n=compare_eval_lines(args.reference.read_text().splitlines(),args.native.read_text().splitlines());print(json.dumps({'status':'PASS','positions':n,'mismatches':0}));return 0
        net=load_quantized(args.checkpoint,args.manifest)
        if args.command=='export':
            payload=serialize(net);write_new(args.out,payload)
            print(json.dumps({'status':'EXPORTED','bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'checkpoint_sha256':sha256(args.checkpoint),'architecture':ARCH}));return 0
        if args.command=='reference':
            count=0
            with args.fens.open(encoding='utf-8') as f,args.out.open('x',encoding='ascii',newline='\n') as out:
                for line in f:
                    fen=line.split('|',1)[0].strip()
                    if not fen:raise ValueError('blank FEN row is not allowed')
                    raw=evaluate(net,fen);out.write(f'{raw} {trunc_div(raw,16)}\n');count+=1
            if not count:raise ValueError('empty parity corpus')
            print(json.dumps({'status':'REFERENCE','positions':count,'fens_sha256':sha256(args.fens),'output_sha256':sha256(args.out)}));return 0
        with args.fens.open(encoding='utf-8') as f:fen=f.readline().split('|',1)[0].strip()
        payload,record=corrupt_active_weight(net,serialize(net),fen);write_new(args.out,payload)
        print(json.dumps(record,sort_keys=True));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
