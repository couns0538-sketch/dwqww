#!/usr/bin/env python3
"""Cold fixed-node Forge relabeling into new FPOS/FHCE files.
IDEA_SOURCE: user deeper-label task and this project's exact FPOS/FHCE contract.
"""
from __future__ import annotations
import argparse, hashlib, json, os, time
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from forge_probe import ProbePool, sha256

@dataclass
class Config:
    pos: Path
    sidecar: Path | None
    out: Path
    probe: Path
    nodes: int=65536
    workers: int=1
    hash_mb: int=1
    start: int=0
    count: int=4096
    stride: int=1
    batch_size: int=128
    allow_reconstructed: bool=False
    stem: str='relabeled'
    sidecar_origin: str='auto'

def require(ok,message):
    if not ok:raise ValueError(message)

def cpu_total():
    import resource
    return sum((resource.getrusage(w).ru_utime+resource.getrusage(w).ru_stime) for w in (resource.RUSAGE_SELF,resource.RUSAGE_CHILDREN))

def run(c:Config,pool_factory=ProbePool):
    from forge_pos import PosReader, PosWriter, Record, text_record, board_to_fen, RECONSTRUCTION_POLICY
    require(c.nodes>0 and 1<=c.workers<=3 and c.hash_mb>0,'invalid probe resources')
    require(c.start>=0 and 0<c.count<=100000 and c.stride>0 and 0<c.batch_size<=4096,'invalid slice: count1..100000, batch1..4096; use separate slices for larger jobs')
    require(c.sidecar is not None or c.allow_reconstructed,'full FEN sidecar required unless --allow-reconstructed')
    require(c.sidecar_origin in ('auto','original_full_fen','reconstructed'),'invalid sidecar origin')
    c.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();parent_cpu=time.process_time();total_cpu_start=cpu_total() if os.name!='nt' else None
    report={'status':'RUNNING','started_utc':datetime.now(timezone.utc).isoformat(),'config':{k:str(v) if isinstance(v,Path) else v for k,v in vars(c).items()},'selected':0,'exact_label_rows':0,'reconstructed_label_rows':0,'score_changed':0,'sum_absolute_score_change':0,'search_nodes':0,'query_cpu_ns':0,'depth_histogram':{},'claim':'Deeper-budget labels, not demonstrated stronger labels or Elo. Original teacher budget may be unknown.'}
    def progress(): (c.out/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
    progress();writer=None
    try:
        inputs={'pos':{'path':str(c.pos.resolve()),'sha256':sha256(c.pos)}}
        if c.sidecar is not None:inputs['sidecar']={'path':str(c.sidecar.resolve()),'sha256':sha256(c.sidecar)}
        report['inputs']=inputs;report['probe_sha256']=sha256(c.probe)
        selected=[];records=[]
        with PosReader(c.pos) as reader:
            last=c.start+(c.count-1)*c.stride
            require(last<reader.n,'slice extends beyond input record count')
            report['input_record_count']=reader.n
            indices=iter(range(c.start,last+1,c.stride));wanted=next(indices,None)
            if c.sidecar is not None:
                lines=0;origins=set()
                inherited=None
                source_summary=c.sidecar.parent/'summary.json'
                if source_summary.is_file():
                    inherited=json.loads(source_summary.read_text()).get('state_origin')
                    inputs['source_summary']={'path':str(source_summary.resolve()),'sha256':sha256(source_summary)}
                if inherited and 'reconstructed' in inherited:
                    require(c.sidecar_origin!='original_full_fen','reconstructed sidecar cannot be promoted to original state')
                with c.sidecar.open(encoding='utf8') as source:
                    for i,line in enumerate(source):
                        require(i<reader.n,'sidecar longer than POS');lines=i+1
                        if i!=wanted:continue
                        record=reader.row(i)
                        if '|' in line:
                            supplied,fen=text_record(line)
                            require((supplied.board,supplied.score,supplied.meta)==(record.board,record.score,record.meta),f'sidecar record mismatch at{i}')
                            origins.add('reconstructed' if c.sidecar_origin=='reconstructed' or (inherited and 'reconstructed' in inherited) else 'original_full_fen')
                        else:
                            # A relabeler-emitted .fen sidecar has no old score/result; verify its feature state.
                            fen=line.strip();white_result=(record.meta>>1)/2
                            supplied,_=text_record(f'{fen} | {record.score} | {white_result}')
                            require((supplied.board,supplied.meta&1)==(record.board,record.meta&1),f'FEN state mismatch at{i}')
                            require(c.sidecar_origin!='auto','FEN-only sidecar requires explicit --sidecar-origin original_full_fen or reconstructed')
                            origins.add(c.sidecar_origin)
                        selected.append((i,fen));records.append(record);wanted=next(indices,None)
                require(lines==reader.n,'sidecar shorter than POS')
                require(len(origins)==1,'mixed sidecar state origin is not supported')
                report['state_origin']='reconstructed_no_castling_no_ep_clock0' if origins=={'reconstructed'} else 'original_full_fen'
                report['alignment_scope']='all sidecar row count; selected board/STM/score/result matches (full corpus audit is separate)'
            else:
                for i in range(c.start,last+1,c.stride):
                    record=reader.row(i);selected.append((i,board_to_fen(record,policy=RECONSTRUCTION_POLICY)));records.append(record)
                report['state_origin']='reconstructed_no_castling_no_ep_clock0'
            writer=PosWriter(c.out,c.stem,with_hce=True)
            with (c.out/'labels.jsonl').open('x',encoding='utf8') as labels:
                with pool_factory(c.probe,c.nodes,c.workers,c.out/'probe_logs',hash_mb=c.hash_mb) as pool:
                    for begin in range(0,len(selected),c.batch_size):
                        rows=selected[begin:begin+c.batch_size];answers=pool.map([(str(i),fen) for i,fen in rows],op='analyze')
                        require(len(rows)==len(answers),'native result count mismatch')
                        for offset,((index,fen),answer) in enumerate(zip(rows,answers)):
                            old=records[begin+offset]
                            require(answer.get('ok') is True and str(answer.get('id'))==str(index),'native failure/misalignment')
                            require(answer.get('terminal') is False and int(answer.get('depth',0))>=1,'terminal or incomplete search cannot be an exact searched label')
                            for field in ('score','hce','nodes','depth','cpu_ns'):require(type(answer.get(field)) is int,'invalid native '+field)
                            require(answer.get('analyzed') is True,'native result was not analyzed')
                            require(0<answer['nodes']<=c.nodes and answer['cpu_ns']>=0,'invalid native node/CPU bounds')
                            require(answer.get('nodes_limit')==c.nodes and answer.get('hash_mb')==c.hash_mb and answer.get('threads')==1,'native configuration differs from request')
                            require(' '.join(str(answer.get('fen','')).split())==' '.join(fen.split()),'native FEN differs from request')
                            score=answer['score'];hce=answer['hce']
                            require(-32767<=score<=32767 and -32767<=hce<=32767,'FPOS/FHCE score overflow')
                            writer.append(Record(old.board,score,old.meta,hce),fen=fen)
                            labels.write(json.dumps({'output_index':report['selected'],'input_index':index,'state_origin':report['state_origin'],'old_score_stm':old.score,'score_stm':score,'hce_stm':hce,'nodes_requested':c.nodes,'nodes':answer['nodes'],'depth':answer['depth'],'bestmove':answer['bestmove']},sort_keys=True)+'\n')
                            report['selected']+=1;report['score_changed']+=score!=old.score;report['sum_absolute_score_change']+=abs(score-old.score)
                            report['search_nodes']+=answer['nodes'];report['query_cpu_ns']+=answer['cpu_ns']
                            depth=str(answer['depth']);report['depth_histogram'][depth]=report['depth_histogram'].get(depth,0)+1
                        progress()
            require(report['selected']==c.count,'incomplete selected slice')
        for item in inputs.values():require(sha256(item['path'])==item['sha256'],'input changed during run')
        writer.close();writer=None
        report['exact_label_rows']=c.count if report['state_origin']=='original_full_fen' else 0
        report['reconstructed_label_rows']=c.count-report['exact_label_rows']
        report['wall_seconds']=time.monotonic()-started;report['parent_cpu_seconds']=time.process_time()-parent_cpu
        report['query_cpu_seconds']=report['query_cpu_ns']/1e9
        if total_cpu_start is not None:
            report['pipeline_cpu_seconds']=cpu_total()-total_cpu_start
            report['positions_per_core_hour']=c.count*3600/report['pipeline_cpu_seconds'] if report['pipeline_cpu_seconds']>0 else None
            report['cpu_accounting']='OS CPU seconds: this process plus reaped owned native children, includes orchestration'
        else:
            child_cpu=getattr(pool,'total_child_cpu_seconds',None)
            report['pipeline_cpu_seconds']=None if child_cpu is None else child_cpu+report['parent_cpu_seconds']
            report['positions_per_core_hour']=None if report['pipeline_cpu_seconds'] is None or report['pipeline_cpu_seconds']<=0 else c.count*3600/report['pipeline_cpu_seconds']
            report['cpu_accounting']='GetProcessTimes for all owned children plus Python process CPU' if child_cpu is not None else 'UNVERIFIED: child GetProcessTimes unavailable; query CPU not substituted as total'
        report['mean_absolute_score_change']=report['sum_absolute_score_change']/c.count
        report.update(status='SEALED',finished_utc=datetime.now(timezone.utc).isoformat())
        report['outputs']={suffix:sha256(c.out/(c.stem+suffix)) for suffix in ('.pos','.hce','.fen')}
        (c.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');progress()
        manifest={str(p.relative_to(c.out)):sha256(p) for p in sorted(c.out.rglob('*')) if p.is_file()}
        (c.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        return report
    except BaseException as e:
        report.update(status='FAILED_UNSEALED',error_type=type(e).__name__,error=str(e));progress()
        (c.out/'failure.json').write_text(json.dumps(report,indent=2)+'\n')
        raise
    finally:
        if writer is not None and hasattr(writer,'abort'):writer.abort()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('pos','out','probe'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sidecar',type=Path);p.add_argument('--allow-reconstructed',action='store_true')
    p.add_argument('--sidecar-origin',choices=('auto','original_full_fen','reconstructed'),default='auto')
    for name,default in [('nodes',65536),('workers',1),('hash-mb',1),('start',0),('count',4096),('stride',1),('batch-size',128)]:p.add_argument('--'+name,type=int,default=default)
    p.add_argument('--stem',default='relabeled');a=p.parse_args(argv)
    report=run(Config(**vars(a)));print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
