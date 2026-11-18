import argparse
import hashlib
from pathlib import Path
import shlex
import subprocess


def run(command, cwd, **options):
    print(shlex.join(command), flush=True)
    return subprocess.run(command, cwd=cwd, check=True, **options)


def main():
    parser = argparse.ArgumentParser(description='Select the plain v3 kernel in only nnue_v3.cpp.')
    parser.add_argument('base', type=Path, help='original kF build dir')
    parser.add_argument('line', type=Path, help='exact archived kF compile line for nnue_v3.cpp')
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    options = iter(shlex.split(args.line.read_text()))
    common = []
    for word in options:
        if word in ('-c', '-MD'):
            continue
        if word in ('-o', '-MT', '-MF'):
            next(options)
            continue
        common.append(word)
    scalar = [*common, '-mno-avx512f', '-mno-avx2', '-fno-tree-vectorize']
    macro_dump = run([*scalar, '-dM', '-E'], args.base, capture_output=True, text=True).stdout
    macros = set(macro_dump.splitlines())
    expected = {'#define FORGE_NNUE_V3_AVX2 0', '#define FORGE_NNUE_V3_AVX512 0',
                '#define FORGE_SPD_NNUE_ZMM 1'}
    assert expected <= macros, 'wrong translation-unit macro selection'
    print('\n'.join(sorted(expected)), flush=True)
    obj = args.out / 'nnue_v3.cpp.o'
    run([*scalar, '-c', '-o', str(obj)], args.base)
    link = shlex.split((args.base / 'CMakeFiles/forge.dir/link.txt').read_text())
    executable = args.out / 'forge'
    link = [str(obj) if word == 'CMakeFiles/forge.dir/src/nnue_v3.cpp.o' else
            str(executable) if word == 'forge' else word for word in link
            if not word.startswith('-Wl,--dependency-file=')]
    assert str(obj) in link and str(executable) in link
    run(link, args.base)
    for path in (obj, executable):
        print(hashlib.sha256(path.read_bytes()).hexdigest(), path)


if __name__ == '__main__':
    main()
