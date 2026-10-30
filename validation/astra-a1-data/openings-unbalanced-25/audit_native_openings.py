"""Fresh native replay of min-25 books; no R8 Windows execution.
IDEA_SOURCE: user bounded imbalance and complete selected-position parity contract.
"""
from pathlib import Path
import sys,json,os,datetime,time
REPO=Path('/tmp/forge-astra-a1-data');ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/'tools/data'))
from forge_probe import ProbeClient,sha256
EXE=Path('/tmp/astra-a1-native-build/fixed/forge_data_probe')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(19)
report={'status':'RUNNING','probe_sha256':sha256(EXE),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'replays':[],'native_R8_windows':'UNVERIFIED; no driver executed','strength_claim':'NONE','minimum_final_abs_cp':25,'maximum_selected_abs_cp':150}
def save(): (ROOT/'native_audit.json').write_text(json.dumps(report,indent=2)+'\n')
save()
try:
 report['standard_second_run']='UNVERIFIED_CPU_BUDGET; one generation already used 29.407022 CPU seconds'
 report['optional_chess960_style']='NOT_RUN_CPU_BUDGET'
 for folder in ['standard-one']:
  base=ROOT/folder;success=json.loads((base/'SUCCESS.json').read_text())
  if success['status']!='PASS' or sha256(base/'MANIFEST.sha256.json')!=success['manifest_sha256']:raise ValueError('seal mismatch')
  for path,digest in json.loads((base/'MANIFEST.sha256.json').read_text()).items():
   if sha256(base/path)!=digest:raise ValueError('manifest mismatch '+path)
 with ProbeClient(EXE,1024,1,workdir=ROOT/'audit-probe') as probe:
  for folder in ['standard-one']:
   base=ROOT/folder;records=[json.loads(x) for x in (base/'metadata.jsonl').read_text().splitlines()]
   book=(base/('openings.moves' if folder=='standard-one' else 'openings.fen')).read_text().splitlines()
   if len(book)!=len(records):raise ValueError('book/metadata count mismatch')
   result={'folder':folder,'positions':len(records),'legal_plies':0,'fresh_score_checks':0,'max_selected_abs_cp':0,'min_final_abs_cp':100000,'max_final_abs_cp':0}
   seen=set()
   for i,row in enumerate(records):
    fen=row['start_fen'];trajectory=[fen]
    if folder=='standard-one' and book[i]!=' '.join(row['moves']):raise ValueError('R8 token sequence mismatch')
    for move in row['moves']:
     state=probe.query(fen,op='inspect');matches=[m for m in state['moves'] if m['uci']==move]
     if state['terminal'] or len(matches)!=1:raise ValueError('illegal/terminal replay move')
     fen=matches[0]['fen'];trajectory.append(fen);result['legal_plies']+=1
    if fen!=row['fen']:raise ValueError('replay final FEN mismatch')
    if trajectory!=[x['fen'] for x in row['checks']]:raise ValueError('selected trajectory missing score check')
    key=' '.join(fen.split()[:2])
    if key in seen:raise ValueError('duplicate final board+STM')
    seen.add(key)
    state=probe.query(fen,op='inspect')
    if state['terminal'] or state['in_check']:raise ValueError('terminal/checked final position')
    if folder=='chess960-style' and (fen!=book[i] or any(x.split()[2]!='-' for x in trajectory)):raise ValueError('960 no-castling FEN mismatch')
    for old in row['checks']:
     actual=probe.query(old['fen'],op='analyze');cp=actual['score'];white=cp if old['fen'].split()[1]=='w' else -cp
     if abs(cp)>150 or cp!=old['score_stm_cp'] or white!=old['score_white_cp'] or actual['nodes']!=old['reported_nodes'] or actual['depth']!=old['depth']:raise ValueError('fresh score or accounting differs')
     result['fresh_score_checks']+=1;result['max_selected_abs_cp']=max(result['max_selected_abs_cp'],abs(cp))
    final_cp=abs(cp)
    if not 25<=final_cp<=150 or cp!=row['score_stm_cp']:raise ValueError('final score outside min25/max150 or metadata inconsistent')
    result['min_final_abs_cp']=min(result['min_final_abs_cp'],final_cp);result['max_final_abs_cp']=max(result['max_final_abs_cp'],final_cp)
   report['replays'].append(result);save()
 report['status']='PASS';report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps(report,indent=2))
except BaseException as e:
 report['status']='FAIL_OR_INCOMPLETE';report['error']=repr(e);save();raise
