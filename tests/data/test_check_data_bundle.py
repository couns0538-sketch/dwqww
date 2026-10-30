#!/usr/bin/env python3
"""Synthetic bundle integrity fixtures, not actual native/training evidence.
IDEA_SOURCE: Forge sealed-data contracts and adversarial filesystem validation.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/data'))
import check_data_bundle as target
from forge_pos import PosWriter, Record, text_record

FEN='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
BINARY='a'*64

class BundleTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='forge-bundle-audit-test-'))
        print('retained synthetic fixture '+str(self.root),file=sys.stderr)

    def fixture(self,kind='filter',missing=None,pending=False):
        out=self.root/kind;out.mkdir()
        writer=PosWriter(out,'fixture',with_hce=True,with_fen=True)
        row,fen=text_record(FEN+' | 10 | 0.5')
        writer.append(Record(row.board,row.score,row.meta,12),fen=fen);writer.close()
        process_dir=out/'probe_logs/worker-0';process_dir.mkdir(parents=True)
        process={'returncode':0,'binary_unchanged':True,'successful_requests':1,
                 'response_count':1,'binary_sha256':BINARY,'synthetic_fixture':True}
        (process_dir/'process.json').write_text(json.dumps(process))
        common={'status':'SEALED','config':{'stem':'fixture','workers':1},'synthetic_fixture':True}
        if kind=='filter':
            summary={**common,'kept':1,'input_rows':1,'rules':{'example':{'eligible':1,'dropped':0}},
                     'policy_order':['example'],'native_queries':1,'probe':{'sha256':BINARY},'supplied_holdout_position_overlap':None}
        else:
            summary={**common,'selected':1,'probe_sha256':BINARY}
            summary['config']['count']=1
        self.seal(out,summary,missing,pending)
        return out

    def seal(self,out,summary=None,missing=None,pending=False):
        kind='filter' if out.name=='filter' else 'relabel'
        if summary is None:summary=json.loads((out/'summary.json').read_text())
        summary['output' if kind=='filter' else 'outputs']={
            suffix:(target.digest(out/('fixture'+suffix)) if kind=='filter' else target.digest(out/('fixture'+suffix))['sha256'])
            for suffix in ('.pos','.hce','.fen')}
        for name in ('summary.json','progress.json'):
            if name!=missing:(out/name).write_text(json.dumps(summary))
        if pending:(out/'summary.json.pending').write_bytes((out/'summary.json').read_bytes())
        manifest={}
        for path in sorted(out.rglob('*')):
            if path.is_file() and path.name not in ('manifest.json','manifest.json.pending'):
                d=target.digest(path)
                manifest[path.relative_to(out).as_posix()]=d if kind=='filter' else d['sha256']
        (out/'manifest.json').write_text(json.dumps(manifest))
        if pending:(out/'manifest.json.pending').write_bytes((out/'manifest.json').read_bytes())

    def test_good_old_and_new_filter_and_relabel(self):
        a=self.fixture('filter',pending=True);b=self.fixture('relabel')
        for out in (a,b):
            before={p.relative_to(out):target.digest(p) for p in out.rglob('*') if p.is_file()}
            for full in (False,True):
                result=target.check_bundle(out,full_records=full)
                self.assertEqual(result['status'],'PASS')
                self.assertEqual(result['records_and_fen_matches_verified'],int(full))
            after={p.relative_to(out):target.digest(p) for p in out.rglob('*') if p.is_file()}
            self.assertEqual(before,after,'auditor must not modify bundle files')

    def test_corrupt_data_fails_hash(self):
        out=self.fixture();p=out/'fixture.pos'
        with p.open('r+b') as f:f.seek(16);f.write(b'\xff')
        with self.assertRaisesRegex(ValueError,'mismatch'):target.check_bundle(out)

    def test_missing_receipt_and_failed_run(self):
        out=self.fixture(missing='summary.json')
        with self.assertRaises(FileNotFoundError):target.check_bundle(out)
        other=self.fixture('relabel');(other/'failure.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'failure.json'):target.check_bundle(other)

    def test_manifest_traversal_and_windows_absolute_rejected(self):
        out=self.fixture();original=json.loads((out/'manifest.json').read_text())
        for bad in ('../outside','..\\outside','/tmp/outside','C:\\outside','a/../outside'):
            with self.subTest(path=bad):
                (out/'manifest.json').write_text(json.dumps({**original,bad:'a'*64}))
                with self.assertRaisesRegex(ValueError,'path rejected|unsafe relative'):
                    target.check_bundle(out)

    def test_windows_relative_separators_and_alias_duplicates(self):
        out=self.fixture();manifest=json.loads((out/'manifest.json').read_text())
        windows={name.replace('/','\\'):value for name,value in manifest.items()}
        (out/'manifest.json').write_text(json.dumps(windows))
        self.assertEqual(target.check_bundle(out)['status'],'PASS')
        key='probe_logs/worker-0/process.json';windows[key]=manifest[key]
        (out/'manifest.json').write_text(json.dumps(windows))
        with self.assertRaisesRegex(ValueError,'duplicate normalized'):target.check_bundle(out)

    def test_symlink_escape_is_rejected(self):
        out=self.fixture();outside=self.root/'outside';outside.write_text('synthetic outside fixture')
        (out/'escape').symlink_to(outside)
        manifest=json.loads((out/'manifest.json').read_text());manifest['escape']=target.digest(outside)
        (out/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'symlink escapes'):target.check_bundle(out)

    def test_header_count_and_summary_count_checked(self):
        out=self.fixture();p=out/'fixture.pos'
        with p.open('r+b') as f:f.seek(8);f.write(struct.pack('<Q',2))
        self.seal(out)
        with self.assertRaisesRegex(ValueError,'file size/count mismatch'):target.check_bundle(out)
        other=self.fixture('relabel');summary=json.loads((other/'summary.json').read_text())
        summary['selected']=2;summary['config']['count']=2;self.seal(other,summary)
        with self.assertRaisesRegex(ValueError,'header count'):target.check_bundle(other)

    def test_full_records_checks_values_and_fen_default_does_not_claim_it(self):
        out=self.fixture();p=out/'fixture.pos'
        with p.open('r+b') as f:f.seek(16);f.write(b'\xff')
        self.seal(out)
        self.assertEqual(target.check_bundle(out)['records_and_fen_matches_verified'],0)
        with self.assertRaisesRegex(ValueError,'invalid piece nibble'):target.check_bundle(out,full_records=True)

    def test_probe_failure_and_aggregate_mismatch(self):
        out=self.fixture();p=out/'probe_logs/worker-0/process.json';original=json.loads(p.read_text())
        for change in ({'returncode':2},{'binary_unchanged':False},{'response_count':0},
                       {'response_count':2,'successful_requests':2}):
            with self.subTest(change=change):
                p.write_text(json.dumps({**original,**change}));self.seal(out)
                with self.assertRaises(ValueError):target.check_bundle(out)

    def test_waterfall_holdout_and_fen_count(self):
        out=self.fixture();summary=json.loads((out/'summary.json').read_text())
        summary['input_rows']=2;self.seal(out,summary)
        with self.assertRaisesRegex(ValueError,'waterfall|kept.dropped'):target.check_bundle(out)
        summary['input_rows']=1;summary['supplied_holdout_position_overlap']=1;self.seal(out,summary)
        with self.assertRaisesRegex(ValueError,'holdout overlap'):target.check_bundle(out)
        summary['supplied_holdout_position_overlap']=0
        (out/'fixture.fen').write_text(FEN+'\n'+FEN+'\n');self.seal(out,summary)
        with self.assertRaisesRegex(ValueError,'FEN line count'):target.check_bundle(out)

    def test_ordered_eligibility_fractions_and_native_minimum(self):
        out=self.fixture();summary=json.loads((out/'summary.json').read_text())
        summary.update(input_rows=2,policy_order=['first','second'],
                       rules={'first':{'eligible':2,'dropped':1},'second':{'eligible':2,'dropped':0}})
        self.seal(out,summary)
        with self.assertRaisesRegex(ValueError,'ordered waterfall eligibility'):target.check_bundle(out)
        summary['rules']['second']['eligible']=1
        summary['rules']['first']['fraction_input']=0.2;self.seal(out,summary)
        with self.assertRaisesRegex(ValueError,'fraction mismatch'):target.check_bundle(out)
        summary['rules']['first']['fraction_input']=0.5
        summary['native_queries']=0;self.seal(out,summary)
        process_path=out/'probe_logs/worker-0/process.json';process=json.loads(process_path.read_text())
        process.update(successful_requests=0,response_count=0);process_path.write_text(json.dumps(process));self.seal(out,summary)
        with self.assertRaisesRegex(ValueError,'queries fewer than kept'):target.check_bundle(out)

    def test_pending_summary_must_match_final(self):
        out=self.fixture(pending=True);(out/'summary.json.pending').write_text('different staged receipt')
        # Preserve the altered pending bytes while updating manifest hashes only.
        manifest=json.loads((out/'manifest.json').read_text())
        manifest['summary.json.pending']=target.digest(out/'summary.json.pending')
        for name in ('manifest.json','manifest.json.pending'):(out/name).write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'pending summary differs'):target.check_bundle(out)

    def test_missing_manifest_coverage_and_extra_file(self):
        out=self.fixture();manifest=json.loads((out/'manifest.json').read_text())
        manifest.pop('summary.json');(out/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'does not cover summary'):target.check_bundle(out)
        self.seal(out);(out/'untracked.txt').write_text('extra synthetic file')
        with self.assertRaisesRegex(ValueError,'unmanifested file'):target.check_bundle(out)

if __name__=='__main__':unittest.main()
