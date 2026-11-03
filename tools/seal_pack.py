"""Seal an explicit owned evidence directory; checksums do not qualify its claims."""
import argparse
from pathlib import Path
from run_policy import Snapshot, free_guard, safe_path

MANIFESTS={'SHA256SUMS','MD5SUMS'}

def payloads(root):
    root=safe_path(root,write=True)
    files=[]
    pending=[root]
    names=set()
    while pending:
        folder=pending.pop()
        for entry in sorted(folder.iterdir()):
            path=safe_path(entry,write=True)
            relative=path.relative_to(root).as_posix()
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                if relative in MANIFESTS:
                    continue
                if relative.casefold() in names:
                    raise ValueError('casefold path collision')
                if '\n' in relative or '\r' in relative:
                    raise ValueError('newline filename')
                names.add(relative.casefold())
                files.append((relative,path))
            else:
                raise ValueError('nonregular evidence entry')
    return sorted(files)


def seal(root):
    root=safe_path(root,write=True)
    if any((root/name).exists() for name in MANIFESTS):
        raise FileExistsError('seal exists; preserve it and use a new pack')
    listing=payloads(root)
    if not listing:
        raise ValueError('empty pack')
    entries=[]
    for relative,path in listing:
        snapshot=Snapshot(path)
        entries.append((relative,snapshot.digest(),snapshot))
    if [name for name,_ in payloads(root)] != [name for name,_ in listing]:
        raise ValueError('pack census changed while hashing')
    for _,_,snapshot in entries:
        snapshot.check()
    free_guard(1024*1024)
    for name,algorithm in (('SHA256SUMS','sha256'),('MD5SUMS','md5')):
        with (root/name).open('x',encoding='ascii',newline='\n') as stream:
            for relative,digests,_ in entries:
                stream.write(f'{digests[algorithm]}  {relative}\n')
    return len(entries)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    print(f'Sealed {seal(args.root)} payload files; qualification statuses remain unchanged.')
