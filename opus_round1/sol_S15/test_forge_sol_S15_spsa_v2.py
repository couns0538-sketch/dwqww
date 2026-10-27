"""Tests for forge_sol_S15_spsa_v2.py.

Part 1: Sol's 13 v1 tests (forge_sol_S15_spsa_tests_20261027.py, sha256 d0eb749f...5043), ported: the exact source
L is this branch's lock tree (two levels up) instead of a /workspace path, the scratch root comes from
FORGE_S15_TEST_ROOT instead of /tmp, and subprocesses run with -I -B. Assertions are unchanged.
Part 2: v2 tests (Windows determinism, e.p. normalization, no adjudication cap, process priority and timeout, the
`run` loop with a Python fake engine and an in-process fake fastchess, and its fail-closed paths).
No real engine or fastchess is started here.
Run:  FORGE_S15_TEST_ROOT=<new dir> python -I -B test_forge_sol_S15_spsa_v2.py -v
Env:  FORGE_S15_TOOL (tool under test; the mutation check points it at mutants), FORGE_S15_SOURCE (lock tree).
"""
import os,hashlib,importlib.util,json,math,pathlib,subprocess,sys,tempfile,time,types,unittest
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
TOOL=pathlib.Path(os.environ.get('FORGE_S15_TOOL',str(HERE/'forge_sol_S15_spsa_v2.py'))).resolve()
L=pathlib.Path(os.environ.get('FORGE_S15_SOURCE',str(HERE.parents[1]))).resolve()
_root=os.environ.get('FORGE_S15_TEST_ROOT')
WORK=pathlib.Path(_root).resolve() if _root else pathlib.Path(tempfile.mkdtemp(prefix='forge_s15_v2_tests_'))
WORK.mkdir(parents=True,exist_ok=True)
PY=[sys.executable,'-I','-B']
def module():
 if not TOOL.exists():return types.SimpleNamespace()
 spec=importlib.util.spec_from_file_location('s15',TOOL);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
M=module()
def fixture(body='int A = 5;',entry='{"A", &A, 0, 10}'):
 return 'namespace tune {\n'+body+'\nconst std::vector<Parameter>& parameters() {static const std::vector<Parameter> table{'+entry+'};return table;}\n} // namespace tune\n'

class Tests(unittest.TestCase):
 # ---------------- Part 1: Sol's v1 tests (ported) ----------------
 def test_exact_L_catalog_accounts_all_51_and_missing_NetScale(self):
  self.assertTrue(callable(getattr(M,'parse_catalog',None)),'Exact-source catalog parser is not implemented')
  c=M.parse_catalog((L/'src/search.cpp').read_text(encoding='utf-8'),(L/'src/uci.cpp').read_text(encoding='utf-8'));self.assertEqual(len(c['parameters']),51)
  self.assertEqual(c['parameters'][0],{'name':'LmrQuietBase','default':85,'minimum':0,'maximum':300})
  self.assertEqual(c['parameters'][-1],{'name':'FailLowContinuationBonus','default':0,'minimum':0,'maximum':300})
  self.assertEqual(c['unsupported_requested'],['NetScale']);self.assertNotIn('NetScale',{p['name'] for p in c['parameters']})
 def test_bad_source_cannot_silently_drop_or_misrange_parameter(self):
  for text in (fixture('int A = 2 + 3;'),fixture(entry='{"B", &A, 0, 10}'),fixture(entry='{"A", &A, 7, 10}'),fixture(entry='{"A", &A, 0, 10}, {"A", &A, 0, 10}'),fixture('int A = 5;\nint B = 2;')):
   with self.subTest(text=text),self.assertRaises(ValueError):M.parse_catalog(text,'')
 def test_integer_probes_stay_in_range_and_differ_at_bounds(self):
  c={'parameters':[{'name':'A','default':0,'minimum':0,'maximum':1}]};p=M.probes(c,[0.0],123,0,.01)
  self.assertEqual({p['plus']['A'],p['minus']['A']},{0,1});self.assertNotEqual(p['effective'][0],0)
 def test_projected_gradient_uses_maximization_sign_and_effective_integer_steps(self):
  c={'parameters':[{'name':'A','default':5,'minimum':0,'maximum':10}]};p={'theta':[.5],'plus':{'A':7},'minus':{'A':3},'effective':[.4]}
  a=M.update(c,p,1.,0.,.1);b=M.update(c,p,0.,1.,.1);self.assertAlmostEqual(a['theta'][0],.75);self.assertEqual(a['values'],{'A':8});self.assertAlmostEqual(b['theta'][0],.25)
  with self.assertRaises(ValueError):M.update(c,p,float('nan'),0.,.1)
 def test_profile_rejects_hidden_duplicate_and_wrong_ranges(self):
  c={'parameters':[{'name':'A','default':5,'minimum':0,'maximum':10}]}
  M.verify_profile(c,['A'],'option name A type spin default 5 min 0 max 10\nuciok\n')
  for text in ('uciok\n','option name A type spin default 5 min 0 max 9\nuciok\n','option name A type spin default 5 min 0 max 10\n'*2+'uciok\n'):
   with self.subTest(text=text),self.assertRaises(ValueError):M.verify_profile(c,['A'],text)
 def test_demo_is_20_iterations_deterministic_and_converges(self):
  paths=[]
  for n in ('demo_first','demo_repeat'):
   out=WORK/n;r=subprocess.run(PY+[str(TOOL),'demo','--source',str(L),'--out',str(out),'--seed','20261027','--iterations','20'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);paths.append(out)
  a={p.name:p.read_bytes() for p in paths[0].iterdir()};b={p.name:p.read_bytes() for p in paths[1].iterdir()};self.assertEqual(a,b)
  result=json.loads(a['forge_sol_S15_demo_results_20261027.json']);self.assertEqual(result['iterations'],20);self.assertLess(result['final_loss'],result['initial_loss']);self.assertEqual(result['engine_runs'],0)
 def test_existing_output_is_not_overwritten(self):
  out=WORK/'existing';out.mkdir(parents=True,exist_ok=True);p=out/'sentinel';p.write_text('keep')
  r=subprocess.run(PY+[str(TOOL),'catalog','--source',str(L),'--out',str(out)],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_text(),'keep');self.assertEqual(list(out.iterdir()),[p])
 def test_selection_rejects_missing_or_duplicate_names(self):
  c=M.parse_catalog(fixture(),'')
  for names in (['NetScale'],['A','A'],[]):
   with self.subTest(names=names),self.assertRaises(ValueError):M.select(c,names)
 def test_owned_pgn_checker_rejects_incomplete_or_non_normal_pair(self):
  checker=M.load_pgn_checker(L/'tools/match/pgn_stats.py')
  good='[Event "fixture"]\n[Round "1"]\n[White "Candidate"]\n[Black "Baseline"]\n[FEN "8/8/8/8/8/2k5/8/K7 w - - 0 1"]\n[Termination "normal"]\n[Result "1/2-1/2"]\n\n1/2-1/2\n\n[Event "fixture"]\n[Round "1"]\n[White "Baseline"]\n[Black "Candidate"]\n[FEN "8/8/8/8/8/2k5/8/K7 w - - 0 1"]\n[Termination "normal"]\n[Result "1/2-1/2"]\n\n1/2-1/2\n'
  self.assertEqual(checker.summarize(good)['score_fraction'],.5)
  for bad in (good.split('[Event "fixture"]')[0]+good.split('[Event "fixture"]')[1],good.replace('normal','time forfeit',1)):
   with self.assertRaises(ValueError):checker.summarize(bad)
 def test_NetScale_advertisement_without_source_range_remains_unsupported(self):
  c=M.parse_catalog(fixture(),'option name NetScale type spin default 100 min 50 max 200')
  self.assertEqual(c['unsupported_requested'],['NetScale'])
  with self.assertRaises(ValueError):M.select(c,['NetScale'])
 def test_mixed_type_duplicate_profile_fails_closed(self):
  c={'parameters':[{'name':'A','default':5,'minimum':0,'maximum':10}]}
  with self.assertRaises(ValueError):M.verify_profile(c,['A'],'option name A type check default false\noption name A type spin default 5 min 0 max 10\nuciok\n')
 def test_finite_scores_whose_difference_overflows_are_rejected(self):
  c={'parameters':[{'name':'A','default':5,'minimum':0,'maximum':10}]};p={'theta':[.5],'plus':{'A':7},'minus':{'A':3},'effective':[.4]}
  with self.assertRaises(ValueError):M.update(c,p,1e308,-1e308,.1)
 def test_plan_observe_preserves_original_and_detects_input_change(self):
  root=WORK/'plan_fixture';root.mkdir(parents=True,exist_ok=False)
  for name in ('engine','fastchess'):(root/name).write_bytes(b'not executable: metadata fixture only')
  fen='8/8/8/8/8/2k5/8/K7 w - - 0 1';(root/'openings.epd').write_text(fen+'\n')
  profile='option name LmrQuietBase type spin default 85 min 0 max 300\noption name QsSeeMargin type spin default 40 min 0 max 500\noption name Hash type spin default 32 min 1 max 2048\noption name Threads type spin default 1 min 1 max 256\noption name OwnBook type check default true\nuciok\n';(root/'uci.txt').write_text(profile)
  plan=root/'planned';args=PY+[str(TOOL),'plan','--source',str(L),'--out',str(plan),'--select','LmrQuietBase,QsSeeMargin','--engine',str(root/'engine'),'--fastchess',str(root/'fastchess'),'--openings',str(root/'openings.epd'),'--uci-transcript',str(root/'uci.txt'),'--pairs','1']
  r=subprocess.run(args,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  manifest=json.loads((plan/'forge_sol_S15_match_plan_20261027.json').read_text());self.assertEqual(manifest['engine_runs'],0);self.assertIn('-games',manifest['command']);self.assertIn('option.OwnBook=false',manifest['command'])
  game=lambda white,black:'[Event "fixture"]\n[Round "1"]\n[White "'+white+'"]\n[Black "'+black+'"]\n[FEN "'+fen+'"]\n[Termination "normal"]\n[Result "1/2-1/2"]\n\n1/2-1/2\n'
  raw=(game('Candidate','Baseline')+'\n'+game('Baseline','Candidate')).encode();pg=root/'synthetic.pgn';pg.write_bytes(raw)
  observed=root/'observed';cmd=PY+[str(TOOL),'observe','--plan',str(plan/'forge_sol_S15_match_plan_20261027.json'),'--pgn',str(pg),'--out',str(observed)]
  r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);state=json.loads((observed/'forge_sol_S15_observed_state_20261027.json').read_text());self.assertEqual(state['statistics']['score_fraction'],.5);self.assertIn('UNVERIFIED',state['execution_binding']);self.assertEqual((observed/'forge_sol_S15_original_games_20261027.pgn').read_bytes(),raw);self.assertEqual(pg.read_bytes(),raw)
  (root/'engine').write_bytes(b'changed fixture')
  cmd[-1]=str(root/'tampered');r=subprocess.run(cmd,capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('Pinned input changed',r.stderr);self.assertFalse((root/'tampered/forge_sol_S15_observed_state_20261027.json').exists())

 # ---------------- Part 2: v2 tests ----------------
 def test_v2_duplicate_declaration_is_rejected(self):
  with self.assertRaises(ValueError):M.parse_catalog(fixture('int A = 5;\nint A = 6;'),'')
 def test_v2_probe_directions_depend_on_iteration_and_seed_only(self):
  c=M.parse_catalog((L/'src/search.cpp').read_text(encoding='utf-8'),'');t=M.initial(c)
  a=M.probes(c,t,7,0,.1);b=M.probes(c,t,7,1,.1);again=M.probes(c,t,7,0,.1);other=M.probes(c,t,8,0,.1)
  self.assertEqual(a,again);self.assertNotEqual(a['direction'],b['direction']);self.assertNotEqual(a['direction'],other['direction'])
 def test_v2_plan_outputs_are_lf_only_have_no_adjudication_cap_and_one_thread(self):
  root=WORK/'plan_v2';root.mkdir(parents=True,exist_ok=False)
  for name in ('engine','fastchess'):(root/name).write_bytes(b'metadata fixture')
  lines=[l.split()[:4] for l in (L/'tools/openings/forge-10000.epd').read_text(encoding='utf-8').splitlines()[:8]];(root/'o.epd').write_bytes(('\n'.join(' '.join(x) for x in lines)+'\n').encode())
  (root/'uci.txt').write_bytes(b'option name LmrQuietBase type spin default 85 min 0 max 300\r\noption name QsSeeMargin type spin default 40 min 0 max 500\r\noption name Hash type spin default 32 min 1 max 2048\r\noption name Threads type spin default 1 min 1 max 256\r\noption name OwnBook type check default true\r\nuciok\r\n')
  out=root/'p';r=subprocess.run(PY+[str(TOOL),'plan','--source',str(L),'--out',str(out),'--select','LmrQuietBase,QsSeeMargin','--engine',str(root/'engine'),'--fastchess',str(root/'fastchess'),'--openings',str(root/'o.epd'),'--uci-transcript',str(root/'uci.txt'),'--pairs','2'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  for p in out.iterdir():
   with self.subTest(file=p.name):self.assertNotIn(b'\r',p.read_bytes())
  cmd=json.loads((out/'forge_sol_S15_match_plan_20261027.json').read_text())['command']
  self.assertNotIn('-maxmoves',cmd);self.assertIn('option.Threads=1',cmd);self.assertEqual(cmd[cmd.index('-concurrency')+1],'1');self.assertEqual(cmd[cmd.index('-report')+1],'penta=true');self.assertIn('-strict',cmd)
 def test_v2_observe_accepts_crlf_and_en_passant_normalized_pgn(self):
  root=WORK/'observe_v2';root.mkdir(parents=True,exist_ok=False)
  for name in ('engine','fastchess'):(root/name).write_bytes(b'metadata fixture')
  epd='r2qkb1r/ppp1pp2/n3bnp1/3p3p/1PPP2P1/N6B/P3PP1P/R1BQK1NR w KQkq h6';(root/'o.epd').write_bytes((epd+'\n').encode())
  (root/'uci.txt').write_bytes(b'option name LmrQuietBase type spin default 85 min 0 max 300\noption name Hash type spin default 32 min 1 max 2048\noption name Threads type spin default 1 min 1 max 256\noption name OwnBook type check default true\nuciok\n')
  plan=root/'p';r=subprocess.run(PY+[str(TOOL),'plan','--source',str(L),'--out',str(plan),'--select','LmrQuietBase','--engine',str(root/'engine'),'--fastchess',str(root/'fastchess'),'--openings',str(root/'o.epd'),'--uci-transcript',str(root/'uci.txt'),'--pairs','1'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  fen='r2qkb1r/ppp1pp2/n3bnp1/3p3p/1PPP2P1/N6B/P3PP1P/R1BQK1NR w KQkq - 0 1'
  game=lambda w,b,res:'[Event "f"]\r\n[Round "1"]\r\n[White "'+w+'"]\r\n[Black "'+b+'"]\r\n[FEN "'+fen+'"]\r\n[Termination "normal"]\r\n[Result "'+res+'"]\r\n\r\n'+res+'\r\n'
  raw=(game('Candidate','Baseline','1-0')+'\r\n'+game('Baseline','Candidate','0-1')).encode();pg=root/'g.pgn';pg.write_bytes(raw)
  obs=root/'obs';r=subprocess.run(PY+[str(TOOL),'observe','--plan',str(plan/'forge_sol_S15_match_plan_20261027.json'),'--pgn',str(pg),'--out',str(obs)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  state=json.loads((obs/'forge_sol_S15_observed_state_20261027.json').read_text());self.assertEqual(state['statistics']['score_fraction'],1.0);self.assertEqual((obs/'forge_sol_S15_original_games_20261027.pgn').read_bytes(),raw)
 def test_v2_matched_openings_rule(self):
  a='rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6';b='rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -'
  self.assertEqual(M.matched_openings({b},{a}),{a});self.assertEqual(M.matched_openings({a},{a}),{a})
  with self.assertRaises(ValueError):M.matched_openings({a.replace('e6','d6')},{a})
  with self.assertRaises(ValueError):M.matched_openings({b},{a,b})
  with self.assertRaises(ValueError):M.matched_openings({a},{b})
 def test_v2_child_priority_is_idle_or_below_normal(self):
  if os.name=='nt':probe='import ctypes;k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p;k.GetPriorityClass.argtypes=[ctypes.c_void_p];print(k.GetPriorityClass(k.GetCurrentProcess()))';want={'idle':0x40,'belownormal':0x4000}
  else:probe='import os;print(os.getpriority(os.PRIO_PROCESS,0))';want={'idle':19,'belownormal':10}
  for priority,expected in want.items():
   out=WORK/f'priority_{priority}.txt'
   self.assertEqual(M.run_process(PY+['-c',probe],str(WORK),None,out,60,priority),0)
   got=int(out.read_text().strip())
   if os.name=='nt':self.assertEqual(got,expected)
   else:self.assertGreaterEqual(got,expected)
  with self.assertRaises(ValueError):M.priority_kwargs('normal')
 def test_v2_run_process_timeout_kills_child_and_refuses_existing_output(self):
  out=WORK/'timeout.txt';t=time.monotonic()
  with self.assertRaises(ValueError) as caught:M.run_process(PY+['-c','import time;time.sleep(60)'],str(WORK),None,out,1,'idle')
  self.assertIn('Timeout',str(caught.exception));self.assertLess(time.monotonic()-t,30)
  with self.assertRaises(FileExistsError):M.run_process(PY+['-c','print(1)'],str(WORK),None,out,10,'idle')

 # ---- the run loop: Python fake engine + in-process fake fastchess ----
 FAKE_ENGINE=('import json,sys\ncfg=json.load(open(sys.argv[1],encoding="utf-8"))\nvals={p["name"]:p["default"] for p in cfg["parameters"]}\n'
  'for line in sys.stdin:\n w=line.split()\n if not w:continue\n if w[0]=="uci":\n  print("id name FakeForge")\n'
  '  print("option name Hash type spin default 16 min 1 max 2048");print("option name Threads type spin default 1 min 1 max 256");print("option name OwnBook type check default false")\n'
  '  if cfg["mode"]!="hidden":\n   for p in cfg["parameters"]:print("option name %s type spin default %d min %d max %d"%(p["name"],vals[p["name"]],p["minimum"],p["maximum"]))\n'
  '  print("uciok",flush=True)\n elif w[0]=="setoption" and cfg["mode"]=="apply":vals[w[2]]=int(w[4])\n elif w[0]=="quit":break\n')
 def make_run(self,name,mode='apply',results=('win',),code=0,termination='normal',penta_ok=True,extra=()):
  root=WORK/name;root.mkdir(parents=True,exist_ok=False)
  catalog=M.select(M.parse_catalog((L/'src/search.cpp').read_text(encoding='utf-8'),''),['LmrQuietBase','QsSeeMargin'])
  (root/'fake_engine.py').write_text(self.FAKE_ENGINE,encoding='utf-8');(root/'cfg.json').write_text(json.dumps({'mode':mode,'parameters':catalog['parameters']}),encoding='utf-8')
  (root/'engine').write_bytes(b'engine placeholder (UCI capture uses the Python fake)');(root/'fastchess').write_bytes(b'fastchess placeholder (the run loop uses the in-process fake)')
  lines=[l.split()[:4] for l in (L/'tools/openings/forge-10000.epd').read_text(encoding='utf-8').splitlines()[:12]];(root/'o.epd').write_bytes(('\n'.join(' '.join(x) for x in lines)+'\n').encode())
  calls=[];original=M.run_process
  def fake(argv,cwd,stdin_bytes,output_path,timeout,priority):
   if pathlib.Path(str(argv[0])).name!='fastchess':return original(argv,cwd,stdin_bytes,output_path,timeout,priority)
   calls.append(list(argv));i=len(calls)-1;kind=results[min(i,len(results)-1)];cwd=pathlib.Path(cwd)
   sel=(cwd/'forge_sol_S15_selected_openings_20261027.epd').read_text(encoding='utf-8').splitlines();games=[];penta=[0]*5
   for r,epd in enumerate(sel,1):
    f=epd.split();fen=' '.join(f[:3]+['-','0','1'])  # fastchess-style: '-' for a non-capturable e.p. square
    first,second,pair={'win':('1-0','0-1',4),'loss':('0-1','1-0',0),'draw':('1/2-1/2','1/2-1/2',2)}[kind]
    for w,b,res in (('Candidate','Baseline',first),('Baseline','Candidate',second)):
     games.append('[Event "fake"]\n[Round "%d"]\n[White "%s"]\n[Black "%s"]\n[FEN "%s"]\n[Termination "%s"]\n[Result "%s"]\n\n%s\n'%(r,w,b,fen,'normal' if i==0 else termination,res,res))  # iteration 0 stays valid
    penta[pair]+=1
   (cwd/'forge_sol_S15_original_games_20261027.pgn').write_bytes('\n'.join(games).encode())
   if not penta_ok:penta=penta[::-1] if penta!=penta[::-1] else [penta[0]+1]+penta[1:]
   pathlib.Path(output_path).write_bytes(('Finished match\nPtnml(0-2): [%s], WL/DD Ratio: 0.00\n'%', '.join(map(str,penta))).encode());return code
  saved=(M.run_process,M.engine_argv)
  M.run_process=fake;M.engine_argv=lambda engine:PY+[str(root/'fake_engine.py'),str(root/'cfg.json')]
  self.addCleanup(lambda:(setattr(M,'run_process',saved[0]),setattr(M,'engine_argv',saved[1])))
  argv=['run','--source',str(L),'--engine',str(root/'engine'),'--fastchess',str(root/'fastchess'),'--openings',str(root/'o.epd'),'--select','LmrQuietBase,QsSeeMargin','--iterations','3','--pairs','2','--tc','1+0.01','--gain','0.05','--perturbation','0.1','--out',str(root/'out')]+list(extra)
  return root,argv,calls
 def summary(self,root):return json.loads((root/'out/forge_sol_S15_run_summary_20261027.json').read_text(encoding='utf-8'))
 def test_v2_run_chains_state_rotates_openings_and_never_applies(self):
  root,argv,calls=self.make_run('run_ok',results=('win','win','win'));result=M.execute(argv)
  self.assertEqual(result['status'],'COMPLETED');s=self.summary(root);its=s['iterations'];self.assertEqual(len(its),3);self.assertEqual(len(calls),3)
  catalog=M.select(M.parse_catalog((L/'src/search.cpp').read_text(encoding='utf-8'),''),['LmrQuietBase','QsSeeMargin'])
  self.assertEqual(its[0]['theta_before'],M.initial(catalog))
  for k in (1,2):self.assertEqual(its[k]['theta_before'],its[k-1]['theta_after'])
  for it in its:
   self.assertEqual(it['score_plus'],1.0);self.assertEqual(it['fastchess_pentanomial'],[0,0,0,0,2])
   for j,d in enumerate(it['direction']):
    moved=it['theta_after'][j]-it['theta_before'][j];self.assertTrue(moved*d>0 or it['theta_after'][j] in (0.,1.),(j,d,moved))
   self.assertEqual({v['result'] for v in it['application_proof'].values()},{'APPLIED'})
  self.assertEqual(len({it['selected_openings_sha256'] for it in its}),3)
  self.assertFalse(s['tune_applied']);self.assertFalse(s['engine_source_modified']);self.assertIsNone(s['strength_claim']);self.assertEqual(s['final_values'],its[-1]['values_after'])
  for cmd in calls:self.assertIn('option.Threads=1',cmd);self.assertEqual(cmd[cmd.index('-concurrency')+1],'1')
  sums=(root/'out/forge_sol_S15_run_SHA256SUMS_20261027.txt').read_text(encoding='utf-8').splitlines();self.assertGreater(len(sums),20)
  for row in sums:
   h,rel=row.split('  ',1);self.assertEqual(M.digest(root/'out'/rel),h)
  for p in (root/'out').rglob('*.json'):self.assertNotIn(b'\r',p.read_bytes())
 def test_v2_run_fails_closed_on_fastchess_error(self):
  root,argv,calls=self.make_run('run_rc',code=1)
  with self.assertRaises(ValueError) as caught:M.execute(argv)
  self.assertIn('fastchess exited with code 1',str(caught.exception));s=self.summary(root)
  self.assertEqual((s['status'],s['iterations_completed'],len(calls)),('FAILED',0,1));self.assertFalse((root/'out/iteration_000/observed').exists())
 def test_v2_run_fails_closed_on_non_normal_termination_after_valid_iterations(self):
  root,argv,calls=self.make_run('run_term',termination='time forfeit')
  with self.assertRaises(ValueError):M.execute(argv)
  s=self.summary(root);self.assertEqual((s['status'],s['iterations_completed'],len(calls)),('FAILED',1,2));self.assertIn('non-normal termination',s['stop_reason'])
 def test_v2_run_fails_closed_on_pentanomial_disagreement(self):
  root,argv,calls=self.make_run('run_penta',penta_ok=False)
  with self.assertRaises(ValueError):M.execute(argv)
  s=self.summary(root);self.assertEqual((s['status'],s['iterations_completed']),('FAILED',0));self.assertIn('Pentanomial cross-check',s['stop_reason'])
 def test_v2_run_refuses_engine_that_ignores_setoption(self):
  root,argv,calls=self.make_run('run_ignore',mode='ignore')
  with self.assertRaises(ValueError):M.execute(argv)
  s=self.summary(root);self.assertEqual((s['status'],len(calls)),('FAILED',0));self.assertIn('did not apply',s['stop_reason'])
 def test_v2_run_refuses_hidden_tunables(self):
  root,argv,calls=self.make_run('run_hidden',mode='hidden')
  with self.assertRaises(ValueError):M.execute(argv)
  s=self.summary(root);self.assertEqual((s['status'],len(calls)),('FAILED',0));self.assertFalse((root/'out/iteration_000').exists())
 def test_v2_run_stops_on_low_ram_and_wall_budget_before_any_game(self):
  root,argv,calls=self.make_run('run_ram');saved=M.free_ram_bytes;M.free_ram_bytes=lambda:2**30;self.addCleanup(setattr,M,'free_ram_bytes',saved)
  self.assertEqual(M.execute(argv)['status'],'STOPPED_LOW_RAM');self.assertEqual(len(calls),0);self.assertEqual(self.summary(root)['iterations_completed'],0)
  M.free_ram_bytes=saved
  root,argv,calls=self.make_run('run_wall',extra=('--max-wall-seconds','10','--iteration-timeout','20'))
  self.assertEqual(M.execute(argv)['status'],'STOPPED_WALL_BUDGET');self.assertEqual(len(calls),0)
 def test_v2_run_refuses_existing_output_directory(self):
  root,argv,calls=self.make_run('run_exists');(root/'out').mkdir()
  with self.assertRaises(FileExistsError):M.execute(argv)
  self.assertEqual(list((root/'out').iterdir()),[])
 def test_v2_free_ram_reading_is_positive(self):
  free=M.free_ram_bytes();self.assertTrue(free is None or free>0)

if __name__=='__main__':unittest.main()
