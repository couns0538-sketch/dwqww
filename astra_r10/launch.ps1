param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference='Stop'
$env:TEMP='D:\a10\tmp'; $env:TMP=$env:TEMP
$env:PYTHONDONTWRITEBYTECODE='1'
& 'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1' -Manifest $Manifest -ProtectedRoots @('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
exit $LASTEXITCODE
