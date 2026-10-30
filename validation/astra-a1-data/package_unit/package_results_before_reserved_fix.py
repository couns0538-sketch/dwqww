#!/usr/bin/env python3
"""Archive ORIGINAL offline results without writing into any input directory.

Usage: python package_results.py --mapping-json mappings.json --output NEW.tar.gz
       [--references-json input_release_references.json] [--max-bytes 2147483647]
Mappings: [{"sourcepath":"/absolute/result", "archiveprefix":"completed/full10m",
            "kind":"sealed"}, ...]. Kinds: sealed, unsealed, auxiliary.
Unsealed prefixes MUST start UNSEALED/. Auxiliary inputs may be explicit outer
logs or a holdout file. Completed source directories require summary.json with
status SEALED and manifest.json, without failure markers. This prerequisite is
not a replacement for the separate full result/manifest semantic validator.
References: [{"url":"https://...", "sha256":"64 hex", "bytes":123,
              "description":"Original 003 release asset; not duplicated"}].
Use constant portable prefixes, not temporary machine paths. Sources must be
quiescent. Hardlinks become ordinary copied file payloads. No input is changed.
Outputs: .partial, final archive, .receipt.json.partial and .receipt.json; partial
files remain even on success (final names are no-replace hardlinks). Failures
retain originals/partials and an external .failure.json. Never silently splits.
IDEA_SOURCE: user evidence-preservation contract; Python tar/gzip/filesystem APIs.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile

MANIFEST_NAME = 'astra_a1_package_manifest.json'
BLOCK = 1024 * 1024


def require(ok, message):
    if not ok: raise ValueError(message)


def stable_json(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf8')


def safe_name(name):
    require(isinstance(name, str) and bool(name), 'empty/non-string archive path')
    require(not name.startswith('/') and '\\' not in name, 'unsafe archive path: '+name)
    parts=name.split('/')
    require(all(p not in ('','.', '..') and re.fullmatch(r'[A-Za-z0-9_.-]+',p) for p in parts), 'unsafe archive path: '+name)
    require(all(not p.endswith('.') and not re.fullmatch(r'(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',p) for p in parts), 'nonportable Windows archive path: '+name)
    return name


def no_symlink(path):
    require('..' not in Path(path).parts, 'source path traversal: '+str(path))
    path=Path(os.path.abspath(path))
    for candidate in [*reversed(path.parents),path]:
        require(not candidate.is_symlink(), 'symlink source/ancestor: '+str(candidate))
    return path


def signature(path):
    info=no_symlink(path).stat()
    require(stat.S_ISREG(info.st_mode), 'input must be an ordinary file: '+str(path))
    return [info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns]


def inventory(mappings):
    require(isinstance(mappings,list) and mappings, 'mapping JSON must be a nonempty list')
    files=[];names=set();prefixes=[]
    for item in mappings:
        require(isinstance(item,dict) and set(item)=={'sourcepath','archiveprefix','kind'}, 'mapping needs exactly sourcepath/archiveprefix/kind')
        source=no_symlink(item['sourcepath'])
        prefix=safe_name(item['archiveprefix']);kind=item['kind']
        require(kind in ('sealed','unsealed','auxiliary'), 'unknown mapping kind')
        require(prefix!=MANIFEST_NAME, 'reserved archive manifest name')
        require(not any(prefix.casefold()==p.casefold() or prefix.casefold().startswith(p.casefold()+'/') or p.casefold().startswith(prefix.casefold()+'/') for p in prefixes), 'overlapping archive prefixes')
        prefixes.append(prefix)
        if kind=='unsealed': require(prefix.startswith('UNSEALED/'), 'unsealed evidence requires UNSEALED/ prefix')
        if kind=='sealed':
            require(source.is_dir(), 'sealed input must be a directory')
            summary=source/'summary.json';manifest=source/'manifest.json'
            require(summary.is_file() and manifest.is_file(), 'sealed summary/manifest missing')
            no_symlink(summary);no_symlink(manifest)
            require(json.loads(summary.read_text())['status']=='SEALED', 'completed input is not SEALED')
            require(not any((source/name).exists() for name in ('failure.json','FAILED.json','FAILURE.json','FAILED.txt')), 'failure marker in completed input')
        if source.is_dir():
            paths=[]
            for current,dirs,leaves in os.walk(source,followlinks=False):
                for name in dirs:
                    no_symlink(Path(current)/name)
                paths.extend(Path(current)/name for name in leaves)
            pairs=[(p,prefix+'/'+p.relative_to(source).as_posix()) for p in sorted(paths)]
        else:pairs=[(source,prefix)]
        for path,name in pairs:
            safe_name(name)
            require(name.casefold() not in names and name!=MANIFEST_NAME,'duplicate/reserved archive member')
            names.add(name.casefold())
            files.append({'sourcepath':str(path),'archivepath':name,'kind':kind,'stat':signature(path)})
    return sorted(files,key=lambda row:row['archivepath'])


def directory_inventory(mappings):
    """Record empty directories too; original metadata stays in the manifest."""
    result=[]
    for item in mappings:
        source=no_symlink(item['sourcepath'])
        if not source.is_dir():continue
        for current,_,_ in os.walk(source,followlinks=False):
            path=no_symlink(current);info=path.stat()
            relative=path.relative_to(source).as_posix()
            name=item['archiveprefix']+('/'+relative if relative!='.' else '')
            safe_name(name)
            result.append({'sourcepath':str(path),'archivepath':name,
                           'stat':[info.st_dev,info.st_ino,info.st_mtime_ns,info.st_ctime_ns]})
    return sorted(result,key=lambda row:row['archivepath'])


def open_source(row):
    path=Path(row['sourcepath'])
    require(signature(path)==row['stat'], 'source changed: '+str(path))
    descriptor=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        info=os.fstat(descriptor)
        require([info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns]==row['stat'], 'source replaced while opening')
        return os.fdopen(descriptor,'rb')
    except BaseException:
        os.close(descriptor);raise


def hash_stream(stream):
    digest=hashlib.sha256();size=0
    while block:=stream.read(BLOCK):digest.update(block);size+=len(block)
    return digest.hexdigest(),size


def hash_source(row):
    with open_source(row) as stream:digest,size=hash_stream(stream)
    require(size==row['stat'][2] and signature(row['sourcepath'])==row['stat'], 'source changed during hash')
    return digest


class HashedReader:
    def __init__(self,stream):self.stream=stream;self.digest=hashlib.sha256();self.size=0
    def read(self,count=-1):
        block=self.stream.read(count);self.digest.update(block);self.size+=len(block);return block


def tar_info(name,size):
    result=tarfile.TarInfo(name);result.size=size;result.mode=0o644
    result.uid=result.gid=result.mtime=0;result.uname=result.gname=''
    return result


def write_archive(path,files,manifest):
    with Path(path).open('xb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,compresslevel=1,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as archive:
                for directory in manifest.get('directories',[]):
                    info=tar_info(directory['archivepath'],0);info.type=tarfile.DIRTYPE;info.mode=0o755
                    archive.addfile(info)
                for row in files:
                    with open_source(row) as stream:
                        reader=HashedReader(stream)
                        archive.addfile(tar_info(row['archivepath'],row['stat'][2]),reader)
                        require(reader.size==row['stat'][2] and reader.digest.hexdigest()==row['sha256'],'source payload changed while packing')
                    require(signature(row['sourcepath'])==row['stat'],'source changed while packing')
                data=stable_json(manifest)
                archive.addfile(tar_info(MANIFEST_NAME,len(data)),io.BytesIO(data))
        raw.flush();os.fsync(raw.fileno())


def verify_archive(path,files,manifest):
    expected={row['archivepath']:(row['sha256'],row['stat'][2]) for row in files}
    directories={row['archivepath'] for row in manifest.get('directories',[])}
    data=stable_json(manifest);expected[MANIFEST_NAME]=(hashlib.sha256(data).hexdigest(),len(data))
    seen=set()
    with tarfile.open(path,'r|gz') as archive:
        for member in archive:
            safe_name(member.name)
            if member.isdir():
                require(member.name in directories and member.name not in seen,'unexpected/duplicate archive directory')
                seen.add(member.name);continue
            require(member.isfile() and member.name in expected and member.name not in seen,'unexpected/duplicate/nonregular archive member')
            payload=archive.extractfile(member)
            require(payload is not None,'missing archive payload')
            with payload:actual=hash_stream(payload)
            require(actual==expected[member.name],'archive byte SHA/size mismatch: '+member.name)
            seen.add(member.name)
    require(seen==set(expected)|directories,'archive member count/membership mismatch')
    # Read through gzip EOF too: tar readers can stop before gzip trailer checks.
    with gzip.open(path,'rb') as stream:
        while stream.read(BLOCK):pass
    return len(seen)


def package(mappings,output,references=None,max_bytes=2147483647):
    output=Path(os.path.abspath(output));no_symlink(output.parent)
    require(output.parent.is_dir(),'output parent must already exist')
    require(max_bytes>0,'max-bytes must be positive')
    paths={key:Path(str(output)+suffix) for key,suffix in [('partial','.partial'),('receipt','.receipt.json'),('receipt_partial','.receipt.json.partial'),('failure','.failure.json')]}
    for path in [output,*paths.values()]:
        if path.exists() or path.is_symlink():raise FileExistsError('use NEW output paths: '+str(path))
    for item in mappings:
        source=no_symlink(item['sourcepath'])
        require(output!=source and not (source.is_dir() and output.is_relative_to(source)), 'output must be outside all source directories')
    try:
        files=inventory(mappings)
        directories=directory_inventory(mappings)
        references=[] if references is None else references
        require(isinstance(references,list),'references must be a list')
        for reference in references:
            require(isinstance(reference,dict) and isinstance(reference.get('url'),str) and reference['url'].startswith('https://') and re.fullmatch(r'[0-9a-fA-F]{64}',reference.get('sha256','')) and type(reference.get('bytes')) is int and reference['bytes']>=0,'reference requires HTTPS URL, SHA256 and nonnegative bytes')
        for row in files:row['sha256']=hash_source(row)
        manifest={'format':'forge-astra-a1-original-results-v1','sources':files,'directories':directories,'references_not_duplicated':references,'hardlinks':'dereferenced regular payloads','scope':'byte preservation; original result semantics require separate validation'}
        write_archive(paths['partial'],files,manifest)
        members=verify_archive(paths['partial'],files,manifest)
        fresh=inventory(mappings)
        require(fresh==[{k:v for k,v in row.items() if k!='sha256'} for row in files], 'source inventory/stat changed during packaging')
        require(directory_inventory(mappings)==directories, 'source directory inventory/stat changed during packaging')
        with paths['partial'].open('rb') as stream:archive_sha,size=hash_stream(stream)
        require(size<=max_bytes,f'archive is {size} bytes, over release-asset limit {max_bytes}; partial retained, no split/publication')
        receipt={'status':'PASS','archive':str(output),'archive_sha256':archive_sha,'archive_bytes':size,'verified_members':members,'source_files':len(files),'source_bytes':sum(row['stat'][2] for row in files),'gzip_level':1,'manifest':manifest,'network_publication':'NOT_ATTEMPTED'}
        with paths['receipt_partial'].open('xb') as handle:
            handle.write(stable_json(receipt));handle.flush();os.fsync(handle.fileno())
        os.link(paths['partial'],output)
        os.link(paths['receipt_partial'],paths['receipt'])
        return receipt
    except BaseException as error:
        with paths['failure'].open('xb') as handle:
            handle.write(stable_json({'status':'FAILED_NOT_PUBLISHED_OR_INCOMPLETE_RECEIPT','error_type':type(error).__name__,'error':str(error),'archive_present':output.exists(),'partials_preserved':True}))
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--mapping-json',type=Path,required=True)
    parser.add_argument('--references-json',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-bytes',type=int,default=2147483647)
    args=parser.parse_args(argv)
    mappings=json.loads(args.mapping_json.read_text())
    references=json.loads(args.references_json.read_text()) if args.references_json else None
    result=package(mappings,args.output,references,args.max_bytes)
    print(json.dumps({key:value for key,value in result.items() if key!='manifest'},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
