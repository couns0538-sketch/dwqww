#!/usr/bin/env python3
"""Finalize and byte-verify the owned immutable experiment capsule."""
from pathlib import Path
import datetime, hashlib, json, zipfile

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
SEMANTIC=json.loads((ROOT/'semantic-record.json').read_text())
DIAGNOSTIC=json.loads((ROOT/'diagnostics-attempt1/record.json').read_text())
assert SEMANTIC['status']=='PASS_BYTE_IDENTICAL_API_PARITY'
assert DIAGNOSTIC['status']=='PASS_EXACT_PARITY_WITH_OPERATION_COUNTS'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
assert (ROOT/'api-reference.stdout').read_bytes()==(ROOT/'api-mask.stdout').read_bytes()
for kind in ['reference','mask']:
    assert (ROOT/'diagnostics-attempt1'/('api-'+kind+'.stdout')).read_bytes()==(ROOT/'api-reference.stdout').read_bytes()
assert (ROOT/'diagnostics-attempt1/bench11-reference.stdout').read_bytes()==(ROOT/'diagnostics-attempt1/bench11-mask.stdout').read_bytes()
assert all(sha(p)==h for p,h in SEMANTIC['immutable_input_sha256_before'].items())
assert sha(SEMANTIC['original_core_path'])==SEMANTIC['original_core_sha256_before']
assert all(sha(Path('/workspace/.cloud-setup/forge-pin-see-source')/p)==h for p,h in SEMANTIC['reference_source_sha256'].items())
assert sha(REPO/'src/board.cpp')==SEMANTIC['reference_source_sha256']['src/board.cpp']

summary={
    'status':'PASS_EXACT_PARITY_WITH_REDUCED_FILTER_QUERY_WORK',
    'decision':'Preserve isolated candidate for root review; measured speed and integration acceptance remain unproven.',
    'source_commit':SEMANTIC['source_commit'],
    'reference_board_sha256':sha(ROOT/'reference-board.cpp'),
    'mask_board_sha256':sha(ROOT/'mask-board.cpp'),
    'mask_patch_sha256':sha(ROOT/'mask.patch'),
    'original_core_sha256':SEMANTIC['original_core_sha256_before'],
    'only_changed_core_member':'board.cpp.o',
    'api_cases':316,
    'fixed_threshold_answers_compared':6320,
    'api_stdout_byte_identical':True,
    'complete_shadow_filter_states_verified':DIAGNOSTIC['api_counters']['mask']['mask_states_verified'],
    'individual_shadow_queries':DIAGNOSTIC['api_counters']['mask']['verification_shadow_queries'],
    'shadow_mask_mismatches':DIAGNOSTIC['api_counters']['mask']['mask_mismatches'],
    'known_promotion_limitations_preserved':2,
    'bench_depth':11,'bench_positions':8,'bench_nodes':DIAGNOSTIC['bench_nodes'],
    'bench_nodes_scores_bestmoves_pvs_byte_identical':True,
    'api_counters':DIAGNOSTIC['api_counters'],
    'bench_counters':DIAGNOSTIC['bench_counters'],
    'engine_execution_seconds_budget_accounting_only':DIAGNOSTIC['engine_elapsed_seconds'],
    'engine_execution_budget_seconds':120,
    'bench_timeout_seconds_each':10,
    'failed_engine_or_build_attempts':0,
    'artifact_write_tool_errors':1,
    'all_original_source_core_and_inputs_unchanged':True,
    'production_board_unchanged':True,
    'performance_claim':None,'strength_claim':None,
    'limitations':[
        'No calibrated speed or NPS comparison was run; durations only account for operational execution limits.',
        'No full candidate CTest/sanitizer/Windows integration gate was run for this mask candidate.',
        'The mask retains the reference LVA, threshold, king-branch, and recapture-promotion behavior.',
        'Complete-mask shadow verification ran on the existing API corpus; it was disabled during bench work counts.'
    ],
    'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()
}
write(ROOT/'SUMMARY.json',summary)
readme="""# Isolated exact SEE filter mask

The forbidden-origin mask preserves the frozen 6.4.15 reference behavior and
shows lower source-level king-filter lookup work on the bounded bench. This
is an isolated prototype result; measured speed and integration acceptance
remain unproven.

DESIGN.md is the original source-only proposal and proof snapshot.
mask.patch changes only the per-candidate king-safety filter. The reference is
source 8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad; the original Release core hash
is 27c8db2caf860c868dbece61a4de0b8121a5d696b846a96e4f7aa2439498ea97.
The core and complete original source export remained unchanged. Only
board.cpp.o differs in copied candidate archives. Production and Git were
not edited by this experiment.

Uninstrumented actual Board API output is byte-identical over the immutable
300-case prototype corpus, four supplemental cases, and 12 coverage controls:
316 rows and 6,320 fixed-threshold answers, including SEE values, legality, and
complete first recapture lists. Both inherited promotion limitations remain
-400 against oracle -1200. This is exact reference parity, not a claim of
universal minimax SEE correctness.

Diagnostics were added only after that semantic gate. Instrumented API
outputs still match the uninstrumented reference byte-for-byte. The candidate
shadow-compared 3,614 complete surviving attacker masks against the actual
reference helper, using 1,275 individual shadow queries, with zero mismatches.
All same-value candidate origins were included.

One serial depth-11 bench capture was run per instrumented build, with a
10-second operational guard each. The dedicated driver reuses UCI bench's
exact eight FENs, Searcher(16), one thread, per-position clearing, and exclusive
TT access, and prints actual per-position depth, nodes, score, best move, and
legal PV. Those stdout files are byte-identical, totaling 385,792 nodes.
Search and NNUE objects were reused unchanged; neither was recompiled.

| Filter work in the eight-position bench | Reference | Mask |
| --- | ---: | ---: |
| SEE calls | 462,049 | 462,049 |
| Visited exchange plies | 426,149 | 426,149 |
| Non-king candidate origins | 371,702 | 371,702 |
| Surviving non-king origins | 369,479 | 369,479 |
| Full per-origin king queries | 371,702 | 0 |
| Occupied bishop/rook queries | 742,109 | 0 |
| Empty-board bishop/rook lookups | 0 | 474,626 |
| Between-ray classifications | 0 | 49,015 |
| Each pawn/knight/king attack test | 371,702 | 237,313 |

These are diagnostic operation counts, with scope limited to the SEE filter.
Reference helper counters were active only around its primary candidate loop.
Candidate shadow queries were counted separately during API verification and
were disabled in both bench runs. Instrumentation itself changes execution
cost and was not used for a performance comparison.

The reduction in occupied-board attack queries and repeated non-slider tests
supports the proposed mechanism. Costs per operation differ, and some
single-candidate positions may require more between work. No wall-time, NPS,
Elo, match, or Ryzen/Windows speed claim follows. Recorded durations exist
only for operational guards and the 120-second engine-execution budget.
Total actual API/bench execution was {:.6f} seconds.

semantic-record.json and diagnostics-attempt1/record.json preserve every
command, exit status, timeout, stdout/stderr hash, source identity, core member
hash, and counter result. All execution phases succeeded. One artifact-writing
tool syntax error occurred before tool execution and is preserved separately
in artifact-write-attempt1.json; it ran no compiler or engine and wrote no files.
INDEPENDENT-AUDIT.md records a separate source/output audit. Full source TARs,
plain and diagnostic Board sources, objects, copied cores, diagnostic
executables, drivers, immutable inputs, and raw outputs are included in
complete-evidence.zip.

archive-manifest.json maps every archived artifact to its SHA-256. The
archive-verification receipt sits outside the ZIP to avoid self-referential
hashing. Root should review the bounded result before any source integration
and require the appropriate full correctness gates for an applied candidate.
""".format(DIAGNOSTIC['engine_elapsed_seconds'])
(ROOT/'README.md').write_text(readme)

excluded={'complete-evidence.zip','archive-manifest.json','archive-verification.json'}
artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*'))
           if p.is_file() and p.name not in excluded}
write(ROOT/'archive-manifest.json',{'files':artifacts,'files_count':len(artifacts)})
archive=ROOT/'complete-evidence.zip'
assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    for relative in artifacts:z.write(ROOT/relative,relative)
    z.write(ROOT/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(artifacts)|{'archive-manifest.json'}
    for relative,expected in artifacts.items():
        assert hashlib.sha256(z.read(relative)).hexdigest()==expected,relative
assert all(sha(ROOT/relative)==h for relative,h in artifacts.items())
write(ROOT/'archive-verification.json',{
    'status':'PASS_ALL_MEMBERS_BYTE_VERIFIED','archive_sha256':sha(archive),
    'archive_bytes':archive.stat().st_size,'manifest_files':len(artifacts),
    'zip_members':len(artifacts)+1,'all_original_source_core_inputs_unchanged':True,
    'engine_execution_seconds_budget_accounting_only':DIAGNOSTIC['engine_elapsed_seconds']
})
print(json.dumps({'status':summary['status'],'archive_sha256':sha(archive),
                  'archive_bytes':archive.stat().st_size,'manifest_files':len(artifacts),
                  'bench_nodes':summary['bench_nodes']}))
