from pathlib import Path
import hashlib,json,shutil
h=Path('/workspace/forge-sol-next-20261024');r=Path('/workspace/dwqww');base=r/'validation/sol-next-20261024'
for profile in ['release','assert-on','asan-on']:
 for f in ['CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/link.txt']:
  q=base/'buffer/raw/compiler-flags'/profile/Path(f).name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(h/('build-buffer-'+profile)/f,q)
for kind in ['buffer','int16']:
 p=h/'oracle-agent'/('CR_DRAFT_'+kind+'.md');original=p.read_bytes();t=original.decode();(base/kind/'CR_DRAFT.original.md').write_bytes(original)
 common={
 '../buffer-release-qa/':'raw/buffer-release-qa/', '../buffer-assert-on-qa/':'raw/buffer-assert-on-qa/', '../buffer-asan-on-qa/':'raw/buffer-asan-on-qa/', '../buffer-original-assert/':'raw/buffer-original-assert/',
 '../buffer-agent/PATCH_DELIVERY_VERIFICATION/':'patch-delivery-verification/', '../buffer-agent/buffer_fix.patch':'../../../releases/sol-next-20261024/buffer_only.patch','../buffer_fix.patch':'../../../releases/sol-next-20261024/buffer_fix.patch', '../buffer-commands.json':'buffer-commands.json','../buffer-original-assert-command.json':'buffer-original-assert-command.json',
 '../buffer-steps/':'raw/buffer-steps/','../buffer-simd-v2':'buffer-simd-v2','../buffer-fma-off/':'fma-off/','../buffer-fma-on/':'fma-on/','../int16-agent/wac-buffer/':'../int16/summaries/wac-buffer/',
 '../int16-release-off-qa/':'raw/release-off-qa/', '../int16-asan-off-qa/':'raw/asan-off-qa/', '../int16-commands.json':'build-commands.json', '../INTEGER-ROOT-SOURCE-FREEZE.json':'SOURCE_FREEZE.json',
 '../int16-release-on-bench/':'ON-bench13-16/', '../int16-steps/':'raw/build-test-steps/', '../int16-asan-on-bench/':'ASAN-ON-bench13/', '../int16-asan-mode-smoke/':'ASAN-ON-smoke/', '../int16-agent/parity-100k/':'parity/',
 '../int16-simd-v2':'SIMD/v2','../int16-FMA/':'SIMD/fma/','../int16-agent/wac-int16/':'summaries/wac-int16/', '../int16-agent/wac-int16-fresh-quiet-2/':'summaries/wac-int16-fresh-quiet-2/', '../int16-agent/WAC_FRESH_QUIET_2_PREDECLARED.json':'WAC_FRESH_QUIET_2_PREDECLARED.json','../int16-agent/nps-avx2-mode/':'NPS-Linux-dry-run/',
 'INT16_DELIVERY_VERIFICATION/':'delivery-independent/','STRICT_PTHREAD_IDENTITY.json':'strict-pthread/BYTE_IDENTITY.json','../strict-pthread-commands.json':'strict-pthread/commands.json','../strict-pthread-off-qa/':'strict-pthread/qa/',
 '../int16-agent/overflow-extremes/':'output-boundary/','../int16-agent/on-missing-depths/':'ON-bench11-20-22/',
 }
 for old,new in common.items():t=t.replace(old,new)
 if kind=='int16':
  t=t.replace('(`cmp` exit 0)','(Python raw-byte equality and matching SHA256)')
  t=t.replace('root\'s correction receipt is **PENDING**','the correction receipt is retained in `CLARIFICATIONS.json`')
  t=t.replace('../build-int16-release/CMakeFiles/{forge_core.dir/flags.make,forge.dir/link.txt}','raw/build-flags/{release-flags.make,release-link.txt}')
  t=t.replace('../buffer-agent/INT16-SIMD-REVIEW.md/.json','integer-SIMD-review.md and integer-SIMD-review.json')
  for name in ['quant-bestmove-selected.tsv','quant-bestmove-results.jsonl','quant-bestmove-summary.json']:t=t.replace('`'+name+'`','`d13-bestmove/'+name+'`')
  t=t.replace('`quant-bestmove-selected.tsv`, `quant-bestmove-results.jsonl`, `quant-bestmove-summary.json`','`d13-bestmove/quant-bestmove-selected.tsv`, `d13-bestmove/quant-bestmove-results.jsonl`, `d13-bestmove/quant-bestmove-summary.json`')
  t+='''\n## Additional retained lifecycle and publication evidence\n\nASan/UBSan T2 mid-search ON/OFF transitions PASS: observed infinite searches, stopped/joined before readiness, ON active acknowledgement, legal subsequent finite d6 searches; actual engine/runner exits0, empty stderr, frozen ASan binary unchanged. Exact exchanges and controller source: `ASAN-midsearch-mode/`, `tools/asan_mode_lifecycle.py`. `clear_hash()` clears TT and every worker evaluation cache after mode changes; search invalidates stack accumulators. No new source change was needed after these checks.\n\nComplete WAC originals are in `wac-int16-original.zip`, `wac-int16-fresh-quiet-2-original.zip` and `diagnostic-wac193-original.zip`, with roundtrip-verified manifests. Numerical originals include `parity/corpus.fen.gz`. `NPS-root-audit.json` independently rechecks all87 process records,80 timed samples and20 pairs; no repeat or pooling.\n\nActual UCI advertisement from the first Release gate:\n\n```text\n'''
  lines=(h/'int16-release-off-qa/precondition-d11/stdout').read_text().splitlines();t+='\n'.join(x for x in lines if x.startswith('option name '))+'\n```\n'
 else:
  t=t.replace('`null-counters/','`../int16/null-counters/')
  t=t.replace('../buffer-agent/proposed/tests/bad_capture_tests.cpp','../../../tests/bad_capture_tests.cpp')
  t=t.replace('../build-buffer-{release,assert-on,asan-on}/Testing/Temporary/LastTest.log','release-LastTest.log, assert-on-LastTest.log, asan-on-LastTest.log')
  t=t.replace('../buffer-{assert,asan}-on-qa/','raw/buffer-{assert,asan}-on-qa/')
  t=t.replace('../buffer-agent/STRICT_RELEASE/','strict-release/')
  t+='''\nRepository-retained original compiler/link flags: `raw/compiler-flags/{release,assert-on,asan-on}/`. Supplemental strict profiles and exact first-d11/ON five-depth/perft records: `strict-release/RECEIPT.md`, `strict-release/PROVENANCE.json`; original profile metadata remains unchanged. Complete original WAC exchanges are in `../int16/wac-buffer-original.zip`.\n'''
 (base/kind/'CR_DRAFT.md').write_text(t)
 (base/kind/'CR_DRAFT_PROVENANCE.json').write_text(json.dumps({'original_handoff':str(p),'original_sha256':hashlib.sha256(original).hexdigest(),'final_sha256':hashlib.sha256(t.encode()).hexdigest(),'root_changes':'Repository path mapping, actual lifecycle/first-UCI advertisement and preserved final receipts; no source/binary/result changes'},indent=2)+'\n')
print('Final handoffs saved with repository paths and original draft provenance.')
