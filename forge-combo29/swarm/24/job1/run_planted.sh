#!/usr/bin/env bash
# seat 24, area 4: the planted-fault proof that "0 reports" means something.
# A scratch copy of the engine (~/work/planted) with ONE unlocked global counter
# (g_planted_race_counter) written by every worker in Worker::should_stop(),
# built with the same flags as the real TSan build, run through THE SAME runner.
set -u
cd "$(dirname "$0")"
echo "$(date -u) start planted control" >> stamps.txt
python3 driver.py --exe "$HOME/work/planted/build-tsan/forge" --fens set_G.epd --count 6 \
    --threads 4 --depth 12 --hash 16 --opts S14 --timeout 600 --out planted >> planted.run.log 2>&1
echo "$(date -u) end planted control exit=$?" >> stamps.txt
echo "--- planted raw: number of TSan reports:"
grep -c "WARNING: ThreadSanitizer" planted.raw
echo "--- planted meta nm_tsan:"
grep nm_tsan planted.meta
