"""Bounded S06 evidence replay. Requires the explicitly supplied handoff and repo.

No engine/compiler/match process is started. Historical PGN/log bytes are inputs
to a new parser only. Every subprocess's original output and return code survive.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--handoff-files',type=Path,required=True)
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    work=Path(__file__).resolve().parent
    a.out.mkdir(exist_ok=False)
    names=[f'forge_sol_S06_{part}_20261026.py' for part in ('gatelog_miner','statistics','pgn','logs','validation')]
    names += [f'test_forge_sol_S06_{part}_20261026.py' for part in ('cli','statistics','pgn','logs')]
    before={name:digest(work/name) for name in names}
    receipt={'schema':'forge_sol_S06_validation_v1','status':'IN_PROGRESS',
             'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'sources_before':before,'commands':[],'checks':{},
             'no_engine_compiler_or_match_execution':True,'acceptance_authorized':False}
    cli=work/'forge_sol_S06_gatelog_miner_20261026.py'
    def run(label,args,expected=0):
        index=len(receipt['commands'])+1
        command=[sys.executable,'-B',*map(str,args)]
        start=time.monotonic()
        r=subprocess.run(command,cwd=work,capture_output=True,timeout=90)
        paths={}
        for role,data in (('stdout',r.stdout),('stderr',r.stderr)):
            p=a.out/f'forge_sol_S06_{index:02d}_{label}_{role}_20261026.txt'
            p.write_bytes(data)
            paths[role]={'path':p.name,'sha256':digest(p),'bytes':len(data)}
        row={'label':label,'argv':command,'cwd':str(work),'returncode':r.returncode,
             'expected_returncode':expected,'elapsed_seconds':time.monotonic()-start,'streams':paths}
        receipt['commands'].append(row)
        assert r.returncode==expected, row
        return r
    def result(name):
        return json.loads((a.out/name/'forge_sol_S06_result_20261026.json').read_text())
    try:
        run('full_suite',['-m','unittest','discover','-s',str(work),'-p','test_forge_sol_S06_*.py','-v'])
        known=[('G95',[13,128,463,137,9],[.23,8.53,-.56]),
               ('G100r',[5,121,458,154,12],[10.89,8.38,2.22]),
               ('G119',[9,130,435,163,13],[9.50,8.84,1.72])]
        cases=[]
        for label,penta,targets in known:
            name=f'forge_sol_S06_{label}_counts_20261026'
            run(label,[cli,'counts','--penta',*penta,'--out',a.out/name])
            s=result(name)['statistics']
            actual=[s['logistic_elo']['estimate'],s['logistic_elo']['ci95_delta_halfwidth'],s['gaussian_llr']['value']]
            assert all(abs(x-y)<.01 for x,y in zip(actual,targets))
            cases.append({'gate':label,'provided_pentabins':penta,'targets':targets,'actual':actual,
                          'status':'PASS_ARITHMETIC_ONLY_NO_MATCH','tolerance':.01})
        receipt['checks']['supplied_three_count_cases']=cases
        # Explicit synthetic illustration from recovery, never an actual G104 reconstruction.
        name='forge_sol_S06_SYNTHETIC_G104_illustration_20261026'
        run('synthetic_G104',[cli,'counts','--penta',9,33,203,98,6,'--out',a.out/name])
        s=result(name)['statistics']
        receipt['checks']['G104']={'status':'UNVERIFIED_ACTUAL_PAIRED_COUNTS_MISSING',
            'synthetic_illustration_only':{'penta':[9,33,203,98,6],'statistics':s},
            'reported_native_llr':2.95,'approximation_disagrees':abs(s['gaussian_llr']['value']-2.95)>.01}
        csvpath=a.handoff_files/'08_status/gate_results_20261025_1335/GATE_RESULTS.csv'
        assert digest(csvpath)=='c220b9e5ac88ee5fd3d419e93c0bfe45d659818e765b78fd4138a5eb9614c230'
        name='forge_sol_S06_supplied_metadata_triage_20261026'
        run('supplied_csv',[cli,'triage','--csv',csvpath,'--out',a.out/name])
        r=result(name);rows={x['gate']:x for x in r['rows']}
        assert len(r['rows'])==35 and rows['G104']['wdl']==[130,497,71]
        assert rows['G120']['wdl']==[184,623,121] and rows['G120']['concurrency']==7
        assert rows['G104']['pentabins'] is None and not any(x['acceptance_verified'] for x in r['rows'])
        receipt['checks']['supplied_csv']={'status':'PASS_METADATA_PARSE_ONLY','rows':35,
            'source_sha256':digest(csvpath),'G104_wdl':rows['G104']['wdl'],
            'G120_reported_state':rows['G120']['raw']['verdict'],'G120_games':rows['G120']['games'],
            'all_acceptance_verified_false':True}
        hist=a.repo/'validation/clock-safety-9850x3d/matches/original-quality-sprt'
        name='forge_sol_S06_historical_178_parser_replay_20261026'
        run('historical_178',[cli,'mine','--pgn',hist/'games.pgn','--log',hist/'console.txt',
            '--gate-id','HISTORICAL_20261019_ORIGINAL_QUALITY','--candidate','Candidate','--baseline','Baseline',
            '--units','logistic','--e1',20,'--out',a.out/name])
        r=result(name)
        assert r['status']=='OUTCOME_CHECKS_PASS'
        assert [r['pgn']['raw'][x] for x in ('W','D','L')]==[66,44,68]
        assert r['pgn']['paired']['pentabins']==[1,10,68,10,0]
        assert r['pgn']['paired']['valid_pairs']==89
        assert all(x['status']=='PASS' for x in r['reconciliation']['comparisons'])
        assert r['log']['reported']['acceptances'][0]['hypothesis']=='H0'
        receipt['checks']['historical_178']={'status':'PASS_EXISTING_EVIDENCE_PARSER_REPLAY_ONLY',
            'games':178,'pairs':89,'wdl':[66,44,68],'pentabins':[1,10,68,10,0],
            'native_reported_hypothesis':'H0','new_games':0,
            'inputs':r['inputs'],'no_new_or_transferred_elo_claim':True}
        fault=a.repo/'validation/clock-safety-9850x3d/diagnostics/repro-forge-2/console.txt'
        name='forge_sol_S06_historical_timeout_parser_replay_20261026'
        run('historical_fault',[cli,'mine','--log',fault,'--gate-id','HISTORICAL_REPRO_FORGE2_20261019',
            '--candidate','Baseline','--baseline','Candidate','--out',a.out/name],expected=1)
        r=result(name)
        assert r['status']=='BLOCKED' and r['log']['faults']['reported_player_totals']['Candidate']['time_loss']==1
        receipt['checks']['historical_fault']={'status':'PASS_EXPECTED_REJECTION_OF_ORIGINAL_TIMEOUT',
            'actual_exit':1,'runner_reported_Candidate_timeouts':1,'inputs':r['inputs']}
        receipt['sources_after']={name:digest(work/name) for name in names}
        assert receipt['sources_after']==before
        receipt['status']='PASS'
    except BaseException as exc:
        receipt['status']='FAIL'
        receipt['error']=repr(exc)
        raise
    finally:
        path=a.out/'forge_sol_S06_validation_receipt_20261026.json'
        path.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print('PASS: offline S06 checks and original historical parser replays; zero new games')


if __name__=='__main__':
    main()
