from pathlib import Path
import collections,hashlib,importlib.util,io,json,math,re,subprocess,tarfile
import chess
R=Path('/workspace/dwqww'); D=R/'validation/hosted-correction-history-strength-20261020/final-audit'; B=Path('/workspace/.cloud-setup/correction-history-result-39502109381/extracted/files')
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def J(p):return json.loads(Path(p).read_text())
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
s=J(B/'strength/summary.json');cfg=J(B/'package/protocol.json'); stats=load('data_pgn',B/'package/match/pgn_stats.py');v=load('data_windows',B/'windows_validate.py');e=load('data_build',D/'build_evidence_archive_adapter.py');w=load('data_wrapper',B/'package/run_hosted.py')
assert s['status']=='completed_independently_audited';assert cfg['baseline_sha']=='b5908f0fe9db227158d39e156652f2467252e68a' and cfg['candidate_sha']=='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
def local(n):
 prefix='/home/runner/work/dwqww/dwqww/'; assert n.startswith(prefix),n
 rel=n[len(prefix):]
 if rel.startswith('hosted-results/'):return B/rel[len('hosted-results/'):]
 if rel.startswith('.github/hosted-correction-history-strength/'):return B/'package'/rel[len('.github/hosted-correction-history-strength/'):]
 if rel=='.github/workflows/forge-hosted-correction-history-strength.yml':return B/'workflow.yml'
 if rel=='tools/match/windows_validate.py':return B/'windows_validate.py'
 return B/'proofs'/rel
assert s['final_input_rehash']['status']=='passed' and not s['final_input_rehash']['mismatches']
assert set(s['final_input_rehash']['inputs'])==set(s['frozen_inputs'])
rehashes=[]
for n,h in s['frozen_inputs'].items():
 p=local(n);a=H(p);rec=s['final_input_rehash']['inputs'][n]
 assert a==h==rec['expected_sha256']==rec['actual_sha256'] and rec['matches'] is True,n
 rehashes.append({'original':n,'archived':str(p.relative_to(B)),'sha256':a})
print('final inputs exact',len(rehashes),flush=True)
for n,h in cfg['correctness_evidence_sha256'].items():assert H(B/'proofs'/n)==h,n
consumed=e.verify_build_evidence(B,cfg,B/'artifacts/baseline/forge',B/'artifacts/candidate/forge',B/'artifacts/runner/fastchess')
print('build evidence PASS',len(consumed),flush=True)
sources={};git_count=0
for label,commit in [('baseline',cfg['baseline_sha']),('candidate',cfg['candidate_sha']),('fastchess',cfg['fastchess_sha'])]:
 inv=e.source_inventory(B/'source'/(label+'.tar'),commit);sources[label]=inv
 with tarfile.open(B/'source'/(label+'.tar')) as t:
  members={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 requests=''.join(commit+':'+n+'\n' for n in members).encode()
 result=subprocess.run(['git','cat-file','--batch'],cwd=R,input=requests,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 assert not result.stderr; stream=io.BytesIO(result.stdout)
 for name,raw in members.items():
  header=stream.readline().decode().strip().split();assert len(header)==3 and header[1]=='blob',(label,name,header)
  obj=stream.read(int(header[2]));assert stream.read(1)==b'\n';assert obj==raw,(label,name);git_count+=1
 assert not stream.read()
 print(label,'actual source files',len(inv),'exactGit',commit,flush=True)
assert sources['baseline']['src/nnue_weights.inc']==sources['candidate']['src/nnue_weights.inc']=='41487f328ff51f27417564df45b6f3139d038b7e940dedb121340bd61be9a4d3'
phase_results={};move_count=0
runtime=J(B/'package/provenance/runtime-order.json')
for phase,cap in [('aa',4),('sprt',256)]:
 out=B/'strength'/phase;text=(out/'games.pgn').read_text();st=stats.summarize(text,require_identical_pairs=phase=='aa');games=stats.games(text)
 assert st==s[phase]['statistics'];assert st['pairs']==cap and st['games']==2*cap
 selected=(out/'selected.epd').read_text().splitlines();expected=runtime[phase]
 assert H(out/'selected.epd')==expected['selected_epd_sha256'];assert selected==expected['ordered_fens'];assert len(selected)==cap
 for tags,moves in games:
  assert tags['Termination']=='normal';assert ' '.join(tags['FEN'].split()[:4])==selected[int(tags['Round'])-1]
  board=chess.Board(tags['FEN']);assert board.is_valid()
  for token in moves.split():
   move=chess.Move.from_uci(token);assert move in board.legal_moves,(phase,tags['Round'],token);board.push(move);move_count+=1
  outcome=board.outcome(claim_draw=True)
  # Native3fold/rule50 draw claims may occur before an automatic outcome; no
  # illegal moves or checkmate result mismatch is permitted.
  if board.is_checkmate(): assert tags['Result']==('0-1' if board.turn else '1-0')
 console=(out/'console.txt').read_text();assert console.rstrip().endswith('(hours:minutes:seconds)')
 assert 'Finished match' in console;assert not re.search(r'^\s*(warning|error|fatal)\b',console,re.I|re.M)
 penta=[int(n.strip()) for n in re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]',console)[-1].split(',')];assert penta==st['pentanomial_0_half_1_1half_2']
 log_lines=0; fault_lines=[]
 with (out/'fastchess.log').open(errors='strict') as log:
  for line in log:
   log_lines+=1
   if re.search(r'\[(WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]',line):fault_lines.append(line[:300])
 assert not fault_lines
 manifest=J(out/'manifest.json');assert manifest['exit_code']==0 and manifest['status']=='completed'
 for n,h in manifest['outputs'].items():assert H(out/n)==h
 command=manifest['command'];assert 'option.Threads=1' in command and 'option.Hash=32' in command and 'option.OwnBook=false' in command and 'restart=on' in command
 assert command[command.index('-concurrency')+1]=='1';assert manifest['inputs']['fastchess']['sha256']==H(B/'artifacts/runner/fastchess')
 if phase=='aa':
  assert 'nodes=10000' in command and 'tc=inf' in command
  assert manifest['inputs']['baseline']['sha256']==manifest['inputs']['candidate']['sha256']==H(B/'artifacts/baseline/forge')
  decision='aa_deterministic_readiness_only'; likelihood=None
 else:
  assert 'tc=10+0.1' in command and not any(x.startswith('nodes=') for x in command);assert '-sprt' in command
  assert manifest['inputs']['baseline']['sha256']==H(B/'artifacts/baseline/forge') and manifest['inputs']['candidate']['sha256']==H(B/'artifacts/candidate/forge')
  decision,likelihood=w.audit_likelihood(console,penta,st['pairs'],256,v);assert decision=='inconclusive_at_pair_cap'
  assert likelihood==s[phase]['likelihood_audit']
  assert not v.native_acceptance(console)
 phase_results[phase]={'statistics':st,'legal_replay':True,'decision':decision,'likelihood':likelihood,'log_lines_scanned':log_lines,'fault_lines':fault_lines,'elapsed_seconds':manifest['elapsed_seconds'],'command':command,'native_elo_last':re.findall(r'^Elo: (.*)$',console,re.M)[-1]}
 print(phase,'PASS',st['games'],'games; loglines',log_lines,flush=True)
processes=[]
for p in sorted((B/'strength').glob('*-process.json')):
 j=J(p);assert j['verdict']=='passed' and j['returncode_before_verdict']==0 and j['returncode_after_cleanup']==0 and j['owned_group_empty_before_verdict'] and j['owned_group_empty_after_cleanup'] and not j['cleanup_attempted']
 stem=p.name[:-len('-process.json')]
 for stream in ['stdout','stderr']:
  actual=H(B/'strength'/(stem+'.'+stream));assert actual==j[stream+'_sha256_before_verdict']==j[stream+'_sha256_after_cleanup']
 processes.append(p.name)
assert len(processes)==11
# Recompute the purely gross baseline readiness calibration from raw block rows.
rows=[J(B/'strength'/('bench-%02d.json'%i)) for i in range(8)]
for field in ['wall_seconds','cpu_seconds']:
 ratios=[rows[i+1][field]/rows[i][field] for i in (2,4,6)];assert ratios==s['bench_aa'][field]['ratios'];assert all(.85<=x<=1.15 for x in ratios) and .95<=sorted(ratios)[1]<=1.05
assert s['selected_cpu']==0 and s['original_affinity']==[0,1,2,3]
changed=[n for n in sorted(set(sources['baseline'])|set(sources['candidate'])) if sources['baseline'].get(n)!=sources['candidate'].get(n)]
result={'status':'PASS_VALID_COMPLETED_CAP_INCONCLUSIVE_NO_ACCEPTED_GAIN','result_commit':'a265945b62d955db454b1d0b9afc346ac3f3998b','protocol_source':{'baseline':cfg['baseline_sha'],'candidate':cfg['candidate_sha'],'fastchess':cfg['fastchess_sha']},'archive':J(Path('/workspace/.cloud-setup/correction-history-result-39502109381/TRANSPORT-VERIFIED.json')),'source_counts':{k:len(v) for k,v in sources.items()},'git_source_blobs_exact':git_count,'source_changed_paths':changed,'accepted_nnue_unchanged':True,'proof_files_rehashed':len(cfg['correctness_evidence_sha256']),'final_input_records_rehashed':len(rehashes),'final_input_records':rehashes,'archive_mode_limitation':'ZIP serializer stores every raw member mode0600; preserved original audit failure then removed ONLY relocated-mode executability replay guard in explicit data-only adapter. Original process execution, hashes and source guard retained; no original executable-mode receipt fabricated.','build_evidence_paths':len(consumed),'phase_results':phase_results,'legal_plies':move_count,'readiness_process_receipts':processes,'readiness_cpu_pin':0,'wall_emergency_seconds':18000,'natural_cap':True,'no_trim_pool_reset_resume':True,'native_descriptive_elo':'8.82 +/-16.65 as printed; not accepted gain, interval includes zero','scope':'Native hosted Linux EPYC7763 GCC14 strictv3generic; equal10+0.1 Threads1 Hash32 OwnBookfalse. No Ryzen/Windows/Stockfish/absolute Elo inference. Independent data-only audit, no engines/builds/matches/network/Git mutations.'}
(D/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print('AUDIT PASS',H(D/'AUDIT.json'),flush=True)
