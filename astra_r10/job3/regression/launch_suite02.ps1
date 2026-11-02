#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTHONNOUSERSITE='1'
$env:CUDA_VISIBLE_DEVICES='';$env:HIP_VISIBLE_DEVICES='';$env:ROCR_VISIBLE_DEVICES=''
$helper='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
$helperSha='17205767AE3EA35A5CCB5A7965BC4988BAE26B4F2260C821411A657C9979C787'
$manifest='D:\a10\wt\astra_r10\job3\regression\suite02.manifest.json'
$runner='D:\a10\wt\astra_r10\job3\regression\run_regression.py'
if((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne $helperSha){throw 'Reviewed helper changed'}
if((Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash -ne '238342D6918923140F55A49641BB6520AC3BAF8DC6FE6B541126DE3E9D787A69'){throw 'Reviewed runner changed'}
if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne '07E92E81F5A8EDA63B04F26A7D76925BCADD3A15447677F89D2106890C3D25E3'){throw 'Manifest changed after preparation'}
$inputs='D:\a10\wt\astra_r10\job3\regression\suite02-inputs.json'
if((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -ne 'C205D7E4A31A3139D341DA67097FBDC693C723CF30182B2B988345277B514D22'){throw 'Input binding map changed after preparation'}
$boundInputs=Get-Content -LiteralPath $inputs -Raw|ConvertFrom-Json
foreach($item in $boundInputs){if((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.sha256){throw ('Bound input changed before launch: '+$item.path)}}
$roots=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$runtimeRoots=@('D:\grok-pc-data\npt\nnue-pytorch-amd')
$toolRoots=@('C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231','C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0','C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0')
$binding='D:\a10\wt\astra_r10\job3\regression\suite02-command.json'
if(Test-Path -LiteralPath $binding){throw 'No evidence overwrite'}
[ordered]@{start_utc=[DateTime]::UtcNow.ToString('o');helper_sha256=$helperSha;runner_sha256='238342D6918923140F55A49641BB6520AC3BAF8DC6FE6B541126DE3E9D787A69';manifest_sha256='07E92E81F5A8EDA63B04F26A7D76925BCADD3A15447677F89D2106890C3D25E3';input_map_sha256='C205D7E4A31A3139D341DA67097FBDC693C723CF30182B2B988345277B514D22';wrapper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}|ConvertTo-Json|Set-Content -LiteralPath $binding -Encoding UTF8
& $helper -Manifest $manifest -ProtectedRoots $roots -ReadOnlyRuntimeRoots $runtimeRoots -ReadOnlyToolchainRoots $toolRoots
$nativeCode=$LASTEXITCODE
foreach($item in $boundInputs){if((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.sha256){throw ('Bound input changed during launch: '+$item.path)}}
exit $nativeCode