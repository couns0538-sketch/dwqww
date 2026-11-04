# Independent reviewer run of the full suite "inherited plus R14" (R14-cont), same scope as D:\a13\evidence\test_logs\full-suite06.
# Launched through opus_lowrun.py --mask 0x4 (CPU 2, Idle priority, GPU hidden); stdout+stderr merged into output.log by cmd.exe (raw bytes).
$ErrorActionPreference = 'Continue'
$env:TEMP = 'D:\a14\tmp'
$env:TMP = 'D:\a14\tmp'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$dir = 'D:\a14\evidence\test_logs\r14\full-suite-r14cont01'
$start = Get-Date
"start=$($start.ToString('yyyy-MM-dd HH:mm:ss'))" | Set-Content -Path "$dir\timing.txt" -Encoding ascii
cmd /c "D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x4 -- D:\a14\runtime\python\python.exe -I -B -m pytest D:\a14\astra_r8\datafilter\tests D:\a14\tests -q -p no:cacheprovider --basetemp D:\a14\evidence\test_logs\r14\full-suite-r14cont01\tmp > $dir\output.log 2>&1"
$code = $LASTEXITCODE
$end = Get-Date
"end=$($end.ToString('yyyy-MM-dd HH:mm:ss'))" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"exit=$code" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"elapsed_s=$([int]($end - $start).TotalSeconds)" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"exit=$code" | Set-Content -Path "$dir\exit.txt" -Encoding ascii
