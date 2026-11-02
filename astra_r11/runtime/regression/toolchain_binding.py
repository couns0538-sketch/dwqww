"""Original R10 identity/configuration glue; installed C toolchain is read-only."""
import hashlib
import os
from pathlib import Path
import shutil
from path_guard import no_reparse

MSVC = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231')
SDK_INCLUDE = Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0')
SDK_LIB = Path('C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0')
COMPILER_BIN = MSVC/'bin/Hostx64/x64'
BOUND_TREES = (COMPILER_BIN, MSVC/'include', MSVC/'lib/x64', SDK_INCLUDE,
               SDK_LIB/'ucrt/x64', SDK_LIB/'um/x64')


def regular_identity(path):
    original = no_reparse(path)
    for entry in (original, *original.parents):
        if getattr(entry.lstat(), 'st_file_attributes', 0) & 0x400 or entry.is_symlink():
            raise ValueError('toolchain reparse path refused: '+str(entry))
    resolved = original.resolve(strict=True)
    before = resolved.stat()
    digest = hashlib.sha256()
    with resolved.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    after = resolved.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError('toolchain file changed while hashing: '+str(resolved))
    return {'path':str(resolved), 'bytes':after.st_size, 'sha256':digest.hexdigest()}


def snapshot():
    files = {}
    for tree in BOUND_TREES:
        if not tree.is_dir():
            raise ValueError('required toolchain input tree missing: '+str(tree))
        for folder, directories, names in os.walk(tree, followlinks=False):
            for entry in [Path(folder), *(Path(folder)/name for name in directories)]:
                if getattr(entry.lstat(), 'st_file_attributes', 0) & 0x400 or entry.is_symlink():
                    raise ValueError('toolchain reparse directory refused: '+str(entry))
            for name in names:
                item = regular_identity(Path(folder)/name)
                files[item['path']] = item
    for executable in ('cl.exe','link.exe'):
        if str((COMPILER_BIN/executable).resolve(strict=True)) not in files:
            raise ValueError('required compiler/linker missing from binding')
    return files


def environment(private_python):
    """No vcvars command, registry discovery, environment dump or C: writes."""
    values = {
        'PATH':os.pathsep.join(map(str,(COMPILER_BIN, Path(private_python), Path('C:/Windows/System32')))),
        'INCLUDE':os.pathsep.join(map(str,(MSVC/'include',SDK_INCLUDE/'ucrt',SDK_INCLUDE/'shared',SDK_INCLUDE/'um'))),
        'LIB':os.pathsep.join(map(str,(MSVC/'lib/x64',SDK_LIB/'ucrt/x64',SDK_LIB/'um/x64'))),
        'CXX':'cl', 'DISTUTILS_USE_SDK':'1', 'MSSdk':'1',
        'VSCMD_ARG_TGT_ARCH':'x64', 'COMSPEC':'C:\\Windows\\System32\\cmd.exe',
    }
    os.environ.update(values)
    for key in ('CL','_CL_','LINK','_LINK_','LIBPATH'):
        os.environ.pop(key, None)
    located = shutil.which('cl.exe')
    if not located or Path(located).resolve(strict=True) != (COMPILER_BIN/'cl.exe').resolve(strict=True):
        raise ValueError('compiler search differs from the declared exact toolchain')
    return {'configured':values, 'cleared_overrides':['CL','_CL_','LINK','_LINK_','LIBPATH'],
            'input_trees':list(map(str,BOUND_TREES)),
            'scope':'installed x64 compiler/linker binaries, headers and libraries; OS-provided Windows system runtime is environmental context, not a portable toolchain claim'}
