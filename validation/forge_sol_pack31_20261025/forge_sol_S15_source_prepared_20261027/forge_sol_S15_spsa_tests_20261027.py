import os,hashlib,importlib.util,json,math,pathlib,subprocess,sys,types,unittest
HERE=pathlib.Path(__file__).resolve().parent
TOOL=HERE/'forge_sol_S15_spsa_20261027.py'
L=pathlib.Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src')
WORK=pathlib.Path(os.environ.get('FORGE_S15_TEST_ROOT','/tmp/forge_sol_S15_prep_20261027/test_cases'))
def module():
 if not TOOL.exists():return types.SimpleNamespace()
 spec=importlib.util.spec_from_file_location('s15',TOOL);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
M=module()
def fixture(body='int A = 5;',entry='{"A", &A, 0, 10}'):
 return 'namespace tune {\n'+body+'\nconst std::vector<Parameter>& parameters() {static const std::vector<Parameter> table{'+entry+'};return table;}\n} // namespace tune\n'
class Tests(unittest.TestCase):
 def test_exact_L_catalog_accounts_all_51_and_missing_NetScale(self):
  self.assertTrue(callable(getattr(M,'parse_catalog',None)),'Exact-source catalog parser is not implemented')
  c=M.parse_catalog((L/'src/search.cpp').read_text(),(L/'src/uci.cpp').read_text());self.assertEqual(len(c['parameters']),51)
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
  WORK.mkdir(parents=True,exist_ok=True);paths=[]
  for n in ('demo_first','demo_repeat'):
   out=WORK/n;r=subprocess.run([sys.executable,'-B',str(TOOL),'demo','--source',str(L),'--out',str(out),'--seed','20261027','--iterations','20'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);paths.append(out)
  a={p.name:p.read_bytes() for p in paths[0].iterdir()};b={p.name:p.read_bytes() for p in paths[1].iterdir()};self.assertEqual(a,b)
  result=json.loads(a['forge_sol_S15_demo_results_20261027.json']);self.assertEqual(result['iterations'],20);self.assertLess(result['final_loss'],result['initial_loss']);self.assertEqual(result['engine_runs'],0)
 def test_existing_output_is_not_overwritten(self):
  out=WORK/'existing';out.mkdir(parents=True,exist_ok=True);p=out/'sentinel';p.write_text('keep')
  r=subprocess.run([sys.executable,'-B',str(TOOL),'catalog','--source',str(L),'--out',str(out)],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_text(),'keep');self.assertEqual(list(out.iterdir()),[p])
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
  plan=root/'planned';args=[sys.executable,'-B',str(TOOL),'plan','--source',str(L),'--out',str(plan),'--select','LmrQuietBase,QsSeeMargin','--engine',str(root/'engine'),'--fastchess',str(root/'fastchess'),'--openings',str(root/'openings.epd'),'--uci-transcript',str(root/'uci.txt'),'--pairs','1']
  r=subprocess.run(args,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  manifest=json.loads((plan/'forge_sol_S15_match_plan_20261027.json').read_text());self.assertEqual(manifest['engine_runs'],0);self.assertIn('-games',manifest['command']);self.assertIn('option.OwnBook=false',manifest['command'])
  game=lambda white,black:'[Event "fixture"]\n[Round "1"]\n[White "'+white+'"]\n[Black "'+black+'"]\n[FEN "'+fen+'"]\n[Termination "normal"]\n[Result "1/2-1/2"]\n\n1/2-1/2\n'
  raw=(game('Candidate','Baseline')+'\n'+game('Baseline','Candidate')).encode();pg=root/'synthetic.pgn';pg.write_bytes(raw)
  observed=root/'observed';cmd=[sys.executable,'-B',str(TOOL),'observe','--plan',str(plan/'forge_sol_S15_match_plan_20261027.json'),'--pgn',str(pg),'--out',str(observed)]
  r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);state=json.loads((observed/'forge_sol_S15_observed_state_20261027.json').read_text());self.assertEqual(state['statistics']['score_fraction'],.5);self.assertIn('UNVERIFIED',state['execution_binding']);self.assertEqual((observed/'forge_sol_S15_original_games_20261027.pgn').read_bytes(),raw);self.assertEqual(pg.read_bytes(),raw)
  (root/'engine').write_bytes(b'changed fixture')
  cmd[-1]=str(root/'tampered');r=subprocess.run(cmd,capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('Pinned input changed',r.stderr);self.assertFalse((root/'tampered/forge_sol_S15_observed_state_20261027.json').exists())
if __name__=='__main__':unittest.main()
