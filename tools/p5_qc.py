"""CPU-only QC of sealed R14-B labels and the separately identified R13 baseline."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import struct
import sys
import time

from qc_core import DuplicateIndex, Profile, decode_pos, fen_info, is_mate, outcome, signed_score
from run_policy import Inputs, Snapshot, ROOT, free_guard, new_directory, safe_path, write_json, strict_json_loads

LABEL_FIELDS = ['row_id','game_id','split','fen','score_stm','old_score_stm','result','depth','nodes']
PREPARED_FIELDS = ['row_id','game_id','split','fen','old_score_stm','result','source','source_row']
SOURCE_PATHS = {str(Path(f'D:/grok-pc-data/selfplay_out/forge_selfplay_{n:03}.txt').resolve()).casefold() for n in (1,2)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, minimum=0):
    require(type(value) is int or isinstance(value,str) and value.isascii() and value.isdecimal(), f'invalid {name}')
    result = int(value)
    require(result >= minimum, f'invalid {name}')
    return result


def table(snapshot, fields, *, consume_bytes=None, include_header=True):
    def lines():
        for index,line in enumerate(snapshot.lines()):
            if consume_bytes is not None and (include_header or index):
                consume_bytes(line.encode('utf-8'))
            yield line
    reader = csv.DictReader(lines(), delimiter='\t')
    require(reader.fieldnames == fields, f'unexpected TSV schema: {snapshot.path}')
    for row in reader:
        require(None not in row and all(v is not None for v in row.values()), 'TSV row width mismatch')
        yield row


def read_text_record(line):
    fields = line.strip().split('|')
    require(len(fields) == 3, 'expected FEN | score | White result')
    return fen_info(fields[0].strip())['fen'], signed_score(fields[1].strip()), outcome(fields[2].strip())


def audit_r14(job, inputs, consume, *, fixture=False):
    require(type(fixture) is bool, 'fixture mode must be explicit boolean')
    job = safe_path(job)
    prepare = inputs.json(job/'prepare.json')
    config = inputs.json(job/'run_config.json')
    status = inputs.json(job/'status.json')
    final = inputs.json(job/'final'/'MANIFEST.json')
    run_id = prepare['run_id']
    require(isinstance(run_id,str) and bool(run_id.strip()),'invalid run ID')
    require(all(x['run_id'] == run_id for x in (config,status,final)), 'run identity mismatch')
    rows = integer(prepare['rows'],'rows',1)
    size = integer(config['shard_size'],'shard size',1)
    shards = (rows+size-1)//size
    for value,fields in ((status,('rows_total','rows_done','shards_total','shards_done')),
                         (final,('rows','train_rows','val_rows','train_games','val_games','game_overlap')),
                         (prepare,('train_rows','val_rows'))):
        for field in fields:
            require(type(value[field]) is int and value[field]>=0,f'invalid publication count: {field}')
    require(status['rows_total'] == status['rows_done'] == rows and status['shards_total'] == status['shards_done'] == shards, 'incomplete R14 status')
    require(final['rows'] == rows and len(final['shard_labels_sha256']) == shards, 'final coverage mismatch')
    inputs.verify(job/'prepare.json', config['prepare_json_sha256'])
    inputs.verify(job/'prepare.json', final['prepare_json_sha256'])
    inputs.verify(job/'rows.tsv', prepare['rows_tsv_sha256'])
    require(set(final['files']) == {'labels.tsv','train.txt','val.txt'}, 'unexpected final file set')
    for name, receipt in final['files'].items():
        require(type(receipt['bytes']) is int and receipt['bytes']>=0,'invalid final file byte count')
        snapshot = inputs.verify(job/'final'/name, receipt['sha256'])
        require(snapshot.initial.st_size == receipt['bytes'] and snapshot.hashes['md5'] == receipt['md5'], f'final length/MD5 mismatch: {name}')
    sources = {}
    for source in prepare['inputs']:
        source_id = integer(source['index'],'source index')
        path = safe_path(source['path'])
        require(str(path).casefold() in SOURCE_PATHS or fixture and path.is_relative_to(ROOT), 'source outside approved source list; use --fixture for owned test data')
        require(source_id not in sources and source['kind']=='selfplay', 'duplicate or unsupported source')
        snapshot = inputs.verify(path,source['sha256'])
        sources[source_id] = dict(iterator=iter(snapshot.lines()), line=0, selected=0)
    prepared = iter(table(inputs.get(job/'rows.tsv'), PREPARED_FIELDS))
    assembled = iter(table(inputs.get(job/'final'/'labels.tsv'), LABEL_FIELDS))
    split_lines = {split:iter(inputs.get(job/'final'/f'{split}.txt').lines()) for split in ('train','val')}
    games = {'train':set(),'val':set()}
    counts = Counter()
    assembly_digest=hashlib.sha256()
    seen = 0
    for index in range(shards):
        free_guard(8 * 1024 * 1024)
        directory = job/'shards'/f'shard_{index:05}'
        manifest = inputs.json(directory/'MANIFEST.json')
        require(set(manifest) == {'labels.tsv','summary.json'}, 'unexpected shard manifest entries')
        for name,digest in manifest.items():
            inputs.verify(directory/name,digest)
        summary = inputs.json(directory/'summary.json')
        for field in ('shard','first_row','rows','nodes_total'):
            require(type(summary[field]) is int and summary[field]>=0,f'invalid shard count: {field}')
        expected_rows = min(size,rows-seen)
        require(summary['run_id']==run_id and summary['shard']==index and summary['first_row']==seen and summary['rows']==expected_rows, 'shard range/identity mismatch')
        require(manifest['labels.tsv']==final['shard_labels_sha256'][index], 'shard/final manifest mismatch')
        shard_rows = node_sum = 0
        for raw in table(inputs.get(directory/'labels.tsv'),LABEL_FIELDS,consume_bytes=assembly_digest.update,include_header=index==0):
            final_row = next(assembled,None)
            require(raw==final_row,'final assembly differs from sealed shard')
            origin = next(prepared,None)
            require(origin is not None, 'prepared rows truncated')
            require(integer(raw['row_id'],'row_id')==seen, 'row sequence mismatch')
            for field in ('row_id','game_id','split','fen','old_score_stm','result'):
                require(raw[field]==origin[field],f'prepared row differs: {field}')
            split=raw['split']
            require(split in games and raw['game_id'], 'invalid split/group')
            source_id = integer(origin['source'],'source')
            source_row = integer(origin['source_row'],'source row',1)
            require(source_id in sources,'unknown source')
            cursor = sources[source_id]
            require(source_row>cursor['selected'],'source rows repeated or reordered')
            source_line = None
            while cursor['line'] < source_row:
                source_line = next(cursor['iterator'],None)
                require(source_line is not None,'original source truncated')
                cursor['line'] += 1
            cursor['selected']=source_row
            require(read_text_record(source_line)==(fen_info(raw['fen'])['fen'],signed_score(raw['old_score_stm']),outcome(raw['result'])), 'original source row differs')
            score=signed_score(raw['score_stm'])
            expected_text=(fen_info(raw['fen'])['fen'],score,outcome(raw['result']))
            line=next(split_lines[split],None)
            require(line is not None and read_text_record(line)==expected_text,'split text differs from labels')
            depth=integer(raw['depth'],'depth')
            nodes=integer(raw['nodes'],'nodes')
            node_sum+=nodes
            record=dict(cohort='r14b',row_id=seen,game_id=raw['game_id'],split=split,fen=raw['fen'],score_stm=score,
                        old_score_stm=signed_score(raw['old_score_stm']),result=outcome(raw['result']),depth=depth,nodes=nodes,
                        source=source_id,source_row=source_row,state_origin='original_fen; inferred_group_id')
            if is_mate(score):
                record.update(original_label=dict(raw),prepared_row=dict(origin),
                              input_path=str(job/'final'/'labels.tsv'),input_line=seen+2)
            consume(record)
            games[split].add(raw['game_id'])
            counts[split]+=1
            seen+=1
            shard_rows+=1
        require(shard_rows==expected_rows and node_sum==summary['nodes_total'],'shard rows/nodes mismatch')
    require(seen==rows and next(assembled,None) is None and next(prepared,None) is None,'extra/missing assembly rows')
    require(assembly_digest.hexdigest()==inputs.get(job/'final'/'labels.tsv').hashes['sha256'],'final assembly bytes differ from concatenated sealed shards')
    for split,iterator in split_lines.items():
        require(next(iterator,None) is None,'extra split text rows')
        require(counts[split]==final[f'{split}_rows']==prepare[f'{split}_rows'],'split row count mismatch')
        require(len(games[split])==final[f'{split}_games'],'split group count mismatch')
    for cursor in sources.values():
        for _ in cursor['iterator']:
            pass # finish hashing complete original sources, including unselected suffixes
    overlap=len(games['train']&games['val'])
    require(overlap==0 and final['game_overlap']==0,'inferred group split overlap')
    return dict(rows=seen,shards=shards,run_id=run_id,counts=dict(counts),inferred_group_overlap=overlap,fixture=fixture,
                provenance_status='UNVERIFIED',authentic_game_overlap=None,
                reason='IDs inferred from FEN/ply/result changes; no authenticated original-game binding')


def audit_old(job, inputs, consume):
    job=safe_path(job)
    status=inputs.json(job/'status.json')
    for field in ('shards_done','shards_total','rows_done','rows_total'):
        require(type(status[field]) is int and status[field]>=0,f'invalid old status count: {field}')
    require(status['rows_total']>=status['rows_done'] and status['shards_total']>=status['shards_done'],'old totals smaller than completed counts')
    require((status['rows_total']==status['rows_done'])==(status['shards_total']==status['shards_done']),'old row/shard completion totals disagree')
    fields=['shard','rows','dir','seconds','pos_sha256','hce_sha256','fen_sha256','run_id']
    entries=list(table(inputs.get(job/'shards.tsv'),fields))
    require(len(entries)==status['shards_done'],'indexed old-shard count mismatch')
    seen=0
    for index,entry in enumerate(entries):
        require(integer(entry['shard'],'shard')==index and entry['dir']==f'shard_{index:05}', 'old shards noncontiguous or unsafe directory')
        require(entry['run_id']==status['run_id'],'old run mismatch')
        count=integer(entry['rows'],'rows',1)
        directory=job/'shards'/entry['dir']
        manifest=inputs.json(directory/'manifest.json')
        summary=inputs.json(directory/'summary.json')
        config=summary['config']
        for value,fields in ((summary,('selected','exact_label_rows','reconstructed_label_rows')),(config,('start','count','stride'))):
            for field in fields:
                require(type(value[field]) is int and value[field]>=0,f'invalid old shard count: {field}')
        require(summary['status']=='SEALED' and summary['selected']==count and config['start']==seen and config['count']==count and config['stride']==1,'old shard not sealed/contiguous')
        require(summary['exact_label_rows']==0 and summary['reconstructed_label_rows']==count and summary['state_origin']=='reconstructed_no_castling_no_ep_clock0','unexpected old-label provenance')
        stem=f'relabel_{index:05}'
        for name in ('summary.json','labels.jsonl',stem+'.pos',stem+'.fen',stem+'.hce'):
            require(name in manifest,'missing core old manifest entry')
            inputs.verify(directory/name,manifest[name])
        for suffix in ('pos','fen','hce'):
            require(manifest[stem+'.'+suffix]==entry[suffix+'_sha256']==summary['outputs']['.'+suffix], 'old output pins disagree')
        payload=inputs.get(directory/(stem+'.pos')).bytes()
        hce=inputs.get(directory/(stem+'.hce')).bytes()
        require(len(hce)==16+2*count and struct.unpack_from('<4sIQ',hce)==(b'FHCE',1,count),'FHCE header/length mismatch')
        fens=inputs.get(directory/(stem+'.fen')).lines()
        labels=inputs.get(directory/'labels.jsonl').lines()
        local=0
        for packed,fen,line in zip_longest(decode_pos(payload),fens,labels):
            require(packed is not None and fen is not None and line is not None,'old sidecar alignment mismatch')
            label=strict_json_loads(line)
            for field in ('input_index','output_index','depth','nodes'):
                require(type(label[field]) is int and label[field]>=0,f'invalid old integer: {field}')
            for field in ('score_stm','old_score_stm','hce_stm'):
                signed_score(label[field])
            info=fen_info(fen.strip())
            board,score,meta=packed
            require(info['board']==board and (info['stm']=='b')==(meta&1),'old FEN board/STM mismatch')
            require(label['input_index']==seen and label['output_index']==local and label['score_stm']==score,'old label row/score mismatch')
            hce_score=signed_score(struct.unpack_from('<h',hce,16+2*local)[0])
            require(label['hce_stm']==hce_score and label['state_origin']==summary['state_origin'],'old HCE/state mismatch')
            require(fen.split()[2:]==['-','-','0','1'],'old reconstructed state convention changed')
            record=dict(cohort='old440k',row_id=seen,split='unspecified',fen=info['fen'],score_stm=score,
                         old_score_stm=signed_score(label['old_score_stm']),result=(meta>>1)/2,
                         state_origin=summary['state_origin'],depth=label['depth'],nodes=label['nodes'])
            if is_mate(score):
                record.update(original_label=dict(label),input_path=str(directory/'labels.jsonl'),input_line=local+1)
            consume(record)
            local+=1
            seen+=1
        require(local==count,'old row count mismatch')
    require(seen==status['rows_done'],'old job row count mismatch')
    return dict(rows=seen,shards=len(entries),source_job_complete=status['shards_done']==status['shards_total'],
                cohort_complete=True,provenance_status='UNVERIFIED',authentic_game_overlap=None,
                reason='440k sealed prefix of unfinished source job; no original game IDs; reconstructed state searched')


def run(args):
    output=new_directory(args.out,384*1024*1024)
    inputs=Inputs()
    index=DuplicateIndex()
    profiles={}
    mate_count=0
    start=time.monotonic()
    try:
        with (output/'mate_rows.jsonl').open('x',encoding='utf-8',newline='\n') as mates:
            def consume(row):
                nonlocal mate_count
                key=row['cohort']
                names=[key,key+':'+row['split']]
                if not is_mate(row['score_stm']):
                    names.append(key+':non_mate')
                for name in names:
                    if name not in profiles:
                        profiles[name]=Profile()
                    profiles[name].add(row['fen'],row['score_stm'],row['result'],row['split'],row['old_score_stm'])
                info=fen_info(row['fen'])
                index.add(key,row['split'],info['fen'])
                if is_mate(row['score_stm']):
                    free_guard(16384)
                    mates.write(json.dumps(dict(row,flag='abs(score_stm)>=30000'),sort_keys=True)+'\n')
                    mate_count+=1
            r14=audit_r14(args.job_a,inputs,consume,fixture=getattr(args,'fixture',False))
            print('R14 verified',r14['rows'],flush=True)
            old=audit_old(args.old_job,inputs,consume)
            print('Old labels verified',old['rows'],flush=True)
        job_b=safe_path(args.job_b)
        other=inputs.json(job_b/'final'/'MANIFEST.json')
        other_labels=inputs.verify(job_b/'final'/'labels.tsv',other['files']['labels.tsv']['sha256'])
        first=inputs.get(safe_path(args.job_a)/'final'/'labels.tsv')
        require(first.hashes==other_labels.hashes,'job A/B final labels differ')
        report=dict(schema=2,status='PASS',fixture=getattr(args,'fixture',False),provenance_status='UNVERIFIED',mate_threshold=30000,mate_rows=mate_count,mate_ledger_schema=2,
                    cohorts={'r14b':r14,'old440k':old},profiles={key:value.report() for key,value in profiles.items()},
                    duplicates={key:index.report(key) for key in ('r14b','old440k')},
                    reproducibility=dict(status='PASS',relation='jobA/jobB final labels byte-content hashes identical',sha256=first.hashes['sha256']),
                    phase_definition='N/B=1,R=2,Q=4 summed both sides; cap24; end0..8,middle9..16,early17..24; material proxy, not actual ply phase',
                    comparison='Unpaired different populations; no strength/label-quality inference',seconds=time.monotonic()-start)
        write_json(output/'statistics.json',report)
        write_json(output/'INPUTS.json',inputs.receipts())
        write_json(output/'COMPLETE.json',dict(status='PASS',scope='fixture QC only' if getattr(args,'fixture',False) else 'QC integrity only',fixture=getattr(args,'fixture',False),
                   files={name:Snapshot(output/name).digest() for name in ('statistics.json','INPUTS.json','mate_rows.jsonl')}))
        print(json.dumps({key:report[key] for key in ('status','provenance_status','mate_rows','seconds')}),flush=True)
        return report
    except BaseException as error:
        # Failure receipt may itself be blocked by the hard disk floor; stdout remains authoritative.
        print(json.dumps(dict(status='FAIL_OR_INCOMPLETE',error=repr(error))),flush=True)
        raise
    finally:
        index.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-a',default='D:/o14b/r2/proof/jobA')
    parser.add_argument('--job-b',default='D:/o14b/r2/proof/jobB')
    parser.add_argument('--old-job',default='C:/o13/p5/job1')
    parser.add_argument('--out',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    parser.add_argument('--fixture',action='store_true',help='Permit owned test sources; results remain fixture-only evidence')
    args=parser.parse_args()
    run(args)

if __name__=='__main__':
    main()
