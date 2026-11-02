#!/usr/bin/env python3
"""Verify every FPOS row against an original full-FEN text sidecar.
IDEA_SOURCE: Forge's FPOS layout and user-provided record-order contract.
Creates a new evidence directory; never edits source data.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from forge_pos import PosReader, aligned_records, file_hash

def verify(pos, sidecar, out):
    out.mkdir(parents=True, exist_ok=False)
    started=time.monotonic()
    report={'status':'RUNNING','started_utc':datetime.now(timezone.utc).isoformat(),
            'pos':str(pos.resolve()),'sidecar':str(sidecar.resolve()),'rows_verified':0,
            'comparison':'every board nibble, STM, signed STM score, White game result; full six-field FEN syntax and exact total count'}
    def progress():
        with (out/'progress.json').open('w',encoding='utf8') as f:
            json.dump(report,f,indent=2);f.write('\n')
    try:
        report['input_sha256']={str(p.resolve()):file_hash(p) for p in (pos,sidecar)}
        progress()
        with PosReader(pos) as reader:
            report['declared_rows']=reader.n
            for row,fen in aligned_records(reader,sidecar):
                report['rows_verified']+=1
                if report['rows_verified']%100000==0:progress()
        for name,digest in report['input_sha256'].items():
            if file_hash(name)!=digest:raise ValueError('input changed during validation: '+name)
        report.update(status='PASS',wall_seconds=time.monotonic()-started,
                      finished_utc=datetime.now(timezone.utc).isoformat())
        progress()
        with (out/'summary.json').open('x',encoding='utf8') as f:
            json.dump(report,f,indent=2);f.write('\n')
        return report
    except BaseException as e:
        report.update(status='FAIL',error=repr(e),wall_seconds=time.monotonic()-started)
        progress()
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('pos','sidecar','out'):p.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(verify(**vars(p.parse_args())),indent=2))
