"""SYNTHETIC process integration; no C++ compiler or real engine is executed."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE / 'forge_sol_S26_netbatch_v4_20261026.py'
DEPS = HERE / 'forge_sol_S26_dependencies_20261026.json'
WAC = Path('/workspace/forge-sol-next-20261024/int16-review/wac300.epd')

# A fake engine is a real child process, with deterministic legal UCI replies.
ENGINE = r'''#!PYTHON
import chess,json,os,sys
NODES=NODES_LITERAL
fen=chess.STARTING_FEN
for raw in sys.stdin:
 s=raw.strip()
 if s=='uci':
  print('id name SYNTHETIC S26 fixture')
  for n,t in [('Threads','spin'),('Hash','spin'),('OwnBook','check'),('Clear Hash','button')]:print('option name '+n+' type '+t)
  print('uciok',flush=True)
 elif s=='isready':print('readyok',flush=True)
 elif s.startswith('bench '):
  d=int(s.split()[1]);print('info string bench depth %d nodes %d time 1 nps 1000'%(d,NODES[str(d)]),flush=True)
 elif s.startswith('position fen '):fen=s[13:]
 elif s.startswith('go '):
  board=chess.Board(fen)
  if s.startswith('go depth '):
   depth=int(s.split()[-1]);move='f6h5' if depth==12 else ('c6d7' if board.turn else 'c3d2');score=(629 if os.environ.get('SYNTHETIC_PIN_MISMATCH') else 661) if depth==12 else 686
   print('info depth %d score cp %d pv %s'%(depth,score,move),flush=True)
  else:move=next(iter(board.legal_moves)).uci()
  print('bestmove '+move,flush=True)
 elif s=='quit':break
'''
CMAKE = r'''#!PYTHON
import json,os,pathlib,shlex,sys
args=sys.argv[1:]
if os.environ.get('SYNTHETIC_HANG'):
 import time
 b=pathlib.Path(args[args.index('-B')+1]);b.mkdir(parents=True,exist_ok=True);(b/'SYNTHETIC_owned_pid.tmp').write_text(str(os.getpid()));os.replace(b/'SYNTHETIC_owned_pid.tmp',b/'SYNTHETIC_owned_pid');time.sleep(20)
if '--build' in args:
 b=pathlib.Path(args[args.index('--build')+1]);c=json.loads((b/'SYNTHETIC_config.json').read_text());net=(pathlib.Path(c['source'])/'src/nnue_weights.inc').read_text()
 nodes={'11':111,'13':113,'16':116,'20':120,'22':122} if net=='NET_A' else {'11':211,'13':213,'16':216,'20':220,'22':222}
 engine=ENGINE_LITERAL.replace('NODES_LITERAL',repr(nodes));p=b/'forge';p.write_text(engine);p.chmod(0o755)
 (b/'SYNTHETIC_private_net.txt').write_text(net)
 obj=b/'CMakeFiles/forge_core.dir/src/nnue.cpp.o';obj.parent.mkdir(parents=True,exist_ok=True);obj.write_text('SYNTHETIC object '+net)
 if os.environ.get('SYNTHETIC_POSTBUILD_DRIFT'):
  rows=json.loads((b/'compile_commands.json').read_text());rows[-1]['arguments'].append('-march=native');(b/'compile_commands.json').write_text(json.dumps(rows))
else:
 assert args[0]=='-S' and '-B' in args,args
 source=pathlib.Path(args[1]);b=pathlib.Path(args[args.index('-B')+1]);b.mkdir(exist_ok=True)
 opts={x[2:].split('=',1)[0]:x.split('=',1)[1] for x in args if x.startswith('-D') and '=' in x}
 cxx=opts.get('CMAKE_CXX_COMPILER',COMPILER_LITERAL);flags=shlex.split(opts.get('CMAKE_CXX_FLAGS',''))
 if opts.get('FORGE_NATIVE','OFF')=='ON':flags.append('-march=native')
 (b/'SYNTHETIC_config.json').write_text(json.dumps({'source':str(source),'argv':args,'compiler':cxx}))
 cache=['CMAKE_CXX_COMPILER:FILEPATH='+cxx]
 for key in ['CMAKE_CXX_FLAGS','CMAKE_BUILD_TYPE','FORGE_NATIVE','CMAKE_INTERPROCEDURAL_OPTIMIZATION','CMAKE_EXPORT_COMPILE_COMMANDS']:cache.append(key+':STRING='+opts.get(key,''))
 (b/'CMakeCache.txt').write_text('\n'.join(cache)+'\n')
 (b/'CTestTestfile.cmake').write_text(''.join('add_test('+name+' \"/synthetic/program\")\n' for name in ['forge_tests', 'forge_correction_history_tests', 'forge_runtime_psqt_tests', 'forge_pawn_span_tests', 'forge_nearest_pawn_tests', 'forge_pv_metadata_tests', 'forge_tt_tests', 'forge_rule50_tests', 'forge_legal_witness_tests', 'match_tool_tests', 'windows_validation_tests', 'uci_regression', 'ponder_regression', 'ownbook_regression']))
 rows=[]
 for rel in ['src/'+n+'.cpp' for n in ['bitboard','board','book','eval','eval_params','nnue','search','uci']]+['tests/tests.cpp']:
  rows.append({'directory':str(b),'file':str(source/rel),'arguments':[cxx,*flags,'-O3','-DNDEBUG','-ffp-contract=off','-std=gnu++20','-o',str(b/(rel+'.o')),'-c',str(source/rel)]})
 (b/'compile_commands.json').write_text(json.dumps(rows))
 for target in ['forge','forge_core']:
  d=b/('CMakeFiles/'+target+'.dir');d.mkdir(parents=True,exist_ok=True)
  (d/'link.txt').write_text(shlex.join([cxx,*flags,'-O3','-DNDEBUG','-o','forge','objects.o'])+'\n' if target=='forge' else '/usr/bin/ar qc libforge_core.a objects.o\n')
 if os.environ.get('SYNTHETIC_CONFIGURE_ONLY'):sys.exit(2)
print('SYNTHETIC CMake: no compiler invoked')
'''
CTEST = r'''#!PYTHON
import json,os,pathlib,sys,xml.etree.ElementTree as E
args=sys.argv[1:]
names=['forge_tests', 'forge_correction_history_tests', 'forge_runtime_psqt_tests', 'forge_pawn_span_tests', 'forge_nearest_pawn_tests', 'forge_pv_metadata_tests', 'forge_tt_tests', 'forge_rule50_tests', 'forge_legal_witness_tests', 'match_tool_tests', 'windows_validation_tests', 'uci_regression', 'ponder_regression', 'ownbook_regression']
if '--show-only=json-v1' in args:
 print(json.dumps({'kind':'ctestInfo','version':{'major':1,'minor':0},'tests':[{'name':name,'command':['/synthetic/program']} for name in names]}));sys.exit(0)
p=pathlib.Path(args[args.index('--output-junit')+1]);root=E.Element('testsuite',name='SYNTHETIC')
t=E.SubElement(root,'testcase',name='forge_tests')
if os.environ.get('SYNTHETIC_BAD_CTEST'):
 E.SubElement(t,'failure').text='FAIL: unexpected board corruption'
elif os.environ.get('SYNTHETIC_PIN_MISMATCH'):
 E.SubElement(t,'failure').text='PIN_MISMATCH: WAC 001 documented f6h5/661/d12/PV=f6h5, observed f6h5/629/d12/PV=f6h5; re-record Job C pins in a reviewed change if the lock changed'
E.SubElement(t,'system-out').text='SYNTHETIC test process'
for name in names[1:]:E.SubElement(root,'testcase',name=name)
E.ElementTree(root).write(p)
print('SYNTHETIC CTest')
sys.exit(8 if os.environ.get('SYNTHETIC_BAD_CTEST') or os.environ.get('SYNTHETIC_PIN_MISMATCH') else 0)
'''
OBJDUMP = '''#!PYTHON
print("""0000000000001000 <forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)>:
1000: vmaxps %ymm0,%ymm1,%ymm2
1001: vminps %ymm0,%ymm1,%ymm2
1002: vmulps %ymm0,%ymm1,%ymm2
1003: vaddps %ymm0,%ymm1,%ymm2
1004: ret
""")
'''

class NetBatchTests(unittest.TestCase):
 def setUp(self):
  self.assertTrue(TOOL.is_file(), 'S26 implementation missing: initial RED contract')
  spec=importlib.util.spec_from_file_location('s26_under_test',TOOL);self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
  self.temp=tempfile.TemporaryDirectory(prefix='SYNTHETIC space ',dir=HERE);self.root=Path(self.temp.name);self.addCleanup(self.temp.cleanup)
 def write(self,p,data):
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data);return p
 def fixture(self):
  b=self.root/'base';self.write(b/'CMakeLists.txt','SYNTHETIC cmake input\n');self.write(b/'tests/tests.cpp','SYNTHETIC tests retained\n');self.write(b/'src/nnue_weights.inc','NET_A');self.write(b/'src/notes.txt','SYNTHETIC original source\n')
  for name in ['bitboard','board','book','eval','eval_params','nnue','search','uci']:self.write(b/('src/'+name+'.cpp'),'SYNTHETIC translation unit '+name+'\n')
  a=self.write(self.root/'candidate A.inc','NET_A');z=self.write(self.root/'candidate B.inc','NET_B')
  refs={'schema':'forge-s26-bench-refs-v1','nets':{hashlib.sha256(x.read_bytes()).hexdigest():{'id':name,'bench':nodes,'wac1000':None,'wac_evidence':'SYNTHETIC_UNKNOWN'} for x,name,nodes in [(a,'A',{'11':111,'13':113,'16':116,'20':120,'22':122}),(z,'B',{'11':211,'13':213,'16':216,'20':220,'22':222})]}}
  self.refs=self.write(self.root/'refs.json',json.dumps(refs));self.allow=self.write(self.root/'allow.json',json.dumps({'schema':'forge-s26-allowlist-v1','test_source_sha256':[hashlib.sha256((b/'tests/tests.cpp').read_bytes()).hexdigest()],'allowed_test_failure':'forge_tests','rules':[],'pins':[]}))
  tools={}
  self.cxx=self.write(self.root/'SYNTHETIC compiler','#!'+sys.executable+'\nprint("SYNTHETIC GCC14.2.0; no compilation")\n');self.cxx.chmod(0o755)
  for k,body in [('cmake',CMAKE.replace('ENGINE_LITERAL',repr(ENGINE.replace('#!PYTHON','#!'+sys.executable))).replace('COMPILER_LITERAL',repr(str(self.cxx)))),('ctest',CTEST),('objdump',OBJDUMP)]:
   p=self.write(self.root/('SYNTHETIC '+k),body.replace('#!PYTHON','#!'+sys.executable));p.chmod(0o755);tools[k]=p
  lock=self.write(self.root/'shared.lock','UNCHANGED_LOCK_BYTES')
  self.args=['--base',str(b),'--net',str(a),'--net',str(z),'--out',str(self.root/'output'),'--bench-ref',str(self.refs),'--allowlist',str(self.allow),'--dependencies',str(DEPS),'--suite',str(WAC),'--lock-file',str(lock),'--cmake',str(tools['cmake']),'--ctest',str(tools['ctest']),'--objdump',str(tools['objdump']),'--cxx',str(self.cxx),'--timeout','3','--evidence-label','SYNTHETIC']
  return b,a,z,lock
 def invoke(self,extra=(),env=None):
  e=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='/workspace/.cloud-setup/venv/lib/python3.12/site-packages');e.update(env or {})
  return subprocess.run([sys.executable,str(TOOL),*self.args,*extra],cwd='/',env=e,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
 def test_actual_fake_process_batch_copies_each_net_and_retains_inputs(self):
  # A dropped private copy, wrong argv, source edit, or missing pipeline stage must fail.
  b,a,z,lock=self.fixture();before={str(p):p.read_bytes() for p in b.rglob('*') if p.is_file()};r=self.invoke(['--compare-lock',str(b)])
  self.assertEqual(r.returncode,0,r.stdout+r.stderr);j=json.loads((self.root/'output/result.json').read_text())
  self.assertEqual(j['evidence_kind'],'SYNTHETIC');self.assertEqual(len(j['nets']),2);self.assertEqual(j['nets'][0]['bench']['11'],111);self.assertEqual(j['nets'][1]['bench']['11'],211)
  self.assertEqual(j['compare_lock']['bench']['22'],122);self.assertEqual(j['nets'][1]['compare_lock_delta']['11'],100)
  for row,net in zip(j['nets'],[a,z]):
   self.assertEqual(Path(row['private_source'],'src/nnue_weights.inc').read_bytes(),net.read_bytes());self.assertEqual(row['wac']['evaluated'],300);self.assertEqual(row['fma']['fma_count'],0);self.assertEqual(row['ctest']['status'],'PASS')
   self.assertTrue(Path(row['engine']).is_absolute());self.assertEqual(row['source_before'],row['source_after'])
  self.assertEqual(before,{str(p):p.read_bytes() for p in b.rglob('*') if p.is_file()});self.assertEqual(lock.read_text(),'UNCHANGED_LOCK_BYTES')
  self.assertEqual(j['resource_lease']['nice'],19);self.assertEqual(len(j['resource_lease']['affinity']),1)
  self.assertLess(sum(p.stat().st_size for p in (self.root/'output').rglob('*') if p.is_file()),1024*1024,'SYNTHETIC output exceeded1MiB')
 def test_fake_ctest_unexpected_failure_aborts_without_relaxing_pins(self):
  self.fixture();r=self.invoke(env={'SYNTHETIC_BAD_CTEST':'1'});self.assertNotEqual(r.returncode,0);j=json.loads((self.root/'output/result.json').read_text());self.assertEqual(j['status'],'FAIL');self.assertIn('unexpected board corruption',j['failure']);self.assertEqual(len(j['nets']),0)
 def test_resource_guard_stops_before_any_build(self):
  self.fixture();r=self.invoke(['--min-available-bytes',str(2**63)]);self.assertNotEqual(r.returncode,0);self.assertFalse(list((self.root/'output').rglob('SYNTHETIC_config.json')))
 def test_existing_output_is_rejected_without_edits(self):
  self.fixture();out=self.root/'output';out.mkdir();self.write(out/'keep','original');r=self.invoke();self.assertNotEqual(r.returncode,0);self.assertEqual(list(out.iterdir()),[out/'keep']);self.assertEqual((out/'keep').read_text(),'original')
 def test_reference_missing_depth_and_noninteger_are_rejected(self):
  for bench in [{'11':1},{'11':True,'13':2,'16':3,'20':4,'22':5}]:
   with self.assertRaises(ValueError):self.mod.validate_bench(bench)
 def test_allowlist_rejects_pin_mismatch_and_excess_known_failures(self):
  allow={'allowed_test_failure':'forge_tests','rules':[{'pattern':r'^FAIL: known horizon$','max_count':1}],'pins':[]}
  self.assertEqual(self.mod.classify_test_output('FAIL: known horizon\n',allow)['status'],'PASS')
  for text in ['PIN_MISMATCH: changed pin\n','FAIL: unknown\n','FAIL: known horizon\nFAIL: known horizon\n']:
   with self.assertRaises(ValueError):self.mod.classify_test_output(text,allow)
 def test_source_symlink_is_rejected_before_copy(self):
  b=self.root/'base';b.mkdir();(b/'escape').symlink_to('/etc/passwd')
  with self.assertRaises(ValueError):self.mod.snapshot(b)
 def test_dependency_hash_drift_is_rejected_before_import(self):
  p=self.write(self.root/'dep.py','raise RuntimeError("must not import")\n')
  with self.assertRaises(ValueError):self.mod.load_dependency({'path':str(p),'sha256':'0'*64},'invalid_dependency')
 def test_owned_sleep_child_is_cleaned_on_ram_drop(self):
  out=self.root/'child';out.mkdir();values=iter([10**15,0]);guard=self.mod.ResourceGuard(3*1024**3,reader=lambda:next(values,0));runner=self.mod.Commands(out,guard,3)
  with self.assertRaises(RuntimeError):runner.run([sys.executable,'-c','import time; time.sleep(20)'],'owned_sleep')
  self.assertIsNotNone(runner.records[-1]['returncode']);self.assertTrue(runner.records[-1]['child_waited'])
 def test_ctest_no_tests_or_failed_unrelated_test_never_passes(self):
  for xml in ['<testsuite/>','<testsuite><testcase name="other"><failure>FAIL: known horizon</failure></testcase></testsuite>']:
   p=self.write(self.root/'ctest.xml',xml)
   with self.assertRaises(ValueError):self.mod.check_ctest(p,8,{'allowed_test_failure':'forge_tests','rules':[],'pins':[]},expected_names=sorted(self.mod.CORE_CTEST_NAMES))
 def test_imported_documentary_unknowns_are_not_measured_results(self):
  out=self.root/'import';r=subprocess.run([sys.executable,str(TOOL),'import-known','--bench-ref',str(HERE/'forge_sol_S26_bench_refs_20261026.json'),'--out',str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  self.assertEqual(r.returncode,0,r.stderr);j=json.loads((out/'result.json').read_text());self.assertFalse(j['engine_execution']);self.assertEqual(j['evidence_kind'],'SUPPLIED_DOCUMENTARY_IMPORT_NO_RERUN');self.assertIsNone(j['nets'][-1]['wac1000']);self.assertIsNone(j['nets'][-2]['wac1000']);self.assertEqual(len(list(out.glob('f0*_DOCUMENTARY.md'))),5)

 def test_every_net_gets_a_failed_table_after_ctest_rejects(self):
  # Failure in the first net must not silently omit later requested nets.
  self.fixture();r=self.invoke(env={'SYNTHETIC_BAD_CTEST':'1'});self.assertNotEqual(r.returncode,0);j=json.loads((self.root/'output/result.json').read_text())
  self.assertEqual(len(j.get('failed_nets',[])),2)
  for row in j['failed_nets']:self.assertEqual(json.loads((Path(row['job'])/'table.json').read_text())['status'],'FAIL')
 def test_reviewed_pin_allowlist_requires_both_source_and_net_identity(self):
  self.assertTrue(hasattr(self.mod,'bind_allowlist'),'reviewed pin identity binding missing')
  allow={'rules':[],'pins':[{'test_source_sha256':'a'*64,'net_sha256':'b'*64,'review_status':'REVIEWED','exact_lines':['PIN_MISMATCH: WAC 001 documented exact reviewed observation']}]}
  bound=self.mod.bind_allowlist(allow,'a'*64,'b'*64)
  self.assertEqual(self.mod.classify_test_output('PIN_MISMATCH: WAC 001 documented exact reviewed observation',bound)['status'],'PASS')
  for source,net in [('c'*64,'b'*64),('a'*64,'c'*64)]:
   with self.assertRaises(ValueError):self.mod.classify_test_output('PIN_MISMATCH: WAC 001 documented exact reviewed observation',self.mod.bind_allowlist(allow,source,net))
  with self.assertRaises(ValueError):self.mod.classify_test_output('PIN_MISMATCH: WAC 001 documented exact reviewed observation EDITED',bound)
 def test_unrelated_passing_test_cannot_emit_known_failure_diagnostics(self):
  p=self.write(self.root/'ctest.xml','<testsuite><testcase name="other"><system-out>FAIL: known horizon</system-out></testcase></testsuite>')
  with self.assertRaises(ValueError):self.mod.check_ctest(p,0,{'allowed_test_failure':'forge_tests','rules':[{'pattern':'FAIL: known horizon','max_count':1}],'pins':[]},expected_names=sorted(self.mod.CORE_CTEST_NAMES))

 def test_ctest_crash_cannot_hide_behind_one_allowed_horizon_line(self):
  allow={'allowed_test_failure':'forge_tests','rules':[{'pattern':'FAIL: known horizon','max_count':1}],'pins':[]}
  for message in ['Segmentation fault','Timeout','Subprocess aborted']:
   p=self.write(self.root/'ctest.xml','<testsuite><testcase name="forge_tests"><failure message="'+message+'"/><system-out>FAIL: known horizon</system-out></testcase></testsuite>')
   with self.assertRaises(ValueError):self.mod.check_ctest(p,8,allow,expected_names=sorted(self.mod.CORE_CTEST_NAMES))
 def test_duplicate_ctest_case_names_cannot_reset_counts(self):
  p=self.write(self.root/'ctest.xml','<testsuite><testcase name="forge_tests"/><testcase name="forge_tests"/></testsuite>')
  with self.assertRaises(ValueError):self.mod.check_ctest(p,0,{'allowed_test_failure':'forge_tests','rules':[],'pins':[]},expected_names=sorted(self.mod.CORE_CTEST_NAMES))
 def test_dependency_import_never_writes_external_bytecode_cache(self):
  dep=self.write(self.root/'dependency.py','VALUE=7\n');record={'path':str(dep),'sha256':hashlib.sha256(dep.read_bytes()).hexdigest()}
  env=dict(os.environ);env.pop('PYTHONDONTWRITEBYTECODE',None)
  code="import runpy; m=runpy.run_path("+repr(str(TOOL))+"); m['load_dependency']("+repr(record)+",'fresh_dependency')"
  r=subprocess.run([sys.executable,'-c',code],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  self.assertEqual(r.returncode,0,r.stderr);self.assertFalse((self.root/'__pycache__').exists())

 def test_reviewed_required_counts_reject_incomplete_test_output(self):
  allow={'rules':[{'pattern':'KNOWN_FAILURE: horizon','max_count':2,'group':'known'}],'required_groups':{'known':2}}
  with self.assertRaises(ValueError):self.mod.classify_test_output('KNOWN_FAILURE: horizon',allow)
 def test_pin_proposal_patch_changes_only_documented_pin_in_isolated_copy(self):
  self.assertTrue(hasattr(self.mod,'record_pin_proposal'),'isolated unreviewed pin proposal missing')
  source='constexpr int original_expected_score = 31997;\nconstexpr std::string_view documented_wac_move = "f6h5";\nconstexpr int documented_wac_score = 661;\n'
  base=self.root/'base';test=self.write(base/'tests/tests.cpp',source);out=self.root/'proposal';out.mkdir()
  obs={'cases':[{'case':'WAC001','depth':12,'score_kind':'cp','score':629,'bestmove':'f6h5','pv0':'f6h5'}]}
  self.mod.record_pin_proposal(base,out,'b'*64,obs)
  proposal=json.loads((out/'pin_proposal.json').read_text());self.assertEqual(proposal['review_status'],'UNREVIEWED');self.assertEqual(test.read_text(),source)
  r=subprocess.run(['patch','--batch','-p1','-d',str(base)],input=(out/'documented_pins_ONLY_UNREVIEWED.patch').read_text(),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(test.read_text(),'constexpr int original_expected_score = 31997;\nconstexpr std::string_view documented_wac_move = "f6h5";\nconstexpr int documented_wac_score = 629;\n')

 def test_reviewed_entry_cannot_suppress_unknown_board_failure(self):
  allow={'rules':[],'pins':[{'test_source_sha256':'a'*64,'net_sha256':'b'*64,'review_status':'REVIEWED','exact_lines':['FAIL: unexpected board corruption']}]}
  with self.assertRaises(ValueError):self.mod.bind_allowlist(allow,'a'*64,'b'*64)

 def test_sigterm_waits_for_owned_configure_child_and_keeps_failure_receipt(self):
  self.fixture();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='/workspace/.cloud-setup/venv/lib/python3.12/site-packages',SYNTHETIC_HANG='1')
  process=subprocess.Popen([sys.executable,str(TOOL),*self.args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);owned=None
  try:
   deadline=time.monotonic()+8
   while time.monotonic()<deadline:
    found=list((self.root/'output').rglob('SYNTHETIC_owned_pid')) if (self.root/'output').exists() else []
    if found:owned=int(found[0].read_text());break
    time.sleep(.025)
   self.assertIsNotNone(owned,'synthetic configure did not start');process.send_signal(signal.SIGTERM);process.communicate(timeout=5)
   self.assertTrue((self.root/'output/result.json').is_file(),'cancelled batch lost final receipt')
   self.assertEqual(json.loads((self.root/'output/result.json').read_text())['status'],'FAIL')
   with self.assertRaises(ProcessLookupError):os.kill(owned,0)
  finally:
   if owned:
    try:os.killpg(owned,signal.SIGKILL)
    except ProcessLookupError:pass
   if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)

 def test_actual_configure_argv_pins_canonical_h256_v3_recipe(self):
  self.fixture();r=self.invoke(env={'SYNTHETIC_CONFIGURE_ONLY':'1'});self.assertNotEqual(r.returncode,0)
  configs=list((self.root/'output').rglob('SYNTHETIC_config.json'));self.assertEqual(len(configs),2)
  expected='-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
  for p in configs:
   argv=json.loads(p.read_text())['argv'];self.assertIn(expected,argv);self.assertIn('-DFORGE_NATIVE=OFF',argv);self.assertIn('-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF',argv);self.assertIn('-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',argv)
 def test_effective_recipe_checks_every_test_and_production_translation_unit(self):
  self.assertTrue(hasattr(self.mod,'audit_build_recipe'),'actual compile-command guard missing')
  base,_,_,_=self.fixture();build=self.root/'fixture_build'
  recipe=self.mod.load_dependency(json.loads(DEPS.read_text())['recipe'],'s27_recipe_test')
  cmake=self.root/'SYNTHETIC cmake';canonical='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
  subprocess.run([str(cmake),'-S',str(base),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS='+canonical,'-DFORGE_NATIVE=OFF','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'],check=True,stdout=subprocess.PIPE)
  self.assertEqual(self.mod.audit_build_recipe(recipe,base,build,self.cxx)['status'],'PASS')
  path=build/'compile_commands.json';original=json.loads(path.read_text())
  for index,bad in [(5,'MISSING_H256'),(8,'MISSING_H256'),(8,'-march=native'),(8,'-DFORGE_NNUE_HIDDEN=128'),(8,'-flto'),(8,'-fprofile-generate'),(8,'-ffast-math'),(8,'-std=c++17'),(8,'-mavx512f')]:
   rows=json.loads(json.dumps(original))
   if bad=='MISSING_H256':rows[index]['arguments'].remove('-DFORGE_NNUE_HIDDEN=256')
   else:rows[index]['arguments'].append(bad)
   path.write_text(json.dumps(rows))
   with self.subTest(bad=bad,index=index),self.assertRaises(ValueError):self.mod.audit_build_recipe(recipe,base,build,self.cxx)
 def test_postbuild_compile_command_drift_blocks_before_any_engine(self):
  self.fixture();r=self.invoke(env={'SYNTHETIC_POSTBUILD_DRIFT':'1'});self.assertNotEqual(r.returncode,0)
  j=json.loads((self.root/'output/result.json').read_text());self.assertFalse(j['engine_execution']);self.assertEqual(len(j['failed_nets']),2);self.assertIn('recipe',j['failure'].lower())

 def wac_fail_fixture(self):
  self.fixture();index=self.args.index('--net',self.args.index('--net')+1);del self.args[index:index+2]
  refs=json.loads(self.refs.read_text())
  for row in refs['nets'].values():row['wac1000']=300
  self.refs.write_text(json.dumps(refs))
 def test_wac_reproduction_failure_retains_planted_pin_and_ctest_failure_once(self):
  self.wac_fail_fixture();r=self.invoke(['--record-pins'],env={'SYNTHETIC_PIN_MISMATCH':'1'});self.assertNotEqual(r.returncode,0)
  j=json.loads((self.root/'output/result.json').read_text());self.assertEqual(len(j['failed_nets']),1);row=j['failed_nets'][0]
  self.assertEqual(row['wac']['reference_status'],'FAIL');self.assertIn('pin_observations',row,'WAC score failure skipped remaining pin observations')
  self.assertEqual(row['pin_observations']['cases'][0]['score'],629);self.assertFalse(row['pin_observations']['cases'][0]['documented_pin_matches'])
  self.assertEqual(row['ctest']['status'],'FAIL');self.assertIn('PIN_MISMATCH',row['ctest']['failure'])
  self.assertEqual(len(json.loads((Path(row['job'])/'wac/processes.json').read_text())),1)
  self.assertEqual(sum(x['label']=='ctest' for x in json.loads((Path(row['job'])/'commands.json').read_text())),1)
  self.assertTrue((Path(row['job'])/'pin_proposal.json').is_file())
 def test_passing_ctest_cannot_override_wac_reproduction_failure(self):
  self.wac_fail_fixture();r=self.invoke();self.assertNotEqual(r.returncode,0);j=json.loads((self.root/'output/result.json').read_text());row=j['failed_nets'][0]
  self.assertEqual(row['wac']['reference_status'],'FAIL');self.assertIn('ctest',row,'WAC score failure skipped CTest');self.assertEqual(row['ctest']['status'],'PASS');self.assertEqual(row['status'],'FAIL');self.assertIn('WAC',row['failure'])

if __name__=='__main__':unittest.main()
