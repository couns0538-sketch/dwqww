#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$root='D:\a10\wt\astra_r10\job3\regression'
$helper='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
$sha='17205767AE3EA35A5CCB5A7965BC4988BAE26B4F2260C821411A657C9979C787'
if((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne $sha){throw 'Reviewed helper changed'}
if((Get-FileHash -LiteralPath (Join-Path $root 'pytest_alias_guard.py') -Algorithm SHA256).Hash -ne '13F8BCF15FE3CC7915BEBC88C03F86E8BDD283A8012221F5E2C9A3AA0A9E00B7'){throw 'Reviewed alias guard changed'}
if((Get-FileHash -LiteralPath (Join-Path $root 'check_pytest_alias_guard.py') -Algorithm SHA256).Hash -ne 'B469051500D1F1500227EC988DEAACCE38167723BACA2459B637D9C3AAE8F961'){throw 'Reviewed fixture changed'}
$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTHONNOUSERSITE='1'
$env:CUDA_VISIBLE_DEVICES='';$env:HIP_VISIBLE_DEVICES='';$env:ROCR_VISIBLE_DEVICES=''
$roots=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$manifest=Join-Path $root 'alias-fixture01.manifest.json'
$binding=Join-Path $root 'alias-fixture01-command.json'
if(Test-Path -LiteralPath $binding){throw 'No evidence overwrite'}
[ordered]@{start_utc=[DateTime]::UtcNow.ToString('o');helper_sha256=$sha;manifest_sha256=(Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash;wrapper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}|ConvertTo-Json|Set-Content -LiteralPath $binding -Encoding UTF8
& $helper -Manifest $manifest -ProtectedRoots $roots
exit $LASTEXITCODE
