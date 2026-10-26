"""Exact two CLOSED B build cache proposal. No archive, unlink or native run."""
from pathlib import Path
import ast, collections, datetime, gzip, hashlib, json, os, shlex, stat

BASE=Path('/workspace/forge-pack24-20261026');S08=BASE/'S08'
BUILDS=tuple(S08/n/'build' for n in ('forge_sol_S08_B_Release_ON_window1_20261026','forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026'))
SOURCE=S08/'B_v2';FREEZE=S08/'forge_sol_S08_B_v2_source_freeze_20261026.json'
FREEZE_SHA='fcd93778dc3bae5bed2f941c9ee0fff08f6ee07ce6ecf22bf82a007e8a8904d7'
OUT=Path('/tmp/forge_sol_S00_seventeenth_B_closed_cache_proposal_20261026.json')
HELPER=BASE/'forge_sol_S00_fourteenth_space_proposal_20261026/forge_sol_S00_fourteenth_readonly_audit_20261026.py'
ACT=BASE/'forge_sol_S00_sixteenth_space_proposal_20261026/forge_sol_S00_sixteenth_activity_preflight_20261026.py'
SCOPE=BASE/'forge_sol_S00_sixteenth_space_proposal_20261026/forge_sol_S00_sixteenth_readonly_audit_20261026.py'
def reuse(path,digest,names):
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
    t=ast.parse(raw);ns=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in ns}==set(names)
    exec(compile(ast.Module(body=ns,type_ignores=[]),str(path),'exec'),globals())
def main():
    assert not OUT.exists()
    reuse(HELPER,'78c072a4d78ada1347461d95417bae12556d52c1b1384a36fe2fd61c90a208af',{'utc','sha','stamp','meta','CounterSink'})
    # Scope and format predicates remain exactly the reviewed two-root predicates.
    reuse(SCOPE,'a733fc2c4a03f12c7705dc101917daabf5c2d24bf10518608c3ba57783091c89',{'scope_path','format_kind','group_reasons'})
    reuse(ACT,'f6e0aff1ca13aaa9e66f9f15248fad33f78cc0eba031c6b56ee55ae1b6f6a60e',{'affected_build','snapshot_proc'})
    started=utc();assert sha(FREEZE)==FREEZE_SHA;freeze=json.loads(FREEZE.read_text());expected=freeze['source_sha256']
    assert freeze['source']==str(SOURCE) and len(expected)==83
    def sources():
        got={r:sha(SOURCE/r) for r in expected};assert got==expected
        orig={r:sha(Path(freeze['original_B'])/r) for r in freeze['original_B_source_sha256']};assert orig==freeze['original_B_source_sha256']
        return got
    sources();bindings={};provenance=[];receipts=[];preserved=[]
    receipt_names=('forge_sol_S08_B_Release_build_result_20261026.json','forge_sol_S08_B_shared_ASAN_build_result_20261026.json')
    receipt_hashes=('98b897b4e02305fcd63cccd4dc1cafa187c9fde5f4f7a2d3046c7c20de2c0357','d97a6011f3a352ad15461f69bdffac413a9d749fc513c67e2898e05660ebb654')
    for index,build in enumerate(BUILDS):
        rp=build.parent/receipt_names[index];assert sha(rp)==receipt_hashes[index];x=json.loads(rp.read_text())
        assert x['status']=='PASS_BUILD_ONLY' and x['source_unchanged'] and not x['pending_targets']
        assert x['source']==str(SOURCE) and x['build_dir']==str(build) and x['source_freeze_sha256']==FREEZE_SHA
        assert x['source_before']==x['source_after']==expected and len(x['completed_targets'])==13
        assert all(c['leader_reaped'] and c['returncode']==0 and not c['running_group_members_after_close'] and not c['all_group_members_after_reap'] for c in x['commands'])
        cache=build/'CMakeCache.txt';entries=dict((l.split('=',1)[0].split(':',1)[0],l.split('=',1)[1]) for l in cache.read_text().splitlines() if '=' in l and not l.startswith(('#','//')))
        assert entries['CMAKE_HOME_DIRECTORY']==str(SOURCE) and entries['CMAKE_PROJECT_NAME']=='ChessEngineForge'
        assert entries['CMAKE_CXX_COMPILER']==freeze['compiler'] and sha(Path(freeze['compiler']))==freeze['compiler_sha256']
        cc=build/'compile_commands.json';commands=json.loads(cc.read_text());assert len(commands)==21
        for c in commands:
            assert c['directory']==str(build);src=Path(c['file']);rel=src.relative_to(SOURCE).as_posix();assert rel in expected
            obj=build/c['output'];assert scope_path(obj)
            a=shlex.split(c['command']);assert a[a.index('-o')+1]==c['output'] and a[a.index('-c')+1]==c['file']
            bindings[str(obj)]={'provenance_id':index,'source':str(src),'source_sha256':expected[rel],'output':c['output'],'compile_command':c['command']}
        lib=build/'libforge_core.a'
        if index==0:
            link=build/'CMakeFiles/forge_core.dir/link.txt';text=link.read_text();outputs=[str(Path(p).relative_to(build)) for p in bindings if Path(p).is_relative_to(build) and '/forge_core.dir/' in p]
            assert lib.is_file() and outputs and all(o in text for o in outputs) and 'libforge_core.a' in text
            bindings[str(lib)]={'provenance_id':index,'link_recipe':str(link),'link_recipe_sha256':sha(link),'compiled_core_objects':outputs}
        else:assert not lib.exists() and entries['BUILD_SHARED_LIBS']=='ON'
        artifacts=x['target_artifacts'];assert len(artifacts)==13+index
        for n,v in artifacts.items():
            p=build/n;assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
            with p.open('rb') as f:head=f.read(20)
            assert head[:4]==b'\x7fELF' and int.from_bytes(head[16:18],'little') in (2,3)
            preserved.append({'path':str(p),'sha256':v['sha256'],'size':v['bytes']})
        receipts.append({'path':str(rp),'sha256':sha(rp),'status':x['status'],'owned_commands_reaped':len(x['commands'])})
        provenance.append({'build_root':str(build),'source_home':str(SOURCE),'source_sha256':expected,'source_freeze':str(FREEZE),'source_freeze_sha256':FREEZE_SHA,'compiler':freeze['compiler'],'compiler_sha256':freeze['compiler_sha256'],'cmake_cache':str(cache),'cmake_cache_sha256':sha(cache),'compile_commands':str(cc),'compile_commands_sha256':sha(cc),'source_and_cache_retained':True})
    runtime=S08/'forge_sol_S08_B_SHARED_ASAN_FULL_NATIVE_20261026/forge_sol_S08_B_shared_ASAN_qualification_result_20261026.json'
    assert sha(runtime)=='5cad1ecb571a0ce3546eed7db5ea74933d90da4fd238b784fd14a54081d3faf4';rt=json.loads(runtime.read_text())
    assert rt['status']=='PASS' and rt['binding_before']==rt['binding_after'] and rt['binding_after']['source_sha256']==expected
    assert len(rt['ctest_proof']['test_cases'])==16 and rt['ctest_proof']['status']=='PASS'
    assert all(c['leader_reaped'] and c['returncode']==0 and not c['running_group_members_after_close'] and not c['all_group_members_after_reap'] for c in rt['commands'])
    prior=set();maps=[]
    for mp in sorted(BASE.glob('forge_sol_S00_*space_20261026/*restore_map*.json')):
        x=json.loads(mp.read_text());rows=x if isinstance(x,list) else x.get('files',x.get('entries',[]));prior.update(r['path'] for r in rows if 'path' in r);maps.append({'path':str(mp),'sha256':sha(mp),'rows':len(rows)})
    activity=snapshot_proc();assert not activity['blocked_build_roots']
    groups=[]
    for name,binding in bindings.items():
        p=Path(name);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and scope_path(p)
        # Every selected inode is a singleton. st_nlink=1 proves full alias closure
        # globally; no directory prefix or partial alias scan is used as proof.
        assert s.st_nlink==1,'Non-singleton requires new full-inode alias audit, not this proposal'
        rows=[meta(p,s)];assert not group_reasons(rows,bindings,prior,set(activity['blocked_build_roots']))
        with p.open('rb') as f:header=f.read(20)
        kind=format_kind(header,p.suffix);assert kind
        sink=CounterSink();digest=hashlib.sha256()
        with gzip.GzipFile(fileobj=sink,filename='',mode='wb',mtime=0,compresslevel=6) as z:
            with p.open('rb') as f:
                for chunk in iter(lambda:f.read(1048576),b''):digest.update(chunk);z.write(chunk)
        assert stamp(s)==stamp(p.stat())
        groups.append({'aliases':[name],'alias_metadata':rows,'dev':s.st_dev,'inode':s.st_ino,'links':1,'size':s.st_size,'allocated_bytes':s.st_blocks*512,'provenance_ids':[binding['provenance_id']],'compiler_bindings':{name:binding},'sha256':digest.hexdigest(),'kind':kind,'magic_hex':header.hex(),'measured_archive_bytes':sink.count,'measured_net_payload_bytes':s.st_size-sink.count,'conservative_projected_net_allocated_bytes':s.st_blocks*512-((sink.count+4095)//4096)*4096,'all_aliases_rechecked':True,'alias_closure_basis':'st_nlink=1 singleton inode: sole named path is full global hardlink closure'})
    assert len(groups)==43 and len({(g['dev'],g['inode']) for g in groups})==43
    groups.sort(key=lambda g:(-g['size'],g['aliases'][0]));sources();assert all(sha(r['path'])==r['sha256'] for r in preserved)
    out={'created_utc':started,'finished_utc':utc(),'state':'READ_ONLY_MEASURED_PROPOSAL_ORIGINALS_RETAINED','scope':'Only exact two CLOSED S08 B Release and shared-ASAN build roots; compiler-bound ELF ET_REL .o and Release libforge_core.a only. Keep all83source/originalB78, all27raw runtimeELFs including sharedcoreSO, evidence, recipes and all other roots unchanged. No unlinks authorized by this proposal.','allowed_build_roots':[str(p) for p in BUILDS],'groups':groups,'summary':{'selected_groups':43,'selected_alias_paths':43,'selected_unique_raw_bytes':sum(g['size'] for g in groups),'measured_gzip6_archive_bytes':sum(g['measured_archive_bytes'] for g in groups),'measured_net_payload_bytes':sum(g['measured_net_payload_bytes'] for g in groups),'conservative_projected_net_allocated_bytes':sum(g['conservative_projected_net_allocated_bytes'] for g in groups),'largest_one_archive_bytes':max(g['measured_archive_bytes'] for g in groups),'free_bytes_at_report':os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize},'source_freeze':{'path':str(FREEZE),'sha256':FREEZE_SHA,'root':str(SOURCE),'files_checked':83,'before':expected,'after':expected,'original_B78_unchanged':True},'fresh_build_source_provenance':provenance,'closed_status_basis':{'root_instruction':'Root explicitly declares these two B builds and full16/runtime131s CLOSED. No resume/rebuild of their caches permitted while archived.','build_receipts':receipts,'qualified_native_receipts':[{'path':str(runtime),'sha256':sha(runtime),'status':'PASS','full_CTest_count':16,'owned_commands_reaped':len(rt['commands'])}],'whole_root_activity_gate':activity},'preserved_ELFs_before_after':preserved,'alias_scan':{'candidate_inodes':43,'singleton_inodes':43,'qualification':'Every inode stat nlink1 before and after gzip sizing. Full global closure follows exactly from one named alias, no broad directory scan assumed.'},'prior_retirement_maps':maps,'missing_bound_objects_not_claimed':[],'skipped_groups':[],'reuse':{'scope_format_group_predicates':str(SCOPE),'activity_gate':str(ACT),'gzip_metadata_helpers':str(HELPER)},'failure_controls':{'exact_two_roots_only':len(BUILDS)==2,'all_selected_aliases_exact_allowlist_and_compile_bound':all(not group_reasons(g['alias_metadata'],bindings,prior,set(activity['blocked_build_roots'])) for g in groups),'source83_and_originalB78_unchanged':sources()==expected,'all27_runtime_ELFs_unchanged':len(preserved)==27 and all(sha(r['path'])==r['sha256'] for r in preserved),'all_inode_aliases_complete':all(g['links']==1==len(g['aliases']) for g in groups),'no_visible_selected_root_references':not activity['blocked_build_roots'],'no_archive_write_no_unlink_no_native_execution':True},'root_execution_requirements':['Root review of exact allowlist and fresh source/artifact/cache/recipe/visibleactivity checks immediately before action.','Reuse tested cache16 executor with only exact OWN/proposal path changes; sequential deterministic gzip6 fsync, Python and GNU gzip independent decode size/SHA, durable restore map+journal before each unlink.','Never archive rawELFs/coreSO/source/evidence/Git/inputs. Preserve exact metadata and all prior failed proposal approaches.']}
    assert all(out['failure_controls'].values())
    with OUT.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'summary':out['summary']}))
if __name__=='__main__':main()
