"""R14 containment and immutable-input receipts. No production mutation APIs."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time

ROOT = Path('D:/a14')
FLOOR = 50 * 1024 ** 3
C_FLOOR = 30 * 1024 ** 3
PROTECTED = ('c:/forge_nnue_train', 'd:/forge_nnue_train', 'f:/forge_push', 'f:/nnue_pytorch')
BLOCKED_COMPONENTS = {'handoff_v7', 'locks', 'gate', 'gates', 'live_gates', 'nnue-pytorch', 'nnue_pytorch', 'forge_nnue_train'}


def safe_path(value, *, write=False):
    raw = str(value).replace('\\', '/')
    if not re.match(r'^[A-Za-z]:/', raw) or raw.startswith('//'):
        raise ValueError('absolute local drive path required')
    parts = raw[3:].split('/')
    if '//' in raw[3:] or any(p in ('.', '..') or p.endswith((' ', '.')) or any(c in p for c in ':*?"<>|') or any(ord(c)<32 for c in p) for p in parts if p):
        raise ValueError('ambiguous path component')
    if any(re.match(r'(?i)^(?:con|prn|aux|nul|conin\$|conout\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)',p) for p in parts):
        raise ValueError('Windows device name is not a file path')
    lower = raw.lower().rstrip('/')
    if any(lower == p or lower.startswith(p + '/') for p in PROTECTED):
        raise ValueError('protected root')
    if any(p.lower() in BLOCKED_COMPONENTS or p.lower().endswith('.nnue') or p.lower().endswith('.lock') for p in parts):
        raise ValueError('protected component')
    path = Path(raw)
    # Check ancestors before resolving: do not follow a junction into protected data.
    for ancestor in reversed((path, *path.parents)):
        if os.path.lexists(ancestor):
            info = ancestor.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError(f'redirected path: {ancestor}')
    resolved = path.resolve()
    if write and not resolved.is_relative_to(ROOT.resolve()):
        raise ValueError('write outside D:/a14')
    return resolved


def free_guard(required=0, *, free=None, c_free=None):
    if type(required) is not int or required < 0:
        raise ValueError('allocation must be a nonnegative integer')
    available = shutil.disk_usage('D:/').free if free is None else free
    if available < FLOOR + required:
        raise OSError(f'D: reserve breached: free={available}, floor={FLOOR}, next={required}')
    available_c = shutil.disk_usage('C:/').free if c_free is None else c_free
    if available_c < C_FLOOR:
        raise OSError(f'C: reserve breached: free={available_c}, floor={C_FLOOR}')
    deadline = os.environ.get('ASTRA_R14_DEADLINE', os.environ.get('ASTRA_R13_DEADLINE'))
    if deadline and time.time() >= float(deadline):
        raise TimeoutError('R14 bounded-job deadline reached')
    return available


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


class Snapshot:
    def __init__(self, path):
        self.path = safe_path(path)
        self.initial = self.path.stat()
        if not stat.S_ISREG(self.initial.st_mode):
            raise ValueError('input must be a regular file')
        self.hashes = None

    def check(self):
        safe_path(self.path)
        if signature(self.path.stat()) != signature(self.initial):
            raise ValueError(f'input changed: {self.path}')

    def chunks(self):
        self.check()
        sha, md5 = hashlib.sha256(), hashlib.md5()
        count = 0
        with self.path.open('rb') as handle:
            if signature(os.fstat(handle.fileno())) != signature(self.initial):
                raise ValueError('opened input identity changed')
            while chunk := handle.read(1024 * 1024):
                free_guard()
                sha.update(chunk)
                md5.update(chunk)
                count += len(chunk)
                yield chunk
            if signature(os.fstat(handle.fileno())) != signature(self.initial):
                raise ValueError('input changed while consumed')
        self.check()
        if count != self.initial.st_size:
            raise ValueError('short input read')
        observed = {'sha256': sha.hexdigest(), 'md5': md5.hexdigest()}
        if self.hashes is not None and observed != self.hashes:
            raise ValueError('input content changed')
        self.hashes = observed

    def digest(self):
        for _ in self.chunks():
            pass
        return self.hashes

    def bytes(self, limit=16 * 1024 * 1024):
        if self.initial.st_size > limit:
            raise ValueError('metadata/file exceeds bounded read')
        return b''.join(self.chunks())

    def lines(self):
        pending = b''
        for chunk in self.chunks():
            pending += chunk
            lines = pending.split(b'\n')
            pending = lines.pop()
            for line in lines:
                if len(line)>1024*1024:
                    raise ValueError('input line too long')
                yield (line + b'\n').decode('utf-8', errors='strict')
            if len(pending) > 1024 * 1024:
                raise ValueError('input line too long')
        if pending:
            yield pending.decode('utf-8', errors='strict')

    def receipt(self):
        if self.hashes is None:
            raise ValueError('input not completely consumed')
        self.check()
        return dict(path=str(self.path), bytes=self.initial.st_size, mtime_ns=self.initial.st_mtime_ns, **self.hashes)


class Inputs:
    def __init__(self):
        self.items = {}

    def get(self, path):
        path = safe_path(path)
        key = str(path).casefold()
        if key not in self.items:
            self.items[key] = Snapshot(path)
        return self.items[key]

    def json(self, path):
        return strict_json_loads(self.get(path).bytes().decode('utf-8-sig'))

    def verify(self, path, expected):
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-fA-F]{64}', expected):
            raise ValueError('expected full SHA256')
        snapshot = self.get(path)
        actual = snapshot.digest()['sha256']
        if actual != expected.lower():
            raise ValueError(f'SHA256 mismatch: {path}')
        return snapshot

    def receipts(self):
        result=[]
        for _,snapshot in sorted(self.items.items()):
            if snapshot.hashes is None:
                raise ValueError('input not completely consumed')
            # Metadata alone misses same-size replacements with restored mtime.
            snapshot.digest()
            result.append(snapshot.receipt())
        return result


def strict_json_loads(text):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key]=value
        return result
    return json.loads(text,object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def write_json(path, value):
    path = safe_path(path, write=True)
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    free_guard(len(payload) + 1024 * 1024)
    with path.open('xb') as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def new_directory(path, required=16 * 1024 * 1024):
    path = safe_path(path, write=True)
    free_guard(required)
    path.mkdir(parents=True, exist_ok=False)
    return path


def install_audit_fence():
    """Deny external writes in this Python process, including library side effects.

    The launcher and explicit input manifests remain required; audit hooks are
    defense in depth, not an OS sandbox for arbitrary native code.
    """
    def audit(event, args):
        paths = []
        writing = False
        if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
            # subprocess.DEVNULL opens the exact OS sink with O_RDWR and no
            # create/truncate flags. It allocates no file on any drive.
            raw=os.fsdecode(args[0])
            if raw.casefold()==os.devnull.casefold() and args[1] is None and isinstance(args[2],int) and not args[2] & (os.O_CREAT|os.O_TRUNC|os.O_APPEND):
                return
            paths = [args[0]]
            mode, flags = args[1], args[2]
            writing = bool(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'):
            paths,writing=[args[0]],True
        elif event in ('os.rename','os.link','os.symlink'):
            paths,writing=list(args[:2]),True
        for item in paths:
            if isinstance(item,int):
                continue
            path=Path(os.fsdecode(item)).absolute()
            lower=str(path).replace('\\','/').lower()
            if any(lower==p or lower.startswith(p+'/') for p in PROTECTED) or any(p.lower() in BLOCKED_COMPONENTS or p.lower().endswith('.nnue') for p in path.parts):
                raise PermissionError(f'protected path access: {path}')
            if writing:
                if event in ('os.remove','os.rmdir') and os.path.lexists(path):
                    info=path.lstat()
                    if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                        # Unlink removes the owned link itself, not its target.
                        # Checking the parent prevents crossing a redirected ancestor.
                        safe_path(path.parent,write=True)
                        continue
                safe_path(path,write=True)
    sys.addaudithook(audit)
