#!/usr/bin/env python3
"""Prepare bounded original FBS1 input for the MIT-only Bullet GPU smoke driver.

FBS1 is this project's mapper interchange, NOT bulletformat or binpack. It stores
both lock feature lists plus exact STM HCE/score labels from aligned FPOS/FHCE/FEN.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'/'data'))
from forge_pos import PosReader, file_hash, match_fen
import export_forge as common


def encode_row(row,fen):
    board,side=common.parse_fen(fen)
    features=[]
    for perspective in (side,1-side):
        values=[((int(c!=perspective)*6+p)*64)+(sq^(56 if perspective else 0)) for c,p,sq in sorted(board,key=lambda x:x[2])]
        if not 2<=len(values)<=32 or len(set(values))!=len(values):raise ValueError('invalid active features')
        features.extend(values+[-1]*(32-len(values)))
    if row.hce is None:raise ValueError('real HCE labels required, never assume zero')
    return struct.pack('<64hff',*features,float(row.hce),float(row.score))


def prepare(pos:Path,hce:Path,fen:Path,out:Path,rows:int,start:int=0):
    if not 1<=rows<=65536 or start<0:raise ValueError('rows1..65536 and nonnegative start required')
    source={name:{'path':str(path),'sha256':file_hash(path),'bytes':path.stat().st_size} for name,path in [('pos',pos),('hce',hce),('fen',fen)]}
    out.mkdir(parents=True,exist_ok=False)
    with PosReader(pos,hce) as data,fen.open(encoding='utf-8') as fs,(out/'input.fbs').open('xb') as target:
        if start+rows>data.n:raise ValueError('slice exceeds source')
        for _ in range(start):
            if not fs.readline():raise ValueError('short FEN sidecar')
        target.write(b'FBS1'+struct.pack('<Q',rows))
        for i in range(start,start+rows):
            row=data.row(i);text=fs.readline()
            if not text:raise ValueError('short FEN sidecar')
            f=match_fen(row,text);target.write(encode_row(row,f))
    for name,path in [('pos',pos),('hce',hce),('fen',fen)]:
        if file_hash(path)!=source[name]['sha256']:raise ValueError('source changed during read')
    m={'status':'SEALED_BOUNDED_SMOKE_INPUT','format':'FBS1 custom Bullet mapper, not bulletformat/binpack','rows':rows,'start_zero_based':start,
       'record_bytes':136,'layout':'FBS1, uint64LEcount, repeated32xi16STM+32xi16NTM+f32LEHCE+f32LEscore',
       'input_sha256':file_hash(out/'input.fbs'),'sources':source,'labels':'original STM score and matched STM HCE; no WDL blend','full_epoch_scope':'only this saved slice'}
    with (out/'manifest.json').open('x',encoding='utf-8') as f:json.dump(m,f,indent=2,sort_keys=True);f.write('\n')
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('pos','hce','fen','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--rows',type=int,default=8192);p.add_argument('--start',type=int,default=0);a=p.parse_args()
    try:print(json.dumps(prepare(a.pos,a.hce,a.fen,a.out,a.rows,a.start),sort_keys=True));return 0
    except (ValueError,OSError) as e:print('ERROR: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
