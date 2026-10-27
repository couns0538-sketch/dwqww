#!/usr/bin/env bash
# Planted-bug check for the C1 tests: each mutation is applied to a copy of the tree, the copy's
# forge_syzygy_tests is built (g++, -O2, one job) and run against the tablebase folder; every
# mutation must make the test fail. The unmodified copy must pass.
# usage: mutation_check.sh <repo> <work_dir> <tablebase_dir>   (needs g++ on PATH; MSYS2 or Linux)
set -uo pipefail
REPO=$(cd "$1" && pwd)
WORK=$2
TB=$3
mkdir -p "$WORK"
WORK=$(cd "$WORK" && pwd)
FLAGS="-std=c++20 -O2 -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -march=x86-64-v3"
LINK="-pthread"
case "$(uname -s)" in MINGW*|MSYS*) LINK="-static -pthread" ;; esac

# Objects that the mutations never touch are built once.
mkdir -p "$WORK/obj"
for f in bitboard board book eval eval_params nnue; do
  [ -f "$WORK/obj/$f.o" ] || g++ $FLAGS -I"$REPO/include" -c "$REPO/src/$f.cpp" -o "$WORK/obj/$f.o" || exit 2
done

run_case() {  # name, file (relative), sed expression ("" = unmodified)
  local name=$1 file=$2 expr=$3 tree="$WORK/tree"
  rm -rf "$tree"; mkdir -p "$tree"
  cp -r "$REPO/src" "$REPO/include" "$REPO/tests" "$tree/"
  if [ -n "$expr" ]; then
    cp "$tree/$file" "$tree/$file.orig"
    sed -i -E "$expr" "$tree/$file"
    if cmp -s "$tree/$file" "$tree/$file.orig"; then echo "MUTATION NOT APPLIED: $name"; return 1; fi
  fi
  if ! g++ $FLAGS -I"$tree/include" -c "$tree/src/search.cpp" -o "$WORK/obj/search_mut.o" 2> "$WORK/$name.build.log" ||
     ! g++ $FLAGS -I"$tree/include" -c "$tree/tests/syzygy_tests.cpp" -o "$WORK/obj/tests_mut.o" 2>> "$WORK/$name.build.log" ||
     ! g++ $LINK -o "$WORK/t_$name.exe" "$WORK"/obj/{bitboard,board,book,eval,eval_params,nnue}.o "$WORK/obj/search_mut.o" "$WORK/obj/tests_mut.o" 2>> "$WORK/$name.build.log"; then
    echo "BUILD FAILED: $name"; return 1
  fi
  "$WORK/t_$name.exe" "$tree/tests/syzygy_fixtures.tsv" "$tree/tests/syzygy_reference.tsv" "$TB" > "$WORK/$name.log" 2>&1
  local rc=$?
  local summary
  summary=$(grep "syzygy tests:" "$WORK/$name.log" | tail -1)
  if [ -z "$expr" ]; then
    [ $rc -eq 0 ] && echo "baseline: PASS ($summary)" || { echo "baseline: FAIL ($summary)"; return 1; }
  else
    [ $rc -ne 0 ] && echo "caught    $name: $summary" || { echo "MISSED    $name: $summary"; return 1; }
  fi
}

status=0
run_case baseline "" "" || status=1
S=src/search/syzygy.inc
run_case king_pair_order        $S 's/if \(both_diagonal != \(pass == 1\)\) continue;/if (both_diagonal != (pass == 0)) continue;/' || status=1
run_case pawn_rank_h_side_first $S 's/g\.pawn_rank\[static_cast<std::size_t>\(make_square\(file, rank\)\)\] = order--;/g.pawn_rank[static_cast<std::size_t>(make_square(file, rank))] = order - 1; --order;/; s/g\.pawn_rank\[static_cast<std::size_t>\(make_square\(7 - file, rank\)\)\] = order--;/g.pawn_rank[static_cast<std::size_t>(make_square(7 - file, rank))] = order + 1; --order;/' || status=1
run_case diagonal_flip_sign     $S 's/            if \(d > 0\) \{/            if (d < 0) {/' || status=1
run_case triple_case2_offset    $S 's/v = 6 \* 63 \* 62 \+ \(static_cast<std::int64_t>\(rank_of\(s0\)\) \* 28/v = 6 * 63 * 62 + (static_cast<std::int64_t>(rank_of(s0) + 1) * 28/' || status=1
run_case other_pawns_no_shift   $S 's/other_pawns > 0\) \? 8 : 0;/other_pawns > 0) ? 0 : 0;/' || status=1
run_case ep_table_when_all_capt $S 's/if \(examined == legal\.size\(\)\) \{/if (examined == legal.size() + 1) {/' || status=1
run_case no_capture_resolution  $S 's/        if \(!capture && !\(pawn_moves && piece_type\(board\.moved_piece\(move\)\) == Pawn\)\) continue;/        if (true) continue;/' || status=1
run_case dtz_moves_not_doubled  $S 's/plies = \(in_plies \? v : 2 \* v\) \+ 1;/plies = v + 1;/' || status=1
run_case dtz_map_category_swap  $S 's/const std::size_t category = wdl == 2 \? 0 : wdl == -2 \? 1 : wdl == 1 \? 2 : 3;/const std::size_t category = wdl == 2 ? 1 : wdl == -2 ? 0 : wdl == 1 ? 2 : 3;/' || status=1
run_case dtz_wrong_side_kept    $S 's/if \(\(t->flags & 1\) != at\.side && /if (false \&\& /' || status=1
run_case castling_probed        $S 's/return r != nullptr && board\.castling_rights\(\) == 0 && /return r != nullptr \&\& /' || status=1
run_case rule50_boundary        $S 's/else if \(dtz > 0\) wdl = distance <= 100 \? 2 : 1;/else if (dtz > 0) wdl = distance < 100 ? 2 : 1;/' || status=1
run_case cursed_offset          $S 's/\(node\.wdl == 1 \|\| node\.wdl == -1 \? 100 : 0\)/(node.wdl == 1 || node.wdl == -1 ? 99 : 0)/' || status=1
run_case root_mate_dtz          $S 's/        if \(mate && dtz == 2\) dtz = 1;/        if (mate \&\& dtz == 3) dtz = 1;/' || status=1
G=src/search/tablebase.inc
run_case search_probe_needs_rule50 $G 's/if \(board\.halfmove_clock\(\) != 0 \|\| board\.castling_rights\(\) != 0\) return ValueNone;/if (board.castling_rights() != 0) return ValueNone;/' || status=1
run_case search_tb_score_sign   $G 's/value = syzygy::TbWin - ss->ply;/value = -syzygy::TbWin + ss->ply;/' || status=1
run_case root_filter_off        $G 's/    limits\.search_moves_specified = true;/    limits.search_moves_specified = false;/' || status=1
echo "mutation_check status=$status"
exit $status
