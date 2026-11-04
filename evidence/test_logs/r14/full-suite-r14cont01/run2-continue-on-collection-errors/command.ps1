# Triage run 2 (independent reviewer): the SAME scope and environment as ..\command.ps1 plus
# --continue-on-collection-errors, so that every collectable test still runs and the totals can be recorded.
# Run 1 (..\output.log) stopped at collection: 10 collection errors (torch missing in the R14 runtime; module-name
# collisions filter_positions / test_converter between astra_r8\datafilter and tools\data + tests\data2).
$ErrorActionPreference = 'Continue'
$env:TEMP = 'D:\a14\tmp'
$env:TMP = 'D:\a14\tmp'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$dir = 'D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run2-continue-on-collection-errors'
$start = Get-Date
"start=$($start.ToString('yyyy-MM-dd HH:mm:ss'))" | Set-Content -Path "$dir\timing.txt" -Encoding ascii
cmd /c "D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x4 -- D:\a14\runtime\python\python.exe -I -B -m pytest D:\a14\astra_r8\datafilter\tests D:\a14\tests -q -p no:cacheprovider --continue-on-collection-errors --basetemp $dir\tmp > $dir\output.log 2>&1"
$code = $LASTEXITCODE
$end = Get-Date
"end=$($end.ToString('yyyy-MM-dd HH:mm:ss'))" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"exit=$code" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"elapsed_s=$([int]($end - $start).TotalSeconds)" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
