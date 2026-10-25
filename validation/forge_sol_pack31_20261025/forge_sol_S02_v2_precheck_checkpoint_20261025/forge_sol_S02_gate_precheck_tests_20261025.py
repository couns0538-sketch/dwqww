#!/usr/bin/env python3
"""Python-only protocol fixtures; no C++ engine/build/benchmark is run."""
import base64,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
TOOL=ROOT/'forge_sol_S02_gate_option_precheck_20261025.py'
FAKE='''#!/usr/bin/env python3
import sys
WARN=__WARN__
NL=__NL__
def emit(s):sys.stdout.buffer.write((s+NL).encode());sys.stdout.buffer.flush()
known={'Threads','Hash','OwnBook','Move Overhead','Ponder','AspirationDelta','Book File'}
for line in sys.stdin:
 line=line.rstrip('\\r\\n')
 if line=='uci':
  emit('id name Python fixture');emit('option name Threads type spin default 1 min 1 max 8');emit('uciok')
 elif line=='isready':emit('readyok')
 elif line.startswith('setoption name'):
  name=' '.join(line[len('setoption name'):].split(' value',1)[0].split())
  if WARN and name not in known:emit('info string unknown option'+(' '+name if name else ''))
 elif line=='quit':break
'''
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='forge_sol_S02_pyfixtures_20261025_',dir=ROOT);self.root=Path(self.tmp.name)
  self.exe=self.root/'forge_sol_S02_fake_uci_20261025.py';self.exe.write_text(FAKE.replace('__WARN__','True').replace('__NL__',repr('\n')));self.exe.chmod(0o700)
  self.manifest=self.root/'forge_sol_S02_gate_fixture_20261025.json';self.out=self.root/'forge_sol_S02_result_20261025'
 def tearDown(self):self.tmp.cleanup()
 def gates(self,options=None):return [{'id':'G_clean','Threads':1,'Hash':16,'OwnBook':False,'options':options or {'Move Overhead':25,'Ponder':False,'AspirationDelta':18}}]
 def run_tool(self,gates=None,extra=()):
  if gates is not None:self.manifest.write_text(json.dumps(gates))
  return subprocess.run([sys.executable,'-B',str(TOOL),'--manifest',str(self.manifest),'--engine',str(self.exe),'--out',str(self.out),*extra],capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 def result(self):return json.loads((self.out/'forge_sol_S02_gate_precheck_results_20261025.json').read_text())
 def test_clean_gate_passes_and_keeps_exact_lines(self):
  p=self.run_tool(self.gates());self.assertEqual(p.returncode,0,p.stderr)
  d=self.result();self.assertEqual(d['status'],'PASS');self.assertEqual(d['gates'][0]['gate'],'G_clean')
  sent=base64.b64decode(d['processes'][0]['stdin']['data']).decode()
  for line in ('setoption name Threads value 1\n','setoption name Hash value 16\n','setoption name OwnBook value false\n','setoption name Move Overhead value 25\n'):self.assertIn(line,sent)
  self.assertNotIn('\ngo ',sent);self.assertNotIn('\nbench ',sent)
 def test_typo_names_gate_and_option(self):
  p=self.run_tool(self.gates({'RefutLmrMinr':5}));self.assertEqual(p.returncode,1,p.stderr)
  text=p.stdout.decode()+p.stderr.decode();self.assertIn('G_clean',text);self.assertIn('RefutLmrMinr',text)
  self.assertEqual(self.result()['failures'][0]['option'],'RefutLmrMinr')
 def test_silent_warning_off_exe_is_rejected(self):
  self.exe.write_text(FAKE.replace('__WARN__','False').replace('__NL__',repr('\n')))
  p=self.run_tool(self.gates());self.assertEqual(p.returncode,1);self.assertIn('warn-ON',p.stdout.decode()+p.stderr.decode())
 def test_multiple_gates_are_independent(self):
  gates=self.gates()+[dict(self.gates({'Ponder':False})[0],id='G_second')]
  p=self.run_tool(gates);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(len(self.result()['processes']),2)
 def test_crlf_parser_keeps_original_bytes(self):
  self.exe.write_text(FAKE.replace('__WARN__','True').replace('__NL__',repr('\r\n')))
  p=self.run_tool(self.gates());self.assertEqual(p.returncode,0,p.stderr)
  self.assertIn(b'\r\n',base64.b64decode(self.result()['processes'][0]['stdout']['data']))
 def test_command_injection_rejected_before_output(self):
  p=self.run_tool(self.gates({'Move Overhead':'25\ngo infinite'}));self.assertEqual(p.returncode,1);self.assertFalse(self.out.exists());self.assertNotIn(b'Traceback',p.stderr)
 def test_existing_output_one_line_error(self):
  self.out.mkdir();marker=self.out/'forge_sol_S02_marker_20261025.txt';marker.write_bytes(b'untouched')
  p=self.run_tool(self.gates());self.assertEqual(p.returncode,1);self.assertEqual(marker.read_bytes(),b'untouched');self.assertEqual(len(p.stderr.decode().splitlines()),1)
 def test_duplicate_json_keys_rejected(self):
  self.manifest.write_text('[{"id":"G","Threads":1,"Hash":16,"OwnBook":false,"options":{"Ponder":true,"Ponder":false}}]')
  p=self.run_tool();self.assertEqual(p.returncode,1);self.assertFalse(self.out.exists())
 def test_overlapping_core_option_rejected(self):
  p=self.run_tool(self.gates({'Hash':32}));self.assertEqual(p.returncode,1);self.assertFalse(self.out.exists())
 def test_inputs_unchanged(self):
  self.manifest.write_text(json.dumps(self.gates()));before=(self.manifest.read_bytes(),self.exe.read_bytes());p=self.run_tool();self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(before,(self.manifest.read_bytes(),self.exe.read_bytes()))
 def test_noncanonical_core_alias_rejected(self):
  p=self.run_tool(self.gates({'Hash ':32}));self.assertEqual(p.returncode,1);self.assertFalse(self.out.exists())
 def test_reserved_name_value_token_rejected(self):
  p=self.run_tool(self.gates({'Threads value 1':999}));self.assertEqual(p.returncode,1);self.assertFalse(self.out.exists())
 def test_multitoken_value_rejected(self):
  p=self.run_tool(self.gates({'Ponder':'false junk'}));self.assertEqual(p.returncode,1);self.assertFalse(self.out.exists())
 def test_late_unknown_reply_is_not_ignored(self):
  self.exe.write_text(FAKE.replace('__WARN__','True').replace('__NL__',repr('\n')).replace("elif line=='quit':break","elif line=='quit':emit('info string unknown option Late Option');break"))
  p=self.run_tool(self.gates());self.assertEqual(p.returncode,1)
  self.assertTrue(any(x['gate']=='G_clean' and x['option']=='Late Option' for x in self.result()['failures']))
 def test_late_invalid_reply_is_not_ignored(self):
  self.exe.write_text(FAKE.replace('__WARN__','True').replace('__NL__',repr('\n')).replace("elif line=='quit':break","elif line=='quit':emit('info string invalid value for option Ponder');break"))
  p=self.run_tool(self.gates());self.assertEqual(p.returncode,1)
  self.assertTrue(any(x['option']=='Ponder' for x in self.result()['failures']))
if __name__=='__main__':unittest.main()
