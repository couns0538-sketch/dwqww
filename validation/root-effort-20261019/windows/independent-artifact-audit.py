#!/usr/bin/env python3
"""Independent read-only static audit; never invokes an engine/build/Wine."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import struct
import subprocess
import traceback
import zipfile

REPO = Path('/workspace/dwqww')
COMMIT = '7125b3379a850de34041d42529cf95993607f93c'
TAG = 'root-effort'
SOURCE = Path('/workspace/.cloud-setup/forge-windows-root-effort-source')
BUILD = Path('/workspace/.cloud-setup/forge-windows-root-effort')
CACHE = Path('/workspace/.cloud-setup/forge-windows-root-effort-evidence')
EVIDENCE = REPO / 'validation/root-effort-20261019/windows'
STAGE = REPO / 'releases/forge-6.4.8-candidate-windows-zen5'
ARCHIVE = STAGE.with_name(STAGE.name + '.zip')
OUTPUT = Path(__file__).with_suffix('.json')
EXPECTED_SHA = '4b4de385808f5a383aa60de6bfc09cf48c02e5d23c191624540026cdac95b55e'
EXPECTED_BYTES = 3619122
MEMBERS = {'forge-6.4.8-ryzen-9850x3d.exe', 'forge_tests.exe', 'forge_tt_tests.exe',
           'forge_rule50_tests.exe', 'forge_legal_witness_tests.exe', 'LICENSE',
           'source-hashes.json', 'test-hashes.json', 'legal_witness_fixtures.tsv',
           'forge-10000.epd', 'provenance.json', 'README.txt', 'SHA256SUMS'}
PE_MAP = {'forge.exe': 'forge-6.4.8-ryzen-9850x3d.exe', 'forge_tests.exe': 'forge_tests.exe',
          'forge_tt_tests.exe': 'forge_tt_tests.exe', 'forge_rule50_tests.exe': 'forge_rule50_tests.exe',
          'forge_legal_witness_tests.exe': 'forge_legal_witness_tests.exe'}
checks = []
findings = []
sha_bytes = lambda b: hashlib.sha256(b).hexdigest()
sha = lambda p: sha_bytes(p.read_bytes())
load = lambda p: json.loads(p.read_text())

def check(name, condition, detail=None):
    result = {'name': name, 'passed': bool(condition)}
    if detail is not None:
        result['detail'] = detail
    checks.append(result)
    if not condition:
        findings.append({'check': name, 'detail': detail})

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])

def file_hashes(directory):
    return {p.relative_to(directory).as_posix(): sha(p) for p in directory.rglob('*') if p.is_file()}

def parse_pe(data):
    assert data[:2] == b'MZ'
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[pe:pe+4] == b'PE\0\0'
    machine, sections, stamp, _, _, optional_size, characteristics = struct.unpack_from('<HHIIIHH', data, pe+4)
    optional = pe+24
    magic = struct.unpack_from('<H', data, optional)[0]
    assert machine == 0x8664 and magic == 0x20b
    mappings = []
    for n in range(sections):
        base = optional + optional_size + 40*n
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from('<IIII', data, base+8)
        mappings.append((rva, max(virtual_size, raw_size), raw_offset))
    def offset(rva):
        for start, size, raw in mappings:
            if start <= rva < start+size:
                return raw+rva-start
        raise ValueError('Unmapped RVA')
    imports_rva, _ = struct.unpack_from('<II', data, optional+112+8)
    imports = []
    at = offset(imports_rva)
    while any(struct.unpack_from('<IIIII', data, at)):
        name_rva = struct.unpack_from('<I', data, at+12)[0]
        name_at = offset(name_rva)
        imports.append(data[name_at:data.index(b'\0', name_at)].decode('ascii'))
        at += 20
    return {'machine': hex(machine), 'optional_magic': hex(magic), 'sections': sections,
            'timestamp': stamp, 'subsystem': struct.unpack_from('<H',data,optional+68)[0], 'characteristics': hex(characteristics), 'imports': imports}

report = {'audit_kind': 'independent_read_only_static_artifact_audit',
          'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'source_and_tests_commit': COMMIT,
          'artifact': str(ARCHIVE), 'stage_directory': str(STAGE),
          'evidence_directory': str(EVIDENCE), 'runtime_directory': str(EVIDENCE/'runtime-attempt1'),
          'cache_runtime_directory': str(CACHE/'runtime-attempt1'),
          'frozen_source_directory': str(SOURCE), 'build_directory': str(BUILD),
          'script_path': str(Path(__file__).resolve()), 'script_sha256': sha(Path(__file__)),
          'commands_executed_scope': 'Python file reads/hashes/decompression/PE parsing and read-only git show/ls-tree only; no engines, Wine, builds or timed benchmarks',
          'limitations': ['Static audit verifies retained process results and transcripts; it does not rerun them.',
                         'Build provenance is locally recorded, not an independent toolchain reproduction.',
                         'Wine correctness/node signatures do not establish native Windows, physical Ryzen speed, accepted Elo or Stockfish superiority.']}
try:
    artifact = load(EVIDENCE/'artifact.json')
    build = load(EVIDENCE/'result.json')
    commands = load(EVIDENCE/'commands.json')
    run = EVIDENCE/'runtime-attempt1'
    protocol = load(run/'protocol.json')
    runtime = load(run/'result.json')
    provenance = load(STAGE/'provenance.json')
    source_hashes = load(EVIDENCE/'source-hashes.json')
    production = load(EVIDENCE/'production-hashes.json')
    tests = load(EVIDENCE/'test-hashes.json')
    report['artifact_sha256'] = sha(ARCHIVE)
    report['artifact_bytes'] = ARCHIVE.stat().st_size
    report['engine_sha256'] = sha(STAGE/'forge-6.4.8-ryzen-9850x3d.exe')
    report['run_identity'] = {'created_utc': protocol['created_utc'], 'protocol_sha256': sha(run/'protocol.json'),
                              'result_sha256': sha(run/'result.json'), 'checks': runtime['checks']}
    check('archive_expected_sha_and_size', report['artifact_sha256']==EXPECTED_SHA and report['artifact_bytes']==EXPECTED_BYTES)
    check('artifact_record_identity', artifact['sha256']==EXPECTED_SHA and artifact['bytes']==EXPECTED_BYTES
          and artifact['artifact']==str(ARCHIVE.relative_to(REPO)) and artifact['status']=='packaged_and_verified')
    check('all_commit_identities', all(x['source_and_tests_commit']==COMMIT for x in
          (artifact, build, commands, protocol, runtime, provenance)))
    actual_stage = {p.name for p in STAGE.iterdir() if p.is_file()}
    check('stage_exact_flat_membership', actual_stage==MEMBERS and all(p.is_file() and not p.is_symlink() for p in STAGE.iterdir()), sorted(actual_stage))
    with zipfile.ZipFile(ARCHIVE) as z:
        names = z.namelist()
        check('zip_crc', z.testzip() is None)
        check('zip_unique_exact_membership', len(names)==len(set(names))==len(MEMBERS)
              and set(names)=={STAGE.name+'/'+name for name in MEMBERS}, names)
        check('every_zip_member_equals_stage', all(z.read(STAGE.name+'/'+name)==(STAGE/name).read_bytes() for name in MEMBERS))
        sums = [line.split('  ', 1) for line in (STAGE/'SHA256SUMS').read_text().splitlines()]
        check('sha256sums_unique_complete', len(sums)==len(MEMBERS)-1 and len({name for _, name in sums})==len(sums)
              and {name for _, name in sums}==MEMBERS-{'SHA256SUMS'})
        check('every_declared_member_sha256', all(re.fullmatch('[0-9a-f]{64}', digest)
              and sha_bytes(z.read(STAGE.name+'/'+name))==digest for digest,name in sums))
    tree = git('ls-tree','-r','--name-only',COMMIT,'--','CMakeLists.txt','LICENSE','include','src','bench','tests','tools').decode().splitlines()
    export_names = {name for name in tree if not name.endswith('.pyc')}
    check('export_manifest_complete_git_scope', set(source_hashes)==export_names, {'export_files':len(export_names)})
    check('frozen_export_matches_complete_manifest', file_hashes(SOURCE)==source_hashes)
    git_hashes = {name:sha_bytes(git('show',COMMIT+':'+name)) for name in export_names}
    check('every_export_matches_exact_git_commit', git_hashes==source_hashes)
    expected_production = {name:digest for name,digest in source_hashes.items() if name=='CMakeLists.txt' or name.startswith(('src/','include/'))}
    expected_tests = {name:digest for name,digest in source_hashes.items() if name.startswith('tests/')}
    check('production_and_test_manifests_complete', production==expected_production and tests==expected_tests
          and len(production)==21 and len(tests)==5, {'production_files':len(production),'test_files':len(tests)})
    check('package_and_provenance_source_manifests', load(STAGE/'source-hashes.json')==production
          and load(STAGE/'test-hashes.json')==tests and provenance['production_source_sha256']==production
          and provenance['test_source_sha256']==tests)
    check('packaged_license_fixtures_and_corpus', (STAGE/'LICENSE').read_bytes()==(SOURCE/'LICENSE').read_bytes()
          and (STAGE/'legal_witness_fixtures.tsv').read_bytes()==(SOURCE/'tests/legal_witness_fixtures.tsv').read_bytes()
          and (STAGE/'forge-10000.epd').read_bytes()==(SOURCE/'tools/openings/forge-10000.epd').read_bytes())
    copied=[]
    for p in CACHE.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(CACHE)
        target=EVIDENCE/rel
        if p.name=='disassembly.log':
            target=target.with_suffix('.log.gz')
            same=gzip.decompress(target.read_bytes())==p.read_bytes()
        else:
            same=target.is_file() and target.read_bytes()==p.read_bytes()
        copied.append({'name':rel.as_posix(),'same':same})
    check('every_cache_evidence_copy_exact', all(p['same'] for p in copied), {'files_checked':len(copied),'mismatches':[p for p in copied if not p['same']]})
    helpers={'build-driver.py':Path('/workspace/.cloud-setup/build-windows-root-effort.py'),
             'validation-driver.py':Path('/workspace/.cloud-setup/validate-windows-root-effort.py'),
             'package-driver.py':Path('/workspace/.cloud-setup/package-windows-6.4.8.py'),
             'forge-root-effort-wine':Path('/workspace/.cloud-setup/forge-root-effort-wine')}
    check('copied_helpers_equal_actual_helpers', all((EVIDENCE/name).read_bytes()==path.read_bytes() for name,path in helpers.items()))
    check('build_driver_recorded_sha', build['script_sha256']==sha(EVIDENCE/'build-driver.py'))
    report['helper_sha256']={name:sha(EVIDENCE/name) for name in helpers}
    pe_actual={name:{'sha256':sha(BUILD/name),'bytes':(BUILD/name).stat().st_size} for name in build['binaries']}
    check('all_six_build_binary_identities_current', len(pe_actual)==6 and all(value['sha256']==build['binaries'][name]['sha256']
          and value['bytes']==build['binaries'][name]['bytes'] and build['binaries'][name]['path']==str(BUILD/name) for name,value in pe_actual.items()))
    libraries=build['libraries']
    check('static_library_build_provenance_and_current_identity', set(libraries)=={'libforge_core.a'}
          and provenance['static_libraries']==libraries
          and all(value['path']==str(BUILD/name) and value['sha256']==sha(BUILD/name)
                  and value['bytes']==(BUILD/name).stat().st_size for name,value in libraries.items()))
    check('before_after_protocol_hashes_equal', protocol['input_sha256_before']==runtime['input_sha256_before']==runtime['input_sha256_after'])
    inputs={name:BUILD/name for name in pe_actual}
    inputs.update(uci_tool=SOURCE/'tools/uci_regression.py',ponder_tool=SOURCE/'tools/ponder_regression.py',
                  fixtures=SOURCE/'tests/legal_witness_fixtures.tsv',corpus=SOURCE/'tools/openings/forge-10000.epd',
                  wrapper=helpers['forge-root-effort-wine'],wine_loader=Path(protocol['commands'][0][1][0]),
                  disassembler=Path(protocol['simd_command'][0]),
                  core_library=BUILD/'libforge_core.a', core_flags=BUILD/'CMakeFiles/forge_core.dir/flags.make',
                  compile_commands=BUILD/'compile_commands.json')
    check('all_16_runtime_inputs_match_current_bytes', len(inputs)==16 and {name:sha(path) for name,path in inputs.items()}==runtime['input_sha256_after'])
    check('five_packaged_pes_match_tested_builds', all(sha(STAGE/dst)==runtime['input_sha256_after'][src]==build['binaries'][src]['sha256']
          and provenance['binaries'][dst]==pe_actual[src] for src,dst in PE_MAP.items()))
    check('engine_hash_records_consistent', artifact['engine_sha256']==report['engine_sha256']==runtime['input_sha256_before']['forge.exe'])
    pe={dst:parse_pe((STAGE/dst).read_bytes()) for dst in PE_MAP.values()}
    report['pe_headers']=pe
    check('all_packaged_pes_x64_console_executables', all(value['machine']=='0x8664' and value['optional_magic']=='0x20b'
          and value['subsystem']==3 and int(value['characteristics'],16)&2 for value in pe.values()))
    headers=(EVIDENCE/'pe-headers-imports.txt').read_text()
    check('retained_pe_headers_match_direct_parse', re.findall(r'^  Name: (.+)$',headers,re.M)==pe['forge-6.4.8-ryzen-9850x3d.exe']['imports']
          and f"(0x{pe['forge-6.4.8-ryzen-9850x3d.exe']['timestamp']:X})" in headers
          and 'COFF-x86-64' in headers and str(BUILD/'forge.exe') in headers)
    flags=(EVIDENCE/'CMakeFiles_forge_core.dir_flags.make').read_text()
    link=(EVIDENCE/'CMakeFiles_forge.dir_link.txt').read_text()
    compilation=load(EVIDENCE/'compile_commands.json')
    compilation_commands=[' '.join(item['arguments']) if 'arguments' in item else item['command'] for item in compilation]
    check('retained_compile_database_equals_actual_build', (EVIDENCE/'compile_commands.json').read_bytes()==(BUILD/'compile_commands.json').read_bytes())
    check('all_compile_commands_retain_strict_zen5_flags', len(compilation_commands)>=10
          and all(all(flag in command for flag in ('-march=znver5','-mtune=znver5','-fno-fast-math','-ffp-contract=off'))
                  and not re.search(r'(?<!\S)-(?:ffast-math|Ofast)(?!\S)',command) for command in compilation_commands))
    check('actual_flags_and_link_are_strict_zen5', all(flag in flags for flag in
          ('-march=znver5','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-O3','-DNDEBUG'))
          and not re.search(r'(?<!\S)-(?:ffast-math|Ofast)(?!\S)',flags) and '-static' in link)
    check('provenance_compile_link_and_compiler_equal_records', provenance['compile_flags_record']==flags and provenance['link_record']==link
          and provenance['compiler']==build['compiler']==(EVIDENCE/'compiler-version.txt').read_text().strip())
    check('build_source_and_toolchain_paths_correct', commands['source_directory']==str(SOURCE) and commands['build_directory']==str(BUILD)
          and commands['commands'][0][2]==str(SOURCE) and commands['parallel_jobs']==2
          and commands['commands'][1][-2:]==['--parallel','2'])
    check('six_expected_runtime_commands_and_windows_paths', [item[0] for item in protocol['commands']]==['core','coherent-tt','rule50','legal-witness','uci','ponder']
          and protocol['commands'][3][1][2:]==['Z:'+str(inputs['fixtures']).replace('/','\\'),'Z:'+str(inputs['corpus']).replace('/','\\')]
          and protocol['commands'][4][1][1]==str(inputs['uci_tool']) and protocol['commands'][5][1][1]==str(inputs['ponder_tool'])
          and all(str(BUILD) in ' '.join(args) for _,args in protocol['commands'][:4]))
    expected_checks=['core','coherent-tt','rule50','legal-witness','uci','ponder','stdin-bench11-signature']
    check('seven_successful_runtime_results', runtime['status']=='passed' and [c['name'] for c in runtime['checks']]==expected_checks
          and all(c['exit_code']==0 for c in runtime['checks']) and provenance['wine_checks']==runtime['checks'])
    check('progress_matches_six_functional_results', load(run/'progress.json')==runtime['checks'][:6])
    check('all_seven_stderr_logs_empty', all((run/(name+'-stderr.log')).read_bytes()==b'' for name in expected_checks[:6]+['bench']))
    core=(run/'core-stdout.log').read_text()
    core_source=(SOURCE/'tests/tests.cpp').read_text()
    check('core_pass_and_six_reference_perft_tests_in_tested_source', core.strip()=='All tests passed'
          and all(str(value) in core_source for value in (197281,97862,43238,9467,62379,89890)))
    check('tt8_log', (run/'coherent-tt-stdout.log').read_text().strip()=='All8 TT coherence/regression groups passed' and runtime['tt_groups']==8)
    rule=(run/'rule50-stdout.log').read_text()
    check('rule50_zero_and_both_reverse_regressions', all(s in rule for s in
          ('targeted_regression_failures=0','reverse_q_direct','reverse_q_score_as_eval')) and not re.search(r'^FAIL',rule,re.M)
          and runtime['rule50_targeted_failures']==0)
    check('legal_witness_18947_log', (run/'legal-witness-stdout.log').read_text().strip()=='All 18947 legal-witness Boolean comparisons passed'
          and runtime['legal_witness_comparisons']==18947)
    uci=load(run/'uci-stdout.log')
    transcript=(run/'uci-transcript.log').read_text()
    check('uci_27_checks_zero_known_failures_and_actual_version', len(uci['passed'])==27 and uci['known_failures']==[]
          and '< id name Chess Engine Forge 6.4.8 candidate' in transcript)
    ponder=(run/'ponder-stdout.log').read_text()
    check('ponder_ten_pass_records', len(re.findall('^PASS ',ponder,re.M))==10 and not re.search(r'^FAIL',ponder,re.M))
    bench=(run/'bench-stdout.log').read_text()
    check('bench_stdin_signature_and_resource_context', (run/'bench-stdin.txt').read_bytes()==b'bench 11\nquit\n'
          and protocol['bench_stdin']=='bench 11\nquit\n' and protocol['bench_hash_mib']==16 and protocol['bench_threads']==1
          and re.findall(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',bench,re.M)==['351063']
          and runtime['bench11_nodes']==351063 and 'Searcher bench_searcher(16)' in (SOURCE/'src/uci.cpp').read_text())
    disassembly=gzip.decompress((run/'disassembly.log.gz').read_bytes()).decode()
    simd={'avx2_minmax_ymm':bool(re.search(r'\bv(?:max|min)ps\b[^\n]*\bymm\d+\b',disassembly)),
          'avx2_multiply_ymm':bool(re.search(r'\bvmulps\b[^\n]*\bymm\d+\b',disassembly)),
          'avx2_add_ymm':bool(re.search(r'\bvaddps\b[^\n]*\bymm\d+\b',disassembly)),
          'fused_operations':re.findall(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b',disassembly)}
    report['independent_disassembly_scan']=simd
    report['uncompressed_disassembly_sha256']=sha_bytes(disassembly.encode())
    check('independent_ymm_and_no_fused_arithmetic_scan', all(simd[key] for key in simd if key!='fused_operations') and simd['fused_operations']==[])
    check('retained_simd_records_match_independent_scan', simd==load(run/'simd.json')==runtime['simd']==provenance['simd'])
    check('disassembly_exact_engine_command_identity', protocol['simd_command'][-1]==str(BUILD/'forge.exe')
          and str(BUILD/'forge.exe') in disassembly[:400])
    search=(SOURCE/'src/search.cpp').read_text()
    parent=git('show',COMMIT+'^:src/search.cpp').decode()
    header=(SOURCE/'include/forge/search.hpp').read_text()
    check('stable_full_move_identity_effort_storage', 'std::array<Move, 256> root_effort_moves_{};' in header
          and 'std::size_t root_effort_count_ = 0;' in header and 'root_best_index_' not in search+header
          and 'std::find(root_effort_moves_.begin(), root_effort_end, move)' in search)
    check('root_effort_reset_and_best_move_lookup', 'root_effort_count_ = root_candidates.size();' in search
          and 'std::copy(root_candidates.begin(), root_candidates.end(), root_effort_moves_.begin());' in search
          and 'root_move_nodes_.fill(0);' in search
          and 'root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;' in search
          and 'std::find(root_effort_moves_.begin(), effort_end, result.best_move)' in search)
    effort_formula='factor *= std::clamp(tune::TmEffortBase / 100.0 - effort, 0.6, 1.4);'
    check('root_effort_constants_and_evaluation_weights_unchanged', effort_formula in parent and effort_formula in search
          and all(git('show',COMMIT+':'+name)==git('show',COMMIT+'^:'+name) for name in
                  ('src/nnue_weights.inc','src/eval_params_table.inc','include/forge/eval_params.hpp')))
    readme=(STAGE/'README.txt').read_text()
    evidence_readme=(EVIDENCE/'README.md').read_text()
    check('documentation_describes_stable_root_effort_attribution', 'root' in readme.lower()
          and 'effort' in readme.lower() and 'move' in readme.lower()
          and any(word in readme.lower() for word in ('identity','identities'))
          and any(word in readme.lower() for word in ('ordinal','order','index')))
    check('provenance_and_readmes_limit_strength_hardware_and_speed_claims', provenance['accepted_elo_gain'] is None
          and provenance['native_windows_tested'] is False and provenance['physical_ryzen_tested'] is False
          and provenance['stockfish_superiority_proven'] is False and 'No accepted Elo gain exists.' in readme
          and 'No Windows throughput or timed match was run' in readme
          and 'Native Windows, physical Ryzen' in readme and 'Stockfish superiority remain unproven.' in readme
          and 'No Windows throughput or timed match was run' in evidence_readme)
    check('package_optional_oracle_inputs_and_command_complete', 'forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd' in readme)
    check('historical_pending_build_status_not_misrepresented', build['runtime_validation']=='pending'
          and runtime['status']=='passed' and artifact['status']=='packaged_and_verified')
    report['source_file_counts']={'all_export':len(source_hashes),'production':len(production),'tests':len(tests)}
    report['source_export_sha256']=source_hashes
    report['audited_input_sha256']=runtime['input_sha256_after']
    report['evidence_sha256']=file_hashes(EVIDENCE)
except Exception as exc:
    findings.append({'fatal_exception':str(exc),'traceback':traceback.format_exc()})
report['checks']=checks
report['findings']=findings
report['checks_passed']=sum(c['passed'] for c in checks)
report['checks_total']=len(checks)
report['status']='passed' if not findings else 'findings'
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
OUTPUT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks_passed':report['checks_passed'],'checks_total':report['checks_total'],
                  'findings':findings,'report_path':str(OUTPUT),'report_sha256':sha(OUTPUT)},indent=2))
raise SystemExit(0 if not findings else 1)
