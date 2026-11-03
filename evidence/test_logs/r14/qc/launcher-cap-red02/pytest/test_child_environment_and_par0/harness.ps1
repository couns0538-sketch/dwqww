$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
$env:CUDA_VISIBLE_DEVICES='sentinel-CUDA_VISIBLE_DEVICES'
$env:HIP_VISIBLE_DEVICES='sentinel-HIP_VISIBLE_DEVICES'
$env:TEMP='sentinel-TEMP'
$env:PYTHONPATH='sentinel-PYTHONPATH'
$env:ASTRA_R14_DEADLINE='1'
$env:ASTRA_R13_DEADLINE='1'
& 'D:\a14\tools\Invoke-R13.ps1' -Script 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-red02\pytest\test_child_environment_and_par0\probe.py' -RunName 'launcher-fd2928db248d' -TimeoutSeconds 30
$exit=$LASTEXITCODE
$values=@{}
$values['CUDA_VISIBLE_DEVICES']=$env:CUDA_VISIBLE_DEVICES
$values['HIP_VISIBLE_DEVICES']=$env:HIP_VISIBLE_DEVICES
$values['TEMP']=$env:TEMP
$values['PYTHONPATH']=$env:PYTHONPATH
$values['ASTRA_R14_DEADLINE']=$env:ASTRA_R14_DEADLINE
$values['ASTRA_R13_DEADLINE']=$env:ASTRA_R13_DEADLINE
$values | ConvertTo-Json | Set-Content -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-red02\pytest\test_child_environment_and_par0\parent.json' -Encoding utf8
exit $exit
