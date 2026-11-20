#!/usr/bin/env bash
set -u
stdbuf -oL /tmp/fastchess/fastchess \
  -engine cmd=/tmp/partner-src/forge-combo29/build/forge name=IdeaS15on option.IdeaS15=true \
  -engine cmd=/tmp/partner-src/forge-combo29/build/forge name=IdeaS15off option.IdeaS15=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file=/agent/repos/dwqww/forge-combo29/grok/015/r_300.epd format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -pgnout file=/agent/repos/dwqww/forge-combo29/grok/015/partner_match.pgn notation=uci nodes=true \
  > /agent/repos/dwqww/forge-combo29/grok/015/partner_match_stdout.txt 2>&1
echo "exit=$?" >> /agent/repos/dwqww/forge-combo29/grok/015/partner_match_stdout.txt
