"""Three inert local Git cases; never opens or mutates the user's repository."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,urllib.parse,zlib

ROOT=Path('/tmp/forge_sol_external_evidence_fixture_v2_20261026')
HELPER=Path('/tmp/forge_sol_external_evidence_rehydrate_v2_20261026.py')
ENV=os.environ.copy();ENV.update(GIT_CONFIG_NOSYSTEM='1',GIT_AUTHOR_NAME='Forge Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_NAME='Forge Fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,cwd=None,env=None,good=0,stdin=None):
    r=subprocess.run(args,cwd=cwd,env=env or ENV,input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    with (ROOT/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':list(map(str,args)),'cwd':str(cwd) if cwd else None,'returncode':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')})+'\n')
    if good is not None:assert r.returncode==good,(args,r.returncode,r.stderr)
    return r
def objects(gitdir):return {str(p.relative_to(gitdir/'objects')):sha(p) for p in (gitdir/'objects').rglob('*') if p.is_file()}
def main():
    ROOT.mkdir();work=ROOT/'work';bare=ROOT/'remote.git';clone=ROOT/'clean_clone';ext=ROOT/'external_objects';ext.mkdir()
    run(['git','init','-b','main',str(work)]);run(['git','init','--bare',str(bare)])
    (work/'fixture_source.txt').write_text('small unchanged source fixture\n')
    run(['git','add','fixture_source.txt'],cwd=work);run(['git','-c','gc.auto=0','commit','-m','fixture baseline'],cwd=work)
    gitdir=work/'.git';primary=gitdir/'objects';base_source_sha=sha(work/'fixture_source.txt')
    # Deterministic incompressible-ish evidence DATA, with spaces in its path.
    body=b''.join(hashlib.sha256(str(i).encode()).digest() for i in range(65536));body_sha=hashlib.sha256(body).hexdigest()
    artifact='validation/forge_fixture_20261026/large evidence.jsonl'
    env=ENV.copy();env['GIT_OBJECT_DIRECTORY']=str(ext);env['GIT_ALTERNATE_OBJECT_DIRECTORIES']=str(primary)
    before=objects(gitdir)
    oid=run(['git','--git-dir',str(gitdir),'hash-object','-w','--stdin'],env=env,stdin=body).stdout.decode().strip()
    assert objects(gitdir)==before and (ext/oid[:2]/oid[2:]).is_file()
    alts=primary/'info/alternates';alts.write_text(str(ext)+'\n')
    run(['git','update-index','--add','--cacheinfo','100644',oid,artifact],cwd=work)
    run(['git','update-index','--skip-worktree','--',artifact],cwd=work)
    assert not (work/artifact).exists()
    run(['git','-c','gc.auto=0','commit','-m','fixture externally stored evidence'],cwd=work)
    commit=run(['git','rev-parse','HEAD'],cwd=work).stdout.decode().strip()
    assert run(['git','status','--porcelain'],cwd=work).stdout==b''
    # Push uses the normal object protocol. No external alternates on remote/clone.
    run(['git','-c','gc.auto=0','push',str(bare),'HEAD:refs/heads/main'],cwd=work)
    run(['git','--git-dir',str(bare),'symbolic-ref','HEAD','refs/heads/main'])
    run(['git','clone','--no-local',str(bare),str(clone)])
    assert not (bare/'objects/info/alternates').exists() and not (clone/'.git/objects/info/alternates').exists()
    assert sha(clone/artifact)==body_sha and sha(work/'fixture_source.txt')==base_source_sha
    assert not (primary/oid[:2]/oid[2:]).exists()
    case1={'status':'PASS','name':'NORMAL_COMMIT_PUSH_CLEAN_CLONE','commit':commit,'oid':oid,'sha256':body_sha,'bytes':len(body),'working_body_materialized':False,'remote_or_clone_alternates':False,'primary_artifact_loose_object_exists':False}
    # Export exact published pinned commit bytes to an immutable local raw fixture.
    pinned=ROOT/'pinned_raw';pinned.mkdir();raw=run(['git','--git-dir',str(bare),'show',commit+':'+artifact]).stdout
    assert raw==body;(pinned/oid).write_bytes(raw)
    url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+commit+'/'+urllib.parse.quote(artifact,safe='/')
    row={'kind':'evidence-data','path':artifact,'bytes':len(body),'sha256':body_sha,'git_blob_oid':oid,'raw_url':url}
    meta=ROOT/'recovery_metadata.json';meta.write_text(json.dumps({'schema':'forge-external-evidence-1','repository':'couns0538-sketch/dwqww','artifact_commit':commit,'files':[row]},indent=2)+'\n')
    ext.rename(ROOT/'preserved_old_external_objects')
    missing=run(['git','cat-file','-e',commit+':'+artifact],cwd=work,good=None);assert missing.returncode!=0
    primary_before=objects(gitdir)
    good=run([sys.executable,'-B',str(HELPER),'--metadata',str(meta),'--git-dir',str(gitdir),'--external-objects',str(ext),'--fixture-blobs',str(pinned)])
    restored=run(['git','cat-file','blob',oid],cwd=work).stdout;assert restored==body
    assert primary_before==objects(gitdir) and not (work/artifact).exists() and sha(work/'fixture_source.txt')==base_source_sha
    case2={'status':'PASS','name':'MISSING_STORE_FAILS_THEN_PINNED_REHYDRATION','missing_returncode':missing.returncode,'restored_sha256':hashlib.sha256(restored).hexdigest(),'primary_object_bytes_unchanged':True,'working_tree_unchanged':True,'helper_result':json.loads(good.stdout)}
    # Wrong pinned payload must fail before writing any Git object; no fallback.
    badraw=ROOT/'bad_pinned_raw';badraw.mkdir();(badraw/oid).write_bytes(b'X'+body[1:]);badstore=ROOT/'rejected_external_objects'
    bad=run([sys.executable,'-B',str(HELPER),'--metadata',str(meta),'--git-dir',str(gitdir),'--external-objects',str(badstore),'--fixture-blobs',str(badraw)],good=None)
    assert bad.returncode!=0 and not (badstore/oid[:2]/oid[2:]).exists() and primary_before==objects(gitdir)
    case3={'status':'PASS','name':'WRONG_PINNED_SHA_REJECTED_BEFORE_GIT_WRITE','returncode':bad.returncode,'expected_stderr_contains':'SHA256/size mismatch','actual_match':b'SHA256/size mismatch' in bad.stderr,'primary_object_bytes_unchanged':True,'new_object_written':False}
    assert case3['actual_match']
    result={'status':'PASS_THREE_LOCAL_FIXTURE_CASES','actual_repository_touched':False,'network_or_credentials_used':False,'git_version':run(['git','--version']).stdout.decode().strip(),'helper_sha256':sha(HELPER),'fixture_sha256':sha(__file__),'cases':[case1,case2,case3],'limitations':['Local bare/clone protocol tested, GitHub API/actual HTTPS download not executed.','Real recovery metadata needs the successfully pushed artifact commit pin, not an unpushed branch name.','External-store disappearance breaks local artifact reads until rehydration; remote ordinary clones remain independent.']}
    (ROOT/'forge_sol_external_evidence_fixture_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
