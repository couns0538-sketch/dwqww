#!/usr/bin/env python3
"""Plan retained-index conversion storage; never run, move, or delete shard data.

Inventory rows/text bytes must come from the actual files or a trusted manifest.
All projected future rows are kept; measured free space already includes existing
sources, prior outputs, prior indexes and failed attempts. Replan before EACH
shard using fresh free space and the actual verified prior retained row count.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import shutil
import sys

SHARD_IDS = tuple(f'{i:03}' for i in range(1, 40) if i not in (13, 14))
INDEX_BYTES_PER_KEY = 64
INDEX_MARGIN_BYTES = 1024**2
PROBE_LOG_BYTES_PER_ROW = 128
DEFAULT_RESERVE_MIB = 32768


def nonnegative(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f'{name} must be a nonnegative integer')
    return value


def validate_inventory(inventory):
    if not isinstance(inventory, dict) or inventory.get('schema') != 1:
        raise ValueError('inventory must use schema 1')
    nonnegative(inventory.get('holdout_rows'), 'holdout_rows')
    shards = inventory.get('shards')
    if not isinstance(shards, list) or len(shards) != 37:
        raise ValueError('inventory must contain all 37 training shards')
    if any(not isinstance(s, dict) for s in shards):
        raise ValueError('each shard must be an object')
    if (any(type(s.get('id')) is not str for s in shards) or
            sorted(s['id'] for s in shards) != list(SHARD_IDS)):
        raise ValueError('inventory must contain 37 unique IDs 001..039 excluding 013/014')
    for shard in shards:
        for field in ('rows', 'text_bytes'):
            nonnegative(shard.get(field), f'{shard["id"]}.{field}')
        nonnegative(shard.get('game_id_bytes', 0), f'{shard["id"]}.game_id_bytes')
        if shard['rows'] and not shard['text_bytes']:
            raise ValueError('nonempty shard requires positive source text_bytes')
    return sorted(shards, key=lambda s: s['id'])


def read_volumes(observed, roots):
    volumes, devices = [], set()
    for item in observed:
        name, separator, value = item.partition('=')
        try:
            amount = Decimal(value)
        except InvalidOperation:
            raise ValueError('observed free space must be NAME=finite_nonnegative_GiB') from None
        if not name or not separator or not amount.is_finite() or amount < 0:
            raise ValueError('observed free space must be NAME=finite_nonnegative_GiB')
        volumes.append({'name': name, 'free_bytes': int(amount * 1024**3),
                        'measurement': 'user_observed'})
    for item in roots:
        name, separator, value = item.partition('=')
        if not name or not separator or not value:
            raise ValueError('volume root must be NAME=existing_directory')
        path = Path(value).resolve(strict=True)
        if not path.is_dir():
            raise ValueError('volume root must be an existing directory')
        device = path.stat().st_dev
        if device in devices:
            raise ValueError('measured roots refer to the same volume; count its free space once')
        devices.add(device)
        volumes.append({'name': name, 'free_bytes': shutil.disk_usage(path).free,
                        'measurement': 'local_disk_usage', 'root': str(path),
                        'device': device})
    if not volumes:
        raise ValueError('supply observed free space or local volume roots; no PC capacity is assumed')
    return volumes


def plan(inventory, volumes, *, reserve_bytes=DEFAULT_RESERVE_MIB * 1024**2,
         start_at='001', prior_retained_rows=None, independent_volumes=False,
         binpack=False):
    shards = validate_inventory(inventory)
    nonnegative(reserve_bytes, 'reserve_bytes')
    if start_at not in SHARD_IDS:
        raise ValueError('start-at must be a training shard ID')
    if start_at != '001' and prior_retained_rows is None:
        raise ValueError('replanning requires --prior-retained-rows from verified completed outputs')
    prior_rows = nonnegative(0 if prior_retained_rows is None else prior_retained_rows,
                             'prior_retained_rows')
    if not volumes or len({v['name'] for v in volumes}) != len(volumes):
        raise ValueError('supply at least one volume with unique names')
    if len(volumes) > 1 and not independent_volumes:
        raise ValueError('multiple capacities require explicitly provisioned independent volumes')
    storage = []
    for volume in volumes:
        free = nonnegative(volume['free_bytes'], 'free_bytes')
        storage.append(dict(volume, free_after_bytes=free, new_retained_bytes=0))
    result = {'schema': 1, 'status': 'PLANNED',
              'capacity_recorded_at_utc': datetime.now(timezone.utc).isoformat(),
              'reserve_bytes_per_volume': reserve_bytes,
              'indexes_retained': True, 'remeasure_before_each_shard': True,
              'future_retention_assumption': 'all input rows kept',
              'independent_volumes_declared': independent_volumes,
              'volumes': storage, 'batches': [], 'steps': []}
    volume_index = 0
    for shard in (s for s in shards if s['id'] >= start_at):
        keys = inventory['holdout_rows'] + prior_rows + shard['rows']
        index_bytes = keys * INDEX_BYTES_PER_KEY + INDEX_MARGIN_BYTES
        output_bytes = shard['text_bytes'] + shard.get('game_id_bytes', 0)
        output_bytes += shard['rows'] * (32 + 32 + PROBE_LOG_BYTES_PER_ROW)
        if binpack:
            output_bytes += shard['text_bytes'] + shard['rows'] * 128
        additional = index_bytes + output_bytes
        while (volume_index < len(storage) and
               storage[volume_index]['free_after_bytes'] < reserve_bytes + additional):
            volume_index += 1
        if volume_index == len(storage):
            result.update(status='BLOCKED', blocked_shard=shard['id'],
                          next_shard_additional_bytes=additional,
                          next_shard_required_free_bytes=reserve_bytes + additional,
                          reason='No remaining provisioned volume can retain the next shard plus reserve')
            break
        volume = storage[volume_index]
        before = volume['free_after_bytes']
        volume['free_after_bytes'] -= additional
        volume['new_retained_bytes'] += additional
        result['steps'].append({
            'shard_id': shard['id'], 'volume': volume['name'],
            'input_rows': shard['rows'], 'prior_retained_rows_upper_bound': prior_rows,
            'index_keys_upper_bound': keys, 'index_bytes_estimate': index_bytes,
            'output_bytes_estimate': output_bytes, 'additional_bytes': additional,
            'free_before_bytes': before, 'free_after_bytes': volume['free_after_bytes']})
        if not result['batches'] or result['batches'][-1]['volume'] != volume['name']:
            result['batches'].append({'volume': volume['name'], 'shard_ids': []})
        result['batches'][-1]['shard_ids'].append(shard['id'])
        prior_rows += shard['rows']
    return result


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--inventory', required=True, type=Path)
    result.add_argument('--observed-free-gib', action='append', default=[], metavar='NAME=GiB')
    result.add_argument('--volume-root', action='append', default=[], metavar='NAME=PATH')
    result.add_argument('--independent-volumes', action='store_true',
                        help='assert multiple supplied capacities are separate provisioned volumes')
    result.add_argument('--start-at', default='001', choices=SHARD_IDS)
    result.add_argument('--prior-retained-rows', type=int)
    result.add_argument('--min-free-mb', type=int, default=DEFAULT_RESERVE_MIB,
                        help='reserve on each volume in MiB (default: 32768)')
    result.add_argument('--binpack', action='store_true', help='include optional binpack output estimate')
    return result


def main():
    args = parser().parse_args()
    try:
        inventory = json.loads(args.inventory.read_text(encoding='utf-8-sig'))
        result = plan(inventory, read_volumes(args.observed_free_gib, args.volume_root),
                      reserve_bytes=args.min_free_mb * 1024**2, start_at=args.start_at,
                      prior_retained_rows=args.prior_retained_rows,
                      independent_volumes=args.independent_volumes, binpack=args.binpack)
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'INVALID', 'reason': str(error)}))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['status'] == 'PLANNED' else 1


if __name__ == '__main__':
    sys.exit(main())
