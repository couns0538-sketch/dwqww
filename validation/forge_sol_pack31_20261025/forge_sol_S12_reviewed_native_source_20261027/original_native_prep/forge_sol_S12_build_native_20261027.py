"""S12 build-only CLI using qualified S11/S09 recipes and owned-process helper.

No engine or test executable runs here. Import is source-only. Execution needs
the root's new serial lease after S11 closure; a publication SHA alone is not a lease.
"""
from pathlib import Path
import argparse
import json
import os
import re
import resource
import shutil
import signal
import time
import forge_sol_S12_native_common_20261027 as common


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--authorization-reference', required=True)
    parser.add_argument('--s11-published-commit', required=True)
    parser.add_argument('--base', choices=('Lprime', 'B'), required=True)
    parser.add_argument('--role', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--feature', choices=('OFF', 'ON'), required=True)
    parser.add_argument('--profile', choices=('Release', 'ASAN'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cpu', type=int, required=True)
    parser.add_argument('--max-seconds', type=float, default=900)
    args = parser.parse_args(argv)
    if not args.execute or not re.fullmatch('[0-9a-f]{40}', args.s11_published_commit) or not 10 <= args.max_seconds <= 900:
        parser.error('finite new root grant and verified S11 closure/publication reference required')
    if args.role == 'baseline' and args.feature != 'OFF':
        parser.error('pristine baseline has no S12 feature')
    if sorted(os.sched_getaffinity(0)) != [args.cpu] or os.getpriority(os.PRIO_PROCESS, 0) != 19:
        parser.error('exact granted CPU/nice19 required')
    if not common.permitted(args.out) or args.out.exists() or not re.fullmatch('[A-Za-z0-9_.-]+', args.out.name):
        parser.error('new literal S12 output descendant required')
    dependencies = common.verify_dependencies()
    common.verify_originals()
    owned = common.old_builder().owned
    signal.signal(signal.SIGTERM, owned._signal_stop)
    signal.signal(signal.SIGINT, owned._signal_stop)
    common.TMP.mkdir(exist_ok=True)
    if shutil.disk_usage(common.TMP).free < 128 * 1048576:
        parser.error('128MiB build start floor')
    cap = 4 * 1024**3
    _, hard = resource.getrlimit(resource.RLIMIT_AS)
    if hard != resource.RLIM_INFINITY:
        cap = min(cap, hard)
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))  # This compiler-only CLI never runs ASAN.
    args.out.mkdir()
    source, build = args.out / 'source', args.out / 'build'
    start = time.monotonic()
    deadline = start + args.max_seconds
    result = {'schema': 'forge.S12.build.v1', 'status': 'FAIL_BUILD_ONLY',
              'base': args.base, 'role': args.role, 'feature': args.feature, 'profile': args.profile,
              'source': str(source), 'source_inventory_sha256': common.INVENTORY_SHA,
              'patch_sha256': common.PATCH_SHA, 'controller_sha256': common.sha(__file__),
              'compiler_sha256': owned.CXX_SHA, 'dependency_sha256': dependencies,
              'S11_published_commit': args.s11_published_commit,
              'authorization_reference': args.authorization_reference,
              'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'commands': [], 'target_artifacts': {},
              'engine_executions': 0, 'cpu': [args.cpu], 'nice': 19, 'max_seconds': args.max_seconds,
              'compiler_RLIMIT_AS_bytes': cap, 'maximum_observed_owned_RSS_bytes': 0,
              'first_main_runtime_required': 'bare bench11/quit before UCI/helpers/CTest'}

    # Same bounded ownership/RSS guard as the actual qualified S11 builder.
    def guard(_job, end):
        if time.monotonic() >= end: return 'OWNED_DEADLINE'
        if owned._STOP_REQUESTED: return 'EXTERNAL_STOP'
        if shutil.disk_usage(common.TMP).free < 32 * 1048576: return 'DISK_FREE_FLOOR'
        pids = {os.getpid()}
        events = args.out / 'events.jsonl'
        if events.exists():
            rows = events.read_text().splitlines()
            if rows: pids.update(x['pid'] for x in owned._all_members(json.loads(rows[-1])['pid']))
        rss = 0
        for pid in pids:
            try:
                for line in Path('/proc', str(pid), 'status').read_text().splitlines():
                    if line.startswith('VmRSS:'): rss += int(line.split()[1]) * 1024
            except (OSError, ValueError): pass
        result['maximum_observed_owned_RSS_bytes'] = max(result['maximum_observed_owned_RSS_bytes'], rss)
        if rss > 4 * 1024**3: return 'OWNED_RSS_LIMIT'

    previous_guard = owned.boundary_reason
    owned.boundary_reason = guard
    def run(command, label, cwd=None):
        row = owned.run_owned(command, args.out, label, cwd or args.out, deadline)
        result['commands'].append(row)
        if row.get('error') or row['stop_reason'] or row['returncode'] != 0 or not row['leader_reaped'] or row['all_group_members_after_reap']:
            raise RuntimeError('owned build command failed/open: ' + label)
    try:
        shutil.copytree(Path(common.frozen()['bases'][args.base]), source)
        if args.role == 'candidate':
            run(['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '-i', common.frozen()['patch']],
                '00_apply_single_v2_patch', source)
        result['source_before'] = common.verify_source(source, args.base, args.role)
        asan = args.profile == 'ASAN'
        kind = 'RelWithDebInfo' if asan else 'Release'
        optimization = '-O2 -g -DNDEBUG' if asan else '-O3 -DNDEBUG'
        configure = [str(owned.CMAKE), '-S', str(source), '-B', str(build), '-DCMAKE_BUILD_TYPE=' + kind,
            '-DCMAKE_CXX_COMPILER=' + str(owned.CXX), '-DCMAKE_CXX_FLAGS=' + owned.FLAGS,
            '-DCMAKE_CXX_FLAGS_' + kind.upper() + '=' + optimization, '-DBUILD_SHARED_LIBS=OFF',
            '-DFORGE_ENABLE_SANITIZERS=' + ('ON' if asan else 'OFF'),
            '-DFORGE_NATIVE=OFF', '-DFORGE_EXPOSE_TUNABLES=OFF', '-DFORGE_BUILD_VALIDATION_TOOLS=OFF',
            '-DFORGE_BUILD_TUNING_TOOLS=OFF', '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF',
            '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        if args.role == 'candidate':
            configure.append('-DFORGE_NNUE_LAZY_ACC=' + args.feature)
        run(configure, '01_configure')
        result['recipe_before'] = common.audit_recipe(source, build, args.profile, args.feature)
        for index, target in enumerate(common.artifact_names(source), 2):
            if target == 'core_archive': continue
            run([str(owned.CMAKE), '--build', str(build), '--target', target, '--parallel', '1', '--verbose'],
                f'{index:02d}_{target}')
        for name in common.artifact_names(source):
            path = build / ('libforge_core.a' if name == 'core_archive' else name)
            result['target_artifacts'][name] = {'path': str(path), 'sha256': common.sha(path), 'bytes': path.stat().st_size}
        result['recipe_after'] = common.audit_recipe(source, build, args.profile, args.feature)
        result['status'] = 'PASS_BUILD_ONLY'
    except BaseException as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        owned.boundary_reason = previous_guard
        result['source_after'] = common.inventory(source)
        result['source_unchanged'] = result.get('source_before') == result['source_after']
        try:
            common.verify_source(source, args.base, args.role)
            common.verify_originals(); common.verify_dependencies()
        except Exception as error:
            result.update(status='FAIL_BUILD_ONLY', postflight_error=str(error))
        if not result['source_unchanged']: result['status'] = 'FAIL_BUILD_ONLY'
        result['elapsed_seconds'] = time.monotonic() - start
        owned.save_new(args.out / 'forge_sol_S12_build_result_20261027.json', result)
    print(json.dumps({'status': result['status'], 'error': result.get('error')}))
    return 0 if result['status'] == 'PASS_BUILD_ONLY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
