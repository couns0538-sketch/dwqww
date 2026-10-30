#!/usr/bin/env python3
"""Measure 100k real aligned rows as two 50k conversion batches, never train."""
import itertools, json, resource, sys, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'tools/data2'))
import convert_dataset as converter
from forge_pos import PosReader, aligned_records


def sizes(root):
    files = [p for p in root.rglob('*') if p.is_file()]
    return {'total_bytes': sum(p.stat().st_size for p in files),
            'index_bytes': sum(p.stat().st_size for p in files if p.name.startswith('index.sqlite')),
            'rows_text_bytes': sum(p.stat().st_size for p in files if p.name == 'rows.txt'),
            'bullet_bytes': sum(p.stat().st_size for p in files if p.name == 'rows.bullet'),
            'provenance_bytes': sum(p.stat().st_size for p in files if p.name == 'provenance.tsv')}


def main():
    root = Path(tempfile.mkdtemp(prefix='astra-qa-disk-100k-', dir='/tmp'))
    source = Path('/tmp/astra-a1-data-input/extracted/forge_selfplay_003')
    result = {'scope':'100000 real aligned rows; two 50000-row format-only batches; no production filtering/holdout claim',
              'min_free_mb_override':0, 'reason':'bounded /tmp qualification only; production default remains 20000 MiB',
              'work_directory':str(root), 'tool_sha256':converter.sha(REPO/'tools/data2/convert_dataset.py'),
              'source_pos':converter.identity(source.with_suffix('.pos')),
              'source_text':converter.identity(source.with_suffix('.txt')), 'pre_prune':[], 'batches':[]}
    before = time.monotonic()
    with PosReader(source.with_suffix('.pos')) as reader:
        rows = aligned_records(reader, source.with_suffix('.txt'))
        try:
            for number in range(2):
                with (root/f'slice_{number}.txt').open('x') as dest:
                    for record, fen in itertools.islice(rows, 50000):dest.write(converter.canonical(record, fen))
        finally:rows.close()
    actual_prune = converter.prune_owned_indexes
    def observed_prune(out, config):
        result['pre_prune'].append({'out':str(out), **sizes(out)})
        return actual_prune(out, config)
    converter.prune_owned_indexes = observed_prune
    prior = []
    for number in range(2):
        out = root/f'output_{number}'
        command = ['convert','--input',str(root/f'slice_{number}.txt'),'--out',str(out),
                   '--no-filters','--min-free-mb','0','--chunk-rows','25000']
        for path in prior:command += ['--dedup-against',path]
        if number == 0:
            converter.run(converter.parser().parse_args(command + ['--stop-after-chunks','1']))
            result['checkpoint'] = sizes(out)
            command += ['--resume']
        converted = converter.run(converter.parser().parse_args(command))
        result['batches'].append({'number':number,'counts':converted['counts'],
            'prior_training_index':converted['prior_training_index'],
            'retained':sizes(out),'verify':converter.verify(out)})
        prior.extend(str(out/chunk['text']) for chunk in converter.read_chunks(out))
    result['elapsed_seconds'] = time.monotonic()-before
    result['cpu_seconds'] = resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime
    result['retained_index_bytes'] = sizes(root)['index_bytes']
    assert result['retained_index_bytes'] == 0
    (Path(__file__).parent/'bounded_measurement.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
