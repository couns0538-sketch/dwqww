#!/usr/bin/env bash
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/tmp/partner-build/forge
python3 "$D/honesty_check.py" "$EXE" PARTNER_HONESTY || echo HONESTY_FAIL
python3 "$D/search_set.py" --exe "$EXE" --fens "$D/first200.fens" --depth 12 --out partner_off_O --switch false || echo OFF_FAIL
python3 "$D/search_set.py" --exe "$EXE" --fens "$D/first200.fens" --depth 12 --out partner_on_O --switch true || echo ON_FAIL
python3 "$D/cmp_rows.py" "$D/B_O_d12.rows" "$D/partner_off_O.rows" > "$D/partner_cmp_off_O.txt"
python3 "$D/cmp_claimed.py" "$D/partner_on_O.rows" "$D/partner_claimed_on.nodes.txt" > "$D/partner_cmp_on_claimed.txt"
python3 "$D/sum_rows.py" "$D/partner_on_O.rows" > "$D/partner_on_O.sum"
echo SEARCH_DONE
FC=/tmp/fastchess/fastchess
rm -f "$D/partner_match.pgn"
"$FC" \
  -engine cmd="$EXE" name=IdeaS28on option.IdeaS28=true \
  -engine cmd="$EXE" name=IdeaS28off option.IdeaS28=false \
  -each nodes=20000 tc=60+0 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/set_R.epd" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 -recover \
  -ratinginterval 50 \
  -pgnout file="$D/partner_match.pgn" notation=uci min=true \
  -event "grok-$S-partner" \
  > "$D/partner_match.txt" 2>&1
echo MATCH_EXIT:$? >> "$D/partner_match.txt"
echo PARTNER_REST_DONE
