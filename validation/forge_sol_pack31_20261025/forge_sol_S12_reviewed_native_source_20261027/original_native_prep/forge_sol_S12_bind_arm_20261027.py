"""Bind exact, closed standard qualification; never launch a native executable.

Reuse is only the pristine S11 baseline with the same source, net, compiler,
flags, main and core bytes. S11 candidate/material-key producer is irrelevant.
Fresh candidate arms require their own S12 FIRST and full-Std receipts.
"""
from pathlib import Path
import argparse
import json
import re
import forge_sol_S12_native_common_20261027 as common
import forge_sol_S12_qualify_native_20261027 as qual

PINS = common.HERE / 'forge_sol_S12_baseline_receipt_pins_20261027.json'
PINS_SHA = 'ec12cbeee9b92196f30f0f3972de7eab513a44ac79ec8f430ea2367e47e1f0d3'
REUSE = Path('/tmp/forge_sol_S11_baseline_reuse_prep_20261026/forge_sol_S11_release_reuse_20261026.py')


def full_steps(profile):
    return (['bench_11'] if profile == 'ASAN' else ['bench_' + str(d) for d in qual.q.REFS]) + [
        ('perft4_' if profile == 'ASAN' else 'perft5_') + p for p in ('startpos','kiwipete')] + [
        'UCI_T1_T2','CTest_inventory','full_CTest','FMA_NNUE_object','FMA_NNUE_scope_ELF','FMA_whole_ELF']


def verify_full_meta(data, build, digest, engine_digest, schema):
    common.require(data.get('schema') == schema and data.get('status') == 'PASS' and data.get('mode') == 'FULL'
        and data.get('build_receipt_sha256') == digest and data.get('engine_sha256') == engine_digest
        and data.get('profile') == build['profile'] and data.get('base') == build['base']
        and data.get('role') == build['role'] and data.get('source_before') == data.get('source_after') == build['source_before']
        and data.get('source_unchanged') is True and data.get('all_artifacts_unchanged') is True
        and data.get('all_engine_groups_closed') is True and data.get('artifact_inventory') == build['target_artifacts'],
        'full Std receipt role/source/build/closure differs')
    if schema == 'forge.S12.full_runtime.v1':
        common.require(data.get('feature') == build['feature'], 'full Std compiled feature ABI differs')
    common.require(data.get('qualified_transport_sha256') == qual.RUNTIME_SHA,
                   'full Std transport differs from qualified S11/S09')
    common.require([s.get('name') for s in data.get('steps',[])] == full_steps(build['profile']),
                   'complete current Std steps required in exact order')
    ownership = data.get('engine_process_ownership',[])
    common.require(bool(ownership) and all(x.get('leader_reaped') is True
        and x.get('all_group_members_after_reap') == [] and not x.get('cleanup_error') for x in ownership),
        'full Std owned groups are not closed')
    for row in data['steps']:
        name, result = row['name'], row['result']
        if name.startswith('bench_'):
            common.require(result.get('status') == 'PASS', 'bench parser did not pass')
        elif name.startswith('FMA_NNUE_'):
            qual.previous.verify_fma(result)
        elif name == 'FMA_whole_ELF':
            common.require(type(result.get('fma_count')) is int and result['fma_count'] == 0, 'whole FMA count differs')
        elif name.startswith('perft'):
            depth = 4 if build['profile'] == 'ASAN' else 5
            nodes = (197281 if depth == 4 else 4865609) if name.endswith('startpos') else (4085603 if depth == 4 else 193690690)
            common.require(result == {'depth':depth,'nodes':nodes}, 'full Std perft reference differs')
    if build['profile'] == 'ASAN':
        common.require(data.get('ASAN_address_space_limit') == -1 and
            data.get('runtime_environment',{}).get('ASAN_OPTIONS') == 'detect_leaks=1:halt_on_error=1' and
            data.get('runtime_environment',{}).get('UBSAN_OPTIONS') == 'halt_on_error=1:print_stacktrace=1',
            'sanitizer environment/shadow/leaks differs')


def verify_full_raw(path, data, build):
    path = Path(path)
    profile = build['profile']
    for depth, nodes in ([(11,308972)] if profile == 'ASAN' else list(qual.q.REFS.items())):
        label = 'bench_' + str(depth)
        parsed = qual.q.s25.inspect_bench((path.parent/(label+'.stdout')).read_bytes(),
            (path.parent/(label+'.stderr')).read_bytes(), 0, depth, nodes)
        common.require(parsed['status'] == 'PASS', 'original full-Std bench bytes fail fixed reference')
    inventory = next(s['result'] for s in data['steps'] if s['name'] == 'CTest_inventory')
    expected = re.findall(r'add_test\(NAME\s+(\w+)',(Path(build['source'])/'CMakeLists.txt').read_text())
    common.require(sorted(inventory['names']) == sorted(expected) and len(set(expected)) == len(expected)
        and inventory['count'] == len(expected) == (14 if build['base'] == 'Lprime' else 15),
        'full current source CTest inventory differs')
    depth = 4 if profile == 'ASAN' else 5
    for name,nodes in (('startpos',197281 if depth == 4 else 4865609),('kiwipete',4085603 if depth == 4 else 193690690)):
        raw = (path.parent/(f'perft{depth}_'+name+'.stdout')).read_text().splitlines()
        common.require(raw and raw[-1] == 'nodes '+str(nodes), 'original perft bytes differ')
    checked = qual.previous.verify_ctest((path.parent/'full_CTest.stdout').read_text(), 0,
                                        inventory['names'], path.parent/'full_ctest.xml')
    common.require(checked == next(s['result'] for s in data['steps'] if s['name'] == 'full_CTest'),
                   'full CTest original bytes differ from receipt')
    for name in ('FMA_NNUE_object','FMA_NNUE_scope_ELF'):
        parsed = json.loads((path.parent/(name+'.stdout')).read_text())
        qual.previous.verify_fma(parsed)
        common.require(parsed == next(s['result'] for s in data['steps'] if s['name'] == name), 'raw FMA differs')
    assembly = path.parent/'whole_ELF_assembly.stdout'
    common.require(common.sha(assembly) == next(s['result']['assembly_sha256'] for s in data['steps'] if s['name'] == 'FMA_whole_ELF')
        and not any(re.match(r'^\s*[0-9a-fA-F]+:\s+vf(?:n)?m(?:add|sub)[a-z0-9]*\b', line) for line in assembly.read_text().splitlines()),
        'whole original assembly changed or contains fused instructions')


def fresh(build_path, first_path, full_path):
    data, source, build = qual.verify_build(Path(build_path))
    first = json.loads(Path(first_path).read_text()); full = json.loads(Path(full_path).read_text())
    engine_digest = common.sha(build/'forge')
    qual.verify_first(first, common.sha(build_path), engine_digest, data['profile'])
    qual.previous.verify_first_files(Path(first_path), first)
    verify_full_meta(full, data, common.sha(build_path), engine_digest, 'forge.S12.full_runtime.v1')
    common.require(full.get('controller_sha256') == common.sha(qual.__file__), 'fresh Std producer changed')
    verify_full_raw(full_path, full, data)
    return {'evidence_class':'FRESH_S12_BUILD_FIRST_FULL', 'base':data['base'], 'role':data['role'],
        'feature':data['feature'], 'profile':data['profile'], 'source':str(source), 'source_inventory':data['source_before'],
        'engine':str(build/'forge'), 'engine_sha256':engine_digest, 'core':str(build/'libforge_core.a'),
        'core_sha256':common.sha(build/'libforge_core.a'), 'recipe':data['recipe_after'],
        'receipts':{name:{'path':str(path),'sha256':common.sha(path)} for name,path in (
            ('build',build_path),('FIRST',first_path),('FULL',full_path))},
        'new_main_ELFs':1,'new_FIRST_runs':1,'new_full_Std_runs':1,'new_JUnit':True}


def pinned(base, name):
    common.require(common.sha(PINS) == PINS_SHA, 'baseline receipt pin list changed')
    row = json.loads(PINS.read_text())['arms'][base][name]
    common.require(common.sha(row['path']) == row['sha256'], 'original baseline receipt changed: ' + name)
    return Path(row['path']), json.loads(Path(row['path']).read_text())


def reused(base, profile):
    common.require(base in ('Lprime','B') and profile in ('Release','ASAN'), 'unknown baseline reuse arm')
    common.verify_originals(); common.verify_dependencies()
    if profile == 'Release':
        reuse = common.load_pinned('s12_original_baseline_reuse', REUSE)
        original = reuse.make_binding(base)  # Verifies actual source/ELF/flags, raw FIRST, full Std and fixed references.
        closed_path, closed = pinned(base, 'Release_reuse')
        light_path, light = pinned(base, 'Release_light')
        common.require(closed.get('evidence') == original and closed.get('base') == base
            and closed.get('role') == 'baseline' and closed.get('status') == 'PASS_ORACLE_ONLY_WITH_REUSED_STD',
            'published Release baseline binding differs')
        core = Path(closed['build'])/'libforge_core.a'
        common.require(common.sha(core) == original['core_archive']['sha256'], 'restored exact baseline core changed')
        common.require(light.get('schema') == 'forge.S11.reused_baseline_light_checks.v1'
            and light.get('status') == 'PASS_NEW_LIGHT_CHECKS_WITH_REUSED_STD'
            and light.get('base') == base and light.get('role') == 'baseline' and light.get('profile') == profile
            and light.get('reuse_receipt_sha256') == common.sha(closed_path)
            and light.get('main_ELF_sha256') == original['main_sha256']
            and light.get('all_new_engine_groups_closed') is True
            and light.get('original_sources_and_all_artifacts_unchanged') is True,
            'original typed UCI/FMA light qualification not closed')
        for name in ('FMA_NNUE_object','FMA_NNUE_scope_ELF'): qual.previous.verify_fma(light[name])
        common.require(light['FMA_whole_ELF']['fma_count'] == 0 and light['UCI_T1_T2']['typed_uci']['status'] == 'PASS',
                       'baseline UCI/FMA differs')
        source = Path(original['source']); engine = Path(original['canonical_build'])/'forge'
        receipt_rows = {'original':{'path':original['original_receipt'],'sha256':original['original_receipt_sha256']},
            'closed_reuse':{'path':str(closed_path),'sha256':common.sha(closed_path)},
            'light':{'path':str(light_path),'sha256':common.sha(light_path)}}
        recipe = {'origin':'EXACT_ORIGINAL_CANONICAL_FLAGS','flags':original['canonical_flags']}
    else:
        build_path, data = pinned(base, 'ASAN_build')
        first_path, first = pinned(base, 'ASAN_FIRST'); full_path, full = pinned(base, 'ASAN_FULL')
        verified, source, build = common.old_qualifier().verify_build(build_path)
        common.require(verified == data and data['role'] == 'baseline' and data['base'] == base, 'ASAN baseline source differs')
        engine = build/'forge'; core = build/'libforge_core.a'
        common.old_qualifier().verify_first(first,common.sha(build_path),common.sha(engine),'ASAN')
        qual.previous.verify_first_files(first_path, first)
        verify_full_meta(full,data,common.sha(build_path),common.sha(engine),'forge.S11.full_runtime.v1')
        verify_full_raw(full_path,full,data)
        receipt_rows = {name:{'path':str(path),'sha256':common.sha(path)} for name,path in (
            ('build',build_path),('FIRST',first_path),('FULL',full_path))}
        recipe = data['recipe_after']
    common.require(common.inventory(source) == common.source_expected(base,'baseline'), 'reuse contains S11 candidate source')
    return {'evidence_class':'REUSE_NOT_NEW_RUN','base':base,'role':'baseline','feature':'OFF','profile':profile,
        'source':str(source),'source_inventory':common.source_expected(base,'baseline'),
        'engine':str(engine),'engine_sha256':common.sha(engine),'core':str(core),'core_sha256':common.sha(core),
        'receipts':receipt_rows,'recipe':recipe,'new_main_ELFs':0,'new_FIRST_runs':0,'new_full_Std_runs':0,'new_JUnit':False,
        'S11_material_key_producer_reused':False}


def resolve(path):
    row = json.loads(Path(path).read_text())
    common.require(row.get('schema') == 'forge.S12.native_arm.v1' and row.get('status') == 'PASS_BINDING_ONLY'
        and row.get('controller_sha256') == common.sha(__file__), 'S12 standard-arm binding changed')
    if row['arm']['evidence_class'] == 'REUSE_NOT_NEW_RUN': actual = reused(row['arm']['base'],row['arm']['profile'])
    else:
        receipts = row['arm']['receipts']
        actual = fresh(*(Path(receipts[k]['path']) for k in ('build','FIRST','FULL')))
    common.require(row['arm'] == actual, 'standard qualification identity changed after binding')
    return actual


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-baseline',action='store_true');parser.add_argument('--base',choices=('Lprime','B'))
    parser.add_argument('--profile',choices=('Release','ASAN'))
    for name in ('build','first','full','out'):parser.add_argument('--'+name,type=Path,required=name=='out')
    args = parser.parse_args(argv)
    common.require(common.permitted(args.out) and not args.out.exists(), 'new S12 binding path required')
    if args.reuse_baseline:
        common.require(args.base and args.profile and not any((args.build,args.first,args.full)), 'reuse takes base/profile only')
        arm = reused(args.base,args.profile)
    else:
        common.require(all((args.build,args.first,args.full)) and not args.base and not args.profile, 'fresh takes three closed receipts')
        arm = fresh(args.build,args.first,args.full)
    result = {'schema':'forge.S12.native_arm.v1','status':'PASS_BINDING_ONLY','controller_sha256':common.sha(__file__),'arm':arm,
              'engine_executions_by_binding':0,'nps_or_Elo_claim':False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream: json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'status':result['status'],'evidence_class':arm['evidence_class']}))


if __name__ == '__main__': main()
