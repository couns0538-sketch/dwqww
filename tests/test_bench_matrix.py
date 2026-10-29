#!/usr/bin/env python3
"""Process-level bench matrix tests with a controlled fake UCI executable."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "bench_matrix.py"
FAKE = r'''#!/usr/bin/env python3
import sys,time
from pathlib import Path
SCENARIO = SCENARIO_VALUE
count_file=Path(__file__).with_suffix(".count")
process_number=int(count_file.read_text())+1 if count_file.exists() else 1
count_file.write_text(str(process_number))
pins={11:312866,13:862329,16:3024920,20:12389307,22:34048354}
mode='OFF'; tune=0
for raw in sys.stdin:
 cmd=raw.strip()
 if cmd=='uci':
  print('option name Threads type spin default 1 min 1 max 256')
  print('option name Hash type string default 32' if SCENARIO=='wrong_control_type' else 'option name Hash type spin default 32 min 1 max 2048')
  print('option name OwnBook type check default true')
  print('option name BundlePreset type combo default OFF var OFF var B1 var B2')
  print('option name Tune type spin default 0 min -5 max 5')
  print('option name Toggle type check default false')
  print('option name Clear Hash type button')
  print('option name Book File type string default <empty>')
  if SCENARIO=='duplicate_option': print('option name Tune type spin default 0 min -5 max 5')
  if SCENARIO=='bad_range': print('option name Broken type spin default 0 min 5 max 1')
  if SCENARIO=='no_uciok': print('info string uciok')
  else: print('uciok')
  if SCENARIO=='blocked_stdin' and process_number>5:
   sys.stdout.flush(); time.sleep(10)
 elif cmd.startswith('setoption'):
  if 'name BundlePreset value ' in cmd: mode=cmd.rsplit('value ',1)[1]; tune=0
  if 'name Tune value ' in cmd: tune=int(cmd.rsplit('value ',1)[1])
  if SCENARIO in ('refused','invalid','unknown'):
   print({'refused':'info string Tune refused: test','invalid':'info string invalid value for option Tune','unknown':'info string unknown option Tune'}[SCENARIO])
 elif cmd=='isready':
  if SCENARIO=='no_ready': print('info string readyok')
  else: print('readyok')
 elif cmd.startswith('bench '):
  d=int(cmd.split()[1]); n=pins[d]+(100 if mode=='B1' else 200 if mode=='B2' else 0)+tune
  if SCENARIO=='mismatch': n+=1
  if SCENARIO=='wrong_depth': d+=1
  if SCENARIO=='timeout': time.sleep(10)
  if SCENARIO=='malformed': print(f'info string bench depth {d} nodes wrong time 1 nps 1000')
  else: print(f'info string bench depth {d} nodes {n} time 100 nps {n*10}')
  if SCENARIO=='duplicate_bench': print(f'info string bench depth {d} nodes {n} time 100 nps {n*10}')
  if SCENARIO=='stderr_error': print('info string unknown option Tune',file=sys.stderr)
  print('raw-stderr-\N{SNOWMAN}',file=sys.stderr)
 elif cmd=='quit':
  if SCENARIO=='bad_exit': sys.exit(7)
  if SCENARIO=='hang_quit': time.sleep(10)
  break
 sys.stdout.flush(); sys.stderr.flush()
'''

class BenchMatrixTests(unittest.TestCase):
    def invoke(self, scenario="normal", sets=None, timeout="2"):
        tmp=tempfile.TemporaryDirectory(prefix="forge matrix ")
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name); exe=root/"fake forge"
        exe.write_text(FAKE.replace("SCENARIO_VALUE",repr(scenario)),encoding="utf-8"); exe.chmod(0o700)
        config=root/"sets.json"; config.write_text(json.dumps(sets or []),encoding="utf-8")
        out=root/"results"
        p=subprocess.run([sys.executable,str(TOOL),str(exe),"--sets",str(config),"--out-dir",str(out),"--timeout",timeout],capture_output=True,text=True,timeout=20,cwd=root)
        return p,out,exe,config

    def test_off_full_matrix_and_byte_logs(self):
        p,out,_,_=self.invoke()
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        doc=json.loads((out/"results.json").read_text())
        self.assertEqual([c["nodes"] for c in doc["cells"]],[312866,862329,3024920,12389307,34048354])
        self.assertEqual(doc["status"],"PASS")
        self.assertEqual(doc["binary_sha256_before"],doc["binary_sha256_after"])
        self.assertIn("raw-stderr-☃".encode(),(out/"cell_000.stderr").read_bytes())
        self.assertIn("d22",p.stdout)

    def test_preset_order_and_override_preserved(self):
        sets=[{"name":"B1override","options":[["BundlePreset","B1"],["Tune",2]]},
              {"name":"B2","options":[["BundlePreset","B2"]]}]
        p,out,_,_=self.invoke(sets=sets)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        doc=json.loads((out/"results.json").read_text())
        self.assertEqual(len(doc["cells"]),15)
        self.assertEqual(doc["cells"][5]["nodes"],312968)
        commands=(out/"cell_005.stdin").read_text()
        self.assertLess(commands.index('BundlePreset value B1'),commands.index('Tune value 2'))

    def test_protocol_failures_cannot_pass(self):
        for scenario in ['duplicate_option','bad_range','no_uciok','no_ready','mismatch','wrong_depth',
                         'malformed','duplicate_bench','wrong_control_type','refused','invalid','unknown','bad_exit','stderr_error','timeout','hang_quit']:
            with self.subTest(scenario=scenario):
                p,out,_,_=self.invoke(scenario,timeout="0.15")
                self.assertNotEqual(p.returncode,0,p.stdout)
                self.assertEqual(json.loads((out/"results.json").read_text())["status"],"FAIL")

    def test_invalid_requested_options_fail(self):
        for option in [["Missing",1],["Tune",6],["Toggle","1"],["BundlePreset","NOPE"],
                       ["Threads",2],["Hash",32],["OwnBook",True],["Clear Hash","false"]]:
            with self.subTest(option=option):
                p,out,_,_=self.invoke(sets=[{"name":"bad","options":[option]}])
                self.assertNotEqual(p.returncode,0,p.stdout)
                self.assertIn("FAIL",p.stdout+p.stderr)

    def test_reserved_off_label_and_injection_fail_before_spawn(self):
        for sets in [[{"name":"OFF","options":[["Tune",1]]}],
                     [{"name":"off","options":[]}],
                     [{"name":"x","options":[["Tune\nquit",1]]}],
                     [{"name":"x","options":[["Book File","x\nquit"]]}]]:
            with self.subTest(sets=sets):
                p,_,_,_=self.invoke(sets=sets)
                self.assertNotEqual(p.returncode,0,p.stdout)

    def test_control_type_rejected_and_button_string_accepted(self):
        p,_,_,_=self.invoke('wrong_control_type')
        self.assertNotEqual(p.returncode,0,p.stdout)
        p,out,_,_=self.invoke(sets=[{"name":"strings","options":[["Clear Hash",None],["Book File","a path with spaces"]]}])
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        wire=(out/"cell_005.stdin").read_text()
        self.assertIn("setoption name Clear Hash\n",wire)
        self.assertIn("setoption name Book File value a path with spaces\n",wire)

    def test_stdin_backpressure_is_bounded(self):
        started=time.monotonic()
        p,out,_,_=self.invoke('blocked_stdin',sets=[{"name":"longpath","options":[["Book File","x"*131072]]}],timeout="0.2")
        self.assertNotEqual(p.returncode,0,p.stdout)
        self.assertLess(time.monotonic()-started,5,"stdin backpressure escaped the cell deadline")
        self.assertEqual(json.loads((out/"results.json").read_text())["status"],"FAIL")

    def test_failed_atomic_replace_preserves_completed_ledger(self):
        p,out,exe,config=self.invoke()
        self.assertEqual(p.returncode,0,p.stderr)
        sys.path.insert(0,str(ROOT/"tools"))
        try:
            spec=importlib.util.spec_from_file_location("matrix_atomic_test",TOOL)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        atomic=out.parent/"atomic_failure"
        real_replace=module.os.replace
        calls=0
        retained=None
        def fail_after_first_cell(source,destination):
            nonlocal calls,retained
            calls+=1
            if calls>=3:
                if retained is None:
                    retained=Path(destination).read_bytes()
                raise OSError("injected replace failure after one completed cell")
            return real_replace(source,destination)
        with mock.patch.object(module.os,"replace",side_effect=fail_after_first_cell):
            with self.assertRaises(OSError):
                module.main([str(exe),"--sets",str(config),"--out-dir",str(atomic),"--timeout","2"])
        self.assertEqual((atomic/"results.json").read_bytes(),retained)
        ledger=json.loads(retained)
        self.assertEqual(ledger["status"],"RUNNING")
        self.assertEqual(len(ledger["cells"]),1)
        self.assertEqual(ledger["cells"][0]["status"],"PASS")
        self.assertEqual(ledger["cells"][0]["nodes"],312866)
        self.assertTrue((atomic/"cell_001.stdout").exists(),"the following cell's raw evidence survives too")

    def test_existing_directory_is_not_overwritten(self):
        p,out,exe,config=self.invoke()
        self.assertEqual(p.returncode,0,p.stderr)
        before=(out/"results.json").read_bytes()
        p=subprocess.run([sys.executable,str(TOOL),str(exe),"--sets",str(config),"--out-dir",str(out)],capture_output=True,text=True,timeout=10)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(before,(out/"results.json").read_bytes())

if __name__=="__main__": unittest.main()
