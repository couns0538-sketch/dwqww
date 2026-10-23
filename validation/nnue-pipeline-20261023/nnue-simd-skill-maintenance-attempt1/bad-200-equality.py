from pathlib import Path
import json
root=Path('/workspace/forge-nnue-handoff-20261023/prepared-fresh-only-attempt1')
manifest=json.loads((root/'manifest.json').read_text())
partition=set(manifest['split']['train_game_ids'])
with (root/'train-provenance.jsonl').open() as stream:
    retained={json.loads(line)['game_id'] for line in stream}
print(json.dumps({'assigned':len(partition),'retained':len(retained),'zero_retained':sorted(partition-retained)}),flush=True)
assert retained == partition, 'Invalid equality rejects genuine filtered zero-row games'
