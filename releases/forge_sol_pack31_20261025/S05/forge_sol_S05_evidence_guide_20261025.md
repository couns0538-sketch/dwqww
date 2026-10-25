# S05 evidence verification — 2026-10-25

Run `sha256sum -c forge_sol_S05_SHA256SUMS_20261025.txt` with this delivery folder as the current directory. The gzip JSONL container preserves 334 original-file records, including native commands/streams, complete CTest logs, fixtures, failed unpublished prototype evidence and the earlier closed S28 baseline controls used only by exact executable SHA. It contains no copied engine source, weights, executable/object products or mutated engine source/generator.

Verify each original record without extracting or overwriting any file:

```bash
python3 -B - <<'PYCODE'
import base64,gzip,hashlib,json
rows=[]
with gzip.open('forge_sol_S05_raw_evidence_20261025.jsonl.gz','rt') as stream:
    for line in stream:
        row=json.loads(line)
        data=base64.b64decode(row['data'],validate=True)
        assert len(data)==row['bytes']
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        rows.append({k:row[k] for k in ('original_path','bytes','sha256')})
index=json.load(open('forge_sol_S05_evidence_index_20261025.json'))
assert rows==index['records'] and len(rows)==index['count']
print('PASS',len(rows),'original records')
PYCODE
```

Source paths in receipts identify the original private experiment layout. A failed prototype patch inside the evidence container is historical data, not a candidate to apply. Apply only the standalone final `forge_sol_S05_ctestwire_20261025.patch`. Old validation-script versions are preserved to explain the final Python-only fix and actual checker/CTest replay; their source is not substituted for final files. Complete engine source copies, binaries and the intentional zero-vector FMA fault source remain retained privately for independent inspection.

The exact environment producer scripts are provenance, not portable PC runners. Use the relative CMake/checker commands in the main report for a fresh source copy. Historical integer-backend controls, Windows behavior, unrecognized ISA lowerings, speed and Elo remain outside verified scope. No native work is left running.
