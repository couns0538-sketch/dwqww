"""Independent checksum/file-coverage verification; no sealer import or native jobs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
sys.path.insert(0, 'D:/a10/wt/astra_r10/job1')  # CR crfix 0e91e02e: shared lane guard (crfix_abcbb9c9 lane_guard.py 596ecbe6)
import lane_guard


def check(ok,message):
    if not ok:raise ValueError(message)


def safe(path,root):
    check(path.is_relative_to(root),'path escapes pack')
    for ancestor in (path,*path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            info=ancestor.lstat()
            check(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
                  'symlink/reparse path refused')
    return path


def read_manifest(root,name,width):
    result={}
    for line in safe(root/name,root).read_text(encoding='utf-8').splitlines():
        match=re.fullmatch(r'([0-9a-f]{'+str(width)+r'})  (.+)',line)
        check(match is not None,'malformed checksum line')
        digest,relative=match.groups()
        check('\\' not in relative and ':' not in relative and all(x not in ('','.','..') for x in relative.split('/')),'unsafe checksum path')
        check(relative.casefold() not in {p.casefold() for p in result},'duplicate checksum path')
        check(relative not in ('MD5SUMS','SHA256SUMS'),'recursive checksum manifest')
        result[relative]=digest
    check(result,'empty checksum manifest')
    return result


def verify(root):
    check(root.is_absolute() and root.is_relative_to(Path('D:/a10')),'D:/a10 pack required')
    safe(root,root);sha=read_manifest(root,'SHA256SUMS',64);md5=read_manifest(root,'MD5SUMS',32)
    check(set(sha)==set(md5),'checksum manifests cover different files')
    found=set();pending=[root]
    while pending:
        current=pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path=safe(Path(entry.path),root)
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                else:found.add(path.relative_to(root).as_posix())
    check(found-{'MD5SUMS','SHA256SUMS'}==set(sha),'unlisted or missing pack files')
    for name in sha:
        h=hashlib.sha256();m=hashlib.md5()
        with safe(root/name,root).open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                h.update(block);m.update(block)
        check(h.hexdigest()==sha[name],'SHA256 mismatch: '+name)
        check(m.hexdigest()==md5[name],'MD5 mismatch: '+name)
    report=json.loads((root/'REPORT.json').read_text(encoding='utf-8'))
    check(report.get('status')=='SEALED_INCOMPLETE' and report.get('strength')=='UNPROVEN',
          'Job1 pack must remain SEALED_INCOMPLETE / UNPROVEN')
    print(json.dumps({'status':'PASS','scope':'Independent SHA256/MD5 and complete file coverage only',
                      'files':len(sha),'pack_status':report['status'],'strength':'UNPROVEN'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads',required=True,type=int,choices=(1,))
    parser.add_argument('--pack',required=True,type=Path)
    pack=parser.parse_args().pack
    lane_guard.check_lane()  # before hashing
    verify(pack)
