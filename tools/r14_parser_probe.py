"""Bounded parser throughput sample; not a corpus qualification result."""
from pathlib import Path
import argparse
import json
import os
import time

from r14_overlap import RuntimeGuard
from r14_scan import load_pins, iter_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu', type=int, default=3)
    parser.add_argument('--rows', type=int, default=100000)
    args = parser.parse_args()
    if not 1 <= args.rows <= 100000:
        raise ValueError('bounded sample only')
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['HIP_VISIBLE_DEVICES'] = '-1'
    guard = RuntimeGuard(60, args.cpu)
    path = Path('D:/grok-pc-data/selfplay_out/forge_selfplay_013.txt')
    pins = load_pins(Path('D:/a14/evidence/r14/input-pins-all.jsonl'))
    receipt = {}
    rows = iter_rows(path, pins[str(path.resolve()).casefold()], receipt)
    started = time.monotonic()
    try:
        for number, row in rows:
            if number % 4096 == 0:
                guard()
            if number >= args.rows:
                break
    finally:
        rows.close()
    elapsed = time.monotonic()-started
    print(json.dumps(dict(scope='bounded_throughput_sample_not_qualification', sampled_rows=receipt['rows'],
                          valid_key_rows=receipt['valid_key_rows'], elapsed_seconds=elapsed,
                          rows_per_second=receipt['rows']/elapsed, full_input_consumed=False,
                          source_full_md5_preflight_pin=pins[str(path.resolve()).casefold()]), indent=2))


if __name__ == '__main__':
    main()
