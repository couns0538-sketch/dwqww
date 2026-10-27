"""S18 (opus-sol-S18) read-only pin check: every input the Windows port of Sol's v4
remaining4 controller needs, hashed on this PC and compared with Sol's pinned values.

No Torch/NumPy import, no training, no writes except the optional --json report.
Pinned values come from Sol's branch 17aa0cae (v4 controller PINS, v4 read-only
preflight, histogram pins, t200 v3 reference binding, v3 controller originals).

Usage (any Python >= 3.9):
  nice -n 19 python -B opus_s18_pin_check.py [--lock DIR] [--sol DIR] [--venv DIR] [--json OUT]
Exit 0 only if every pinned file exists and matches.
"""
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

LOCK_DEFAULT = r'D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039'
SOL_DEFAULT = r'F:\opus_scratch\sol_s18\sol_src'
VENV_DEFAULT = r'C:\Users\Administrator\grok-pc\nnue\.venv'

# (label, root key, relative path, sha256, md5 or None, where Sol pinned it)
PINS = [
    ('trainer train_resid_v3b.py', 'lock', '5_nnue/trainers/train_resid_v3b.py',
     '5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f', None, 'v4 PINS[TRAINER]'),
    ('qa_adam_dml.py', 'lock', '5_nnue/trainers/cpu_smoke/qa_adam_dml.py',
     '799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba', None, 'v4 PINS[ADAM]'),
    ('holdout h000.pos', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/h000.pos',
     '92c40ae25c3b650db9f5db235786133afed3e9a8f6691e7860dff6bdc5aa11b3', 'b263af9969f8ace979e25db061eb37ef', 'v4 PINS + arms index holdout'),
    ('holdout h000.hce', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/h000.hce',
     '212e51e6c108f3ff6b879b0f247277925f9483102e34230b5024e5fb7ef2cc44', 'f248959bc791424407a37af5ac60752a', 'v4 PINS + arms index holdout'),
    ('train t00000.pos', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t00000.pos',
     '7a8727fa19f857f5b3ac1c79219b06ca1aefdb971f72167b775d1a1dfa2794c8', '90604b88767d885be1ea337fb42d4a60', 'filter inputs_before / preflight sealed_off'),
    ('train t00000.hce', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t00000.hce',
     'b5dd1729246a630d8e079882913311858b7ad063d026245b5b60a8141097f637', '2819d3e015653244a4d3590c292e8c04', 'filter inputs_before / preflight sealed_off'),
    ('train t01000.pos', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t01000.pos',
     '0252d5f924c67aea939d55229ebd514c3fb6c767619f6a27075993b89f846b9a', 'f030a32d4f6845d91872333f3486dbed', 'filter inputs_before / preflight sealed_off'),
    ('train t01000.hce', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t01000.hce',
     'fcb63b0ce7e68f05445bb6376e0a6d61abbc8ee12979ba533872524d194270ea', 'd37a4d479445e7a356fa3cc807d67ab9', 'filter inputs_before / preflight sealed_off'),
    ('train t02000.pos', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t02000.pos',
     '9630ea73c53159375e7e821c01b0a39e4d598d4acebb29d384ed4cf70cd9e693', '9e35b59d2e249ce72544de4dc86d5e7a', 'filter inputs_before / preflight sealed_off'),
    ('train t02000.hce', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t02000.hce',
     '78e4c77c5efb34029d85aaa1ccc43b877079e76c47507aff6416d3a7e384ba55', '6496458371a69367b060ef0ba283e304', 'filter inputs_before / preflight sealed_off'),
    ('train t03000.pos', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t03000.pos',
     '7753665ec40e98a4b58db3a61ea74116245aaa4ced1355345bf460041306fe98', '26016f9ffb5ea745012d364f1d6212b7', 'filter inputs_before / preflight sealed_off'),
    ('train t03000.hce', 'lock', '5_nnue/sample_data/data32_sample/data32_sample_50k/t03000.hce',
     '77a6a237a771f275c2def1fca2c5d50f4854d78a8f560c1e2dc5f6c0edc79f8d', 'cd704ca88bf11550041f82a05b236fb3', 'filter inputs_before / preflight sealed_off'),
    ('accepted net h256_e12 .inc', 'lock', '5_nnue/nets/PARENT_h256_e12/nnue_weights_h256_e12_md5_6d22f612.inc',
     '74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b', None, 'v4 PINS[ACCEPTED_NET]'),
    ('f006 reference .inc', 'lock', '5_nnue/nets/history_all_CR_passed/resid_h256_e48_f006_b06_ep48.inc',
     '0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661', None, 'v4 PINS[F006_REFERENCE]'),
    ('phase header eval.hpp', 'lock', '1_source/forge_AL1_s198_src/include/forge/eval.hpp',
     'e6cb2b620f5c7fd87cef7a680aea04c4ba756f106b78d5a8fa7ab3cdd5d0cc35', None, 'histogram pins phase_header_sha256'),
    ('Sol v4 controller', 'sol', 'forge_sol_S18_train_selected_v4_20261027.py',
     '643e71ea1854b5a881944f969e5a22f36775e7f912a167b341fa3708c86736b7', None, 'remaining4 prereg controller'),
    ('Sol arms index', 'sol', 'forge_sol_S18_training_arms_index_20261026.json',
     'fb5d2575d2d9aabaaff6143f9137e786af5351785a558b6ef46e53ba08944ff0', None, 'remaining4 prereg index'),
    ('f006 recipe json', 'sol', 'pinned/forge_sol_S09_f006_recipe_20261026.json',
     '97b4a2a85f76af148055db951e7922ce92b535a55e33c3c94b96c27be137d800', None, 'v4 PINS[RECIPE]'),
    ('postscore preregistration', 'sol', 'pinned/forge_sol_S18_postscore_preregistration_20261026.json',
     'aa8fed66b82399b62f77cf792f25d2582771aefabed39ab08c0e5e63ab771d7e', None, 'v4 PINS[POSTSCORE_PROTOCOL]'),
    ('S09 full holdout result', 'sol', 'pinned/forge_sol_S09_full_holdout_result_20261026.json',
     '63487797d80f96de9cbb0cfad7a8de3487f58d0877ecd6bb662b0f1e25fc4fda', None, 'v4 PINS[S09_SUCCESS]'),
    ('S09 diagnostic (Linux-only; to be replaced)', 'sol', 'pinned/forge_sol_S09_shutdown_diagnostic_20261026.py',
     '84b3f7f5a773340dfaddb3c2942d117a03ee68f82faaec7bfef756a6e4648729', None, 'v4 PINS[DIAGNOSTIC]'),
    ('S08 subreaper (Linux-only; to be replaced)', 'sol', 'pinned/forge_sol_S08_build_window_subreaper_20261026.py',
     '85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0', None, 'v4 PINS[OWNED]'),
    ('datafilter base (S16 codec)', 'sol', 'instrument/forge_sol_datafilter_20261025.py',
     '6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3', None, 'v2 BASE_SHA256'),
    ('datafilter v2 (D filter)', 'sol', 'instrument/forge_sol_datafilter_v2_20261026.py',
     '5dd0c009566bc5a8c8e06300a8541c5d130d458ca75266a432d1477d1d156332', None, 'filter case TOOL_SHA'),
    ('histogram describe tool', 'sol', 'orig_ckpt/x/source_and_history/forge_sol_S18_describe_20261026.py',
     '5ff1e6d7fa15f86404d0ab71cdb24bebc28d1cede651d27d55cc853dd960c5ef', None, 'histogram pins tool_sha256'),
    ('filter case runner (Linux-only reference)', 'sol', 'orig_ckpt/x/source_and_history/forge_sol_S18_filter_case_20261026.py',
     None, None, 'reference only'),
    ('v4 preflight (arm shard fingerprints)', 'sol', 'prereg/forge_sol_S18_remaining4_v4_readonly_preflight_20261027.json',
     '72b6343c4eb427ab8f11442ede63b8c1c9c25fcab2b96efe46b74d2945162795', None, 'remaining4 prereg'),
    ('v4 preregistration', 'sol', 'prereg/forge_sol_S18_remaining4_v4_preregistration_20261027.json',
     'e55cdd0fdf6f6bba5d5b3ac59a5e72a3923808b31cab2425d733ea7ba9d8f9aa', None, 'remaining4 prereg'),
    ('v4 grant TEMPLATE (not a grant)', 'sol', 'prereg/forge_sol_S18_remaining4_v4_root_grant_TEMPLATE_20261027.json',
     '1e4d11cd31ab6cf24beb6ec28269ffd9ee7eb6e48c2a3996feadc6761180b063', None, 'remaining4 prereg'),
    ('t200 v3 reference binding', 'sol', 'prereg/forge_sol_S18_v4_t200_reference_binding_20261027.json',
     '311d97f70a5b3f162b88c77a12f7aba8513991df15f6af3a3bb76d47833ad0f2', None, 'remaining4 prereg'),
    ('qualified none v3 controller result', 'sol', 'v3_originals/forge_sol_S18_none_v3_controller_original_20261027.json',
     'f008b5db1d74e79bf6de759e380c68594aadcc32269c259111671569b79f890a', None, 'prereg qualified_none'),
    ('failed t200 v3 controller result', 'sol', 'v3_originals/forge_sol_S18_t200_v3_failed_controller_original_20261027.json',
     'fd0107bcc0f3ef56634c873224ecaf2e89ec9f71b2fe6de5953cc47df196db3d', None, 'grant template previous_failed_t200_result'),
    ('Sol S18 original checkpoint archive', 'sol', 'orig_ckpt/orig.tar.gz',
     '1f48fb1ffa21bf9ea5a20844d7ede3c6c1ccbb7b231f4a62878876f373c6c59e', None, 'evidence_archive_result archive_sha256'),
    ('Sol v3 training evidence archive', 'sol', 'v3_evidence/v3.tar.gz',
     'e9ccce4439523deb8b3abf2391362b91b984c891ca2b3b74e5525f58ba91b77c', None, 'data_archive_result archive.sha256'),
]
T200 = 'v3_evidence/x/failed_remaining4_v3/runtime/t200/trainer-run/'
for name, digest in [('epoch001-step000000016.bin', '68aba06af05484ad9bca3c34c20488feeba4a816d862e4923ce0fd386e0d89ef'),
                     ('epoch001-step000000016.inc', '3bfb95e0ee4b0f429accaa93f11eccfcf43ab36cada922bc025183b0dd6f2172'),
                     ('epoch001-step000000016.json', '95f50967f21912123e026b3caf3a6761410895e3d1214546b8caaef540ce555a'),
                     ('epoch001-step000000016.pt', '3ee50aba91314c6d967bd4677b1eacb9c5f3dbf444a3551450e5941aa1115260'),
                     ('epoch002-step000000032.bin', '75de4aaf2d22f1a118efcd51b6666b654778e611685375d30cd8b2e562d7ac89'),
                     ('epoch002-step000000032.inc', 'e3407f3971c459abc8b30d4c8150a9beaa5df2ada1adafd636a86e30f673bce5'),
                     ('epoch002-step000000032.json', 'c1c1437477ac8bd19f3c3dea23e19be5460796637fde863c48e910dadf65d111'),
                     ('epoch002-step000000032.pt', '0014c1a7b85b13893153e79125e8bf26e5f008258009e9e9008f6174876d9494')]:
    PINS.append(('Sol t200 v3 ' + name, 'sol', T200 + name, digest, None, 't200 reference binding epoch_artifacts'))
PINS.append(('Sol t200 v3 raw stdout', 'sol', 'v3_evidence/x/failed_remaining4_v3/runtime/t200/stdout',
             '9d1405abae5ee0bb8785cbeb1425a504d214043a3bfb151cdc9cb3f6033dd7fe', None, 't200 reference binding old_t200_raw_stdout'))


def digests(path):
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            sha.update(block); md5.update(block); size += len(block)
    return sha.hexdigest(), md5.hexdigest(), size


def free_ram_bytes():
    if os.name != 'nt':
        return None
    class MemoryStatus(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ('total_phys', 'avail_phys', 'total_page', 'avail_page',
                                              'total_virtual', 'avail_virtual', 'avail_extended')]
    status = MemoryStatus(); status.length = ctypes.sizeof(status)
    return status.avail_phys if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) else None


def environment(venv):
    venv = Path(venv); site = venv / 'Lib' / 'site-packages'; info = {'venv': str(venv)}
    cfg = venv / 'pyvenv.cfg'
    info['pyvenv_cfg'] = cfg.read_text(encoding='utf-8').strip().splitlines() if cfg.is_file() else None
    exe = venv / 'Scripts' / 'python.exe'
    info['venv_python_sha256'] = digests(exe)[0] if exe.is_file() else None
    version = site / 'torch' / 'version.py'
    if version.is_file():  # read the text only; Torch is never imported here
        for line in version.read_text(encoding='utf-8').splitlines():
            if line.startswith('__version__') or line.startswith('git_version'):
                info[line.split('=')[0].strip()] = line.split('=', 1)[1].strip().strip("'\"")
    info['numpy_dist'] = sorted(p.name for p in site.glob('numpy-*.dist-info')) if site.is_dir() else None
    info['psutil_dist'] = sorted(p.name for p in site.glob('psutil-*.dist-info')) if site.is_dir() else None
    info['free_ram_bytes'] = free_ram_bytes()
    info['free_disk_F_bytes'] = shutil.disk_usage('F:\\').free if os.name == 'nt' and Path('F:\\').exists() else None
    info['checker_python'] = sys.version
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lock', default=LOCK_DEFAULT); ap.add_argument('--sol', default=SOL_DEFAULT)
    ap.add_argument('--venv', default=VENV_DEFAULT); ap.add_argument('--json', type=Path)
    a = ap.parse_args(argv)
    roots = {'lock': Path(a.lock), 'sol': Path(a.sol)}
    rows = []; failures = 0
    for label, root, rel, want_sha, want_md5, where in PINS:
        path = roots[root] / rel
        row = {'label': label, 'path': str(path), 'pinned_by': where, 'expected_sha256': want_sha, 'expected_md5': want_md5}
        if not path.is_file():
            row['status'] = 'MISSING'; failures += 1
        else:
            sha, md5, size = digests(path); row.update(sha256=sha, md5=md5, bytes=size)
            if want_sha is None:
                row['status'] = 'RECORDED'
            elif sha == want_sha and (want_md5 is None or md5 == want_md5):
                row['status'] = 'MATCH'
            else:
                row['status'] = 'MISMATCH'; failures += 1
        rows.append(row)
        print('{:<9} {:<46} {}'.format(row['status'], label, row.get('sha256', '-')[:16]))
    env = environment(a.venv)
    result = {'schema': 'opus-S18-pin-check-v1', 'status': 'PASS_ALL_PINS' if not failures else 'FAIL',
              'pins': len([r for r in rows if r['expected_sha256']]), 'failures': failures,
              'rows': rows, 'environment': env, 'torch_imported': False, 'training_run': False}
    print(json.dumps({k: v for k, v in env.items()}, sort_keys=True))
    print('RESULT {} pinned={} failures={}'.format(result['status'], result['pins'], failures))
    if a.json:
        with open(a.json, 'x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
