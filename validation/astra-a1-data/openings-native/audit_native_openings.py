"""Independent native replay of generated books; not an R8 Windows execution.
IDEA_SOURCE: user legal opening/score-band contract and original Forge probe API.
"""
from pathlib import Path
import sys,json,hashlib,os,datetime
repo=Path('/tmp/forge-astra-a1-data');root=Path('/tmp/astra-a1-openings-real')
sys.path.insert(0,str(repo/'tools/data'))
from forge_probe import ProbeClient,sha256
exe=Path('/tmp/astra-a1-native-build/fixed/forge_data_probe')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
os.nice(19)
report={'status':'RUNNING','probe_sha256':sha256(exe),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'replays':[],'native_R8_windows':'UNVERIFIED; no driver executed','strength_claim':'NONE'}
def save(): (root/'native_audit.json').write_text(json.dumps(report,indent=2)+'\n')
save()
try:
 for name in ['openings.moves','metadata.jsonl','settings.json','generation.json']:
  if (root/'standard-one'/name).read_bytes()!=(root/'standard-two'/name).read_bytes():raise ValueError('deterministic output mismatch: '+name)
 report['standard_replay_identical_files']=['openings.moves','metadata.jsonl','settings.json','generation.json']
 for folder in ['standard-one','standard-two','chess960-style']:
  base=root/folder;success=json.loads((base/'SUCCESS.json').read_text())
  if success['status']!='PASS' or sha256(base/'MANIFEST.sha256.json')!=success['manifest_sha256']:raise ValueError('seal mismatch')
  for path,digest in json.loads((base/'MANIFEST.sha256.json').read_text()).items():
   if sha256(base/path)!=digest:raise ValueError('manifest mismatch '+path)
 with ProbeClient(exe,1024,1,workdir=root/'audit-probe') as probe:
  for folder in ['standard-one','chess960-style']:
   base=root/folder;records=[json.loads(x) for x in (base/'metadata.jsonl').read_text().splitlines()]
   book=(base/('openings.moves' if folder=='standard-one' else 'openings.fen')).read_text().splitlines()
   if len(book)!=len(records):raise ValueError('book/metadata count mismatch')
   result={'folder':folder,'positions':len(records),'legal_plies':0,'fresh_score_checks':0,'max_abs_cp':0}
   for i,row in enumerate(records):
    fen=row['start_fen']
    if folder=='standard-one' and book[i]!=' '.join(row['moves']):raise ValueError('R8 token sequence mismatch')
    for move in row['moves']:
     state=probe.query(fen,op='inspect');matches=[m for m in state['moves'] if m['uci']==move]
     if state['terminal'] or len(matches)!=1:raise ValueError('illegal/terminal replay move')
     fen=matches[0]['fen'];result['legal_plies']+=1
    if fen!=row['fen']:raise ValueError('replay final FEN mismatch')
    state=probe.query(fen,op='inspect')
    if state['terminal'] or state['in_check']:raise ValueError('terminal/checked final position')
    if folder=='chess960-style' and (fen!=book[i] or fen.split()[2]!='-'):raise ValueError('960 no-castling FEN mismatch')
    for old in row['checks']:
     actual=probe.query(old['fen'],op='analyze');cp=actual['score'];white=cp if old['fen'].split()[1]=='w' else -cp
     if abs(cp)>150 or cp!=old['score_stm_cp'] or white!=old['score_white_cp'] or actual['nodes']!=old['reported_nodes'] or actual['depth']!=old['depth']:raise ValueError('fresh score or accounting differs')
     result['fresh_score_checks']+=1;result['max_abs_cp']=max(result['max_abs_cp'],abs(cp))
   report['replays'].append(result);save()
 report['status']='PASS';report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps(report,indent=2))
except BaseException as e:
 report['status']='FAIL_OR_INCOMPLETE';report['error']=repr(e);save();raise
