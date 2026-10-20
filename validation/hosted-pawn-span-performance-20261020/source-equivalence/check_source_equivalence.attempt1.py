#!/usr/bin/env python3
"""Source/proof reads only; never imports runners or launches another process.

Use --write once to preserve this preparer's addendum. Default verification
recomputes the same evidence and compares it with the saved JSON and diff.
This is a source-equivalence review, not another probe execution or root review.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile

REPO = Path('/workspace/dwqww')
HERE = Path(__file__).resolve().parent
PROTOTYPE = Path('/workspace/.cloud-setup/pawn-span-fill-prototype-source')
FROZEN = Path('/workspace/.cloud-setup/pawn-span-fill-native-source')
EVIDENCE = REPO / 'validation/pawn-span-fill-20261020'
NATIVE = REPO / 'validation/pawn-span-fill-native-20261020'
PUBLIC = EVIDENCE / 'independent-review/public-diff-attempt1'
COMMIT = 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
EXPECTED_CHANGES = ('CMakeLists.txt', 'src/uci.cpp', 'tests/pawn_span_tests.cpp')
SUMMARY_SHA = '5d2f549005c36f19ec635d0c0e4399456046db79afe62a09f473551558548e13'
ROOT_SHA = '9d20b35515e4be3e9230039869409a4a46003fede3a11949e93c720e3c4ab770'
ARCHIVE_SHA = 'd462b5d67d41ff448f2d3c830d49a774c2ec0b072972be73bb0a2fc1a95d73c5'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key: ' + str(path))
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observation(path):
    require(path.is_file() and not path.is_symlink(), 'Unsafe/missing input: ' + str(path))
    return {'sha256': sha(path), 'mode': stat.S_IMODE(path.stat().st_mode)}


def all_files(root):
    return {p.relative_to(root).as_posix(): sha(p)
            for p in sorted(root.rglob('*')) if p.is_file()}


def check():
    initial_path = EVIDENCE / 'release-attempt1/summary.json'
    root_path = NATIVE / 'ROOT-FROZEN-SOURCE-GATES.json'
    archive_path = NATIVE / 'frozen-source-fc23918.tar'
    records = [
        initial_path, root_path, archive_path,
        EVIDENCE / 'EXPECTED-SOURCE-75.json', EVIDENCE / 'FINAL-SOURCE-75.json',
        EVIDENCE / 'CHECKPOINT.json',
        EVIDENCE / 'independent-review/SOURCE-CHECK.json',
        EVIDENCE / 'independent-review/PROBE-PREPARATION.json',
        EVIDENCE / 'independent-review/PROBE-RECEIPT.json',
        EVIDENCE / 'independent-review/run_public_diff.py',
        EVIDENCE / 'independent-review/public_eval_probe.cpp',
        EVIDENCE / 'independent-review/public-eval-fens.txt',
        PUBLIC / 'RESULT.json', PUBLIC / 'inputs-before.json', PUBLIC / 'inputs-after.json',
        PUBLIC / 'baseline19-run/stdout.txt', PUBLIC / 'prototype20_first_GREEN-run/stdout.txt',
        NATIVE / 'SOURCE-AND-DRIVER-FREEZE.json',
        NATIVE / 'frozen-source-fc23918-files.json',
        Path(__file__).resolve(),
    ]
    initial = read_json(initial_path)
    expected = read_json(EVIDENCE / 'EXPECTED-SOURCE-75.json')
    intermediate = read_json(EVIDENCE / 'FINAL-SOURCE-75.json')
    root = read_json(root_path)
    before = read_json(PUBLIC / 'inputs-before.json')
    after = read_json(PUBLIC / 'inputs-after.json')
    result = read_json(PUBLIC / 'RESULT.json')
    receipt = read_json(EVIDENCE / 'independent-review/PROBE-RECEIPT.json')
    consumed = set(records) | {PROTOTYPE / n for n in expected} | {FROZEN / n for n in root['inputs']} | set(map(Path, before))
    frozen_inputs = {str(p): observation(p) for p in sorted(consumed)}
    require(sha(initial_path) == SUMMARY_SHA, 'Initial prototype build summary changed')
    require(sha(root_path) == ROOT_SHA, 'Frozen20 root source record changed')
    require(sha(archive_path) == ARCHIVE_SHA == root['source_archive_sha256'], 'Frozen20 archive changed')
    require(root['source_commit'] == COMMIT, 'Frozen20 source pin differs')
    require(len(expected) == len(root['inputs']) == 75, 'Expected exact 75-file maps')
    require(initial['source_root'] == str(PROTOTYPE), 'Original prototype path differs')
    require(initial['exported_source_sha256_before_build'] == expected, 'Original build map differs')
    require(initial['exported_source_sha256_final'] == expected, 'Original build source changed')
    require(all_files(PROTOTYPE) == expected, 'Actual original prototype export differs')
    require(all_files(FROZEN) == root['inputs'], 'Actual frozen20 export differs')
    require(read_json(NATIVE / 'frozen-source-fc23918-files.json') == root['inputs'], 'Native exported map differs')
    archive_inventory = {}
    with tarfile.open(archive_path) as archive:
        require(archive.pax_headers.get('comment') == COMMIT, 'Archive PAX source identity differs')
        for member in archive:
            name = PurePosixPath(member.name)
            require(not name.is_absolute() and '..' not in name.parts and name.as_posix() == member.name,
                    'Unsafe archive path')
            if member.isdir():
                continue
            require(member.isfile() and member.name not in archive_inventory, 'Unsafe/duplicate archive member')
            archive_inventory[member.name] = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
    require(archive_inventory == root['inputs'], 'Archive/member/root inventory differs')
    require(set(expected) == set(root['inputs']), 'Source file set differs')
    changed = [name for name in expected if expected[name] != root['inputs'][name]]
    require(tuple(changed) == EXPECTED_CHANGES, 'Unexpected source changes: ' + repr(changed))
    replacements = {
        'CMakeLists.txt': ('project(ChessEngineForge VERSION 6.4.19 LANGUAGES CXX)',
                          'project(ChessEngineForge VERSION 6.4.20 LANGUAGES CXX)'),
        'src/uci.cpp': ('id name Chess Engine Forge 6.4.19 candidate',
                        'id name Chess Engine Forge 6.4.20 candidate'),
        'tests/pawn_span_tests.cpp': ('span from independent attack tables',
                                     'span from stored pawn attack tables'),
    }
    diff = ''
    for name in changed:
        old = (PROTOTYPE / name).read_text()
        new = (FROZEN / name).read_text()
        a, b = replacements[name]
        require(old.count(a) == 1 and old.replace(a, b) == new, 'Non-label source change: ' + name)
        diff += ''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                           fromfile='prototype-first-GREEN/' + name, tofile='frozen20/' + name))
    require([n for n in intermediate if intermediate[n] != root['inputs'][n]] == ['CMakeLists.txt', 'src/uci.cpp'],
            'Intermediate label-only map differs unexpectedly')
    cmake = (FROZEN / 'CMakeLists.txt').read_text()
    require(cmake.count('VERSION') == 1 and 'configure_file' not in cmake,
            'Project version may affect generated production source')
    core_list = cmake.split('add_library(forge_core\n', 1)[1].split(')', 1)[0].split()
    require(core_list == ['src/bitboard.cpp', 'src/board.cpp', 'src/book.cpp', 'src/eval.cpp',
                          'src/eval_params.cpp', 'src/nnue.cpp', 'src/search.cpp'], 'Unexpected core TU set')
    protected = [n for n in expected if n.startswith(('include/', 'src/')) and n != 'src/uci.cpp']
    require(len(protected) == 19 and all(expected[n] == root['inputs'][n] for n in protected),
            'Protected core source/include bytes differ')
    require(before == after and len(before) == 55, 'Original public-diff before/after input observations differ')
    require(before[str(initial_path)]['sha256'] == SUMMARY_SHA, 'Public diff did not bind initial build summary')
    public_prototype = {str(Path(n).relative_to(PROTOTYPE)): v['sha256']
                        for n, v in before.items() if Path(n).is_relative_to(PROTOTYPE)}
    require(public_prototype == {n: h for n, h in expected.items() if n.startswith(('include/', 'src/'))},
            'Original public-diff prototype source paths differ')
    for name, expected_observation in before.items():
        require(observation(Path(name)) == expected_observation, 'Original public input currently differs: ' + name)
    require(result['source_identity_qualification'].startswith('Candidate is first GREEN working-tree export, still version19'),
            'Original producer identity qualification was relabeled')
    require(result['status'] == receipt['status'] == 'PASS_EXACT_95_PUBLIC_EVALUATION_AND_FULL_TRACE_ROWS',
            'Original public result status differs')
    originals = [(PUBLIC / name / 'stdout.txt').read_bytes() for name in ('baseline19-run', 'prototype20_first_GREEN-run')]
    require(originals[0] == originals[1], 'Original public transcripts differ')
    rows = originals[0].decode('ascii').splitlines()
    require(len(rows) == 95 and all(len(row.split()) == 647 for row in rows), 'Original transcript shape differs')
    require(sha(PUBLIC / 'baseline19-run/stdout.txt') == receipt['matching_stdout_sha256'], 'Original transcript digest differs')
    require(result['executables'][str(Path('/workspace/.cloud-setup/pawn-span-fill-public-diff-attempt1/prototype20_first_GREEN'))]['sha256']
            == '858300d42f881ce2e9ffa6a8ee26dbfb70a620691698abf873f3d69f0ba71bd7', 'Original prototype probe identity differs')
    final_inputs = {str(p): observation(p) for p in sorted(consumed)}
    require(frozen_inputs == final_inputs, 'Inputs changed during preparer check')
    return {
        'status': 'PREPARER_SOURCE_EQUIVALENCE_VERIFIED_ROOT_REVIEW_PENDING',
        'scope': 'Read-only source/proof analysis; no Git, compiler, engine, benchmark, new probe execution, or network.',
        'frozen20_source_commit': COMMIT,
        'prototype_identity_preserved': 'first GREEN working-tree export, version19; historical 95-row probe, not an actual frozen20 probe execution',
        'source_files_each': 75,
        'changed_source_paths': changed,
        'unchanged_source_files': 72,
        'protected_core_source_include_and_data': {n: expected[n] for n in protected},
        'core_translation_units': core_list,
        'original_public_consumed_inputs': 55,
        'original_public_source_paths_bound': len(public_prototype),
        'original_public_rows': 95,
        'original_public_fields_per_row': 647,
        'original_public_compared_integer_fields': 61465,
        'original_public_transcript_sha256': receipt['matching_stdout_sha256'],
        'source_archive_pax_and_complete_inventory_verified': True,
        'source_equivalence_argument': 'All seven core translation units, all eight headers and four included data files are byte identical. Only project version, UCI executable identification and a test diagnostic label differ. CMake version creates no production definition/header; UCI and test files are not forge_core translation units. This supports applying the historical finite source-level evaluation/trace parity to unchanged frozen20 evaluation code; it does not claim a new frozen20 probe execution or byte-identical compiled core.',
        'root_review_required': True,
        'engine_correctness_performance_or_elo_acceptance': False,
        'input_bytes_and_modes_rechecked': True,
        'consumed_inputs': frozen_inputs,
        'exact_diff_sha256': hashlib.sha256(diff.encode()).hexdigest(),
    }, diff


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true', help='Create the addendum once; never overwrite')
    args = parser.parse_args()
    result, diff = check()
    json_path = HERE / 'PREPARER-SOURCE-EQUIVALENCE.json'
    diff_path = HERE / 'prototype-to-frozen20.diff'
    if args.write:
        with diff_path.open('x') as stream:
            stream.write(diff)
        with json_path.open('x') as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write('\n')
    else:
        require(read_json(json_path) == result and diff_path.read_text() == diff, 'Saved addendum differs from recomputation')
    print(json.dumps({k: v for k, v in result.items() if k != 'consumed_inputs'}, indent=2))


if __name__ == '__main__':
    main()
