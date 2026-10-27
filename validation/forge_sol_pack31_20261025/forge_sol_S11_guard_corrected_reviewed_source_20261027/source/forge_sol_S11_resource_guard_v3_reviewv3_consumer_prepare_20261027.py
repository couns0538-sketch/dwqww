#!/usr/bin/env python3
"""Source-only guard-v3 dispatch generator; frozen numerical logic is retained."""
from pathlib import Path
import ast
import copy
import hashlib
import json

HERE=Path(__file__).resolve().parent
OLD=Path('/tmp/forge_sol_S11_scalar_observer_v2_prep_20261026/forge_sol_S11_scalar_parity_observer_v2_run_20261026.py')
OLD_SHA='ebfec0ac47b32503318bc455a05b4901eb0ace704123d39eb1d350e461ba4464'
RESOURCE=HERE/'forge_sol_S11_resource_guard_v3_reviewv3_20261027.py'
RESOURCE_SHA='1f963425a0c1deeb13f740d4de4b37a4bc7e48d6364ecd21caa95149469f38cd'
GLOBAL='''RESOURCE_PATH=Path('/tmp/forge_sol_S11_resource_guard_v3_prep_20261027/forge_sol_S11_resource_guard_v3_reviewv3_20261027.py')
RESOURCE_SHA='1f963425a0c1deeb13f740d4de4b37a4bc7e48d6364ecd21caa95149469f38cd'
TIMEOUT_FAIL_PATH=Path('/tmp/forge_sol_S11_native_20261026/Lprime_three_arm_observer_v2_once_20261026/forge_sol_S11_scalar_parity_result_20261026.json')
TIMEOUT_FAIL_SHA='8289dd4760d78edf8ebff33ab43b814e221275a80431c4f780087c9848c5b763'
if hashlib.sha256(RESOURCE_PATH.read_bytes()).hexdigest()!=RESOURCE_SHA:raise ValueError('versioned resource observer source changed')
if hashlib.sha256(TIMEOUT_FAIL_PATH.read_bytes()).hexdigest()!=TIMEOUT_FAIL_SHA:raise ValueError('original capture timeout receipt changed')
resource_observer=load('s11_resource_observer_v3_reviewv3',RESOURCE_PATH)
'''
PRE="if proof.sha(RESOURCE_PATH)!=RESOURCE_SHA or proof.sha(TIMEOUT_FAIL_PATH)!=TIMEOUT_FAIL_SHA:p.error('resource observer/original timeout FAIL identity changed')"
META="result.update(schema='forge.S11.three_arm_parity.resource_guard_v3',resource_observer_version=3,resource_observer_review_revision=3,resource_observer_path=str(RESOURCE_PATH),resource_observer_sha256=RESOURCE_SHA,original_capture_timeout_receipt=str(TIMEOUT_FAIL_PATH),original_capture_timeout_receipt_sha256=TIMEOUT_FAIL_SHA)"
INIT='resource_guard=resource_observer.OwnedResourceGuard(a.out,deadline-2,owned,result)'
FIN1='resource_end_reason=resource_guard.finalize()'
FIN2="result['resource_guard']=resource_guard.snapshot()"
FIN3="if resource_end_reason:result['status']='FAIL';result['resource_guard_end_reason']=resource_end_reason"
POST="if proof.sha(RESOURCE_PATH)!=RESOURCE_SHA or proof.sha(TIMEOUT_FAIL_PATH)!=TIMEOUT_FAIL_SHA:raise ValueError('resource observer or original capture timeout changed during successor parity')"
POSTBOOL="result['original_capture_timeout_receipt_unchanged']=True"


def replace(text,old,new):
    assert text.count(old)==1,old[:80]
    return text.replace(old,new)


def dump(node):return ast.dump(node,include_attributes=False)


def main():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==OLD_SHA
    assert hashlib.sha256(RESOURCE.read_bytes()).hexdigest()==RESOURCE_SHA
    old=OLD.read_text();tree=ast.parse(old);oldmain=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    oldguard=next(n for n in oldmain.body if isinstance(n,ast.FunctionDef) and n.name=='guard')
    lines=old.splitlines(True)
    start=''.join(lines[oldguard.lineno-1:oldguard.end_lineno])
    new=replace(old,start,'    def guard(_job=None,end=None):\n        return resource_guard.reason(_job,end)\n')
    new=replace(new,"qual=load('s11_std_bindings',HERE/'forge_sol_S11_qualify_native_20261026.py')\n",GLOBAL+"qual=load('s11_std_bindings',HERE/'forge_sol_S11_qualify_native_20261026.py')\n")
    new=replace(new,'    baseline=bind_arm(a.baseline_build','    '+PRE+'\n    baseline=bind_arm(a.baseline_build')
    new=replace(new,'    previous=owned.boundary_reason\n','    '+META+'\n    previous=owned.boundary_reason\n    '+INIT+'\n')
    new=replace(new,'        owned.boundary_reason=previous\n','        owned.boundary_reason=previous\n        '+FIN1+'\n        '+FIN2+'\n        '+FIN3+'\n')
    new=replace(new,"            result['original_failed_parity_receipt_unchanged']=True\n",'            '+POST+'\n            '+POSTBOOL+"\n            result['original_failed_parity_receipt_unchanged']=True\n")
    out=HERE/'forge_sol_S11_scalar_parity_resource_guard_v3_reviewv3_run_20261027.py'
    if out.exists():raise FileExistsError('new named successor output required')
    out.write_text(new)
    olddefs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    newdefs={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
    assert olddefs.keys()==newdefs.keys()
    same=[name for name in olddefs if name!='main' and dump(olddefs[name])==dump(newdefs[name])]
    assert len(same)==len(olddefs)-1
    allowed={dump(ast.parse(code).body[0]) for code in [PRE,META,INIT,FIN1,FIN2,FIN3,POST,POSTBOOL]}
    class NormalizeResourceOnly(ast.NodeTransformer):
        removed=0;guards=0
        def visit(self,node):
            if isinstance(node,ast.FunctionDef) and node.name=='guard':
                self.guards+=1;return copy.deepcopy(oldguard)
            if isinstance(node,ast.stmt) and dump(node) in allowed:
                self.removed+=1;return None
            return super().visit(node)
    normalize=NormalizeResourceOnly();normal=normalize.visit(newdefs['main'])
    assert normalize.removed==8 and normalize.guards==1,(normalize.removed,normalize.guards)
    assert dump(normal)==dump(oldmain)
    receipt={'scope':'SOURCE_ONLY_NO_NATIVE','old_consumer_sha256':OLD_SHA,'resource_helper_sha256':RESOURCE_SHA,'new_consumer_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'unchanged_helper_functions_AST':same,'main_AST_identical_after_exact_resource_guard_replacement_and_eight_pin_metadata_statements_removed':True,
        'engine_source_producer_numerical_proof_flags_corpus_capture_retention_and_timers':'unchanged','native_retries':0}
    (HERE/'forge_sol_S11_resource_guard_v3_reviewv3_consumer_source_receipt_20261027.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
