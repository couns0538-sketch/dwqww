#!/usr/bin/env python3
"""Versioned source-only dispatch: original binding/transport code retained."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = Path('/tmp/forge_sol_S11_baseline_reuse_prep_20261026/forge_sol_S11_scalar_parity_reuse_run_20261026.py')
OLD_SHA = 'da2abfb05d257758f3e043f883c42db1819154b180ab23bda141f6eaa7a51163'
OBSERVER = HERE/'forge_sol_S11_scalar_parity_observer_v2_20261026.py'
OBSERVER_SHA = '63aac4e48c5aeacf5254e18a3e08774946b1cda97468b1edf5b812c03cd130cd'

GLOBALS = '''OBSERVER_PATH=Path('/tmp/forge_sol_S11_scalar_observer_v2_prep_20261026/forge_sol_S11_scalar_parity_observer_v2_20261026.py')
OBSERVER_SHA='63aac4e48c5aeacf5254e18a3e08774946b1cda97468b1edf5b812c03cd130cd'
FAILED_PARITY_PATH=Path('/tmp/forge_sol_S11_native_20261026/Lprime_three_arm_reused_baseline_once_20261026/forge_sol_S11_scalar_parity_result_20261026.json')
FAILED_PARITY_SHA='7877d436b260d802035d98d497d715a3d8c218c20df4e0180ebb425ba8c67630'
if hashlib.sha256(OBSERVER_PATH.read_bytes()).hexdigest()!=OBSERVER_SHA:raise ValueError('versioned ISA observer source changed')
if hashlib.sha256(FAILED_PARITY_PATH.read_bytes()).hexdigest()!=FAILED_PARITY_SHA:raise ValueError('original failed parity receipt changed')
proof=load('s11_scalar_proof_observer_v2',OBSERVER_PATH)
'''
PRE = "if proof.sha(OBSERVER_PATH)!=OBSERVER_SHA or proof.sha(FAILED_PARITY_PATH)!=FAILED_PARITY_SHA:p.error('versioned ISA observer/original FAIL identity changed')"
META = "result.update(schema='forge.S11.three_arm_parity.observer_v2',ISA_observer_version=2,ISA_observer_path=str(OBSERVER_PATH),ISA_observer_sha256=OBSERVER_SHA,original_failed_parity_receipt=str(FAILED_PARITY_PATH),original_failed_parity_receipt_sha256=FAILED_PARITY_SHA,observer_scope='scalar float32 arithmetic with only vmovdqa YMM-to-RSP transfers and four-XMM vblendvps selection')"
POST = "if proof.sha(OBSERVER_PATH)!=OBSERVER_SHA or proof.sha(FAILED_PARITY_PATH)!=FAILED_PARITY_SHA:raise ValueError('ISA observer or original failed attempt changed during successor parity')"
POST_RECEIPT = "result['original_failed_parity_receipt_unchanged']=True"


def replace(text, old, new):
    assert text.count(old)==1,old[:70]
    return text.replace(old,new)


def dump(node):return ast.dump(node,include_attributes=False)


def main():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==OLD_SHA
    assert hashlib.sha256(OBSERVER.read_bytes()).hexdigest()==OBSERVER_SHA
    original=OLD.read_text()
    modified=replace(original,"proof=load('s11_scalar_proof',HERE/'forge_sol_S11_scalar_parity_20261026.py')\n",GLOBALS)
    modified=replace(modified,"    baseline=bind_arm(a.baseline_build",'    '+PRE+'\n    baseline=bind_arm(a.baseline_build')
    modified=replace(modified,'    previous=owned.boundary_reason\n','    '+META+'\n    previous=owned.boundary_reason\n')
    modified=replace(modified,"            result['original_sources_and_all_artifacts_unchanged']=True\n",'            '+POST+'\n            '+POST_RECEIPT+"\n            result['original_sources_and_all_artifacts_unchanged']=True\n")
    out=HERE/'forge_sol_S11_scalar_parity_observer_v2_run_20261026.py'
    if out.exists():raise FileExistsError('new/versioned source output required')
    out.write_text(modified)
    olddefs={node.name:node for node in ast.parse(original).body if isinstance(node,ast.FunctionDef)}
    newdefs={node.name:node for node in ast.parse(modified).body if isinstance(node,ast.FunctionDef)}
    assert olddefs.keys()==newdefs.keys()
    unchanged=[name for name in olddefs if name!='main' and dump(olddefs[name])==dump(newdefs[name])]
    assert len(unchanged)==len(olddefs)-1
    # Only the explicitly enumerated pre/post identity checks and result
    # metadata may differ inside main. Every existing native/binding/corpus/
    # retention/ISA invocation/timer statement remains structurally identical.
    allowed={dump(ast.parse(code).body[0]) for code in [PRE,META,POST,POST_RECEIPT]}
    class StripOnlyObserverMetadata(ast.NodeTransformer):
        removed=0
        def visit(self,node):
            if isinstance(node,ast.stmt) and dump(node) in allowed:
                self.removed+=1;return None
            return super().visit(node)
    strip=StripOnlyObserverMetadata();normal=strip.visit(newdefs['main'])
    assert strip.removed==4,strip.removed
    assert dump(normal)==dump(olddefs['main'])
    receipt={'scope':'SOURCE_ONLY_NO_NATIVE','old_consumer':str(OLD),'old_consumer_sha256':OLD_SHA,
        'new_consumer':out.name,'new_consumer_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'new_observer_sha256':OBSERVER_SHA,'unchanged_helper_functions_AST':unchanged,
        'main_AST_identical_after_removing_exactly_four_observer_pin_metadata_statements':True,
        'binding_corpus_capture_retention_flags_and_timers_unchanged':True,'native_retries':0}
    (HERE/'forge_sol_S11_scalar_observer_v2_consumer_receipt_20261026.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
