import hashlib,json,queue,re,subprocess,threading,time
from pathlib import Path
out=Path(__file__).resolve().parent;repo=Path('/tmp/forge-astra-a1-data')
engine=Path('/tmp/astra-a1-probe-full-build-v2/core/forge');probe=Path('/tmp/astra-a1-native-build/budget-status/forge_data_probe');sample=Path('/tmp/astra-a1-relabel-256-65536/relabeled.fen')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
fens=sample.read_text().splitlines();indices=[i*255//31 for i in range(32)]
if len(fens)!=256:raise RuntimeError('expected authoritative 256-FEN sample')
selected=[{'id':str(i),'sample_index':i,'fen':fens[i]} for i in indices]
selected.append({'id':'budget27772','sample_index':None,'fen':'r1bq2k1/pp3r1p/3b1n2/P2p1Np1/5p2/3Q2P1/1BP1PPBP/R4RK1 b - - 8 21'})
summary={'status':'IN_PROGRESS','engine_sha256':sha(engine),'helper_sha256':sha(probe),'sample_sha256':sha(sample),'nodes_limit':1024,'hash_mb':1,'threads':1,'selected_rows':indices,'results':[],'scope':'UCI/helper correctness; no speed claim','node_semantics':'UCI info nodes belongs to its last completed iteration; helper nodes is final SearchInfo total after stopping. Compare equality only when the final info reaches that total.'}
def save():(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
p=None;reader=None
try:
 save();data=''.join(row['id']+'\tanalyze\t'+row['fen']+'\n' for row in selected).encode();command=[str(probe),'--nodes','1024','--hash-mb','1'];(out/'helper.command.json').write_text(json.dumps(command)+'\n');(out/'helper.stdin').write_bytes(data)
 native=subprocess.run(command,input=data,capture_output=True,timeout=30);(out/'helper.stdout').write_bytes(native.stdout);(out/'helper.stderr').write_bytes(native.stderr);(out/'helper.exit').write_text(str(native.returncode)+'\n')
 if native.returncode:raise RuntimeError('helper returned nonzero')
 native_rows=[json.loads(line) for line in native.stdout.splitlines()]
 if len(native_rows)!=33 or any(not row['ok'] for row in native_rows):raise RuntimeError('helper response invalid')
 (out/'engine.command.json').write_text(json.dumps([str(engine)])+'\n')
 stdout_file=(out/'engine.stdout').open('xb');stderr_file=(out/'engine.stderr').open('xb');stdin_file=(out/'engine.stdin').open('xb');events=(out/'interaction.jsonl').open('x');q=queue.Queue();started=time.monotonic()
 p=subprocess.Popen([str(engine)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr_file)
 def read_stdout():
  for line in iter(p.stdout.readline,b''):
   stdout_file.write(line);stdout_file.flush();q.put(line.decode('utf-8').rstrip('\r\n'))
  q.put(None)
 reader=threading.Thread(target=read_stdout,daemon=True);reader.start()
 def send(line):
  data=(line+'\n').encode();stdin_file.write(data);stdin_file.flush();p.stdin.write(data);p.stdin.flush();events.write(json.dumps({'direction':'stdin','line':line,'elapsed_seconds':time.monotonic()-started})+'\n');events.flush()
 def until(prefix):
  lines=[];deadline=time.monotonic()+30
  while True:
   line=q.get(timeout=max(.001,deadline-time.monotonic()))
   if line is None:raise RuntimeError('engine EOF before '+prefix)
   events.write(json.dumps({'direction':'stdout','line':line,'elapsed_seconds':time.monotonic()-started})+'\n');events.flush();lines.append(line)
   if line.startswith(prefix):return lines
 send('uci');uci=until('uciok')
 for required in ('Threads','Hash','OwnBook'):
  if not any(line.startswith('option name '+required+' type ') for line in uci):raise RuntimeError('missing UCI option '+required)
 for line in ('setoption name Threads value 1','setoption name Hash value 1','setoption name OwnBook value false','isready'):send(line)
 until('readyok')
 info_pattern=re.compile(r'^info depth (\d+) seldepth (\d+) score (cp|mate) (-?\d+) nodes (\d+) ')
 for request,native in zip(selected,native_rows):
  if request['id']!=native['id']:raise RuntimeError('helper request association failure')
  send('ucinewgame');send('isready');until('readyok');send('position fen '+request['fen']);send('go nodes 1024');lines=until('bestmove ')
  infos=[(line,info_pattern.match(line)) for line in lines if info_pattern.match(line)]
  best=lines[-1].split()[1];result={'id':request['id'],'sample_index':request['sample_index'],'fen':request['fen'],'native':native,'uci_bestmove':best,'uci_info':lines[:-1]}
  if native['analyzed']:
   if not infos:raise RuntimeError('completed helper has no UCI info '+request['id'])
   last,match=infos[-1];depth=int(match[1]);kind=match[3];score=int(match[4]);nodes=int(match[5]);expected_kind='cp';expected_score=native['score']
   # Match Forge UCI score formatting. Mate moves cannot be inverted to a
   # unique ply score, so compare the public representation directly.
   if abs(native['score'])>=31872:
    expected_kind='mate';expected_score=((32000-abs(native['score'])+1)//2)*(1 if native['score']>0 else -1)
   checks={'bestmove':best==native['bestmove'],'completed_depth':depth==native['depth'],'completed_score':(kind,score)==(expected_kind,expected_score),'completed_nodes_do_not_exceed_final_nodes':0<=nodes<=native['nodes']<=1024}
   result.update({'uci_last_full_depth':depth,'uci_last_full_score_type':kind,'uci_last_full_score':score,'uci_last_full_nodes':nodes,'final_node_totals_publicly_comparable':nodes==native['nodes'],'checks':checks,'status':'PASS' if all(checks.values()) else 'FAIL'})
  else:
   expected=(native.get('analysis_status')=='insufficient_budget' and native['depth']==0 and native['score'] is None and native['bestmove'] is None and not infos)
   result.update({'status':'PASS' if expected else 'FAIL','expected_incomplete':'no completed UCI score/depth; helper deliberately exposes no exact label','uci_fallback_bestmove':best})
  summary['results'].append(result);save()
 send('quit');p.stdin.close();p.wait(timeout=30);reader.join(timeout=5)
 if reader.is_alive():raise RuntimeError('stdout reader failed to finish')
 stdin_file.close();stdout_file.close();stderr_file.close();events.close();(out/'engine.exit').write_text(str(p.returncode)+'\n')
 if p.returncode:raise RuntimeError('UCI engine returned nonzero')
 summary['completed_matches']=sum(row['native']['analyzed'] and row['status']=='PASS' for row in summary['results']);summary['incomplete_expected']=sum(not row['native']['analyzed'] and row['status']=='PASS' for row in summary['results']);summary['mismatches']=sum(row['status']!='PASS' for row in summary['results']);summary['status']='PASS' if not summary['mismatches'] else 'FAIL'
except Exception as error:
 summary['status']='FAIL';summary['error']=repr(error)
 # Best-effort graceful cleanup of this owned process only; no kill or signal.
 if p is not None and p.poll() is None:
  try:p.stdin.write(b'stop\nquit\n');p.stdin.flush();p.stdin.close();p.wait(timeout=30)
  except Exception as cleanup:summary['cleanup_error']=repr(cleanup)
finally:
 save();(out/'SHA256SUMS.json').write_text(json.dumps({f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file() and f.name!='SHA256SUMS.json'},indent=2)+'\n')
print(json.dumps({key:value for key,value in summary.items() if key!='results'},indent=2));raise SystemExit(summary['status']!='PASS')
