#!/usr/bin/env python3
"""Restore pinned evidence DATA blobs to an external Git object store only.

Does not edit a working tree, index, refs, primary objects or alternates file.
The caller must already have configured the external store as an alternate.
"""
import argparse, hashlib, json, os, re, subprocess, tempfile, urllib.parse, urllib.request
from pathlib import Path, PurePosixPath

DATA_SUFFIXES={'.gz','.xz','.zst','.bz2','.jsonl','.epd','.pgn','.log','.stdout','.stderr','.json'}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--metadata',type=Path,required=True)
    ap.add_argument('--git-dir',type=Path,required=True)
    ap.add_argument('--external-objects',type=Path,required=True)
    ap.add_argument('--fixture-blobs',type=Path,help='Tests only: OID-named blobs exported from a pinned local fixture commit')
    a=ap.parse_args();m=json.loads(a.metadata.read_text())
    assert m['schema']=='forge-external-evidence-1'
    repo=m['repository'];commit=m['artifact_commit']
    assert repo=='couns0538-sketch/dwqww' and re.fullmatch('[0-9a-f]{40}',commit)
    primary=(a.git_dir/'objects').resolve();external=a.external_objects.absolute()
    assert external.resolve()==external and external!=primary and not external.is_relative_to(primary)
    assert len(m['files'])>0
    # Validate the full manifest before creating any downloaded object bytes.
    for row in m['files']:
        p=PurePosixPath(row['path'])
        assert not p.is_absolute() and '..' not in p.parts and p.parts[0] in ('validation','releases')
        assert p.suffix in DATA_SUFFIXES and row['kind']=='evidence-data'
        assert re.fullmatch('[0-9a-f]{64}',row['sha256']) and re.fullmatch('[0-9a-f]{40}',row['git_blob_oid'])
        assert isinstance(row['bytes'],int) and row['bytes']>0
        url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+urllib.parse.quote(str(p),safe='/')
        assert row['raw_url']==url
    external.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['GIT_OBJECT_DIRECTORY']=str(external);env['GIT_ALTERNATE_OBJECT_DIRECTORIES']=str(primary)
    results=[]
    for row in m['files']:
        url=row['raw_url'];source=None
        if a.fixture_blobs is not None:
            root=a.fixture_blobs.resolve();source=root/row['git_blob_oid']
            assert source.resolve().is_relative_to(root) and not source.is_symlink()
        size=0;sha=hashlib.sha256();blob=hashlib.sha1(b'blob '+str(row['bytes']).encode()+b'\0')
        # Temporary download lives alongside external objects, never on primary storage.
        with tempfile.TemporaryFile(dir=external) as body:
            with (source.open('rb') if source is not None else urllib.request.urlopen(url,timeout=120)) as raw:
                while True:
                    block=raw.read(1048576)
                    if not block:break
                    size+=len(block);assert size<=row['bytes'],'Evidence larger than manifest'
                    sha.update(block);blob.update(block);body.write(block)
            assert size==row['bytes'] and sha.hexdigest()==row['sha256'],'SHA256/size mismatch; no Git blob written'
            assert blob.hexdigest()==row['git_blob_oid'],'Git blob OID mismatch; no Git blob written'
            body.seek(0)
            done=subprocess.run(['git','--git-dir',str(a.git_dir),'hash-object','-w','--stdin'],stdin=body,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,check=True)
            assert done.stdout.decode().strip()==row['git_blob_oid']
        results.append({'path':row['path'],'git_blob_oid':row['git_blob_oid'],'sha256':row['sha256'],'bytes':size,'source':'PINNED_FIXTURE' if source else 'PINNED_HTTPS_RAW'})
    print(json.dumps({'status':'PASS_REHYDRATED_DATA_OBJECTS','artifact_commit':commit,'files':results,'primary_mutations':'NONE','external_objects':str(external)},sort_keys=True))
if __name__=='__main__':main()
