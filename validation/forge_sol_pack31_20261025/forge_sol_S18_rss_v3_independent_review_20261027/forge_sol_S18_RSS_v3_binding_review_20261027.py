"""Read-only binding/AST/raw-control audit; no imports of the reviewed controller."""
import ast
import copy
import hashlib
import json
from pathlib import Path

if not __debug__:
    raise RuntimeError('Run without -O/PYTHONOPTIMIZE')
OUT=Path(__file__).resolve().parent
ROOT=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027')
OLD=Path('/tmp/forge_sol_S18_TRAIN_SMOKE_V2_PREP_20261026/forge_sol_S18_train_selected_v2_20261026.py')
NEW=ROOT/'prep/forge_sol_S18_train_selected_v3_20261027.py'
FAIL=Path('/tmp/forge_sol_S18_none_smoke_failed_checkpoint_20261027')
EXTRA={'last_rss_observation','first_fallback_observation','fallback_samples'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(node):return ast.dump(node,include_attributes=False)
def verify_manifest(root,name,expected):
    p=root/name
    assert sha(p)==expected
    paths=[]
    for row in p.read_text().splitlines():
        digest,rel=row.split('  ',1);r=Path(rel)
        assert not r.is_absolute() and '..' not in r.parts
        f=root/r;assert f.is_file() and not f.is_symlink() and sha(f)==digest
        paths.append(rel)
    assert len(paths)==len(set(paths))
    return {'path':str(p),'sha256':expected,'entries':len(paths),'all_actual_bytes_match':True}
def main():
    packet=verify_manifest(ROOT,'forge_sol_S18_rss_v3_checkpoint_SHA256SUMS_20261027.txt','943de8940e7ced4d1fa9f9d8742ce4d220b447f375511e6ea2254d73feb0297a')
    failure=verify_manifest(FAIL,'forge_sol_S18_none_failed_SHA256SUMS_20261027.txt','3659229a73d0d2daff73d50bb4f75259f87b542501d71a44769bb09e1505f964')
    assert sha(OLD)=='469f341ac5b5d1a3859c8bc9ad3815757bf93d048ba24ff30413e84010433b35'
    assert sha(NEW)=='ab02ac6a4579bf37b3ea65f2bb07c4d5d08a33bd6b19d6130bc3f8d1369f1e76'
    assert sha(NEW)==sha(Path('/tmp/forge_sol_S18_RSS_SCOPE_V3_PREP_20261027')/NEW.name)
    old=ast.parse(OLD.read_text());new=ast.parse(NEW.read_text())
    olddefs={x.name:x for x in old.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    newdefs={x.name:x for x in new.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    changed=[n for n in olddefs if dump(olddefs[n])!=dump(newdefs[n])]
    added=sorted(set(newdefs)-set(olddefs))
    assert set(changed)=={'read_rss_bytes','RSSGuard','run_controller'}
    assert added==['owned_task_ids','read_proc_status']
    exclude=set(changed)|set(added)
    assert dump(ast.Module(body=[x for x in old.body if getattr(x,'name',None) not in exclude],type_ignores=[]))==dump(ast.Module(body=[x for x in new.body if getattr(x,'name',None) not in exclude],type_ignores=[]))
    class RestoreOldGuard(ast.NodeTransformer):
        counts={'diagnostic_assignments':0,'observation_local':0,'fallback_diagnostic_if':0,'observation_keyword':0}
        def visit_Assign(self,node):
            if len(node.targets)==1:
                target=node.targets[0]
                if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and target.value.id=='self' and target.attr in EXTRA:
                    self.counts['diagnostic_assignments']+=1;return None
                if isinstance(target,ast.Name) and target.id=='observation':
                    self.counts['observation_local']+=1;return None
            return self.generic_visit(node)
        def visit_If(self,node):
            test=node.test
            if isinstance(test,ast.Compare) and isinstance(test.left,ast.Call) and isinstance(test.left.func,ast.Attribute) and isinstance(test.left.func.value,ast.Name) and test.left.func.value.id=='observation':
                assert ast.unparse(test)=="observation.get('scope') == 'OWNED_LIVE_THREAD_SHARED_MM'"
                self.counts['fallback_diagnostic_if']+=1;return None
            return self.generic_visit(node)
        def visit_Call(self,node):
            if isinstance(node.func,ast.Name) and node.func.id=='read_rss_bytes':
                assert len(node.keywords)==1 and node.keywords[0].arg=='observation'
                node.keywords=[];self.counts['observation_keyword']+=1
            return self.generic_visit(node)
    transform=RestoreOldGuard();restored=transform.visit(copy.deepcopy(newdefs['RSSGuard']))
    assert dump(restored)==dump(olddefs['RSSGuard'])
    assert transform.counts=={'diagnostic_assignments':5,'observation_local':1,'fallback_diagnostic_if':1,'observation_keyword':1}
    class RestoreOldReceipts(ast.NodeTransformer):
        removed=0
        def visit_Dict(self,node):
            keep=[]
            for key,value in zip(node.keys,node.values):
                if isinstance(key,ast.Constant) and key.value in EXTRA:self.removed+=1
                else:keep.append((key,value))
            node.keys=[x[0] for x in keep];node.values=[x[1] for x in keep]
            return self.generic_visit(node)
    receipts=RestoreOldReceipts();restored=receipts.visit(copy.deepcopy(newdefs['run_controller']))
    assert receipts.removed==6 and dump(restored)==dump(olddefs['run_controller'])
    controls=[]
    for label in ('natural','rss_limit'):
        p=ROOT/'live_controls'/label/'forge_sol_S18_live_control_result_20261027.json';r=json.loads(p.read_text())
        assert r['status']=='PASS_OWN_CONTROL' and r['leader_reaped'] and r['all_owned_group_members_after_close']==[] and not r['forced_cleanup'] and r['stderr_bytes']==0
        obs=r['first_fallback_observation'];assert obs['owned_pid']==r['pid'] and obs['scope']=='OWNED_LIVE_THREAD_SHARED_MM' and obs['leader_state']=='Z'
        task=next(x for x in obs['tasks'] if x['tid']==obs['selected_tid'])
        fields={k:v.strip() for k,sep,v in (line.partition(':') for line in task['status_original'].splitlines()) if sep}
        assert int(fields['Tgid'])==r['pid'] and int(fields['Pid'])==obs['selected_tid'] and fields['State'].split()[0] not in ('Z','X')
        assert int(fields['VmRSS'].split()[0])*1024==obs['rss_bytes']==task['rss_bytes']
        if label=='natural':assert r['returncode']==0 and r['guard_stop_reason'] is None and r['first_guard_signal_monotonic'] is None and r['fallback_samples']==92
        else:assert r['returncode']==-15 and r['guard_stop_reason']=='RSS_LIMIT' and r['max_sampled_rss_bytes']>r['rss_limit_bytes']==1048576 and r['fallback_samples']==1
        controls.append({k:r[k] for k in ('pid','returncode','fallback_samples','guard_stop_reason','rss_limit_bytes','max_sampled_rss_bytes','all_owned_group_members_after_close','leader_reaped','forced_cleanup','stderr_bytes')})
        controls[-1].update(case=label,result_path=str(p),result_sha256=sha(p),actual_same_Tgid_selected_worker_RSS_verified=True)
    report={'status':'PASS_READ_ONLY_BINDING_AUDIT','packet':packet,'original_failed_case':failure,'old_source_sha256':sha(OLD),'new_source_sha256':sha(NEW),'changed_existing_AST_nodes':changed,'added_AST_nodes':added,'all_other_top_level_AST_including_globals_imports_identical':True,'unchanged_definitions':[n for n in olddefs if n not in changed],'guard_identical_after_only_bounded_observer_diagnostic_delta':True,'guard_normalization_counts':transform.counts,'run_controller_identical_after_six_new_receipt_fields_removed':True,'raw_live_controls':controls,'no_native_reexecution':True}
    path=OUT/'forge_sol_S18_RSS_v3_binding_review_result_20261027.json'
    with path.open('x') as stream:json.dump(report,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'status':report['status'],'result':str(path),'sha256':sha(path),'packet_entries':packet['entries'],'original_failure_entries':failure['entries'],'unchanged_definitions':len(report['unchanged_definitions'])},sort_keys=True))
if __name__=='__main__':main()
