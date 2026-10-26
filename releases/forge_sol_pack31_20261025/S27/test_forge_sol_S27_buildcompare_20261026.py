import importlib.util
from pathlib import Path
import unittest
import tempfile
import shutil
import copy

HERE=Path(__file__).resolve().parent
MODULE=(HERE if (HERE/'forge_sol_S27_buildcompare_20261026.py').is_file() else HERE.parent)/'forge_sol_S27_buildcompare_20261026.py'
spec=importlib.util.spec_from_file_location('compare',MODULE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ParserTests(unittest.TestCase):
 def test_numeric_timing_and_line_endings_only_are_normalized(self):
  a=m.parse_bench(b'info string bench depth 11 nodes 308972 time 9 nps 34330\n',b'',0,11,308972)
  b=m.parse_bench(b'info string bench depth 11 nodes 308972 time 15 nps 20598\r\n',b'',0,11,308972)
  self.assertIsInstance(a,dict);self.assertEqual(a['status'],'PASS');self.assertEqual(a['normalized'],b['normalized'])
 def test_tail_still_preserves_numeric_gate_for_option_audit(self):
  a=m.parse_bench(b'info string bench depth 11 nodes 308972 time 9 nps 34330\ninfo string stats 0\n',b'',0,11,308972)
  self.assertIsInstance(a,dict);self.assertEqual(a['status'],'FAIL');self.assertTrue(a['reference_gate']);self.assertIn('post_summary_bytes',a['errors'])
 def test_bench_malformed_cases(self):
  good=b'info string bench depth 11 nodes 308972 time 9 nps 34330\n'
  for stdout,stderr,exitcode in [(good+b'\n',b'',0),(good[:-1],b'',0),(b'\n'+good,b'',0),(good+good,b'',0),(good,b'warning\n',0),(good,b'',2),(good.replace(b'308972',b'308971'),b'',0)]:
   with self.subTest(stdout=stdout,stderr=stderr,exitcode=exitcode):
    result=m.parse_bench(stdout,stderr,exitcode,11,308972);self.assertIsInstance(result,dict);self.assertEqual(result['status'],'FAIL')
 def test_typed_uci_and_ids(self):
  raw=b'id name Forge\nid author team\noption name Hash type spin default 32 min 1 max 2048\noption name Book File type string default <empty>\noption name Clear Hash type button\nuciok\n'
  a=m.parse_uci(raw,b'',0);self.assertIsInstance(a,dict);self.assertEqual(a['status'],'PASS');self.assertEqual(a['options'][0]['type'],'string');self.assertEqual(len(a['ids']),2)
  for bad in [raw.replace(b'max 2048',b'max invalid'),raw+ b'stats\n',raw.replace(b'uciok\n',b''),raw.replace(b'uciok\n',b'uciok\nuciok\n'),raw.replace(b'uciok\n',b'option name Hash type check default false\nuciok\n')]:
   with self.subTest(bad=bad):self.assertEqual(m.parse_uci(bad,b'',0)['status'],'FAIL')
 def test_metadata_changes_remain_visible(self):
  a=m.parse_uci(b'option name Hash type spin default 32 min 1 max 2048\nuciok\n',b'',0)
  b=m.parse_uci(b'option name Hash type spin default 16 min 1 max 2048\nuciok\n',b'',0)
  self.assertIsInstance(a,dict);self.assertNotEqual(a['options'],b['options'])
 def test_defined_symbols_ignore_only_addresses_and_keep_multiplicity(self):
  a=m.parse_symbols(b'00001 T main\n00002 b counter\n00003 b counter\n',b'',0)
  b=m.parse_symbols(b'00020 T main\n00040 b counter\n00050 b counter\n',b'',0)
  self.assertIsInstance(a,dict);self.assertEqual(a['status'],'PASS');self.assertEqual(a['normalized'],b['normalized']);self.assertEqual(len(a['normalized']),3)
  self.assertEqual(m.parse_symbols(b'',b'',0)['status'],'FAIL');self.assertEqual(m.parse_symbols(b'00001 T main\n',b'bad',0)['status'],'FAIL')
 def test_timeout_cannot_pass_even_with_complete_looking_output(self):
  for result in [m.parse_uci(b'option name Clear Hash type button\nuciok\n',b'',None),m.parse_symbols(b'00001 T main\n',b'',None)]:
   with self.subTest(result=result):self.assertEqual(result['status'],'FAIL')
 def test_probe_rejects_file_replacement_during_protocol_capture(self):
  with tempfile.TemporaryDirectory()as folder:
   exe=Path(folder)/'protocol_fixture';exe.write_bytes(b'original');exe.chmod(0o700)
   class CaptureFixture:
    def run(self,label,argv,stdin=None):
     if label.endswith('_first_d11'):return 0,b'info string bench depth 11 nodes 308972 time 1 nps 308972000\n',b''
     if label.endswith('_uci'):
      exe.write_bytes(b'replaced');return 0,b'option name Clear Hash type button\nuciok\n',b''
     return 0,b'00001 T main\n',b''
   result=m._probe(exe,'fixture',CaptureFixture(),m.REFS,[11])
   self.assertEqual(result['status'],'FAIL')
   self.assertNotEqual(result['sha256'],result['post_probe_sha256'])
 def test_effective_recipes_reject_unsafe_math_and_changed_recipe(self):
  result=m.recipe_signature([],Path('/source'),Path('/build'),{})
  self.assertIsInstance(result,dict);self.assertEqual(result['status'],'FAIL')
 def test_realistic_recipe_root_normalization_and_strict_flag_controls(self):
  def fixture(source,build):
   rows=[]
   for name in ['bitboard','board','book','eval','eval_params','nnue','search','uci']:
    file=source+'/src/'+name+'.cpp'
    rows.append({'file':file,'directory':build,'arguments':['/usr/bin/c++']+m.FLAGS.split()+['-I'+source+'/include','-O3','-DNDEBUG','-std=gnu++20','-o',build+'/'+name+'.o','-c',file]})
   return rows,{'forge':'/usr/bin/c++ '+m.FLAGS+' -O3 -DNDEBUG main.o -o forge libforge_core.a','forge_core':'/usr/bin/ar qc libforge_core.a board.o\n/usr/bin/ranlib libforge_core.a'}
  rows,links=fixture('/source','/build');other,otherlinks=fixture('/other_source','/other_build')
  a=m.recipe_signature(rows,Path('/source'),Path('/build'),links);b=m.recipe_signature(other,Path('/other_source'),Path('/other_build'),otherlinks)
  self.assertEqual(a['status'],'PASS');self.assertEqual(a['normalized'],b['normalized'])
  for flag in ['-ffast-math','-ffp-contract=fast','-march=native','-flto=auto','-fprofile-use=/tmp/profile','-Ofast','@flags.rsp','-ffp-model=fast']:
   bad=copy.deepcopy(rows);bad[0]['arguments'].insert(1,flag)
   with self.subTest(flag=flag):self.assertEqual(m.recipe_signature(bad,Path('/source'),Path('/build'),links)['status'],'FAIL')
  missing=copy.deepcopy(rows);missing[0]['arguments'].remove('-ffp-contract=off')
  self.assertEqual(m.recipe_signature(missing,Path('/source'),Path('/build'),links)['status'],'FAIL')
 def test_compiler_cache_actual_supported_types_and_duplicates(self):
  for kind in ['STRING','FILEPATH']:
   self.assertEqual(m.compiler_from_cache('CMAKE_CXX_COMPILER:'+kind+'=/usr/bin/g++\n'),'/usr/bin/g++')
  for bad in ['', 'CMAKE_CXX_COMPILER:UNSUPPORTED=/compiler\n', 'CMAKE_CXX_COMPILER:STRING=/a\nCMAKE_CXX_COMPILER:FILEPATH=/b\n']:
   with self.subTest(cache=bad):
    with self.assertRaises(ValueError):m.compiler_from_cache(bad)
if __name__=='__main__':unittest.main()
