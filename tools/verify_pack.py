"""Independent manifest parser/census/hash verifier for R13 evidence payloads."""
import argparse
import hashlib
import os
from pathlib import Path
import re
from run_policy import free_guard, safe_path


def manifest_bytes(path):
    path=safe_path(path,write=True)
    before=path.stat()
    if before.st_size>16*1024*1024:
        raise ValueError('manifest exceeds bounded read')
    raw=path.read_bytes()
    after=path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError('manifest changed while read')
    return raw


def parse_manifest(path,width,raw=None):
    entries={}
    folded=set()
    for line in (manifest_bytes(path) if raw is None else raw).decode('ascii').splitlines():
        match=re.fullmatch(r'([0-9a-f]{'+str(width)+r'})  (.+)',line)
        if not match:
            raise ValueError('malformed checksum line')
        digest,relative=match.groups()
        if '\\' in relative or any(p in ('','.', '..') or ':' in p for p in relative.split('/')) or relative.startswith('/'):
            raise ValueError('unsafe manifest relative path')
        if relative in ('SHA256SUMS','MD5SUMS') or relative.casefold() in folded:
            raise ValueError('self-reference or duplicate manifest path')
        entries[relative]=digest
        folded.add(relative.casefold())
    if not entries:
        raise ValueError('empty manifest')
    return entries


def census(root):
    actual=set()
    for folder,directories,files in os.walk(root,followlinks=False):
        for directory in directories:
            safe_path(Path(folder)/directory,write=True)
        for filename in files:
            path=safe_path(Path(folder)/filename,write=True)
            relative=path.relative_to(root).as_posix()
            if relative not in ('SHA256SUMS','MD5SUMS'):
                actual.add(relative)
    return actual


def verify(root):
    root=safe_path(root,write=True)
    originals={name:manifest_bytes(root/name) for name in ('SHA256SUMS','MD5SUMS')}
    expected_sha=parse_manifest(root/'SHA256SUMS',64,originals['SHA256SUMS'])
    expected_md5=parse_manifest(root/'MD5SUMS',32,originals['MD5SUMS'])
    if set(expected_sha)!=set(expected_md5):
        raise ValueError('checksum inventories disagree')
    actual=census(root)
    if actual!=set(expected_sha):
        raise ValueError('pack census differs: missing or extra payload')
    for relative in sorted(actual):
        path=safe_path(root/relative,write=True)
        before=path.stat()
        sha,md5=hashlib.sha256(),hashlib.md5()
        with path.open('rb') as stream:
            opened=os.fstat(stream.fileno())
            if (opened.st_ino,opened.st_size,opened.st_mtime_ns)!=(before.st_ino,before.st_size,before.st_mtime_ns):
                raise ValueError('input changed before read')
            while block:=stream.read(1024*1024):
                free_guard()
                sha.update(block)
                md5.update(block)
            after=os.fstat(stream.fileno())
        current=path.stat()
        if any((s.st_ino,s.st_size,s.st_mtime_ns)!=(before.st_ino,before.st_size,before.st_mtime_ns) for s in (after,current)):
            raise ValueError('input changed while read')
        if sha.hexdigest()!=expected_sha[relative] or md5.hexdigest()!=expected_md5[relative]:
            raise ValueError('payload checksum mismatch: '+relative)
    if census(root)!=actual:
        raise ValueError('pack census changed while verifying')
    if any(manifest_bytes(root/name)!=raw for name,raw in originals.items()):
        raise ValueError('checksum manifest changed while verifying')
    return dict(status='PASS',payloads=len(actual),meaning='Exact checksum/census only; no provenance or training clearance')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    print(verify(args.root))
