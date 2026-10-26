"""Generate one always-on, unsigned-polynomial-exact history-key experiment."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

F=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
BASES={'L':F/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
       'Lprime':F/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
       'B':F/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
OUT=Path(__file__).resolve().parent
VIEW=Path('/tmp/forge_sol_S11_materialkey_source_20261026')
OLD='''// Hash of the piece counts of both sides, for material-indexed statistics.
[[nodiscard]] std::uint64_t material_key(const Board& board) {
    std::uint64_t key = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            key = key * 1099511628211ULL + static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return key * 0x9E3779B97F4A7C15ULL;
}
'''
NEW='''// Expand the existing material-key polynomial modulo2^64. A population count
// has65 possible values, so every lookup is in range even for synthetic boards.
constexpr auto MaterialKeyContributions = [] {
    constexpr std::size_t slots = static_cast<std::size_t>(2 * (Queen - Pawn + 1));
    constexpr std::size_t counts = static_cast<std::size_t>(std::numeric_limits<Bitboard>::digits + 1);
    std::array<std::array<std::uint64_t, counts>, slots> values{};
    std::uint64_t factor = 0x9E3779B97F4A7C15ULL;
    for (std::size_t slot = slots; slot-- > 0;) {
        for (std::size_t count = 0; count < counts; ++count) {
            values[slot][count] = factor * (static_cast<std::uint64_t>(count) + 1U);
        }
        factor *= 1099511628211ULL;
    }
    return values;
}();

// Hash of the piece counts of both sides, for material-indexed statistics.
[[nodiscard]] std::uint64_t material_key(const Board& board) {
    std::uint64_t key = 0;
    std::size_t slot = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            const auto count = static_cast<std::size_t>(popcount(board.pieces(color, static_cast<PieceType>(type))));
            key += MaterialKeyContributions[slot++][count];
        }
    }
    return key;
}
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def snapshot(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def main():
 VIEW.mkdir(exist_ok=False);L=BASES['L'];files=['src/search.cpp','IDEA_SOURCE.md','README.md']
 old={p:(L/p).read_text() for p in files};new=dict(old)
 if old['src/search.cpp'].count(OLD)!=1:raise ValueError('unique original material-key function required')
 new['src/search.cpp']=old['src/search.cpp'].replace(OLD,NEW)
 additions={
 'IDEA_SOURCE.md':'\n## S11 material-history key contribution table — 2026-10-26\n\nIdea sources only: the supplied Forge profile_notes.md reserve called material_key table-sum and the user S11 job. The implementation expands Forge\'s own unsigned64 Horner polynomial algebraically; its two existing mixing values remain unchanged. No external code or tuned values were used. This is separate from prior picker/piece-type and TT-prefetch speed work.\n',
 'README.md':'\n## S11 material-history key experiment — 2026-10-26\n\nUNPROVEN. This always-on S11 experiment replaces the ten dependent Horner products and final mix in the material-correction history key with a 5,200-byte constexpr contribution table and ten additions. Unsigned64 modular arithmetic preserves the exact original key. Counts0..64 are covered. There is no new board state, runtime allocation, NNUE/evaluation formula, TT access, move order, UCI option or build flag. S11 specifically requires an always-on exact-speed patch; no adoption follows from preparing it. Both-base fixed benchmarks, perft5, FMA0, full correctness/sanitizer suites and million-position scalar/AVX2 parity remain required. Linux ABBA is advisory; the owner PC speed CI rule decides eligibility.\n'}
 for p,text in additions.items():
  first,rest=old[p].split('\n',1);new[p]=first+'\n'+text+'\n'+rest
 patch=OUT/'forge_sol_S11_material_history_key_20261026.patch'
 if patch.exists():raise FileExistsError(patch)
 patch.write_text(''.join(''.join(difflib.unified_diff(old[p].splitlines(keepends=True),new[p].splitlines(keepends=True),fromfile='a/'+p,tofile='b/'+p,n=3)) for p in files))
 freezes={};before={label:snapshot(base) for label,base in BASES.items()}
 for label,base in BASES.items():
  dst=VIEW/label;shutil.copytree(base,dst)
  text=(dst/'src/search.cpp').read_text()
  if text.count(OLD)!=1:raise ValueError('base material function differs: '+label)
  (dst/'src/search.cpp').write_text(text.replace(OLD,NEW))
  for p,text in additions.items():
   first,rest=(dst/p).read_text().split('\n',1);(dst/p).write_text(first+'\n'+text+'\n'+rest)
  freezes[label]=snapshot(dst)
 if {label:snapshot(base) for label,base in BASES.items()}!=before:raise ValueError('original source changed')
 result={'status':'SOURCE_PREPARED_NOT_NATIVE_QUALIFIED','patch':str(patch),'patch_sha256':sha(patch),'source_views':{k:str(VIEW/k) for k in BASES},'source_freezes':freezes,'original_source_freezes':before,'table_bytes':5200,'always_on_by_S11_specific_rule':True,'new_options':[],'new_build_flags':[],'compiler_or_engine_runs':0}
 (OUT/'forge_sol_S11_source_inventory_20261026.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if 'freezes' not in k},indent=2))

if __name__=='__main__':main()
