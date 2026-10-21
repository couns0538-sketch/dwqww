"""Bounded source-only adapter controls. Never run a child or imported helper."""
import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepared22capture',H/'capture_actual_five.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def check(name,fn):
 fn();checks.append(name)
def equal(a,b):
 if a!=b:raise AssertionError((a,b))
def reject(fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError):return
 raise AssertionError('Expected fail-closed rejection')
with patch.object(subprocess,'Popen',side_effect=AssertionError('No child authorized')):
 check('trusted461a_helper',lambda:equal(m.digest(m.HELPER),m.EXPECTED_HELPER))
 for label,p in m.PLANS.items():check('actual_'+label+'_source_release_identity',lambda label=label,p=p:equal(len(m.inspect_plan(label,p)['source_sha256_before']),p['files']))
 baseline=m.PLANS['baseline'];candidate=m.PLANS['candidate']
 with patch.object(m,'PLANS',{'baseline':baseline}):check('genuine21_full_native_and_windows_schema',m.require_full_native)
 check('authorization_example_blocks_before_helper_load',lambda:reject(lambda:m.authorize(H/'ROOT-CAPTURE-AUTHORIZATION.example.json')))
 check('actual22_full_native_gate_not_yet_complete',lambda:reject(m.require_full_native))
 original=m.read;rp=m.receipt_path(candidate)
 for label,mutate in [('missing_pv_summary',lambda x:x.pop('pv_metadata_contract_actual_summaries')),('wrong_pv_summary_type',lambda x:x.update(pv_metadata_contract_actual_summaries=56)),('wrong_pv_test_order',lambda x:x['ctest_names'].reverse()),('wrong_commit',lambda x:x.update(source_commit=m.BASELINE))]:
  receipt=copy.deepcopy(original(rp));mutate(receipt)
  with patch.object(m,'read',side_effect=lambda path,receipt=receipt:copy.deepcopy(receipt) if path==rp else original(path)):
   check(label,lambda:reject(lambda:m.inspect_plan('candidate',candidate)))
 # Repeat the genuine single22 row only as a DERIVED parser fixture, never as a producer capture.
 original_single=(candidate['native']/'release-signature-wrapper-attempt1/bench11.stdout.bin').read_bytes()
 equal(len(original_single.splitlines()),1)
 check('derived_five22_rows_expected292545',lambda:equal(len(m.sample.parse_bench(original_single*5,292545)),5))
 check('derived22_rows_reject_old321912',lambda:reject(lambda:m.sample.parse_bench(original_single*5,321912)))
 check('partial_four_rows_reject',lambda:reject(lambda:m.sample.parse_bench(original_single*4,292545)))
 check('warning_row_reject',lambda:reject(lambda:m.sample.parse_bench(original_single*5+b'warning\n',292545)))
 before=json.loads((H/'CANONICAL-PACKET-BEFORE.json').read_text())
 for path,facts in before.items():
  p=m.REPO/path;equal(hashlib.sha256(p.read_bytes()).hexdigest(),facts['sha256']);equal(p.stat().st_mode&0o7777,facts['mode'])
 checks.append('canonical_packet_byte_and_mode_unchanged')
result={'status':'PASS_PREPARATION_ONLY_NO_CAPTURES','checks':checks,'count':len(checks),'engine_compiler_child_executions':0,'derived_parser_fixture':'One genuine frozen22 native signature row repeated five times IN MEMORY, not a capture; old21 files untouched.','actual_full22_qualification':False}
(H/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
