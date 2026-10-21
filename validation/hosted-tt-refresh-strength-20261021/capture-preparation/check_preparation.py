"""Source-only checks against actual22/23 receipts; child creation forbidden."""
import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepared23capture',H/'capture_actual_five.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def equal(a,b):
 if a!=b:raise AssertionError((a,b))
def check(name,fn):fn();checks.append(name)
def reject(fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError,TypeError):return
 raise AssertionError('Expected fail-closed rejection')
with patch.object(subprocess,'Popen',side_effect=AssertionError('No child authorized')):
 check('trusted461a_helper_byte_exact',lambda:equal(m.digest(m.HELPER),m.EXPECTED_HELPER))
 for label,plan in m.PLANS.items():check('actual_'+label+'_77source_release_identity',lambda label=label,plan=plan:equal(len(m.inspect_plan(label,plan)['source_sha256_before']),77))
 check('genuine22_23_complete_native_actual_schema',m.require_full_native)
 check('no_windows_dependency',lambda:equal(any('WINDOWS' in str(p) for p in m.proof_paths()),False))
 check('unauthorized_example_blocks_before_helper_load',lambda:reject(lambda:m.authorize(H/'ROOT-CAPTURE-AUTHORIZATION.example.json')))
 original=m.read;candidate=m.PLANS['candidate'];final=candidate['native']/'FINAL-RECEIPT.json';root=candidate['root_proof'];release=m.receipt_path(candidate)
 for path,key,bad in [(final,'native_ctests','42'),(final,'default_tsan_active_checks',True),(final,'default_bench11_nodes','292545'),(final,'source_export_files',True),(final,'pv_metadata_assertions_each_profile','56'),(final,'tt_coherence_groups_each_profile','12'),(final,'benchmark_processes',True),(root,'ctest','42'),(root,'active_uci','8'),(root,'engine_gate_retries',False),(root,'bench11_nodes','292545'),(root,'tt_coherence_groups_each_profile','12'),(release,'pv_metadata_contract_actual_summaries',56),(release,'tt_coherence_contract_actual_groups',12)]:
  for mode in ('missing','wrong_type'):
   altered=copy.deepcopy(original(path));altered.pop(key) if mode=='missing' else altered.update({key:bad})
   with patch.object(m,'read',side_effect=lambda p,path=path,altered=altered:copy.deepcopy(altered) if p==path else original(p)):
    check(mode+'_'+path.parent.name+'_'+key,lambda:reject(m.require_full_native))
 for key,bad in [('ctest_names',list(reversed(m.CTESTS))),('source_commit',m.BASELINE),('pv_metadata_contract_actual_summaries',[['55','0']]),('tt_coherence_contract_actual_groups',['11'])]:
  altered=copy.deepcopy(original(release));altered[key]=bad
  with patch.object(m,'read',side_effect=lambda p,altered=altered:copy.deepcopy(altered) if p==release else original(p)):
   check('release_'+key+'_reject',lambda:reject(lambda:m.inspect_plan('candidate',candidate)))
 bindings={p.relative_to(m.REPO).as_posix():m.digest(p) for p in m.proof_paths()}
 check('all_actual_named_proofs_bind',lambda:m.verify_bindings(bindings))
 for name in bindings:
  changed=dict(bindings);changed.pop(name)
  check('mandatory_missing_'+name,lambda changed=changed:reject(lambda:m.verify_bindings(changed)))
 check('wrong_type_proofmap_reject',lambda:reject(lambda:m.verify_bindings([])))
 raw=(candidate['native']/'release-signature-wrapper-attempt1/bench11.stdout.bin').read_bytes();equal(len(raw.splitlines()),1)
 check('derived_actual23_row_times5_parses',lambda:equal(len(m.sample.parse_bench(raw*5,292545)),5))
 check('wrong_signature_reject',lambda:reject(lambda:m.sample.parse_bench(raw*5,321912)))
 check('partial4rows_reject',lambda:reject(lambda:m.sample.parse_bench(raw*4,292545)))
 check('warning_reject',lambda:reject(lambda:m.sample.parse_bench(raw*5+b'warning\n',292545)))
 before=json.loads((H/'CANONICAL-PACKET-BEFORE.json').read_text())
 for path,facts in before.items():
  p=m.REPO/path;equal(m.digest(p),facts['sha256']);equal(p.stat().st_mode&0o7777,facts['mode'])
 checks.append('canonical_packet_bytes_modes_unchanged')
 for path,facts in json.loads((H/'INHERITED-REFERENCES.json').read_text()).items():equal(m.digest(m.REPO/path),facts['sha256'])
 checks.append('historical22_support_unchanged')
result={'status':'PASS_SOURCE_ONLY_PREPARATION_NOT_AUTHORIZED','checks':checks,'count':len(checks),'mandatory_proof_count':len(bindings),'mandatory_missing_controls':len(bindings),'native_actual_fields_checked':True,'native22_and23_full_qualification':True,'windows_required':False,'engine_compiler_child_executions':0,'derived_parser_fixture':'One genuine frozen23 first signature row repeated five times IN MEMORY; not an actual five-command producer capture.','driver_sha256':m.digest(H/'capture_actual_five.py'),'helper_sha256':m.digest(m.HELPER),'proof_bindings':bindings}
(H/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('checks','proof_bindings')},indent=2))
