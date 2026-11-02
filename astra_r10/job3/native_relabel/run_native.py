"""Bounded actual Forge relabel proof on a frozen physical-source sample. UNPROVEN."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('D:/a10')
HERE = Path(__file__).resolve().parent
TOOL = HERE.parent/'tool'
SOURCE = ROOT/'job3/inputs/source001/forge_selfplay_001.txt'
SOURCE_SHA = 'de27d81720c0e33f10e0fa95e48b1f619b1325bf35675cd2fcd016fe48f338a2'
PROBE = ROOT/'job3/probe01/forge_data_probe.exe'
PROBE_SHA = '64b8199ebe4368f1935d1d855bdffa14a83e9ff7b63fa936dba2cf910b251616'
PINNED_TOOLS = {
    'full_state.py':'6f764190b8eb13d8976bedfbf446facc5225b91ade001849c3b38fb9031dbd27',
    'data/relabel_positions.py':'0cfd0be703e85ec5d814137f4c382533e837259c5c41d931d79988bd82240ef7',
    'data/forge_pos.py':'1a9f31d3ec14577d84b52f5ea5493411186e1e0b6371b27fb683a871cb92b069',
    'data/forge_probe.py':'980c20ccca62dae8b332ba3614e22362d35e937a464360326493f44978375d82',
    'datafilter/records.py':'db114d5fd4368759926e13dc0ea2bd99a060f6b387b35979a16d3c75b00cf408',
}


def own(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() == ROOT.resolve() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('path must resolve strictly under D:/a10')
    return path.resolve()


def identity(path):
    path = own(path)
    md5, sha = hashlib.md5(), hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            md5.update(block);sha.update(block);size+=len(block)
    return dict(path=str(path),bytes=size,md5=md5.hexdigest(),sha256=sha.hexdigest())


def write_new(path, value):
    with own(path).open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def guard():
    for volume, reserve in [('C:/',30*1024**3),('D:/',50*1024**3+16*1024**2)]:
        if shutil.disk_usage(volume).free < reserve:
            raise ValueError('free-space floor violated: '+volume)


def version(out):
    argv = [str(PROBE),'--version']
    with (out/'version.stdout').open('xb') as stdout, (out/'version.stderr').open('xb') as stderr:
        child = subprocess.Popen(argv,stdout=stdout,stderr=stderr,cwd=str(out),
                creationflags=subprocess.IDLE_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
        try:
            child.wait(timeout=15)
        finally:
            if child.poll() is None:
                child.kill();child.wait(timeout=5)  # only this owned Popen handle
            write_new(out/'version-process.json',dict(argv=argv,pid=child.pid,returncode=child.returncode,
                      binary=identity(PROBE),idle_creation_flag=True,affinity='inherited CPU3',owned_process_only=True))
    if child.returncode != 0:
        raise ValueError('native --version failed')
    result = json.loads((out/'version.stdout').read_bytes())
    if result.get('protocol')!='forge-data-probe-v1' or result.get('threads')!=1 or result.get('search_options')!='default_OFF':
        raise ValueError('unexpected native protocol/resources/options')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    out = own(args.out)
    guard();out.mkdir(parents=True,exist_ok=False)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        TEMP=str(out),TMP=str(out),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        CUDA_VISIBLE_DEVICES='',HIP_VISIBLE_DEVICES='',ROCR_VISIBLE_DEVICES='')
    sys.path[:0]=[str(TOOL),str(TOOL/'data'),str(TOOL/'datafilter'),'D:/a10/pydeps']
    try:
        import chess
        from forge_pos import PosWriter, text_record
        from records import selfplay_record
        from full_state import write_state, verify_state
        import relabel_positions
        initial = [identity(SOURCE),identity(PROBE),identity(__file__)]
        if initial[0]['sha256']!=SOURCE_SHA or initial[1]['sha256']!=PROBE_SHA:
            raise ValueError('frozen source/probe SHA256 mismatch')
        for relative,expected in PINNED_TOOLS.items():
            item=identity(TOOL/relative)
            if item['sha256']!=expected:raise ValueError('reviewed tool changed: '+relative)
            initial.append(item)
        build_evidence=[identity(PROBE.parent/name) for name in ('REPORT.json','command.json','stdout.log','stderr.log','describe.stdout','describe.stderr')]
        initial.extend(build_evidence)
        write_new(out/'INPUTS.json',dict(inputs=initial,claim='UNPROVEN',auxiliary_probe_only=True,
            selection='first 16 legal nonterminal physical rows, scan bounded at 10000 lines; no shuffle',
            seed=None,nodes_per_position=2048,threads=1,hash_mb=1,
            prior_describe=dict(exit_code=2,classification='INCORRECT_DIAGNOSTIC_FLAG; not a probe correctness failure')))
        protocol=version(out)
        rows=[];raw_lines=[];physical=[];features=dict(castling=0,en_passant=0,noncapturable_ep=0,capturable_ep=0)
        with SOURCE.open('rb') as stream:
            for physical_row,raw in enumerate(stream,1):
                if physical_row>10000:break
                text=raw.decode('utf-8-sig').strip()
                if not text or text.startswith('#'):continue
                row=selfplay_record(text,str(SOURCE),physical_row)
                board=chess.Board(row['fen'])
                if not board.is_valid() or board.is_game_over():continue
                row.update(game_id=None,physical_source_row=physical_row,source_sha256=SOURCE_SHA,
                           physical_line_sha256=hashlib.sha256(raw).hexdigest())
                rows.append(row);raw_lines.append(raw);physical.append(physical_row)
                fields=row['fen'].split()
                features['castling']+=fields[2]!='-'
                features['en_passant']+=fields[3]!='-'
                features['noncapturable_ep']+=fields[3]!='-' and not board.has_legal_en_passant()
                features['capturable_ep']+=board.has_legal_en_passant()
                if len(rows)==16:break
        if len(rows)!=16 or not all(features[key]>0 for key in ('castling','en_passant','noncapturable_ep')):
            raise ValueError('bounded sample lacks required row count/castling/EP coverage')
        sample=out/'sample';sample.mkdir()
        with (sample/'source-lines.txt').open('xb') as stream:
            for raw in raw_lines:stream.write(raw)
            stream.flush();os.fsync(stream.fileno())
        with PosWriter(sample,'source',False,with_fen=True) as writer:
            for row,raw in zip(rows,raw_lines):
                record,fen=text_record(raw.decode('utf-8-sig'))
                if fen.split()!=row['fen'].split():raise ValueError('sample conversion changed full FEN')
                writer.append(record,fen=fen)
        state=sample/'source.state.json'
        write_state(writer.pos_path,rows,state,binary_format='fpos1',sources=[SOURCE,sample/'source-lines.txt'])
        state_hash=identity(state)['sha256']
        if verify_state(state,state_hash,writer.pos_path)!=rows:raise ValueError('sample state binding failed')
        write_new(out/'SAMPLE.json',dict(rows=16,physical_source_rows=physical,coverage=features,
            missing_game_ids=16,game_id_status='UNVERIFIED',source=initial[0],
            files=[identity(writer.pos_path),identity(writer.fen_path),identity(state),identity(sample/'source-lines.txt')]))
        guard()
        # No injected/fake pool: this is the reviewed real ProbePool path.
        report=relabel_positions.run(relabel_positions.Config(pos=writer.pos_path,sidecar=writer.fen_path,
            out=out/'relabel',probe=PROBE,nodes=2048,workers=1,hash_mb=1,count=16,batch_size=16,
            state_manifest=state,state_sha256=state_hash))
        output=out/'relabel'
        output_fens=(output/'relabeled.fen').read_text(encoding='utf8').splitlines()
        if len(output_fens)!=16:raise ValueError('native output row count mismatch')
        mismatches=[i for i,(old,new) in enumerate(zip(rows,output_fens)) if old['fen'].split()!=new.split()]
        if mismatches:raise ValueError('native output six-field FEN mismatch: '+str(mismatches))
        state_rows=verify_state(Path(report['full_state']['manifest']),report['full_state']['sha256'],output/'relabeled.pos')
        if any(row.get('game_id') is not None or row['physical_source_row']!=physical[i] or row['fen'].split()!=rows[i]['fen'].split()
               for i,row in enumerate(state_rows)) or len(state_rows)!=16:
            raise ValueError('native output state/provenance changed')
        process_path=output/'probe_logs/worker-0/process.json'
        process=json.loads(process_path.read_text())
        if process['returncode']!=0 or process['successful_requests']!=16 or process['response_count']!=16 or process['binary_sha256']!=PROBE_SHA or not process['binary_unchanged']:
            raise ValueError('native process evidence failed')
        with gzip.open(output/'probe_logs/worker-0/requests.tsv.gz','rt',encoding='ascii') as stream:requests=stream.read().splitlines()
        with gzip.open(output/'probe_logs/worker-0/responses.jsonl.gz','rt',encoding='utf8') as stream:answers=[json.loads(line) for line in stream]
        if len(requests)!=16 or len(answers)!=16:raise ValueError('native transcript count mismatch')
        for index,(row,request,answer) in enumerate(zip(rows,requests,answers)):
            if request.split('\t')!=[str(index),'analyze',row['fen']]:raise ValueError('native request/source mismatch')
            if str(answer['id'])!=str(index) or answer['fen'].split()!=row['fen'].split() or answer.get('analyzed') is not True or not 0<answer['nodes']<=2048:
                raise ValueError('native answer/source/budget mismatch')
        for item in initial:
            if identity(item['path'])!=item:raise ValueError('pinned input/tool changed during native proof')
        scope=dict(upstream_scope='native-relabel',auxiliary_probe_only=True,kit_candidate=False,
                   fixture_factory=False,training='NOT_RUN',game_id_clearance='UNVERIFIED',claim='UNPROVEN')
        write_new(out/'SCOPE.json',scope)
        final=dict(status='PASS',claim='UNPROVEN',rows=16,fen_mismatches=0,missing_game_ids=16,
                   physical_source_rows=physical,coverage=features,protocol=protocol,nodes_per_position=2048,
                   total_search_nodes=sum(a['nodes'] for a in answers),depths=[a['depth'] for a in answers],
                   process=identity(process_path),summary=identity(output/'summary.json'),
                   outputs={name:identity(output/('relabeled'+name)) for name in ('.pos','.fen','.hce')},
                   scope=scope,teacher_quality='UNPROVEN; bounded relabeling does not establish label quality or Elo')
        write_new(out/'REPORT.json',final)
        write_new(out/'input-provenance.json',dict(schema=1,upstream_scope='native-relabel',claim='UNPROVEN; actual auxiliary native probe',
            outputs={role:identity(output/('relabeled.'+role)) for role in ('pos','fen')},
            evidence=identity(output/'summary.json'),scope_evidence=identity(out/'SCOPE.json')))
        print(json.dumps(dict(status='PASS',rows=16,fen_mismatches=0,missing_game_ids=16,scope='native-relabel; UNPROVEN')))
    except BaseException as error:
        write_new(out/'FAILURE.json',dict(status='FAIL',type=type(error).__name__,error=str(error),claim='UNPROVEN'))
        raise


if __name__=='__main__':main()
