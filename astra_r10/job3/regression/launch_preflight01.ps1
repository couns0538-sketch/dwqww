#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTHONNOUSERSITE='1'
$env:CUDA_VISIBLE_DEVICES='';$env:HIP_VISIBLE_DEVICES='';$env:ROCR_VISIBLE_DEVICES=''
$helper='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
$helperSha='17205767AE3EA35A5CCB5A7965BC4988BAE26B4F2260C821411A657C9979C787'
$manifest='D:\a10\wt\astra_r10\job3\regression\preflight01.manifest.json'
$runner='D:\a10\wt\astra_r10\job3\regression\run_regression.py'
if((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne $helperSha){throw 'Reviewed helper changed'}
if((Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash -ne '743E673FC07453938840C820871B0E5AD6DFD41EFC684CE0958ABD0D7B690573'){throw 'Reviewed runner changed'}
if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne '7CE0ABAC31BABE7D7465B91E34AFFDD6A6F3E73DC12533971EB51DF5FBA3262C'){throw 'Manifest changed after preparation'}
$inputs='D:\a10\wt\astra_r10\job3\regression\preflight01-inputs.json'
if((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -ne '2E2D34569D7ED736C706F208D764BDBE3409656F8F05C25003F3C83ACB208832'){throw 'Input binding map changed after preparation'}
$boundInputs=Get-Content -LiteralPath $inputs -Raw|ConvertFrom-Json
foreach($item in $boundInputs){if((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.sha256){throw ('Bound input changed before launch: '+$item.path)}}
$roots=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$runtimeRoots=@('D:\grok-pc-data\npt\nnue-pytorch-amd')
$toolRoots=@('C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231','C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0','C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0')
$binding='D:\a10\wt\astra_r10\job3\regression\preflight01-command.json'
if(Test-Path -LiteralPath $binding){throw 'No evidence overwrite'}
[ordered]@{start_utc=[DateTime]::UtcNow.ToString('o');helper_sha256=$helperSha;runner_sha256='743E673FC07453938840C820871B0E5AD6DFD41EFC684CE0958ABD0D7B690573';manifest_sha256='7CE0ABAC31BABE7D7465B91E34AFFDD6A6F3E73DC12533971EB51DF5FBA3262C';input_map_sha256='2E2D34569D7ED736C706F208D764BDBE3409656F8F05C25003F3C83ACB208832';wrapper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}|ConvertTo-Json|Set-Content -LiteralPath $binding -Encoding UTF8
& $helper -Manifest $manifest -ProtectedRoots $roots -ReadOnlyRuntimeRoots $runtimeRoots -ReadOnlyToolchainRoots $toolRoots
$nativeCode=$LASTEXITCODE
foreach($item in $boundInputs){if((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.sha256){throw ('Bound input changed during launch: '+$item.path)}}
exit $nativeCode