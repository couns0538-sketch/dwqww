"""Compile diagnostic helpers only after the exact main's closed FIRST/Std.
No helper or engine executable runs in this compiler-only, AS-capped process.
"""
from pathlib import Path
import argparse
import json
import os
import re
import resource
import signal
import time
import forge_sol_S12_bind_arm_20261027 as binding
import forge_sol_S12_native_common_20261027 as common

DRIVERS = {
    'regression': common.HERE/'inputs/forge_sol_S12_lazyacc_native_regression_20261026.cpp',
    'alias': common.HERE/'forge_sol_S12_alias_oracle_20261027.cpp',
    'counters': common.HERE/'inputs/forge_sol_S12_benchcounter_helper_20261026.cpp',
}
DRIVER_SHAS = {
    'regression':'6cc93b1b0c052fe7acad64c3f65b3cdf130c8586dd52af3209da54a7bc400b3a',
    'alias':'704dadabbe5a7320312e2760b6ed0729217b195951a3693dd9ae7aa40d5c15f3',
    'counters':'628caa63d3166b5aabd9c4c3a0ed5436f74e841d396e4ad47954f22f1499bbfb',
}


def helper_specs(arm):
    specs = [('regression', None)]
    if arm['profile'] == 'Release':
        if arm['role'] == 'baseline': specs.append(('alias', 0))
        elif arm['feature'] == 'ON': specs += [('alias', 1),('alias', 2),('counters', None)]
    common.require(arm['role'] == 'baseline' or arm['feature'] == 'ON',
                   'candidate helpers require the feature-capable ABI')
    return specs


def link_argv(arm, kind, mode, dest, map_path):
    common.require(common.sha(DRIVERS[kind]) == DRIVER_SHAS[kind], 'frozen actual helper driver changed')
    source, core = Path(arm['source']), Path(arm['core'])
    argv = common.profile_api(arm['profile']).manual_command(source, core, DRIVERS[kind], dest)
    extras = (['-DFORGE_NNUE_LAZY_ACC=1'] if arm['feature'] == 'ON' else [])
    if kind == 'alias': extras.append('-DFORGE_SOL_S12_ALIAS_MODE=' + str(mode))
    argv[1:1] = extras
    argv.append('-Wl,-Map,' + str(map_path))
    common.profile_api(arm['profile']).strict_tokens(argv)
    expected = ['-DFORGE_NNUE_HIDDEN=256'] + extras
    common.require(sorted(x for x in argv if x.startswith(('-DFORGE_','-UFORGE_'))) == sorted(expected),
                   'helper/core/header diagnostic ABI differs')
    common.require(argv.count(str(core)) == 1 and [x for x in argv if x.startswith('-I')] == ['-I' + str(source/'include')],
                   'helper must use the bound core and exact header')
    return argv


def verify_link_map(text, core):
    core = str(core)
    members = sorted(set(re.findall(re.escape(core) + r'\(([^)]+)\)', text)))
    loads = re.findall(r'^\s*LOAD\s+(.+?)\s*$', text, re.M)
    common.require(loads.count(core) == 1 and not any(Path(x).name == 'libforge_core.a' and x != core for x in loads),
                   'wrong or ambiguous Forge core LOAD')
    common.require(all(sum(Path(x).name == name for x in members) == 1 for name in ('search.cpp.o','nnue.cpp.o')),
                   'actual Worker and NNUE archive members must both be selected')
    return {'archive':core,'selected_archive_members':members,'actual_Worker_from_core':True,'actual_NNUE_from_core':True}


def verify(path):
    path = Path(path); row = json.loads(path.read_text())
    common.require(row.get('schema') == 'forge.S12.helpers_build.v1' and row.get('status') == 'PASS_COMPILE_ONLY'
        and row.get('controller_sha256') == common.sha(__file__), 'helper build source/status changed')
    arm = binding.resolve(Path(row['arm_receipt']))
    common.require(row['arm'] == arm and row['arm_receipt_sha256'] == common.sha(row['arm_receipt']), 'helper source/core arm changed')
    expected = helper_specs(arm)
    common.require(len(row.get('helpers',[])) == len(expected) and row.get('source_unchanged') is True,
                   'helper set/source incomplete')
    for item, (kind,mode) in zip(row['helpers'],expected):
        dest = Path(item['path']); map_path = Path(item['map_path'])
        common.require(dest.parent == path.parent and map_path.parent == path.parent and
            item.get('kind') == kind and item.get('mode') == mode and
            item.get('driver_sha256') == common.sha(DRIVERS[kind]) and
            item.get('argv') == link_argv(arm,kind,mode,dest,map_path) and
            item.get('sha256') == common.sha(dest) and item.get('map_sha256') == common.sha(map_path) and
            item.get('map_proof') == verify_link_map(map_path.read_text(),Path(arm['core'])), 'helper compilation/ELF/map differs')
        command = row['commands'][item['command_index']]
        common.require(command.get('argv') == item['argv'], 'helper compile command not observed')
    common.require(bool(row['commands']) and all(c.get('returncode') == 0 and type(c['returncode']) is int
        and c.get('leader_reaped') is True and c.get('all_group_members_after_reap') == []
        and not c.get('stop_reason') and not c.get('error') for c in row['commands']), 'helper compiler failed or open')
    return row, arm


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--authorization-reference',required=True)
    parser.add_argument('--arm',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cpu',type=int,required=True);parser.add_argument('--max-seconds',type=float,default=180)
    args = parser.parse_args(argv)
    if not args.execute or not 10 <= args.max_seconds <= 300: parser.error('new finite compiler-only grant required')
    if sorted(os.sched_getaffinity(0)) != [args.cpu] or os.getpriority(os.PRIO_PROCESS,0) != 19:
        parser.error('exact granted core/nice19 required')
    if not common.permitted(args.out) or args.out.exists(): parser.error('new S12 helper output directory required')
    arm = binding.resolve(args.arm); expected = helper_specs(arm)
    common.verify_dependencies(); common.verify_originals()
    owned = common.old_builder().owned
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    cap = 4 * 1024**3; _, hard = resource.getrlimit(resource.RLIMIT_AS)
    if hard != resource.RLIM_INFINITY: cap = min(cap,hard)
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))  # Never run a sanitizer target in this CLI.
    args.out.mkdir(); start = time.monotonic()
    guard = binding.qual.previous.RSSGuard(args.out,args.out/'ROOT_STOP',start+args.max_seconds)
    previous = owned.boundary_reason
    def boundary(job=None,end=None):
        if owned._STOP_REQUESTED: return 'EXTERNAL_STOP'
        return guard.reason(job,end)
    owned.boundary_reason = boundary
    row = {'schema':'forge.S12.helpers_build.v1','status':'FAIL_COMPILE_ONLY','arm_receipt':str(args.arm),
        'arm_receipt_sha256':common.sha(args.arm),'arm':arm,'controller_sha256':common.sha(__file__),
        'authorization_reference':args.authorization_reference,'cpu':[args.cpu],'nice':19,'max_seconds':args.max_seconds,
        'compiler_RLIMIT_AS_bytes':cap,'helpers':[],'commands':[],'engine_or_helper_executions':0}
    try:
        for kind, mode in expected:
            suffix = kind + ('' if mode is None else '_mode' + str(mode))
            dest = args.out/('forge_sol_S12_' + suffix + '_20261027')
            map_path = dest.with_suffix('.map')
            command = link_argv(arm,kind,mode,dest,map_path)
            result = owned.run_owned(command,args.out,suffix,args.out,guard.deadline); row['commands'].append(result)
            common.require(result.get('returncode') == 0 and result.get('leader_reaped') is True
                and result.get('all_group_members_after_reap') == [] and not result.get('stop_reason') and not result.get('error'),
                'helper compiler failed or open: ' + suffix)
            row['helpers'].append({'kind':kind,'mode':mode,'path':str(dest),'sha256':common.sha(dest),
                'driver':str(DRIVERS[kind]),'driver_sha256':common.sha(DRIVERS[kind]),'argv':command,
                'command_index':len(row['commands'])-1,'map_path':str(map_path),'map_sha256':common.sha(map_path),
                'map_proof':verify_link_map(map_path.read_text(),Path(arm['core']))})
        common.require(binding.resolve(args.arm) == arm, 'source/core qualification changed during helper build')
        row['status'] = 'PASS_COMPILE_ONLY'
    except BaseException as error: row['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        owned.boundary_reason = previous
        row['source_unchanged'] = common.inventory(arm['source']) == arm['source_inventory']
        if not row['source_unchanged']: row['status'] = 'FAIL_COMPILE_ONLY'
        row['maximum_observed_owned_RSS_bytes'] = guard.maximum_owned_RSS_bytes
        row['elapsed_seconds'] = time.monotonic()-start
        owned.save_new(args.out/'forge_sol_S12_helpers_build_result_20261027.json',row)
    print(json.dumps({'status':row['status'],'error':row.get('error')}))
    return 0 if row['status'] == 'PASS_COMPILE_ONLY' else 1


if __name__ == '__main__': raise SystemExit(main())
