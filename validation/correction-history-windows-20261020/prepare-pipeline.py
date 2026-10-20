from pathlib import Path
import datetime,difflib,hashlib,json,subprocess
ROOT=Path('/workspace/dwqww');OLD=ROOT/'validation/promotion-see-20261020/windows';OUT=ROOT/'validation/correction-history-windows-20261020'
COMMIT='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b';PARENT='47f0560221d986e41a309853e1295c557fcf5bf6'
SOURCE=Path('/workspace/.cloud-setup/windows6418-source');BUILD=Path('/workspace/.cloud-setup/windows6418-build')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
replacements=[('47f0560221d986e41a309853e1295c557fcf5bf6',COMMIT),('553caef144ae2e1b696ba35d7a0eb1a50a03fde9',PARENT),('validation/promotion-see-20261020/windows','validation/correction-history-windows-20261020'),('/workspace/.cloud-setup/forge-promotion-windows-source',str(SOURCE)),('/workspace/.cloud-setup/forge-promotion-windows-build',str(BUILD)),('/workspace/.cloud-setup/forge-promotion-windows-package-capture','/workspace/.cloud-setup/windows6418-package-capture'),('forge-promotion-wine','forge-correction-history-wine'),('17 WINDOWS BUILD CLEAR','18 WINDOWS BUILD CLEAR'),('6.4.17','6.4.18'),('candidate17','candidate18'),('actual17','actual18'),('frozen17','frozen18'),('first actual17','first actual18'),('parent6416-preservation','parent6417-preservation')]
provenance={}
for name in ['prepare-source.py','build-driver.py','run-phase.py','validation-driver.py','package-driver.py','run-package.py']:
 original=(OLD/name).read_text();text=original
 for a,b in replacements:text=text.replace(a,b)
 if name=='validation-driver.py':
  text=text.replace(" ('coherent-tt',", " ('correction-history',[str(WINE),str(BUILD/'forge_correction_history_tests.exe')]),\n ('coherent-tt',")
  text=text.replace("    ownbook_result=json.loads", "    correction=(OUT/'correction-history-stdout.log').read_text()\n    correction_summary=re.findall(r'^SUMMARY checks=(\\d+) failures=(\\d+)\\s*$',correction,re.M)\n    assert len(correction_summary)==1 and int(correction_summary[0][0])>0 and int(correction_summary[0][1])==0\n    assert 'Correction-history residual increment contract' in correction and 'FAIL ' not in correction\n    ownbook_result=json.loads")
  text=text.replace("'rule50_targeted_failures':0,", "'correction_history_checks':int(correction_summary[0][0]),'correction_history_failures':0,'rule50_targeted_failures':0,")
  text=text.replace('Promotion recapture behavior intentionally changes; preserve one actual positive signature without imposing prior-version counts','Correction-history residual-increment search behavior intentionally changes; preserve one actual positive signature without imposing prior-version counts')
 if name=='package-driver.py':
  text=text.replace("len(runtime['checks']) == 8", "len(runtime['checks']) == 9")
  text=text.replace("assert runtime['legal_witness_comparisons'] == 18947", "assert runtime['correction_history_checks'] > 0 and runtime['correction_history_failures'] == 0\nassert runtime['legal_witness_comparisons'] == 18947")
  text=text.replace("validation/pin-mask-see-20261020/windows/source-hashes.json","validation/promotion-see-20261020/windows/source-hashes.json")
  text=text.replace("['CMakeLists.txt', 'src/board.cpp', 'src/uci.cpp']","['CMakeLists.txt', 'src/search.cpp', 'src/uci.cpp']")
  text=text.replace("['CMakeLists.txt','src/board.cpp','src/uci.cpp','tests/tests.cpp']","['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/correction_history_tests.cpp']")
  text=text.replace("if name!='tests/tests.cpp'", "if name!='tests/correction_history_tests.cpp'")
  text=text.replace("Only promotion recapture SEE, five mirrored fixtures plus zero-threshold assertions, and version labels changed; NNUE/eval sources, headers and weights are byte-identical to frozen 6.4.16.","Only the correction-history EMA-to-residual increment search ablation, its dedicated actual-method test/registration and version labels changed; NNUE/eval sources, headers and weights are byte-identical to frozen 6.4.17.")
  text=text.replace("'wine_functional_and_signature_checks': runtime['checks'],", "'wine_functional_and_signature_checks': runtime['checks'],")
  start=text.index("(OUT / 'README.md').write_text");end=text.index('\n# Snapshot every original Windows record',start)
  text=text[:start]+'''(OUT / 'README.md').write_text(f\'''Frozen Forge 6.4.18 Windows correctness evidence

Source/tests: `{COMMIT}`. Parent: `{PARENT}` (6.4.17).
Strict static LLVM-MinGW23.1.3 Zen5 C++20 Release build, one job, no FMA/LTO/fast-math.
Nine Wine checks passed: core/perft with 28 mirrored SEE cases, correction-history
actual-method contract ({runtime['correction_history_checks']} checks), eight TT groups,
rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions and
first observed candidate18 bench11 signature {runtime['bench11_nodes']}.
That signature was unknown before execution. No prior-version count was imposed.

This independent unaccepted search ablation changes correction-history EMA decay
to a residual increment. It is not a known-bug repair or accepted strength
improvement. Only search.cpp, its dedicated test, CMake registration/version and UCI
version label differ from frozen17; NNUE/eval sources, headers and weights match.
Original 6.4.16 full TSan FAILED 8/9; its separate five-case OwnBook diagnostic remains
finite coverage only. Candidate 6.4.18 native gates are reported separately.
This Windows stage establishes bounded correctness only; it is not an accepted release.
No NPS/Elo/native Windows/Ryzen claim follows. All original PEs/core/source/logs retained.
\''')
''' + text[end:]
  text=text.replace("'forge_legal_witness_tests.exe': 'forge_legal_witness_tests.exe'", "'forge_legal_witness_tests.exe': 'forge_legal_witness_tests.exe',\n           'forge_correction_history_tests.exe': 'forge_correction_history_tests.exe'")
  text=text.replace("Separate candidate18 native gates", "Separate candidate18 native gates")
  text=text.replace("Rare back-rank SEE path accounts for later pawn promotion recaptures, new victim value and promotion material; ordinary threshold path remains inherited. This intentionally changes promotion exchange behavior.","Independent unaccepted search ablation: correction-history EMA decay becomes a residual increment, retaining signed depth weight/clipping and table read policy. This intentionally changes learned correction and search behavior; no established bug or Elo gain is claimed.")
  text=text.replace("'evaluation_network_replacement_unchanged': True,", "'evaluation_network_replacement_unchanged': True, 'search_change_accepted':False, 'known_bug_repair':False,")
  text=text.replace("'tt_groups': 8,", "'tt_groups': 8, 'correction_history_checks':runtime['correction_history_checks'], 'correction_history_failures':0,")
  start=text.index("(PACKAGE / 'README.txt').write_text");end=text.index("\n(PACKAGE / 'SHA256SUMS')",start)
  text=text[:start]+'''(PACKAGE / 'README.txt').write_text(f\'''Forge 6.4.18 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.18-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
Frozen source/tests: {COMMIT}. Parent: {PARENT} (6.4.17).

This independent unaccepted search ablation changes correction-history EMA decay
to a residual increment. It is not a known-bug repair or accepted strength
improvement. The new dedicated test exercises the actual worker methods for signed
depth/clipping, learned-entry retention, feedback convergence, material/pawn-table
coupling, saturation and mate-score output clamps. NNUE/eval source, headers and
weights remain byte-identical to 6.4.17; inherited 6.4.17 promotion SEE remains.

Nine Wine checks passed: core/perft with 28 mirrored SEE cases, correction-history
actual-method contract ({runtime['correction_history_checks']} checks), eight TT groups,
rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions and
first observed candidate18 bench11 signature {runtime['bench11_nodes']}.
The new signature was unknown before execution; prior-version counts were not imposed.
AVX2 clamp/multiply/add and output-layer checks passed without fused arithmetic.

Compiler: LLVM-MinGW23.1.3, strict C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, no LTO. Seven original PEs, actual
core, frozen source, commands, stdout/stderr and disassembly remain retained and archived
in manifest-verified windows-originals.zip. Earlier clock/TT/legal/rule50/OwnBook and
path-accounting policies remain inherited with their existing limits.

This Windows stage establishes bounded correctness only; native gates are separate.
This is not an accepted release. Original 6.4.16 full TSan FAILED 8/9; the separate 6.4.16
five-case OwnBook diagnostic provides finite coverage only. Candidate 6.4.18 native gates
are reported separately. No accepted NPS or Elo improvement exists. No throughput
or timed match ran. Native Windows, physical Ryzen and Stockfish superiority remain unproven.

Optional tests:
forge_tests.exe
forge_correction_history_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See provenance.json, source-hashes.json, test-hashes.json, nnue-parent-identity.json,
windows-originals-SHA256.json and SHA256SUMS.
\''')
''' + text[end:]
  text=text.replace("'runtime_checks': 8", "'runtime_checks': 9")
 (OUT/name).write_text(text);compile(text,str(OUT/name),'exec')
 (OUT/(name+'.adaptation.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True),text.splitlines(keepends=True),fromfile='17/'+name,tofile='18/'+name)))
 provenance[name]={'source_script':str((OLD/name).relative_to(ROOT)),'source_sha256':sha(OLD/name),'adapted_sha256':sha(OUT/name),'compiled_syntax_only':True}
write('PIPELINE-ADAPTATION.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scripts':provenance,'policy':'Reuse exact17 build, phase, validation and packaging logic; path/source/version updates, additional actual correction-history check and distribution, truthful ablation scope; no retries or weakened gates.','no_compiler_engine_wine_archive_execution':True})
print(json.dumps(provenance,indent=2))
