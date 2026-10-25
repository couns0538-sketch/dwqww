#!/usr/bin/env python3
"""Cheap byte/typed-metadata controls for the output-contract reader."""
from pathlib import Path
import importlib.util,json,unittest
h=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('s25_contract',h/'forge_sol_S25_outcontract_20261025.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);allowed=json.loads((h/'forge_sol_S25_options_20261025.json').read_text())['options'];summary=b'info string bench depth 11 nodes 308972 time 123 nps 2511967\n'
def option_text(rows):
 lines=[]
 for r in rows:
  s='option name '+r['name']+' type '+r['type']
  if r['type']=='spin':s+=' default '+str(r['default'])+' min '+str(r['min'])+' max '+str(r['max'])
  elif r['type']=='check':s+=' default '+str(r['default']).lower()
  elif r['type']=='string':s+=' default '+r['default']
  lines.append(s)
 return ('\n'.join(lines)+'\nuciok\n').encode()
class ContractTests(unittest.TestCase):
 def test_canonical_bytes_and_typed_options_pass(self):
  self.assertEqual(module.inspect_bench(summary,b'',0)['status'],'PASS');self.assertEqual(module.inspect_uci(option_text(allowed),b'',0,allowed)['status'],'PASS')
 def test_CRLF_final_terminator_is_accepted_without_stripping_tail(self):
  self.assertEqual(module.inspect_bench(summary[:-1]+b'\r\n',b'',0)['status'],'PASS');self.assertEqual(module.inspect_bench(summary[:-1]+b'\r\n\r\n',b'',0)['status'],'FAIL')
 def test_blank_tail_is_rejected(self):self.assertTrue(any(r['code']=='bench_post_summary_bytes' for r in module.inspect_bench(summary+b'\n',b'',0)['errors']))
 def test_stats_tail_is_rejected(self):self.assertEqual(module.inspect_bench(summary+b'info string stats 0\n',b'',0)['status'],'FAIL')
 def test_duplicate_summary_is_rejected(self):self.assertEqual(module.inspect_bench(summary+summary,b'',0)['status'],'FAIL')
 def test_malformed_summary_is_rejected(self):self.assertEqual(module.inspect_bench(summary.replace(b' nps ',b' rate '),b'',0)['status'],'FAIL')
 def test_missing_final_newline_is_rejected(self):self.assertEqual(module.inspect_bench(summary[:-1],b'',0)['status'],'FAIL')
 def test_wrong_fixed_nodes_fails_reference_gate(self):self.assertFalse(module.inspect_bench(summary.replace(b'308972',b'308973'),b'',0)['first_d11_reference_gate_passed'])
 def test_extra_option_is_rejected(self):self.assertTrue(any(r['code']=='unexpected_option' for r in module.inspect_uci(option_text(allowed+[{'name':'Extra','type':'check','default':False}]),b'',0,allowed)['errors']))
 def test_changed_default_and_range_are_rejected(self):
  rows=[dict(r) for r in allowed];rows[0]['default']=64;rows[0]['max']=4096;self.assertTrue(any(r['code']=='option_metadata_mismatch' for r in module.inspect_uci(option_text(rows),b'',0,allowed)['errors']))
 def test_duplicate_option_is_rejected(self):self.assertTrue(any(r['code']=='duplicate_option' for r in module.inspect_uci(option_text(allowed+allowed[:1]),b'',0,allowed)['errors']))
 def test_malformed_option_is_rejected(self):self.assertEqual(module.inspect_uci(option_text(allowed).replace(b'type spin default 32',b'type spin value 32'),b'',0,allowed)['status'],'FAIL')
if __name__=='__main__':unittest.main()
