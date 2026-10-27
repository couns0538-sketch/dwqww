"""At most four old GENERATED release working copies; proposal/backups only.

No index/object/source/history mutation, omission, network or engine execution.
"""
from pathlib import Path
import datetime,hashlib,json,os,stat,struct,subprocess,zipfile,zlib
if not __debug__:raise RuntimeError("Run without -O/PYTHONOPTIMIZE")
REPO=Path('/workspace/dwqww')
OUT=Path('/tmp/forge_sol_historical_windows_release_plan_v2_20261027')
BACKUPS=Path('/tmp/forge_sol_historical_windows_release_backups_v2_20261027')
VERSIONS=(8,9,10,11)
PATHS=[f'releases/forge-6.4.{n}-candidate-windows-zen5.zip' for n in VERSIONS]
KNOWN=REPO/'validation/forge_sol_pack31_20261025/forge_sol_published_release_sparse_plan_20261026.json'
ENV=os.environ.copy();ENV.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=REPO,env=ENV)
def active_smoke():
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            args=(p/'cmdline').read_bytes().split(b'\0');s=(p/'stat').read_text();state=s[s.rfind(')')+2:].split()[0]
            if state!='Z' and args and Path(args[0].decode()).name.startswith('python') and any(b'forge_sol_S18' in a and a.endswith(b'.py') for a in args[1:5]) and b'--execute' in args:found.append(int(p.name))
        except OSError:pass
    return found
def tree(commit):
    result={}
    for row in git('ls-tree','-z',commit,'--',*PATHS).split(b'\0'):
        if row:
            head,path=row.split(b'\t',1);mode,kind,oid=head.decode().split();assert kind=='blob';result[path.decode()]={'mode':mode,'oid':oid}
    return result
def primary_storage(oid,body):
    obj=REPO/'.git/objects';loose=obj/oid[:2]/oid[2:]
    expected=b'blob '+str(len(body)).encode()+b'\0'+body
    if loose.is_file():
        assert not loose.is_symlink()
        compressed=loose.read_bytes();assert zlib.decompress(compressed)==expected
        return {'kind':'PRIMARY_LOOSE','path':str(loose),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'compressed_bytes':len(compressed),'actual_decoded_blob_header_and_bytes_match':True}
    wanted=bytes.fromhex(oid);found=[]
    for idx in sorted((obj/'pack').glob('*.idx')):
        with idx.open('rb') as f:
            assert f.read(8)==b'\xfftOc'+struct.pack('>I',2)
            fan=struct.unpack('>256I',f.read(1024));lo=fan[wanted[0]-1] if wanted[0] else 0;hi=fan[wanted[0]]
            while lo<hi:
                mid=(lo+hi)//2;f.seek(1032+20*mid);value=f.read(20)
                if value<wanted:lo=mid+1
                else:hi=mid
            if lo<fan[-1]:
                f.seek(1032+20*lo)
                if f.read(20)==wanted:found.append(idx)
    assert found,'Exact selected OID absent from primary loose storage and primary pack indexes'
    idx=found[0];pack=idx.with_suffix('.pack');assert pack.is_file() and not idx.is_symlink() and not pack.is_symlink()
    proof=OUT/'primary_object_probe';packs=proof/'pack';packs.mkdir(parents=True,exist_ok=True)
    for source in (idx,pack):
        target=packs/source.name
        if not target.exists():target.symlink_to(source)
        assert target.resolve()==source
    # Isolated object directory has no alternates. Git must decode an actual primary
    # pack via the two symlinks, not borrow any /tmp external artifact objects.
    assert not (proof/'info/alternates').exists()
    env=ENV.copy();env.update(GIT_OBJECT_DIRECTORY=str(proof),GIT_ALTERNATE_OBJECT_DIRECTORIES='')
    actual=subprocess.check_output(['git','-c','gc.auto=0','cat-file','blob',oid],cwd=REPO,env=env)
    assert actual==body
    return {'kind':'PRIMARY_PACK','index':str(idx),'index_sha256':sha(idx),'index_bytes':idx.stat().st_size,'pack':str(pack),'pack_bytes':pack.stat().st_size,'pack_mtime_ns':pack.stat().st_mtime_ns,'exact_oid_in_primary_v2_index':True,'isolated_probe_object_directory':str(proof),'probe_pack_paths_are_symlinks_to_primary_only':True,'probe_has_no_alternates':True,'actual_primary_pack_decoded_blob_bytes_match':True}
def main():
    assert os.sched_getaffinity(0)=={4} and os.getpriority(os.PRIO_PROCESS,0)==19
    assert not active_smoke(),'S18 smoke active: no streaming/copy work'
    assert not OUT.exists() and not BACKUPS.exists()
    known=json.loads(KNOWN.read_text());published=known['artifact_commit'];assert published=='92220ccf0400dc45828bcfad9ba9993c72ddb56d'
    assert known['files'][0]['http']==200
    head=git('rev-parse','HEAD').decode().strip();git('merge-base','--is-ancestor',published,head)
    index_before=sha(REPO/'.git/index');index={};flags={}
    for row in git('ls-files','--stage','-z','--',*PATHS).split(b'\0'):
        if row:
            a,p=row.split(b'\t',1);mode,oid,stage=a.decode().split();assert stage=='0';index[p.decode()]={'mode':mode,'oid':oid}
    for row in git('ls-files','-v','-z','--',*PATHS).split(b'\0'):
        if row:flags[row[2:].decode()]=row[:1].decode()
    assert set(index)==set(PATHS) and index==tree(head)==tree(published)
    assert not git('diff','--name-only','--',*PATHS) and not git('diff','--cached','--name-only','--',*PATHS)
    assert len(PATHS)==4 and sum((REPO/p).stat().st_size for p in PATHS)<=100*1024**2
    # Complete small metadata qualification before writing backups.
    prepared=[]
    for version,path in zip(VERSIONS,PATHS):
        p=REPO/path;s=p.stat();assert p.resolve()==p and not p.is_symlink() and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and flags[path]=='H'
        prefix=f'forge-6.4.{version}-candidate-windows-zen5/'
        with zipfile.ZipFile(p) as z:
            names=z.namelist();assert len(names)==13 and all(n.startswith(prefix) for n in names)
            # These early binary kits contain no nested source/checkpoint archive.
            assert not any(Path(n).suffix.lower() in {'.cpp','.hpp','.h','.c','.cc','.inc','.py','.patch','.diff','.pt','.pos','.hce','.zip','.gz','.xz','.7z','.tar'} for n in names)
            assert sum(n.endswith('.exe') for n in names)==5
            raw=z.read(prefix+'provenance.json');provenance=json.loads(raw)
            assert provenance['engine_version']==f'6.4.{version} candidate'
            outside=REPO/'releases'/prefix/'provenance.json';assert outside.read_bytes()==raw
            prepared.append((path,s,{'classification':'Historical generated Windows binary/test release kit, not an upload, source archive, checkpoint or current output','package_entries':names,'provenance_member':prefix+'provenance.json','provenance_sha256':hashlib.sha256(raw).hexdigest(),'unpacked_matching_provenance':str(outside),'source_and_tests_commit':provenance['source_and_tests_commit']}))
    OUT.mkdir();BACKUPS.mkdir(mode=0o700);rows=[]
    for path,before,provenance in prepared:
        assert not active_smoke(),'S18 started: stop before next archive copy'
        p=REPO/path;body=p.read_bytes();s=p.stat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)==(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,1)
        digest=hashlib.sha256(body).hexdigest();oid=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest();assert oid==index[path]['oid']
        storage_proof=primary_storage(oid,body)
        dest=BACKUPS/Path(path).name
        with dest.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
        assert dest.stat().st_nlink==1 and not os.path.samefile(dest,p) and dest.stat().st_dev!=p.stat().st_dev and sha(dest)==digest
        dest.chmod(stat.S_IMODE(before.st_mode));os.utime(dest,ns=(before.st_atime_ns,before.st_mtime_ns))
        assert dest.stat().st_mtime_ns==before.st_mtime_ns and stat.S_IMODE(dest.stat().st_mode)==stat.S_IMODE(before.st_mode)
        rows.append({'path':path,'bytes':len(body),'sha256':digest,'git_blob_oid':oid,'git_mode':index[path]['mode'],'index_flag_before':'H','artifact_commit':published,'candidate_immutable_url':f'https://raw.githubusercontent.com/couns0538-sketch/dwqww/{published}/{path}','fresh_target_HTTP_readback':'NOT_RUN_NO_NETWORK_IN_THIS_TASK','primary_storage_proof':storage_proof,'backup':str(dest),'backup_device':dest.stat().st_dev,'backup_inode':dest.stat().st_ino,'backup_nlink':1,'backup_sha256':digest,'backup_independent_and_exact':True,'new_tmp_restore_probe':{'basis':'Isolated primary Git blob decode equals original bytes; independent new tmp body fsynced and SHA/size/mode/mtime verified. No worktree/index restore was performed.','passed':True},'metadata_before':{'mode':stat.S_IMODE(before.st_mode),'uid':before.st_uid,'gid':before.st_gid,'atime_ns':before.st_atime_ns,'mtime_ns':before.st_mtime_ns,'device':before.st_dev,'inode':before.st_ino,'nlink':1,'allocated_bytes':before.st_blocks*512},'provenance':provenance,'restore_commands':[['git','-C',str(REPO),'update-index','--no-skip-worktree','--',path],['git','-C',str(REPO),'restore','--source='+published,'--worktree','--ignore-skip-worktree-bits','--',path]],'restore_metadata_after_bytes_verified':{'chmod':stat.S_IMODE(before.st_mode),'utime_ns':[before.st_atime_ns,before.st_mtime_ns]},'independent_restore_alternative':'Copy exact backup to a NEW destination or use root-reviewed overwrite-free materialization; verify SHA256/size and restore captured metadata.'})
    current=git('rev-parse','HEAD').decode().strip();assert index==tree(current)
    for row in rows:
        p=REPO/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and p.stat().st_nlink==1
    assert not git('diff','--name-only','--',*PATHS) and not git('diff','--cached','--name-only','--',*PATHS)
    index_after=sha(REPO/'.git/index')
    plan={'status':'VERIFIED_LOCAL_METADATA_PLAN_NOT_OMITTED','snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'EXACT4 older generated published Windows release ZIP working copies only. No uploads, inputs, source/checkpoint archives, current outputs, S11/S18 files, originals, Git objects/history or index modified. No omission performed.','repository':str(REPO),'head_before':head,'head_after':current,'known_published_commit':published,'known_publication_evidence':{'path':str(KNOWN),'sha256':sha(KNOWN),'basis':'Existing verified HTTP200 publication of another artifact at this same immutable commit; all4 exact blobs verified in its local commit tree. No new target HTTP readback was performed.','root_preaction_requirement':'Before omission, root should verify each selected immutable URL or bind already available target-specific publication evidence; no fresh HTTP200 is claimed here.'},'index_sha256_before':index_before,'index_sha256_after':index_after,'whole_index_unchanged':index_before==index_after,'all_selected_index_HEAD_working_bytes_unchanged':True,'files':rows,'summary':{'files':4,'logical_bytes':sum(r['bytes'] for r in rows),'estimated_allocated_gain_bytes':sum(r['metadata_before']['allocated_bytes'] for r in rows),'all_primary_Git_objects_decoded_and_exact':True,'independent_tmp_backups':4,'backups_bytes':sum(r['bytes'] for r in rows),'maximum_scope_bytes':100*1024**2,'CPU':[4],'nice':19},'root_only_later_actions':['Review/publish the plan first; fresh verify selected working bytes, index/HEAD OIDs, primary objects, backup bytes and publication evidence.','Root alone sets skip-worktree on exact4 paths then removes only those redundant working copies.','Do not alter objects/history or original unpacked release files. Normal clones remain complete. Recheck no staged/deletion/content diff after omission.','Restore using exact commands and byte/metadata checks above when capacity permits. All backup bodies remain separate /tmp copies.'],'excluded':'Nested windows-originals/source or validation-bundle archives, all uploads and current/S11/S18 artifacts. source-hashes.json inside selected kits is metadata only; no source files or nested archives exist in these4 packages.','no_compression_no_network_no_native_engine':True}
    p=OUT/'forge_sol_generated_windows_release_sparse_plan_v2_20261027.json';p.write_text(json.dumps(plan,indent=2)+'\n')
    (OUT/'forge_sol_generated_windows_release_sparse_notes_v2_20261027.md').write_text('Plan only. Exactly6.4.8/9/10/11 generated Windows binary kits; no local omissions, index or Git mutations. All4 exact blobs remain in primary Git and independent/tmp backups. Root publication/readback and review are required before any sparse-materialization action. New network checks were prohibited, so individual immutable ZIP HTTP checks are explicitly NOT RUN; local tree membership in previously verified published commit92220ccf is proven. Backups/hashes ran only after exact S18 Python controller/child activity was absent, onCPU4/nice19. No compression, compiler, Torch or engine executed.\n')
    print(json.dumps({'plan':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'summary':plan['summary'],'index_unchanged':index_before==index_after}))
if __name__=='__main__':main()
