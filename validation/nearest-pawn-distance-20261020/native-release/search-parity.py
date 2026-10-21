#!/usr/bin/env python3
"""Bounded one-thread cold/warm parity using the frozen trusted byte-capture engine."""
from pathlib import Path
import importlib.util, json, os, re, sys, time
from types import SimpleNamespace
import chess

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
preclear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text())
assert preclear.get('authorized') is True, 'Preparation only: root build clearance pending'
spec=importlib.util.spec_from_file_location('trusted_full_engine_tt',HERE/'trusted-run-full-engine-tt.py')
trusted=importlib.util.module_from_spec(spec);spec.loader.exec_module(trusted)
INFO=re.compile(r'^info depth (?P<depth>\d+) seldepth (?P<seldepth>\d+) score (?P<kind>cp|mate) (?P<score>-?\d+)(?: (?P<bound>lowerbound|upperbound))? nodes (?P<nodes>\d+) nps (?P<nps>\d+) hashfull (?P<hashfull>\d+) time (?P<time>\d+) pv(?: (?P<pv>.*))?$')
BESTMOVE=re.compile(r'^bestmove (?P<best>[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder (?P<ponder>[a-h][1-8][a-h][1-8][qrbn]?))?$')
VOLATILE=re.compile(r'\b(time|nps)\s+\d+\b')

def save(path,value):trusted.save_json(path,value)
def legal_line(board,moves,label):
    position=board.copy()
    for text in moves:
        move=chess.Move.from_uci(text)
        if move not in position.legal_moves:raise AssertionError(label+': illegal PV move '+text)
        position.push(move)

class DepthEngine(trusted.Engine):
    def depth_search(self,case,state):
        self.quiesce();self.send('position '+case['position']);self.ready()
        board=chess.Board() if case['position']=='startpos' else chess.Board(case['position'].removeprefix('fen '))
        item={'label':case['name']+'/'+state,'state':state,'position':case['position'],'depth_limit':case['depth'],'completed':False}
        self.result['searches'].append(item);self.record('search_start',**item)
        self.send('go depth '+str(case['depth']));self.active=True
        rows=self.until(lambda row:row.startswith('bestmove '),self.args.search_timeout,item['label']+': bestmove',accept_bestmove=True)
        self.active=False
        item['raw_lines']=rows
        self.record('search_output_captured',label=item['label'],raw_lines=rows)
        infos=[]
        for row in rows[:-1]:
            match=INFO.fullmatch(row)
            if match is None:raise AssertionError(item['label']+': unexpected structured info '+repr(row))
            fact=match.groupdict()
            for key in ['depth','seldepth','score','nodes','nps','hashfull','time']:fact[key]=int(fact[key])
            fact['pv']=(fact['pv'] or '').split()
            if fact['nodes']<=0 or not 0<=fact['hashfull']<=1000 or not fact['pv']:raise AssertionError('invalid real-search structured values')
            legal_line(board,fact['pv'],item['label']);infos.append(fact)
        best=BESTMOVE.fullmatch(rows[-1])
        if best is None or not infos:raise AssertionError('missing final bestmove or real search info')
        legal_line(board,[best['best']]+([best['ponder']] if best['ponder'] else []),item['label']+': bestmove/ponder')
        if infos[-1]['pv'][0]!=best['best'] or not 1<=infos[-1]['depth']<=case['depth']:raise AssertionError('final searched depth/PV disagrees with bestmove')
        if infos[-1]['depth']!=case['depth'] and infos[-1]['kind']!='mate':raise AssertionError('fixed-depth search ended early without a mate result')
        item.update(completed=True,structured_info=infos,bestmove=best['best'],ponder=best['ponder'],pv_legality='all_reported_pvs_and_bestmove_ponder_checked_with_python_chess',
                    normalized_lines=[VOLATILE.sub(lambda m:m[1]+' <excluded>',row) for row in rows])
        self.record('search_complete',**item);self.quiesce()
        return item

def main():
    protocol=json.loads((HERE/'PARITY-PROTOCOL.json').read_text())
    clear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text())
    assert clear.get('authorized') is True and clear.get('source_commit') is None and clear.get('prototype') is True
    release=json.loads((HERE/'frozen-release-attempt1/summary.json').read_text())
    assert release['status']=='PASS' and release['source_commit']==clear['source_commit']
    output=HERE/'search-parity-attempt1';output.mkdir(exist_ok=False)
    candidates={key:Path(value) for key,value in protocol['engines'].items()}
    before={key:trusted.digest(value) for key,value in candidates.items()}
    configuration={'source_commit':clear['source_commit'],'protocol':protocol,'engine_sha256_before':before,'driver_sha256':trusted.digest(Path(__file__)),'trusted_driver_sha256':trusted.digest(HERE/'trusted-run-full-engine-tt.py'),'python':sys.executable,'python_chess_version':chess.__version__,'attempts':1,'timing_comparison':False}
    save(output/'configuration.json',configuration)
    evidence=trusted.Evidence(output);summary={'status':'running','configuration':configuration,'sessions':[],'comparisons':[]}
    started=time.monotonic();deadline=started+1100;environment=os.environ.copy();evidence_closed=False
    for key in ['ASAN_OPTIONS','UBSAN_OPTIONS','TSAN_OPTIONS','LSAN_OPTIONS']:environment.pop(key,None)
    environment['PYTHONDONTWRITEBYTECODE']='1'
    try:
        assert before['baseline']==protocol['baseline_engine_sha256']
        data={};index=0
        for mode in protocol['nnue_modes']:
            for case in protocol['cases']:
                for label,binary in candidates.items():
                    if time.monotonic()>=deadline:raise TimeoutError('overall parity deadline reached; no replacements')
                    result={'index':index,'engine_label':label,'nnue_mode':mode,'case':case['name']};summary['sessions'].append(result)
                    launch=SimpleNamespace(engine=binary,engine_arg=[],cwd=binary.parent,environment=environment,output=output,handshake_timeout=15,search_timeout=30,stop_timeout=15,quit_timeout=10)
                    engine=None
                    try:
                        engine=DepthEngine(launch,evidence,index,result);index+=1
                        engine.handshake();engine.option('Threads',1);engine.option('Hash',32)
                        if not any(row=='option name UseNNUE type check default true' for row in result['identification']):raise AssertionError('UseNNUE advertised default is not true')
                        if mode=='disabled':engine.option('UseNNUE','false')
                        engine.quiesce();engine.send('ucinewgame');engine.ready()
                        cold=engine.depth_search(case,'cold');warm=engine.depth_search(case,'warm')
                        result['completed']=True;data[(mode,case['name'],label)]=[cold['normalized_lines'],warm['normalized_lines']]
                    finally:
                        if engine is not None:engine.shutdown()
                        save(output/'summary.json',summary)
                    if not (result.get('exit_code')==0 and result.get('capture_complete') and result.get('sanitizer_classification')=='none' and result.get('stream_hashes_final')):raise AssertionError('incomplete session capture or engine failure')
                    if any(row not in ['sent stop','sent quit'] for row in result.get('cleanup',[])) or result.get('reader_errors'):raise AssertionError('unexpected session cleanup or reader error')
                reference=data[(mode,case['name'],'baseline')];actual=data[(mode,case['name'],'candidate')]
                item={'nnue_mode':mode,'case':case['name'],'cold_exact':reference[0]==actual[0],'warm_exact':reference[1]==actual[1],'excluded_fields':['time','nps']}
                summary['comparisons'].append(item);save(output/'summary.json',summary)
                if not item['cold_exact'] or not item['warm_exact']:raise AssertionError('cold/warm exact parity mismatch: '+mode+'/'+case['name'])
        summary['status']='passed'
    except BaseException as exc:summary.update(status='failed',error=repr(exc))
    finally:
        summary['elapsed_seconds_operational_only']=time.monotonic()-started
        summary['engine_sha256_after']={key:trusted.digest(value) for key,value in candidates.items()}
        if summary['engine_sha256_after']!=before:summary.update(status='failed',identity_error='engine bytes changed')
        evidence.record('run_complete',status=summary['status']);evidence.close();evidence_closed=True
        summary['events_sha256']=trusted.digest(output/'events.jsonl');save(output/'summary.json',summary)
    print(json.dumps({'status':summary['status'],'sessions':len(summary['sessions']),'comparisons':len(summary['comparisons']),'error':summary.get('error')}))
    return 0 if summary['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
