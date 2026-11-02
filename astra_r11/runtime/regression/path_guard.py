"""Lexical Windows policy followed by root-to-leaf reparse checks."""
import ntpath
import os
from pathlib import Path
import stat


def lexical_path(path):
    raw = os.fsdecode(path)
    if not isinstance(raw, str) or '\x00' in raw or raw.startswith(('\\\\', '//')):
        raise ValueError('device/UNC/NUL path refused')
    pieces = raw.replace('/', '\\').split('\\')
    if any(part in ('.', '..') or part.endswith((' ', '.')) for part in pieces if part):
        raise ValueError('Windows dot/space path aliases refused before normalization')
    drive, tail = ntpath.splitdrive(raw)
    if ':' in tail or (drive and (len(drive) != 2 or drive[1] != ':')):
        raise ValueError('alternate stream or non-drive path refused')
    full = ntpath.normcase(ntpath.abspath(raw))
    leaf = ntpath.basename(full)
    if full.startswith(('f:\\', 'd:\\a10\\')) or full == 'd:\\a10' or leaf.endswith('.nnue') or leaf == 'forge_queue_state.json' or leaf.split('.')[0] in ('stop', 'pause'):
        raise ValueError('forbidden R11 input/output path')
    return full


def no_reparse(path):
    """Never inspect descendants until each existing ancestor is accepted."""
    full = lexical_path(path)
    drive, tail = ntpath.splitdrive(full)
    current = drive + '\\'
    chain = [current]
    for part in tail.lstrip('\\').split('\\'):
        if part:
            current = ntpath.join(current, part)
            chain.append(current)
    for current in chain:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            break
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('R11 reparse path refused')
    return Path(full)


def owned(path):
    full = lexical_path(path)
    if not full.startswith('d:\\a11\\'):
        raise ValueError('write/output path must resolve strictly under D:/a11')
    return no_reparse(full)


def audit_open(event, args):
    if event != 'open' or isinstance(args[0], int):
        return
    path, mode, flags = args
    full = lexical_path(path)
    writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    writing = writing or isinstance(mode, str) and any(c in mode for c in 'wax+')
    if writing:
        owned(full)
    else:
        no_reparse(full)
