#!/usr/bin/env python3
"""Emit a diagnostic C++ helper bound to the actual canonical Forge bench.

Pure source production only: never invokes CMake, a compiler, an engine, or Git.
The generated helper must later be built/run under the existing owned protocol.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
BASE = Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src')
INPUT_SHA = {
    'src/uci.cpp': '13c7c87a377ec30616f9a733bc5d74072c697c6e48db9eb39d751409f3cc0f97',
    'include/forge/board.hpp': '5b42d3557730edc65f795a097e45d18a3cb621d56bdfa8b379773bb496204c77',
    'tools/search_benchmark.cpp': 'f12fb4681ac91c782a29b7ca77959278c03a1f1db1424fefe16cc3feaa1cb83f',
}
PATCH_SHA = '66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d'
HEADER_SHA = 'f1e61dcf7ec82339f6bef582fe5af0ff256171b3824e7964de3fd10c2b10b140'
PATCH = Path('/tmp/forge_sol_S12_delivery_prepared_20261026/forge_sol_S12_lazyacc_h256e12_reviewv2_20261026.patch')
TEMPLATE = HERE / 'forge_sol_S12_benchcounter_template_20261026.cpp.in'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(text):
    return re.sub(r'\s+', '', text)


def extract(uci, board_header, old_tool):
    """Fail closed on unknown bench grammar or changed search semantics."""
    start = '        } else if (command == "bench") {'
    end = '        } else if (command == "ponderhit") {'
    if uci.count(start) != 1 or uci.count(end) != 1:
        raise ValueError('expected unique canonical bench branch delimiters')
    block = uci.split(start, 1)[1].split(end, 1)[0]
    arrays = list(re.finditer(r'constexpr\s+std::array<std::string_view,\s*8>\s+fens\s*\{(.*?)\};', block, re.S))
    if len(arrays) != 1:
        raise ValueError('expected one exact eight-FEN array')
    array = arrays[0]
    entries = [x.strip() for x in array.group(1).split(',') if x.strip()]
    if len(entries) != 8 or entries[0] != 'forge::Board::StandardStartFen':
        raise ValueError('expected startpos plus seven literal FENs, in canonical order')
    match = re.search(r'StandardStartFen\s*=\s*("[^"\\]*")\s*;', board_header)
    if not match:
        raise ValueError('unknown StandardStartFen declaration')
    fens = [json.loads(match.group(1))]
    for entry in entries[1:]:
        if not re.fullmatch(r'"[^"\\]*"', entry):
            raise ValueError('only literal FENs supported, no guessed expression evaluation')
        fens.append(json.loads(entry))
    for fen in fens:
        if len(fen.split()) != 6 or len(fen.split()[0].split('/')) != 8 or any(ord(x) < 32 or x in '"\\' for x in fen):
            raise ValueError('unsupported FEN encoding')
    loop = block[array.end():].split('            const auto elapsed_ms', 1)[0]
    expected = '''std::uint64_t total_nodes = 0;
        const auto start = std::chrono::steady_clock::now();
        forge::Searcher bench_searcher(16);
        for (const std::string_view fen : fens) {
            forge::Board bench_board;
            if (!bench_board.set_fen(fen)) continue;
            forge::SearchLimits limits;
            limits.depth = depth;
            bench_searcher.clear();
            total_nodes += bench_searcher.search(
                bench_board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
        }'''
    if compact(loop) != compact(expected):
        raise ValueError('bench search/clear/Hash16/depth/exclusive-TT contract changed')
    if not re.search(r'forge::Board board;.*forge::Searcher searcher\(32\);', old_tool, re.S):
        raise ValueError('existing constructor initialization example changed')
    return {'fens': fens, 'bench_block_sha256': sha(block.encode()),
            'suite_sha256': sha(('\n'.join(fens) + '\n').encode()),
            'canonical_array_sha256': sha(array.group(0).encode()),
            'initialization': 'existing Board/Searcher constructors; no extra initialization API',
            'search_contract': '8 ordered FENs; one Searcher(16, default1thread); clear before every FEN; default SearchLimits except depth; emit_info=false; TTAccess::Exclusive'}


def emit(out):
    if out.exists():
        raise FileExistsError('new output directory required; never overwrite sealed output')
    inputs = {}
    for name, expected in INPUT_SHA.items():
        data = (BASE / name).read_bytes()
        if sha(data) != expected:
            raise ValueError('canonical input changed: ' + name)
        inputs[name] = data.decode()
    if sha(PATCH.read_bytes()) != PATCH_SHA:
        raise ValueError('S12 candidate patch changed')
    spec = extract(inputs['src/uci.cpp'], inputs['include/forge/board.hpp'], inputs['tools/search_benchmark.cpp'])
    template = TEMPLATE.read_text()
    replacements = {
        '@@FEN_LITERALS@@': '\n'.join('    ' + json.dumps(fen) + ',' for fen in spec['fens']),
        '@@UCI_SHA@@': INPUT_SHA['src/uci.cpp'], '@@BLOCK_SHA@@': spec['bench_block_sha256'],
        '@@SUITE_SHA@@': spec['suite_sha256'], '@@HEADER_SHA@@': HEADER_SHA, '@@PATCH_SHA@@': PATCH_SHA,
    }
    generated = template
    for token, value in replacements.items():
        if generated.count(token) != 1:
            raise ValueError('unique template token required: ' + token)
        generated = generated.replace(token, value)
    if '@@' in generated:
        raise ValueError('unexpanded template token')
    out.mkdir(parents=True)
    helper = out / 'forge_sol_S12_benchcounter_helper_20261026.cpp'
    helper.write_text(generated)
    binding = {'scope': 'source-only production; all native UNVERIFIED', 'status': 'PREPARED',
               'canonical_base': str(BASE), 'canonical_input_sha256': INPUT_SHA,
               'candidate_patch_sha256': PATCH_SHA, 'candidate_header_sha256': HEADER_SHA,
               'template_sha256': sha(TEMPLATE.read_bytes()),
               'producer_sha256': sha(Path(__file__).read_bytes()), 'helper_sha256': sha(helper.read_bytes()),
               **spec,
               'native_requirements': ['featureON same core/header ABI and strict flags',
                   'actual archive and link-map source closure',
                   'new main ELF FIRST bare bench11 PASS before this diagnostic helper',
                   'owned bounded execution and complete original stdout/stderr',
                   'OFF and ON fresh processes for each five reference depths'],
               'engine_executions': 0, 'compiler_executions': 0,
               'diagnostic_only': 'No time/NPS output or claim; no engine/UCI changes'}
    receipt = out / 'forge_sol_S12_benchcounter_source_binding_20261026.json'
    receipt.write_text(json.dumps(binding, indent=2, sort_keys=True) + '\n')
    return binding


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = emit(args.out)
    print(json.dumps({'status': result['status'], 'suite_count': len(result['fens']),
                      'helper_sha256': result['helper_sha256'], 'native': 'UNVERIFIED'}, indent=2))
