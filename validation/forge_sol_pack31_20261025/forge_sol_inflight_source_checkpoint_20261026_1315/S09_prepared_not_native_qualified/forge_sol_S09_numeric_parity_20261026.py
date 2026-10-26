"""Bounded NumPy duplicate-head parity; not native-engine or trainer validation."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import tempfile
import time
# Validation process only; set these before importing NumPy.
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'): os.environ[name] = '1'
import numpy as np
import forge_sol_S09_buckets_20261026 as buckets


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def run(net_path, pos_path, hce_dir, trainer):
    refs = [net_path, pos_path, hce_dir / (pos_path.stem + '.hce'), trainer, Path(buckets.__file__)]
    before = {str(p): digest(p) for p in refs}
    original = buckets.inspect_inc(net_path)
    selected = [node for node in ast.parse(trainer.read_text()).body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in {'read_pos_header', 'CatMap', 'load_set_mmap', 'make_batch'}]
    namespace = {'np': np, 'Path': Path}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(trainer), 'exec'), namespace)
    data = namespace['load_set_mmap']([str(pos_path)], str(hce_dir), limit=10000)
    if data['n'] != 10000: raise ValueError('10,000 source rows required')
    temporary = Path(tempfile.mkdtemp(prefix='forge_sol_S09_parity_', dir=Path(__file__).parent))
    start = time.perf_counter()
    try:
        converted_path = temporary / 'eight.inc'
        conversion = buckets.replicate_1_to_8(net_path, converted_path)
        converted = buckets.inspect_inc(converted_path)
        # A deliberately changed output bias must make this same comparator fail.
        control = dict(converted); control['b2'] = [value + 64 * (head + 1) for head, value in enumerate(converted['b2'])]
        bit_mismatches = cp_mismatches = control_mismatches = 0
        largest_logit = 0.0; largest_cp = 0; heads = np.zeros(8, dtype=np.int64)
        for begin in range(0, 10000, 128):
            idx = np.arange(begin, min(begin + 128, 10000), dtype=np.int64)
            codes, stm, _, _, _ = namespace['make_batch'](data, idx)
            one = buckets.evaluate_numeric(codes, stm, original)
            eight = buckets.evaluate_numeric(codes, stm, converted)
            negative = buckets.evaluate_numeric(codes, stm, control)
            bit_mismatches += int(np.count_nonzero(one['logits'].view(np.uint32) != eight['logits'].view(np.uint32)))
            cp_mismatches += int(np.count_nonzero(one['cp'] != eight['cp']))
            control_mismatches += int(np.count_nonzero(one['cp'] != negative['cp']))
            largest_logit = max(largest_logit, float(np.max(np.abs(one['logits'] - eight['logits']))))
            largest_cp = max(largest_cp, int(np.max(np.abs(one['cp'] - eight['cp']))))
            heads += np.bincount(eight['heads'], minlength=8)
        if bit_mismatches or cp_mismatches or largest_logit or largest_cp: raise ValueError('numeric duplicate-head parity failed')
        if not control_mismatches: raise ValueError('negative head-bias control did not change comparator results')
        after = {str(p): digest(p) for p in refs}; assert before == after
        return {'scope': 'NUMPY_FLOAT32_REFERENCE_ONLY; no native or training execution',
                'positions': 10000, 'source_scope': 'first10k supplied synthetic data32 stand-in holdout rows',
                'logit_bit_mismatches': bit_mismatches, 'cp_mismatches': cp_mismatches,
                'max_abs_logit_difference': largest_logit, 'max_abs_cp_difference': largest_cp,
                'negative_bias_control_cp_mismatches': control_mismatches,
                'head_counts': heads.tolist(), 'conversion': conversion,
                'source_sha256_before': before, 'source_sha256_after': after, 'source_unchanged': True,
                'record_parser': 'AST-executed unchanged v3b read_pos_header/CatMap/load_set_mmap/make_batch',
                'elapsed_seconds': time.perf_counter() - start,
                'peak_rss_linux_KiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                'cpu_affinity': sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else 'UNVERIFIED',
                'thread_environment': {name: os.environ[name] for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS')},
                'native_1M_parity': 'UNVERIFIED_NOT_RUN', 'trainer_holdout_loss': 'UNVERIFIED_TORCH_UNAVAILABLE',
                'trained_bucket8_null_pruning_regression': 'UNVERIFIED_NO_TRAINED_NET_OR_NATIVE_TESTS'}
    finally:
        shutil.rmtree(temporary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--net', type=Path, required=True); parser.add_argument('--pos', type=Path, required=True)
    parser.add_argument('--hce-dir', type=Path, required=True); parser.add_argument('--trainer', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.net, args.pos, args.hce_dir, args.trainer), indent=2, sort_keys=True))
