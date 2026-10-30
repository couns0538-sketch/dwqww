#!/usr/bin/env python3
"""Independent read-only audit of sealed Forge filter evidence.
IDEA_SOURCE: frozen Forge filter/IPC/FPOS contracts, original evidence and user rules.
No engine invocation; output is restricted to a new directory outside the source run.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
import gzip
import hashlib
import heapq
import json
import math
import mmap
from pathlib import Path
import re
import resource
import sqlite3
import struct
import sys
import time

DECISION_HEADER='input_index\tdecision\tbestmove\tteacher_score\tnodes'
KEPT_HEADER='output_index\tinput_index\tinput_file\tinput_row\tstate_origin\tteacher_nodes\tteacher_depth\tteacher_score\tbestmove\toriginal_score'
OLD_POLICY=['holdout','disagreement','exact_duplicate','near_duplicate','in_check','terminal','bestmove_capture','bestmove_promotion']
NEW_POLICY=OLD_POLICY[:6]+['teacher_incomplete']+OLD_POLICY[6:]
MOVE=re.compile(r'[a-h][1-8][a-h][1-8][nbrq]?\Z')
MASK=(1<<256)-1


def require(ok,message):
    if not ok:raise ValueError(message)


def stamp(path):
    s=path.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]


def digest(path):
    h=hashlib.sha256();m=hashlib.md5();n=0
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block);m.update(block);n+=len(block)
    return {'bytes':n,'sha256':h.hexdigest(),'md5':m.hexdigest()}


def read_json(path):
    with path.open() as f:return json.load(f)


def write_json(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


class Columns:
    """Independent read-only column offsets; original payload compared byte for byte."""
    def __init__(self,path,magic,unit,stack):
        f=stack.enter_context(path.open('rb'))
        self.map=stack.enter_context(mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ))
        require(len(self.map)>=16,'truncated column header')
        found,version,self.n=struct.unpack_from('<4sIQ',self.map)
        require(found==magic and version==1 and len(self.map)==16+self.n*unit,'column magic/version/size mismatch')
    def row(self,index):
        require(0<=index<self.n,'column row out of range')
        return (self.map[16+32*index:16+32*(index+1)],
                struct.unpack_from('<h',self.map,16+32*self.n+2*index)[0],self.map[16+34*self.n+index])
    def hce(self,index):return struct.unpack_from('<h',self.map,16+2*index)[0]


def validate_response(r,identifier,fen,config):
    require(isinstance(r,dict) and r.get('id')==str(identifier),'native response ID mismatch')
    require(r.get('operation')=='filter' and r.get('ok') is True,'native operation/ok failure')
    require(isinstance(r.get('fen'),str) and ' '.join(r['fen'].split())==fen,'native request/response FEN mismatch')
    for key,value in [('nodes_limit',config['nodes']),('hash_mb',config['hash_mb']),('threads',1)]:
        require(type(r.get(key)) is int and r[key]==value,'native configuration mismatch: '+key)
    for key in ('in_check','terminal','analyzed','capture','promotion'):
        require(type(r.get(key)) is bool,'native boolean missing: '+key)
    for key in ('nodes','depth','cpu_ns','process_cpu_ns','elapsed_ns'):
        require(type(r.get(key)) is int and r[key]>=0,'invalid native integer: '+key)
    require(r['nodes']<=config['nodes'],'native node budget exceeded')
    require(r['process_cpu_ns']>=r['cpu_ns'],'native CPU accounting inconsistent')
    require(type(r.get('hce')) is int and -32767<=r['hce']<=32767,'native HCE invalid')
    reason=r.get('terminal_reason')
    require((r['terminal'] and reason in ('checkmate','stalemate','fifty_move','insufficient_material')) or
            (not r['terminal'] and reason==''),'native terminal status inconsistent')
    if r['in_check'] or r['terminal']:
        require(not r['analyzed'] and r.get('score') is None and r.get('bestmove') is None and
                r['nodes']==0 and r['depth']==0 and not r['capture'] and not r['promotion'],'native skipped root contract')
        return 'in_check' if r['in_check'] else 'terminal'
    if not r['analyzed']:
        require(r.get('analysis_status')=='insufficient_budget' and r['depth']==0 and
                r.get('score') is None and r.get('bestmove') is None and
                not r['capture'] and not r['promotion'],'native incomplete teacher contract')
        return 'teacher_incomplete'
    require(r['depth']>=1 and r['nodes']>0,'native completed-iteration contract')
    require(type(r.get('score')) is int and -32000<=r['score']<=32000,'native score invalid')
    require(isinstance(r.get('bestmove'),str) and MOVE.fullmatch(r['bestmove']) is not None,'native bestmove invalid')
    return 'bestmove_capture' if r['capture'] else 'bestmove_promotion' if r['promotion'] else 'kept'


def native_stream(worker,config,probe_sha,worker_reports):
    receipt=read_json(worker/'process.json')
    require(receipt.get('returncode')==0 and receipt.get('binary_unchanged') is True,'native worker did not exit cleanly')
    require(receipt.get('binary_sha256')==probe_sha,'native worker binary hash mismatch')
    require(receipt.get('argv')==[config['probe'],'--nodes',str(config['nodes']),'--hash-mb',str(config['hash_mb'])],
            'native worker argv mismatch')
    count=0;cpu=0;previous=-1;previous_process_cpu=0;statuses=Counter()
    with gzip.open(worker/'requests.tsv.gz','rt',encoding='ascii') as requests,gzip.open(worker/'responses.jsonl.gz','rt',encoding='ascii') as responses:
        while True:
            request=requests.readline();response=responses.readline()
            require(bool(request)==bool(response),'native request/response count mismatch')
            if not request:break
            require(request.endswith('\n') and response.endswith('\n') and len(response)<=131072,'native frame invalid')
            parts=request.rstrip('\n').split('\t')
            require(len(parts)==3 and parts[0].isdigit() and parts[1]=='filter','native request schema invalid')
            identifier=int(parts[0]);fen=' '.join(parts[2].split())
            require(str(identifier)==parts[0] and identifier>previous,'native request IDs not strictly increasing')
            r=json.loads(response);status=validate_response(r,identifier,fen,config)
            require(r['process_cpu_ns']>=previous_process_cpu,'native process CPU moved backwards')
            previous=identifier;previous_process_cpu=r['process_cpu_ns'];cpu+=r['cpu_ns'];count+=1;statuses[status]+=1
            yield identifier,r,fen,status
    require(count==receipt.get('successful_requests')==receipt.get('response_count'),'native process receipt count mismatch')
    require(cpu==receipt.get('reported_query_cpu_ns'),'native process receipt CPU mismatch')
    worker_reports.append({'worker':worker.name,'responses_checked':count,'cpu_ns_sum':cpu,'statuses':dict(statuses),
                           'stderr_bytes':(worker/'stderr.bin').stat().st_size,'exit_code':receipt['returncode']})


def audit(args,report):
    run=args.run_dir.resolve(strict=True);out=args.out.resolve()
    require(run!=out and run not in out.parents,'audit output must be outside sealed source')
    require((run/'summary.json').is_file() and (run/'manifest.json').is_file(),'unsealed: summary or manifest missing')
    require(not (run/'failure.json').exists(),'source contains failure.json')
    summary=read_json(run/'summary.json');manifest=read_json(run/'manifest.json');config=summary['config']
    require(summary.get('status')=='SEALED','run status is not SEALED')
    policy=summary['policy_order'];require(policy in (OLD_POLICY,NEW_POLICY),'unknown frozen policy order')
    require(set(summary['rules'])==set(policy),'rule schema mismatch')
    n=summary['input_rows'];kept=summary['kept'];require(type(n) is int and n>=0 and type(kept) is int and 0<=kept<=n,'bad summary counts')
    if args.expected_rows is not None:require(n==args.expected_rows,'unexpected selected row count')
    started=time.monotonic();stamps={};digests={};inode_cache={}
    # Ignore serialized absolute paths: the manifest's relative keys are authoritative for relocation.
    for name,expected in manifest.items():
        rel=Path(name);require(not rel.is_absolute() and '..' not in rel.parts,'unsafe manifest key')
        path=run/rel;require(path.is_file() and not path.is_symlink(),'manifest file missing or symlink: '+name)
        current_stamp=stamp(path);stamps[str(path)]=current_stamp;inode=tuple(current_stamp)
        if inode not in inode_cache:inode_cache[inode]=digest(path)
        observed=inode_cache[inode];require(all(observed[k]==expected[k] for k in ('bytes','sha256','md5')),'manifest hash mismatch: '+name)
        digests[name]=observed
    actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
    require(not (actual-set(manifest)-{'manifest.json','manifest.json.pending'}),'unmanifested source files')
    for name in ('summary.json','progress.json','decisions.tsv.gz','kept_rows.tsv','position_index.sqlite'):
        require(name in manifest,'required file absent from manifest: '+name)
    require(read_json(run/'progress.json')==summary,'final progress/summary disagreement')
    stamps[str(run/'manifest.json')]=stamp(run/'manifest.json')
    report['manifest']={'files_checked':len(manifest),'sha256':digest(run/'manifest.json')['sha256']}
    report['frozen_implementation']='UNVERIFIED_NOT_SUPPLIED'
    if args.frozen_dir:
        checked={}
        for name,expected in summary['implementation'].items():
            path=args.frozen_dir/name;observed=digest(path)
            require(all(observed[k]==expected[k] for k in ('bytes','sha256','md5')),'frozen implementation mismatch: '+name)
            checked[name]=observed
        report['frozen_implementation']=checked
    if args.verify_external_hashes:
        verified=[]
        for expected in [v for item in summary['inputs'] for v in item.values()]+summary['holdouts']+[summary['probe']]:
            path=Path(expected['path']);observed=digest(path)
            require(all(observed[k]==expected[k] for k in ('bytes','sha256','md5')),'external input/probe hash mismatch: '+str(path))
            stamps[str(path)]=stamp(path);verified.append({'path':str(path),**observed})
        report['external_hashes']=verified
    else:report['external_hashes']='UNVERIFIED_THIS_AUDIT; selected original payload/state still compared'
    worker_reports=[];workers=sorted((run/'probe_logs').glob('worker-*'))
    require([p.name for p in workers]==[f'worker-{i}' for i in range(config['workers'])],'worker directory set mismatch')
    native=heapq.merge(*(native_stream(w,config,summary['probe']['sha256'],worker_reports) for w in workers),key=lambda row:row[0])
    current=next(native,None);native_used=0;native_seen=0;speculative=0;drops=Counter();shard_drops=[];observed_kept=0
    identity_sum=0;identity_xor=0;MOD=(1<<256)-1
    db=sqlite3.connect((run/'position_index.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        db.execute('PRAGMA query_only=ON');db.execute('PRAGMA cache_size=-16384')
        kept_sql=db.execute('SELECT count(*) FROM kept').fetchone()[0]
        hold_sql=db.execute('SELECT count(*) FROM holdout').fetchone()[0]
        require(kept_sql==kept and hold_sql==summary['holdout_unique_positions'],'SQL count mismatch')
        equal,different=db.execute('SELECT coalesce(sum(k.key=h.key),0),coalesce(sum(k.key<>h.key),0) FROM holdout h JOIN kept k USING(digest)').fetchone()
        require(equal==0 and different==0,'SQL retained/holdout overlap or digest collision')
        report['sql']={'kept_count':kept_sql,'holdout_count':hold_sql,'identity_overlap':equal,'digest_key_collisions':different}
        with ExitStack() as stack:
            output=Columns(run/(config['stem']+'.pos'),b'FPOS',35,stack)
            output_hce=Columns(run/(config['stem']+'.hce'),b'FHCE',2,stack)
            require(output.n==output_hce.n==kept,'output column count mismatch')
            for suffix in ('.pos','.hce','.fen'):
                expected=summary['output'][suffix];observed=digests[config['stem']+suffix]
                require(all(observed[k]==expected[k] for k in ('bytes','sha256','md5')),'summary output digest mismatch')
            fen_output=stack.enter_context((run/(config['stem']+'.fen')).open())
            decisions=stack.enter_context(gzip.open(run/'decisions.tsv.gz','rt'))
            provenance=stack.enter_context((run/'kept_rows.tsv').open())
            require(decisions.readline().rstrip('\n')==DECISION_HEADER,'decision header mismatch')
            require(provenance.readline().rstrip('\n')==KEPT_HEADER,'kept provenance header mismatch')
            global_index=0
            require(len(summary['shards'])==len(config['positions'])==len(config['sidecars']),'shard schema mismatch')
            for shard_index,shard in enumerate(summary['shards']):
                source_path=Path(config['positions'][shard_index]);sidecar_path=Path(config['sidecars'][shard_index])
                source=Columns(source_path,b'FPOS',35,stack);stamps[str(source_path)]=stamp(source_path);stamps[str(sidecar_path)]=stamp(sidecar_path)
                sidecar=stack.enter_context(sidecar_path.open());selected=shard['input_rows'];local_drop=Counter();local_kept=0
                require(0<=selected<=source.n,'selected shard count exceeds source')
                alignment=summary['source_alignment'][shard_index]
                require(alignment['record_matches_verified']==selected and alignment['total_rows']==source.n and alignment['sidecar_rows']==source.n,'declared alignment count mismatch')
                for source_row in range(selected):
                    original=source.row(source_row);line=sidecar.readline();require(bool(line),'original sidecar short')
                    fields=line.rstrip('\n').split('|');require(len(fields)==3,'original sidecar schema')
                    original_fen=' '.join(fields[0].split())
                    decision=decisions.readline().rstrip('\n').split('\t')
                    require(len(decision)==5 and decision[0]==str(global_index),'decision index/count mismatch')
                    reason=decision[1];require(reason in policy+['kept'],'unknown decision reason')
                    response=None;native_status=None
                    if current is not None:
                        require(current[0]>=global_index,'native duplicate/out-of-order or unconsumed ID')
                        if current[0]==global_index:
                            _,response,requested_fen,native_status=current
                            require(requested_fen==original_fen,'native request differs from original full FEN')
                            native_seen+=1;current=next(native,None)
                    expected_fields=[str(response.get(k,'')) for k in ('bestmove','score','nodes')] if response else ['','','']
                    require(decision[2:]==expected_fields,'decision/native fields mismatch')
                    if reason in policy[:4]:
                        if response is not None:speculative+=1
                    else:
                        require(response is not None and reason==native_status,'native decision/status mismatch')
                        native_used+=1
                    if reason!='kept':drops[reason]+=1;local_drop[reason]+=1
                    else:
                        row=provenance.readline().rstrip('\n').split('\t')
                        require(len(row)==10 and row[:5]==[str(observed_kept),str(global_index),config['positions'][shard_index],str(source_row),'exact_full_fen'],
                                'kept provenance original/output index mismatch')
                        require(row[5:]==[str(response[k]) for k in ('nodes','depth','score','bestmove')]+[str(original[1])],
                                'kept provenance teacher/original fields mismatch')
                        require(output.row(observed_kept)==original,'retained original board/score/meta changed')
                        require(output_hce.hce(observed_kept)==response['hce'],'retained HCE/native mismatch')
                        require(fen_output.readline().rstrip('\n')==original_fen,'retained original FEN mismatch')
                        key=original[0]+bytes([original[2]&1]);d=hashlib.sha256(key).digest()
                        found=db.execute('SELECT key FROM kept WHERE digest=?',(d,)).fetchone()
                        require(found is not None and found[0]==key,'retained identity missing/mismatched in SQL')
                        value=int.from_bytes(d,'big');identity_sum=(identity_sum+value)&MOD;identity_xor^=value
                        observed_kept+=1;local_kept+=1
                    global_index+=1
                    if global_index%1000000==0:print(json.dumps({'rows_checked':global_index,'kept_checked':observed_kept,'elapsed_seconds':time.monotonic()-started}),flush=True)
                require(local_kept==shard['kept'],'shard kept count mismatch')
                shard_drops.append((local_drop,selected,shard['rules']))
            require(global_index==n and observed_kept==kept,'decision/provenance total mismatch')
            require(not decisions.readline() and not provenance.readline() and not fen_output.readline(),'extra decision/provenance/FEN output rows')
            require(current is None,'extra native response ID after all decisions')
        require(native_seen==summary['native_queries'] and speculative==summary['speculative_native_queries_not_used'],
                'native total/speculative count mismatch')
        require(sum(w['responses_checked'] for w in worker_reports)==native_seen,'native worker total mismatch')
        require(sum(w['cpu_ns_sum'] for w in worker_reports)==summary['native_cpu_ns'],'native summary CPU mismatch')
        require(summary['exact_label_rows']==kept and summary['reconstructed_label_rows']==0,'label-origin count mismatch')
        for counts,total,declared in [(drops,n,summary['rules'])]+shard_drops:
            eligible=total
            for rule in policy:
                recorded=declared[rule];number=counts[rule]
                require(recorded['eligible']==eligible and recorded['dropped']==number and recorded['not_evaluated_after_earlier_rule']==total-eligible,'waterfall count mismatch: '+rule)
                require(math.isclose(recorded['fraction_input'],number/total if total else 0.0,rel_tol=1e-13,abs_tol=1e-15),'fraction input mismatch')
                expected=number/eligible if eligible else None
                require(recorded['fraction_eligible']==expected,'fraction eligible mismatch')
                eligible-=number
        require(kept+sum(drops.values())==n,'decision conservation failure')
        # Membership/count plus two order-independent 256-bit digest checks expose duplicate/missing identities.
        sql_sum=0;sql_xor=0;sql_rows=0
        for d,key in db.execute('SELECT digest,key FROM kept'):
            require(len(d)==32 and len(key)==33 and hashlib.sha256(key).digest()==d,'SQL kept identity digest invalid')
            value=int.from_bytes(d,'big');sql_sum=(sql_sum+value)&MOD;sql_xor^=value;sql_rows+=1
        require(sql_rows==kept and (sql_sum,sql_xor)==(identity_sum,identity_xor),'retained/SQL identity multiset digest mismatch')
        report['sql'].update(retained_membership_checks=kept,kept_digest_rows_checked=sql_rows,
                             output_sql_identity_sum256=f'{sql_sum:064x}',output_sql_identity_xor256=f'{sql_xor:064x}')
    finally:db.close()
    for path,expected in stamps.items():require(stamp(Path(path))==expected,'source artifact changed during audit: '+path)
    report.update(status='PASS',input_rows=n,retained_rows=kept,decision_counts={'kept':kept,**dict(drops)},
                  native_responses_checked=native_seen,native_used=native_used,speculative_native_queries=speculative,
                  workers=worker_reports,source_stat_stability_verified=True,
                  declared_source_alignment=summary['source_alignment'],
                  scope=['Every decision, kept provenance row, retained payload/FEN/HCE and native request/response checked.',
                         'SQL identity overlap checks cover the supplied holdout index only; no missing 014/full013/game-ID claim.',
                         'Native logs are contract-checked; legality, search scores and filtering hypotheses are not recomputed.',
                         'Cheap-rule reasons are counted, not independently rerun; expensive near-deduplication is not replayed.',
                         'Native cpu_ns values are recorded query timers, not independently measured process CPU usage.',
                         'Original input paths come from the sealed summary; selected payload/state is compared, hash verification is optional and explicit.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--frozen-dir',type=Path);parser.add_argument('--expected-rows',type=int)
    parser.add_argument('--verify-external-hashes',action='store_true')
    args=parser.parse_args();run=args.run_dir.resolve();out=args.out.resolve()
    if run==out or run in out.parents:raise SystemExit('Audit output must be outside source run')
    out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();cpu=time.process_time();report={'status':'FAIL','argv':sys.argv,'source_run':str(run),'audit_source':digest(Path(__file__))}
    code=0
    try:audit(args,report)
    except Exception as e:report.update(error_type=type(e).__name__,error=str(e));code=1
    report.update(wall_seconds=time.monotonic()-started,actual_audit_process_cpu_seconds=time.process_time()-cpu,
                  peak_rss_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(out/'summary.json',report);print(json.dumps(report,indent=2));return code


if __name__=='__main__':raise SystemExit(main())
