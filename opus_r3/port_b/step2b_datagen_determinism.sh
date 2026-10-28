#!/usr/bin/env bash
# port_b step 2b: S32's determinism run (25 games, 5000 nodes, seed 20261027, --text) into det_a and det_b.
# (In step 2 the loop variable was overwritten by waitram's RAM value: its first run went to datagen_smoke/9/, the
# second hit the same prefix and was refused, exit 1.) All three runs are compared, file by file, with S32's recorded
# sha256 (opus_round1/sol_S32/logs/run_outputs.sha256, det_a lines), then a reused prefix must be refused.
set -u
B=/f/opus_scratch/build/r3_port_b
L=/f/opus_scratch/r3/port_b
D=$L/datagen_smoke
for run in det_a det_b; do
  nice -n 19 $B/head_datagen.exe datagen --out F:/opus_scratch/r3/port_b/datagen_smoke/$run/g --games 25 --seed 20261027 --text > $L/datagen_smoke_$run.log 2>&1
  echo "$run rc=$?"; cat $L/datagen_smoke_$run.log
done
cd $D
files="g.games g_000.hce g_000.info g_000.pos g_000.txt"
for run in 9 det_a det_b; do for f in $files; do echo "$(sha256sum $run/$f | cut -d' ' -f1)  $run/$f"; done; done > $L/datagen_smoke.sha256
cat $L/datagen_smoke.sha256
pass=1
for f in $files; do
  ref=$(grep " det_a/$f\$" $L/datagen_smoke_s32_reference.sha256 | cut -d' ' -f1)
  [ -n "$ref" ] || { echo "no S32 reference for $f"; pass=0; }
  for run in 9 det_a det_b; do
    h=$(sha256sum $run/$f | cut -d' ' -f1)
    if [ "$h" = "$ref" ]; then echo "OK $run/$f = S32 ${ref:0:8}"; else echo "MISMATCH $run/$f $h ref $ref"; pass=0; fi
  done
done
[ $pass = 1 ] && echo "DATAGEN DETERMINISM: 3 runs x 5 files == S32 reference: PASS" || echo "DATAGEN DETERMINISM: FAIL"
before=$(sha256sum det_a/* | cut -d' ' -f1 | tr '\n' ' ')
nice -n 19 $B/head_datagen.exe datagen --out F:/opus_scratch/r3/port_b/datagen_smoke/det_a/g --games 1 --seed 1 > $L/datagen_reuse_refused.log 2>&1
rc=$?
after=$(sha256sum det_a/* | cut -d' ' -f1 | tr '\n' ' ')
cat $L/datagen_reuse_refused.log
if [ $rc -eq 1 ] && [ "$before" = "$after" ]; then echo "REUSED PREFIX: refused (exit 1), det_a files unchanged: PASS"; else echo "REUSED PREFIX: FAIL rc=$rc"; fi
