"""Stage exact closed S08 evidence using hardlinks, never builds/cache payloads."""
from pathlib import Path
import datetime, hashlib, json, os, zlib

BASE=Path('/workspace/forge-pack24-20261026')
S08=BASE/'S08'
DEST=Path('/workspace/dwqww/validation/forge_sol_pack31_20261025/forge_sol_S08_B_delivery_evidence_20261026')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not DEST.exists()
    pairs={}
    def add(p,relative):
        assert p.is_file() and not p.is_symlink(),p
        assert p.suffix not in ('.o','.a','.gz','.zip','.xz','.exe','.so'),p
        assert 'payloads' not in p.parts
        header=p.read_bytes()[:8]
        assert header[:4]!=b'\x7fELF' and header!=b'!<arch>\n',p
        r=Path(relative);assert not r.is_absolute() and '..' not in r.parts
        assert str(r) not in pairs or pairs[str(r)]==p
        pairs[str(r)]=p
    def tree(root,relative,skip=()):
        assert root.is_dir(),root
        for p in sorted(root.rglob('*')):
            rel=p.relative_to(root)
            if any(s in rel.parts for s in skip) or not p.is_file():continue
            add(p,Path(relative)/rel)
    # Entire closed build evidence and recipes; compiler caches/runtime ELFs excluded.
    for n in ('forge_sol_S08_B_Release_ON_window1_20261026','forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026'):
        tree(S08/n,Path('S08')/n,skip=('build',))
    for n in ('forge_sol_S08_B_Release_qualification_once_20261026','forge_sol_S08_B_FIRST_native_20261026','forge_sol_S08_B_FIRST_native_window2_20261026','forge_sol_S08_B_SHARED_FIRST_native_20261026','forge_sol_S08_documentation_TLS_v2_20261026'):
        tree(S08/n,Path('S08')/n)
    # Current B controllers and every retained B version/failure are closed per worker.
    for p in sorted(S08.iterdir()):
        if p.is_file() and ('S08_B_' in p.name or p.name=='forge_sol_S08_TLS_v2_source_freeze_20261026.json'):
            add(p,Path('S08')/p.name)
    # Exact manifest-bound OFF proof fixtures, plus proof implementation/tests.
    off=S08/'forge_sol_S08_OFF_reuse_SHA256SUMS_20261026.txt'
    for line in off.read_text().splitlines():
        digest,rel=line.split('  ',1);p=S08/rel;assert sha(p)==digest
        add(p,Path('S08')/rel)
    for name in ('forge_sol_S08_OFF_reuse_SHA256SUMS_20261026.txt','forge_sol_S08_OFF_reuse_report_20261026.md','forge_sol_S08_OFF_preprocess_reuse_20261026.py','forge_sol_S08_OFF_token_reuse_v2_20261026.py','forge_sol_S08_OFF_reuse_final_audit_20261026.py','forge_sol_S08_libclang_token_hash_20261026.py','test_forge_sol_S08_libclang_tokens_20261026.py','forge_sol_S08_libclang_tokens_pure5_20261026.log','forge_sol_S08_Lprime_B_profile_comparison_20261026.json'):
        add(S08/name,Path('S08')/name)
    tree(S08/'forge_sol_S08_packet_only_portability_20261026','S08/forge_sol_S08_packet_only_portability_20261026',skip=('packet with spaces',))
    tree(BASE/'forge_sol_S08_packet_only_portability_v2_20261026','forge_sol_S08_packet_only_portability_v2_20261026',skip=('packet with spaces',))
    # All retirement metadata; deterministic gzip payload bytes remain exclusively local.
    for word in ('fourteenth','fifteenth','sixteenth'):
        for d in sorted(BASE.glob(f'forge_sol_S00_{word}_space*20261026')):
            for p in sorted(d.rglob('*')):
                if not p.is_file() or 'payloads' in p.relative_to(d).parts or p.suffix=='.gz':continue
                add(p,Path('storage_metadata')/d.name/p.relative_to(d))
    add(BASE/'forge_sol_S00_seventeenth_readonly_S26_20261026.py','storage_metadata/forge_sol_S00_seventeenth_readonly_S26_20261026.py')
    review=Path('/tmp/forge_sol_S08_independent_delivery_review_20261026.json')
    add(review,review.name)
    before={r:dict(original=str(p),relative=r,sha256=sha(p),bytes=p.stat().st_size) for r,p in pairs.items()}
    DEST.mkdir()
    for rel,p in sorted(pairs.items()):
        q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
        assert q.stat().st_ino==p.stat().st_ino and q.stat().st_dev==p.stat().st_dev
        assert sha(q)==before[rel]['sha256']
    assert all(sha(p)==before[r]['sha256'] for r,p in pairs.items())
    estimate=0
    for p in pairs.values():
        data=p.read_bytes();estimate+=len(zlib.compress(b'blob '+str(len(data)).encode()+b'\0'+data,6))
    mapping=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state='STAGED_CLOSED_EVIDENCE_ONLY_NO_GIT',scope='Exact original bytes by hardlink. No source edits, native tests, ELF/object/archive/cache payload copies. Active B shared-ASAN full runtime directory excluded until closed.',files=list(before.values()),counts=dict(files=len(pairs),logical_bytes=sum(v['bytes'] for v in before.values()),git_loose_blob_zlib6_estimated_payload_bytes=estimate),qualifications=['Estimate is sum of individually compressed Git blob payloads, excludes Git object filesystem allocation/metadata/commit/tree/index cost, actual push pack may differ.','Hardlinks preserve original data blocks; original st_nlink intentionally increases; original bytes unchanged.','Original source-private fulltrees excluded; only explicit manifest-bound OFF overlay source snippets retained.','The failed cache17 read-only proposal script stopped before output write; no archive/unlink occurred. Its transport traceback was not separately captured as OS raw evidence.','No final report or accepted/delivered claim is made by this staging tool.'])
    mp=DEST/'forge_sol_S08_B_evidence_binding_20261026.json';mp.write_text(json.dumps(mapping,indent=2)+'\n')
    addscript=DEST/'forge_sol_S08_stage_closed_evidence_20261026.py';os.link(Path(__file__),addscript)
    manifest=DEST/'forge_sol_S08_B_evidence_SHA256SUMS_20261026.txt'
    fs=sorted(p for p in DEST.rglob('*') if p.is_file())
    manifest.write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in fs))
    print(json.dumps(dict(destination=str(DEST),mapped_files=len(pairs),manifest_entries=len(fs),manifest_sha256=sha(manifest),binding_sha256=sha(mp),logical_bytes=mapping['counts']['logical_bytes'],git_loose_blob_zlib6_estimated_payload_bytes=estimate)))
if __name__=='__main__':main()
