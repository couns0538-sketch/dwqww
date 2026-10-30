#!/usr/bin/env python3
"""Read-only scalar profile of original Forge FPOS + full-FEN text sidecar.
IDEA_SOURCE: Forge data-state omissions and user-requested source profiling.
No native queries, new filtering rules, board reconstruction or training.
"""
import argparse
import bisect
from collections import Counter
import hashlib
import json
import mmap
from pathlib import Path
import resource
import struct
import time


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def metadata(path):
    return {'original_path':str(path),'bytes':path.stat().st_size,'sha256':sha256(path)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pos',required=True,type=Path)
    p.add_argument('--sidecar',required=True,type=Path)
    p.add_argument('--expected-rows',type=int,default=10000000)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    inputs=[metadata(args.pos),metadata(args.sidecar)]
    started=time.monotonic();started_cpu=time.process_time()
    stm=Counter();result=Counter();cp=Counter();clocks=Counter();rights=Counter();ep=Counter()
    cp_ends=[-999,-499,-199,-99,0,1,100,200,500,1000]
    cp_labels=['<=-1000','-999..-500','-499..-200','-199..-100','-99..-1','0','1..99','100..199','200..499','500..999','>=1000']
    halfmove_ends=[10,30,50,70,90,100]
    halfmove_labels=['0-9','10-29','30-49','50-69','70-89','90-99','100+']
    labels={'0':0,'0.0':0,'0.5':1,'1':2,'1.0':2}
    total=0; min_cp=None;max_cp=None; max_halfmove=0
    with args.pos.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as binary:
        if len(binary)<16:raise ValueError('Truncated FPOS')
        magic,version,n=struct.unpack_from('<4sIQ',binary)
        if (magic,version)!=(b'FPOS',1) or n!=args.expected_rows or len(binary)!=16+35*n:
            raise ValueError('Unexpected FPOS header/count/size')
        score_offset=16+32*n;meta_offset=16+34*n
        with args.sidecar.open('rt',encoding='ascii') as text:
            for index,line in enumerate(text):
                if index>=n:raise ValueError('Extra sidecar row')
                fields=line.strip().split('|')
                if len(fields)!=3:raise ValueError(f'Malformed sidecar row {index}')
                fen,score_text,result_text=(x.strip() for x in fields)
                fen_fields=fen.split()
                if len(fen_fields)!=6 or fen_fields[1] not in ('w','b'):
                    raise ValueError(f'Malformed FEN state row {index}')
                score=int(score_text);white_code=labels[result_text]
                is_black=int(fen_fields[1]=='b')
                if struct.unpack_from('<h',binary,score_offset+2*index)[0]!=score or binary[meta_offset+index]!=(white_code<<1)|is_black:
                    raise ValueError(f'Original scalar label alignment mismatch row {index}')
                halfmove=int(fen_fields[4])
                if halfmove<0:raise ValueError('Negative halfmove clock')
                stm[fen_fields[1]]+=1;result[('0','0.5','1')[white_code]]+=1
                cp[cp_labels[bisect.bisect_right(cp_ends,score)]]+=1
                clocks[halfmove_labels[bisect.bisect_right(halfmove_ends,halfmove)]]+=1
                rights['empty' if fen_fields[2]=='-' else 'nonempty']+=1
                ep['empty' if fen_fields[3]=='-' else 'nonempty']+=1
                min_cp=score if min_cp is None else min(min_cp,score)
                max_cp=score if max_cp is None else max(max_cp,score)
                max_halfmove=max(max_halfmove,halfmove);total+=1
                if total%1000000==0:print(json.dumps({'rows':total,'elapsed_seconds':time.monotonic()-started}),flush=True)
    if total!=args.expected_rows:raise ValueError('Sidecar count mismatch')
    after=[metadata(args.pos),metadata(args.sidecar)]
    if inputs!=after:raise ValueError('Input changed during profiling')
    def distribution(counter,order):
        return {key:{'count':counter[key],'fraction':counter[key]/total} for key in order}
    result_record={'status':'PASS_READ_ONLY_SOURCE_PROFILE','rows':total,'scalar_alignment_rows':total,
        'inputs':inputs,'unchanged_after':True,'source_script_sha256':sha256(Path(__file__)),
        'stm':distribution(stm,['w','b']),'white_result':distribution(result,['0','0.5','1']),
        'source_score_stm_cp':distribution(cp,cp_labels),'source_score_min_cp':min_cp,'source_score_max_cp':max_cp,
        'halfmove_clock':distribution(clocks,halfmove_labels),'maximum_halfmove_clock':max_halfmove,
        'castling_rights':distribution(rights,['empty','nonempty']),'en_passant_target':distribution(ep,['empty','nonempty']),
        'wall_seconds_from_initial_hash_completion':time.monotonic()-started,
        'actual_process_cpu_seconds_from_initial_hash_completion':time.process_time()-started_cpu,
        'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope':['All 10M scalar labels checked against original FPOS; full board/FEN alignment was validated separately.',
                 'FPOS does not encode rights, en passant or clocks; these counts come from the original full-FEN sidecar.',
                 'Presence of rights or an en-passant target does not imply a currently legal castle/capture.',
                 'No native search, filtering, reconstruction or training; no strength or gain conclusion.']}
    for counts in (stm,result,cp,clocks,rights,ep):
        if sum(counts.values())!=total:raise ValueError('Distribution total mismatch')
    with args.output.open('x') as f:json.dump(result_record,f,indent=2);f.write('\n')
    print(json.dumps(result_record,indent=2))


if __name__=='__main__':main()
