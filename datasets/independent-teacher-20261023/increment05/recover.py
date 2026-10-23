#!/usr/bin/env python3
"""Stream closed files into opaque <=31 MiB ZIP slices; verify without reassembly."""
import argparse
from bisect import bisect_right
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import zipfile

LIMIT = 31 * (1 << 20)


def require(value, message):
    if not value: raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''): digest.update(block)
    return digest.hexdigest()


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name and '\x00' not in name, 'unsafe member name')
    path = PurePosixPath(name)
    require(path.parts and not path.is_absolute() and path.as_posix() == name and ':' not in path.parts[0]
            and all(part not in ('.', '..', '') for part in path.parts), 'unsafe member path')
    return name


def regular(path):
    path = Path(path).absolute()
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'symlink source/part rejected')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode), 'source/part must be regular')
    return info


class PartsWriter:
    def __init__(self, root, limit):
        self.root, self.limit, self.parts, self.stream = root, limit, [], None
        self.offset = self.part_size = 0
        self.digest = hashlib.sha256(); self.part_digest = None

    def tell(self): return self.offset
    def seek(self, *args): raise io.UnsupportedOperation('streaming ZIP')
    def flush(self):
        if self.stream is not None: self.stream.flush()

    def finish(self):
        if self.stream is not None:
            self.stream.flush(); os.fsync(self.stream.fileno()); self.stream.close()
            self.parts.append({'name':self.name, 'bytes':self.part_size, 'sha256':self.part_digest.hexdigest()})
            self.stream = None

    def write(self, value):
        data = memoryview(value); total = len(data)
        while data:
            if self.stream is None:
                self.name = 'dataset.zip.%04d' % (len(self.parts) + 1)
                self.stream = (self.root / self.name).open('xb'); self.part_size = 0; self.part_digest = hashlib.sha256()
            block = data[:self.limit - self.part_size]
            self.stream.write(block); self.part_digest.update(block); self.digest.update(block)
            self.offset += len(block); self.part_size += len(block); data = data[len(block):]
            if self.part_size == self.limit: self.finish()
        return total


class PartsReader(io.RawIOBase):
    def __init__(self, root, records):
        super().__init__(); self.root, self.records = Path(root), records
        self.starts = [0]
        for record in records: self.starts.append(self.starts[-1] + record['bytes'])
        self.offset = 0; self.stream = None; self.index = None

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.offset
    def seek(self, offset, whence=0):
        require(whence in (0, 1, 2), 'invalid seek origin')
        value = offset + (self.offset if whence == 1 else self.starts[-1] if whence == 2 else 0)
        require(value >= 0, 'negative seek'); self.offset = value; return value

    def read(self, size=-1):
        remaining = max(0, self.starts[-1] - self.offset)
        size = remaining if size is None or size < 0 else min(size, remaining)
        output = bytearray()
        while size:
            index = bisect_right(self.starts, self.offset) - 1
            if index != self.index:
                if self.stream is not None: self.stream.close()
                self.stream = (self.root / self.records[index]['name']).open('rb'); self.index = index
            self.stream.seek(self.offset - self.starts[index])
            block = self.stream.read(min(size, self.starts[index + 1] - self.offset))
            require(block, 'truncated part during seekable read')
            output.extend(block); self.offset += len(block); size -= len(block)
        return bytes(output)

    def close(self):
        if self.stream is not None: self.stream.close()
        super().close()


def verify_records(root, manifest):
    require(manifest.get('schema') == 'forge-streaming-multipart-zip-v1', 'unsupported recovery manifest')
    limit = manifest['part_bytes_limit']; require(type(limit) is int and 1 <= limit <= LIMIT, 'invalid part cap')
    parts = manifest['parts']; require(parts, 'missing parts'); digest = hashlib.sha256(); total = 0
    expected_names = set()
    for index, record in enumerate(parts):
        name = 'dataset.zip.%04d' % (index + 1); require(record['name'] == name, 'part order/name differs')
        require(type(record['bytes']) is int and 0 < record['bytes'] <= limit
                and (index == len(parts)-1 or record['bytes'] == limit), 'part size/cap differs')
        path = root / name; info = regular(path); require(info.st_size == record['bytes'], 'part bytes differ')
        part_hash = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1 << 20), b''): part_hash.update(block); digest.update(block)
        require(part_hash.hexdigest() == record['sha256'], 'part hash differs: ' + name)
        total += info.st_size; expected_names.add(name)
    require({path.name for path in root.glob('dataset.zip.*')} == expected_names, 'unexpected/missing part files')
    require(total == manifest['archive']['bytes'] and digest.hexdigest() == manifest['archive']['sha256'], 'archive bytes/hash differs')
    records = {safe_name(record['path']):record for record in manifest['members']}
    require(len(records) == len(manifest['members']), 'duplicate member identities')
    names = set(records)
    for alias in manifest.get('aliases', []):
        name = safe_name(alias['path']); require(name not in names and alias['target'] in records, 'duplicate/invalid alias')
        names.add(name)
        require(all(alias[key] == records[alias['target']][key] for key in ('bytes','sha256','mode')), 'alias identity differs')
    folded = {name.casefold() for name in names}
    require(len(folded) == len(names), 'casefold namespace collision')
    for name in folded:
        require(not any(str(parent) in folded for parent in PurePosixPath(name).parents), 'file/ancestor namespace collision')
    with PartsReader(root, parts) as reader, zipfile.ZipFile(reader) as archive:
        reader.seek(-22, 2); tail = reader.read()
        require(tail[:4] == b'PK\x05\x06' and tail[4:8] == bytes(4) and tail[-2:] == bytes(2), 'ZIP trailing bytes/comment/disk fields differ')
        infos = archive.infolist()
        require(len(infos) == len(records) and {item.filename for item in infos} == set(records), 'ZIP member set/duplicates differ')
        for item in infos:
            record = records[safe_name(item.filename)]; mode = item.external_attr >> 16
            require(item.create_system == 3 and stat.S_ISREG(mode) and stat.S_IMODE(mode) == record['mode']
                    and item.compress_type == zipfile.ZIP_STORED and item.file_size == record['bytes']
                    and item.compress_size == item.file_size, 'ZIP mode/size/compression differs')
            member_hash = hashlib.sha256(); count = 0
            with archive.open(item) as stream:
                for block in iter(lambda: stream.read(1 << 20), b''): member_hash.update(block); count += len(block)
            require(count == record['bytes'] and member_hash.hexdigest() == record['sha256'], 'member bytes/hash differs')
    return {'status':'PASS_PART_AND_LOGICAL_ZIP_MEMBER_SHA_CRC_MODE', 'parts_verified':len(parts),
            'members_verified':len(records), 'aliases_verified':len(manifest.get('aliases', [])), 'archive_bytes':total}


def pack(declarations_path, out, part_bytes=LIMIT):
    require(type(part_bytes) is int and 1 <= part_bytes <= LIMIT, 'part cap must be <=31 MiB')
    declaration_bytes = Path(declarations_path).read_bytes(); declaration_sha = hashlib.sha256(declaration_bytes).hexdigest()
    declaration = json.loads(declaration_bytes)
    require(declaration.get('status') == 'CLOSED_INPUTS_FROZEN' and declaration.get('files'), 'explicit closed input declarations required')
    out = Path(out); out.mkdir(parents=True, exist_ok=False); writer = PartsWriter(out, part_bytes)
    records, names, aliases = [], set(), []
    try:
        with zipfile.ZipFile(writer, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            for entry in declaration['files']:
                name = safe_name(entry['member']); require(name not in names, 'duplicate member'); names.add(name)
                source = Path(entry['source']).absolute(); before = regular(source)
                require(re.fullmatch('[0-9a-f]{64}', entry['sha256']) and type(entry['bytes']) is int
                        and entry['bytes'] == before.st_size, 'invalid source hash/bytes declaration')
                mode = stat.S_IMODE(before.st_mode); require(not mode & ~0o777, 'unsafe source permission bits')
                item = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0)); item.create_system = 3
                item.external_attr = (stat.S_IFREG | mode) << 16; item.file_size = before.st_size
                count = 0; member_hash = hashlib.sha256()
                descriptor = os.open(source, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
                with os.fdopen(descriptor, 'rb') as incoming, archive.open(item, 'w', force_zip64=True) as target:
                    current = os.fstat(incoming.fileno())
                    require(stat.S_ISREG(current.st_mode) and (current.st_dev,current.st_ino,current.st_size,current.st_mtime_ns)
                            == (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns), 'source changed at open')
                    for block in iter(lambda: incoming.read(1 << 20), b''): target.write(block); member_hash.update(block); count += len(block)
                require(count == entry['bytes'] and member_hash.hexdigest() == entry['sha256'] and sha(source) == entry['sha256'], 'source hash changed/mismatched')
                after = regular(source)
                require((after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_mode)
                        == (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_mode), 'source metadata changed')
                records.append({'path':name,'source':str(source),'bytes':count,'sha256':entry['sha256'],'mode':mode})
        writer.finish(); by_name = {record['path']:record for record in records}
        for entry in declaration.get('aliases', []):
            name = safe_name(entry['member']); require(name not in names and entry['target'] in by_name, 'duplicate/invalid alias')
            names.add(name); target = by_name[entry['target']]; source = Path(entry['source']).absolute(); info = regular(source)
            require(info.st_size == target['bytes'] and stat.S_IMODE(info.st_mode) == target['mode'] and sha(source) == target['sha256'], 'alias source identity differs')
            aliases.append({**{key:target[key] for key in ('bytes','sha256','mode')}, 'path':name,'source':str(source),'target':entry['target']})
        manifest = {'schema':'forge-streaming-multipart-zip-v1','parts_are':'opaque ordered slices of one ZIP; not ZIP split volumes',
                    'part_bytes_limit':part_bytes,'parts':writer.parts,'archive':{'bytes':writer.offset,'sha256':writer.digest.hexdigest()},
                    'members':records,'aliases':aliases,'declarations_sha256':declaration_sha}
        manifest['verification'] = verify_records(out, manifest)
        for record in records + aliases:
            info = regular(record['source'])
            require(info.st_size == record['bytes'] and stat.S_IMODE(info.st_mode) == record['mode']
                    and sha(record['source']) == record['sha256'], 'source changed before manifest commit')
        require(sha(declarations_path) == declaration_sha, 'source declarations changed before commit')
        temporary = out/'RECOVERY-MANIFEST.pending'
        with temporary.open('x') as stream: json.dump(manifest, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, out/'RECOVERY-MANIFEST.json')
        if os.name == 'posix':
            descriptor = os.open(out, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try: os.fsync(descriptor)
            finally: os.close(descriptor)
        return manifest
    except BaseException as failure:
        writer.finish()
        committed = out/'RECOVERY-MANIFEST.json'
        (out/'FAILURE.json').write_text(json.dumps({
            'status':'COMMITTED_VERIFIED_DURABILITY_UNCONFIRMED' if committed.exists() else 'FAILED_NO_COMMITTED_MANIFEST',
            'manifest_sha256':sha(committed) if committed.exists() else None,
            'error':repr(failure),'completed_parts':writer.parts},indent=2)+'\n')
        raise


def verified_snapshot(manifest_path, expected_sha):
    path = Path(manifest_path); regular(path)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_sha, 'recovery manifest hash differs')
    manifest = json.loads(raw)
    return manifest, verify_records(path.parent, manifest)


def verify(manifest_path, expected_sha):
    return verified_snapshot(manifest_path, expected_sha)[1]


def restore(manifest_path, expected_sha, out):
    manifest, result = verified_snapshot(manifest_path, expected_sha); manifest_path = Path(manifest_path)
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    with PartsReader(manifest_path.parent, manifest['parts']) as reader, zipfile.ZipFile(reader) as archive:
        for record in manifest['members']:
            target = out/record['path']; target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(record['path']) as source, target.open('xb') as destination: shutil.copyfileobj(source, destination, 1 << 20)
            require(sha(target) == record['sha256'], 'restored member hash differs')
    for alias in manifest.get('aliases', []):
        target = out/alias['path']; target.parent.mkdir(parents=True, exist_ok=True)
        try: os.link(out/alias['target'], target)
        except OSError: shutil.copyfile(out/alias['target'], target)
        require(sha(target) == alias['sha256'], 'restored alias hash differs')
    for record in manifest['members'] + manifest.get('aliases', []): (out/record['path']).chmod(record['mode'])
    return {**result,'restored_to':str(out)}


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='command', required=True)
    packer = commands.add_parser('pack'); packer.add_argument('--files', type=Path, required=True); packer.add_argument('--out', type=Path, required=True)
    packer.add_argument('--part-bytes', type=int, default=LIMIT)
    for name in ('verify','restore'):
        verifier = commands.add_parser(name); verifier.add_argument('--manifest', type=Path, required=True); verifier.add_argument('--sha256', required=True)
        if name == 'restore': verifier.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'pack':
        result = pack(args.files, args.out, args.part_bytes)
        print(json.dumps({'status':'PASS_STREAMED_VERIFIED_PARTS','manifest_sha256':sha(args.out/'RECOVERY-MANIFEST.json'),
                          'parts':len(result['parts']),'archive':result['archive']}))
    else: print(json.dumps(restore(args.manifest,args.sha256,args.out) if args.command == 'restore' else verify(args.manifest,args.sha256)))


if __name__ == '__main__': main()
