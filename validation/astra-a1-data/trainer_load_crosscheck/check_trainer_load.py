#!/usr/bin/env python3
"""Compare unchanged v3b read-only mmap columns against Forge's shared reader.
IDEA_SOURCE: same-project producer/trainer record contract; no training executed.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np
import torch


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--paired-pos',type=Path,nargs=2,required=True)
    parser.add_argument('--original-pos',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    repo=args.repo.resolve(strict=True)
    sys.path.insert(0,str(repo/'tools/data'))
    from forge_pos import PosReader
    trainer=repo/'tools/nnue/train_resid_v3b.py'
    shared=repo/'tools/data/forge_pos.py'
    files=[trainer,shared,Path(__file__).resolve(),args.original_pos.resolve(strict=True)]
    for p in args.paired_pos:files.extend([p.resolve(strict=True),p.with_suffix('.hce').resolve(strict=True)])
    before={str(p):{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in files}
    spec=importlib.util.spec_from_file_location('forge_unchanged_v3b_load_check',trainer)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    started=time.monotonic();reports=[]
    for number,pos in enumerate(args.paired_pos+[args.original_pos]):
        paired=number<2;pos=pos.resolve(strict=True);hce=pos.with_suffix('.hce') if paired else None
        loaded=module.load_set_mmap([str(pos)],str(pos.parent) if paired else None,need_hce=paired)
        with PosReader(pos,hce) as reader:
            expected_n=256 if paired else 10000000
            if reader.n!=expected_n or loaded['n']!=expected_n:raise ValueError('Unexpected record count')
            indices=np.arange(256,dtype=np.int64) if paired else np.array([i*(reader.n-1)//255 for i in range(256)],dtype=np.int64)
            values={key:loaded[key][indices] for key in ('boards','score','meta','hce')}
            mismatches=[]
            for j,index in enumerate(indices):
                row=reader.row(int(index))
                if values['boards'][j].tobytes()!=row.board:mismatches.append([int(index),'board'])
                if int(values['score'][j])!=row.score:mismatches.append([int(index),'score'])
                if int(values['meta'][j])!=row.meta:mismatches.append([int(index),'meta'])
                if paired and int(values['hce'][j])!=row.hce:mismatches.append([int(index),'hce'])
            if mismatches:raise ValueError('Trainer/shared-reader mismatches: '+repr(mismatches))
            if not paired and np.any(values['hce']):raise ValueError('Unexpected no-HCE placeholder')
            reports.append({'input_id':f'relabel_{number+1}' if paired else 'original_10m',
                'original_path':str(pos),'records_declared':reader.n,'rows_compared':256,
                'row_indices':[int(i) for i in indices],'scope':'every row' if paired else 'strided 256 including endpoints; not all 10M rows',
                'fields_compared':['board','score','meta']+(['hce'] if paired else []),'mismatches':0,
                'hce_status':'compared against real paired FHCE' if paired else 'UNVERIFIED: original FHCE unavailable; trainer ZeroMap placeholder is not a label',
                'read_only_mappings':all(not part.flags.writeable for key in ('boards','score','meta') for part in loaded[key].parts)})
    for path,item in before.items():
        p=Path(path)
        if p.stat().st_size!=item['bytes'] or sha256(p)!=item['sha256']:raise ValueError('Input/source mutated: '+path)
    report={'status':'PASS_MMAP_FORMAT_CROSSCHECK','trainer_relative_path':str(trainer.relative_to(repo)),
            'shared_reader_relative_path':str(shared.relative_to(repo)),
            'versions':{'python':sys.version,'numpy':np.__version__,'torch':torch.__version__,'torch_cuda_build':torch.version.cuda},
            'inputs_and_sources':before,'datasets':reports,'unchanged_after':True,
            'loader_and_comparison_wall_seconds':time.monotonic()-started,
            'process_peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'limitations':['No training or native search performed.','10M input is mapped read-only; only 256 rows cross-compared.','The existing loader scans the 10M metadata column for its invalid sentinel; this is not full record validation.']}
    with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'datasets':[{k:v for k,v in row.items() if k not in ('row_indices','original_path')} for row in reports],'peak_rss_kib':report['process_peak_rss_kib_linux']},indent=2))


if __name__=='__main__':main()
