$ErrorActionPreference='Continue'
$o='D:\forge-qa\lockproof_combo29_20261108'
$ad='C:\Users\Administrator\grok-pc\forge_push\sdk_speedonly_20261107\gate0415'
$py='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
$fens='C:\Users\Administrator\grok-pc\sdk_longjob_20261106_copy\data\fens_12k_v2.txt'
$ref='C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe'
$cand='D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\m2use\forge_m2use.exe'
$tsv=(Get-ChildItem "$ad\refcache\4181a589" -Filter '*UseNNUE-true*.tsv').FullName
"start $(Get-Date -f s)" | Set-Content "$o\STATUS.txt"
& $py -I -B "$ad\warm_identity.py" $ref $cand $fens "$o\warm1000" --n 1000 --nodes 20000 *> "$o\warm.log"
$w=$LASTEXITCODE; "warm exit $w $(Get-Date -f s)" | Add-Content "$o\STATUS.txt"
& $py -I -B "$ad\soak.py" $ref $cand $fens $tsv "$o\soak_t4" *> "$o\soak.log"
$k=$LASTEXITCODE; "soak exit $k $(Get-Date -f s)" | Add-Content "$o\STATUS.txt"
@{warm=$w;soak=$k;finished=(Get-Date -f s)} | ConvertTo-Json | Set-Content "$o\DONE.json"
