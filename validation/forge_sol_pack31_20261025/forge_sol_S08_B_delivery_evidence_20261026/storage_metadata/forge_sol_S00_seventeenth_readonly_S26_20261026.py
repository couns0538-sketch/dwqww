"""Measured proposal only: no archives, unlinks, source changes or native run."""
from pathlib import Path
import gzip, hashlib, json, os, shlex, stat, datetime

BASE = Path('/workspace/forge-pack24-20261026')
OUT = BASE / 'forge_sol_S00_seventeenth_closed_S26_proposal_20261026.json'
ROOTS = tuple(next((BASE/'S26').glob(f'forge_sol_S26_NATIVE_{n}_once_20261026/00_*')) for n in ('f019','f020','f021'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    result = dict(state='READ_ONLY_PROPOSAL_ORIGINALS_RETAINED', created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), allowed_build_roots=[str(p/'build') for p in ROOTS], provenance=[], groups=[], preserved_ELFs=[], process_scan={})
    for index,root in enumerate(ROOTS):
        tablep=root/'table.json';table=json.loads(tablep.read_text());src=root/'source';build=root/'build'
        assert table['private_source']==str(src)
        expected=table['private_source_sha256_before']
        assert len(expected)==78 and all(sha(src/r)==v['sha256'] for r,v in expected.items())
        assert table['recipe_before']==table['recipe_after'] and table['recipe_after']['status']=='PASS'
        cp=root/'commands.json';cmds=json.loads(cp.read_text())
        assert cmds and all(c['child_waited'] and c['returncode']==0 and not c['error'] for c in cmds)
        assert all(sha(p)==s for p,s in table['binary_sha256_after'].items())
        cc=build/'compile_commands.json';compiles=json.loads(cc.read_text());assert len(compiles)==19
        bindings={}
        for c in compiles:
            assert c['directory']==str(build)
            sr=Path(c['file']);rel=str(sr.relative_to(src));assert rel in expected
            args=shlex.split(c['command']);assert args[args.index('-c')+1]==str(sr)
            obj=build/c['output'];assert args[args.index('-o')+1]==c['output']
            assert str(obj.relative_to(build)).startswith('CMakeFiles/forge') and obj.suffix=='.o'
            bindings[str(obj)]=dict(source=str(sr),source_sha256=expected[rel]['sha256'],compile_command=c['command'],output=c['output'],provenance_id=index)
        lib=build/'libforge_core.a';link=build/'CMakeFiles/forge_core.dir/link.txt';text=link.read_text()
        outputs=[str(Path(p).relative_to(build)) for p in bindings if '/forge_core.dir/' in p]
        assert outputs and all(o in text for o in outputs) and 'libforge_core.a' in text
        bindings[str(lib)]=dict(link_recipe=str(link),link_recipe_sha256=sha(link),compiled_core_objects=outputs,provenance_id=index)
        result['provenance'].append(dict(root=str(root),source=str(src),table=str(tablep),table_sha256=sha(tablep),source_sha256={r:v['sha256'] for r,v in expected.items()},commands=str(cp),commands_sha256=sha(cp),owned_commands_all_waited=True,recipe=table['recipe_after'],compile_commands=str(cc),compile_commands_sha256=sha(cc),original_result_status=table['status'],original_result_failure=table.get('failure')))
        for p in sorted(build.rglob('*')):
            if not p.is_file() or p.is_symlink(): continue
            with p.open('rb') as h: magic=h.read(20)
            if magic[:4]==b'\x7fELF' and int.from_bytes(magic[16:18],'little') in (2,3):
                result['preserved_ELFs'].append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
        for pstr,binding in bindings.items():
            p=Path(pstr);s=p.stat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink()
            # Singleton inode gives complete alias closure without a prefix-based assumption.
            assert s.st_nlink==1, (p,'non-singleton requires independent alias scan')
            data=p.read_bytes();kind='AR_static_core_library' if p.suffix=='.a' else 'ELF_ET_REL_compiler_object'
            assert data[:8]==b'!<arch>\n' if p.suffix=='.a' else data[:4]==b'\x7fELF' and int.from_bytes(data[16:18],'little')==1
            zipped=gzip.compress(data,compresslevel=6,mtime=0);assert gzip.decompress(zipped)==data
            m=dict(path=str(p),device=s.st_dev,inode=s.st_ino,nlink=s.st_nlink,size=s.st_size,allocated_bytes=s.st_blocks*512,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,gid=s.st_gid,atime_ns=s.st_atime_ns,mtime_ns=s.st_mtime_ns)
            result['groups'].append(dict(aliases=[str(p)],alias_metadata=[m],dev=s.st_dev,inode=s.st_ino,links=1,size=s.st_size,allocated_bytes=s.st_blocks*512,compiler_bindings={str(p):binding},sha256=hashlib.sha256(data).hexdigest(),kind=kind,measured_archive_bytes=len(zipped),measured_net_payload_bytes=len(data)-len(zipped),all_aliases_rechecked=True,closure_basis='st_nlink=1; unique alias is complete inode namespace'))
    own=os.getpid();hits=[];denied=[];scanned=0
    needles=result['allowed_build_roots']
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==own: continue
        try:
            st=(p/'stat').read_text();state=st[st.rfind(')')+2:].split()[0]
            if state=='Z':continue
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');refs=[cmd]
            for d in ('cwd','exe'):
                try:refs.append(os.readlink(p/d))
                except OSError:pass
            try:
                for f in (p/'fd').iterdir():
                    try:refs.append(os.readlink(f))
                    except OSError:pass
            except OSError:pass
            scanned+=1
            if any(n in v for n in needles for v in refs):hits.append(dict(pid=int(p.name),state=state,cmd=cmd,matching_refs=[v for v in refs if any(n in v for n in needles)]))
        except (OSError,ValueError) as e:denied.append(dict(pid=p.name,error=type(e).__name__))
    result['process_scan']=dict(visible_non_zombies_scanned=scanned,hits=hits,denied=denied,qualification='visible local /proc only; must refresh before archive')
    assert not hits
    result['summary']=dict(groups=len(result['groups']),aliases=sum(len(g['aliases']) for g in result['groups']),raw_bytes=sum(g['size'] for g in result['groups']),measured_gzip_bytes=sum(g['measured_archive_bytes'] for g in result['groups']),measured_net_payload_bytes=sum(g['measured_net_payload_bytes'] for g in result['groups']),preserved_ELFs=len(result['preserved_ELFs']),not_authorized='READ ONLY. Root review and new explicit archive authorization required. No original removed.')
    OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(OUT),sha256=sha(OUT),summary=result['summary'])))
if __name__=='__main__':main()
