"""Bounded source/data checks only. No engines, compiler children or captures."""
import ast, copy, importlib.util, json, subprocess
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('capture24_prepared',HERE/'capture_actual_five.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
checks=[]
def equal(a,b):
 if a!=b:raise AssertionError((a,b))
def check(name,fn):fn();checks.append(name)
def reject(fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError,TypeError):return
 raise AssertionError('Expected fail-closed rejection')
with patch.object(subprocess,'Popen',side_effect=AssertionError('No child authorized')):
 for name in ('capture_actual_five.py','owned_process.frozen.py','capture_validation.py','common.historical21.py'):
  check('AST_'+name,lambda name=name:ast.parse((HERE/name).read_text(),filename=name))
 check('trusted461a_byte_exact',lambda:equal(module.digest(module.HELPER),module.EXPECTED_HELPER))
 native=module.inspect_native();check('genuine_actual24_source77',lambda:equal(len(native['source_sha256_before']),77))
 check('genuine23_reuse_original_candidate_label',lambda:equal(module.inspect_reused23()['provenance_capture_label'],'candidate'))
 check('exactly_one24_plan_no23_process',lambda:equal(module.STDIN,b'bench 11\n'*5+b'quit\n'))
 check('disabled_authorization_rejected',lambda:reject(lambda:module.authorize(HERE/'ROOT-CAPTURE-AUTHORIZATION.example.json')))
 root_pending=not module.ROOT_PROOF.is_file() or module.read(HERE/'ROOT-PROOF-SCHEMA.json')['status']!='REVIEWED_GENUINE24_ROOT_PROOF_SCHEMA'
 if root_pending:check('missing_or_pending_genuine_root_proof_blocks_runtime',lambda:reject(module.require_root))
 else:
  check('genuine_root24_actual_schema_positive',module.require_root)
  with patch.object(module,'ROOT_PROOF',HERE/'NONEXISTENT-ROOT-PROOF.json'):
   check('missing_genuine_root_proof_blocks_runtime',lambda:reject(module.require_root))
  actual_read=module.read;actual_root=module.ROOT_PROOF
  for key,bad in [('ctest','42'),('active_uci',True),('exact_cold_warm_searches','56')]:
   altered=copy.deepcopy(actual_read(actual_root));altered[key]=bad
   with patch.object(module,'read',side_effect=lambda p,altered=altered:copy.deepcopy(altered) if p==actual_root else actual_read(p)):
    check('wrong_type_root_'+key+'_reject',lambda:reject(module.require_root))
  bindings={str(p):module.digest(p) for p in module.proof_paths()}
  check('every_consumed_source_build_native_root_reuse_proof_bound',lambda:module.verify_bindings(bindings))
  changed=dict(bindings);changed.pop(str(actual_root))
  check('missing_root_binding_reject',lambda:reject(lambda:module.verify_bindings(changed)))
  check('wrong_type_binding_map_reject',lambda:reject(lambda:module.verify_bindings([])))
 original=module.read;final=module.NATIVE/'FINAL-RECEIPT.json'
 for key in ('native_ctests','default_tsan_active_checks','see_threshold_assertions_each_profile','exact_cold_warm_searches'):
  altered=copy.deepcopy(original(final));altered.pop(key)
  with patch.object(module,'read',side_effect=lambda p,altered=altered:copy.deepcopy(altered) if p==final else original(p)):
   check('missing_native_'+key+'_rejected',lambda:reject(module.inspect_native))
 altered=copy.deepcopy(original(final));altered['native_ctests']='42'
 with patch.object(module,'read',side_effect=lambda p:copy.deepcopy(altered) if p==final else original(p)):
  check('wrong_type_native_count_rejected',lambda:reject(module.inspect_native))
 raw=(module.NATIVE/'release-signature-wrapper-attempt1/bench11.stdout.bin').read_bytes()
 check('genuine_first24_row_times5_derived_parser_positive',lambda:equal(len(module.sample.parse_bench(raw*5,module.EXPECTED_NODES)),5))
 check('partial_four_rows_rejected',lambda:reject(lambda:module.sample.parse_bench(raw*4,module.EXPECTED_NODES)))
 check('wrong_signature_rejected',lambda:reject(lambda:module.sample.parse_bench(raw*5,321912)))
 check('warning_row_rejected',lambda:reject(lambda:module.sample.parse_bench(raw*5+b'warning\n',module.EXPECTED_NODES)))
 for name,facts in json.loads((HERE/'PACKET-BEFORE.json').read_text()).items():
  path=module.REPO/name;equal(module.digest(path),facts['sha256']);equal(path.stat().st_mode&0o7777,facts['mode'])
 checks.append('canonical_disabled_packet_bytes_modes_unchanged')
result={'status':'PASS_SOURCE_DATA_ONLY_NOT_AUTHORIZED','checks':checks,'check_count':len(checks),
 'root_proof_schema_pending':root_pending,'candidate_sources':77,'candidate_native_manifest_entries':native['native_manifest_entries'],
 'candidate_processes_executed':0,'baseline23_processes_executed':0,'compiler_processes_executed':0,
 'derived_fixture':'One genuine first24 row repeated five times in memory; not an actual five-command capture.',
 'driver_sha256':module.digest(HERE/'capture_actual_five.py'),'helper_sha256':module.digest(module.HELPER)}
(HERE/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
