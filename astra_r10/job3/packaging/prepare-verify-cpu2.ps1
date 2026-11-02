# Scheduling-only adaptation of reviewed run-seal-verify.ps1 Verify phase.
# Root structured self-review: same verifier, read paths, output scope and1worker;
# CPU2 replaces busyCPU3. No changes to the sealed pack or verification algorithm.
$ErrorActionPreference='Stop'
$p=[Diagnostics.Process]::GetCurrentProcess();$p.PriorityClass='Idle';$p.ProcessorAffinity=4
$py='D:\a10\python\python.exe'
$folder='D:\a10\wt\astra_r10\job3\packaging'
$file=Join-Path $folder 'verify-cpu2final01.manifest.json'
$output=Join-Path $folder 'verify-cpu2final01-launch'
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $output)){throw 'Fresh verification evidence required'}
$job=[ordered]@{schema=1;executable=$py;executable_sha256=(Get-FileHash -LiteralPath $py -Algorithm SHA256).Hash;
arguments=@('-B',(Join-Path $folder 'verify_job3_pack.py'),'--pack','D:\a10\wt\astra_r10\job3\pack','--threads','1');
working_directory='D:\a10';output_directory=$output;read_paths=@($py,'D:\a10');write_paths=@($output);
logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000}
[IO.File]::WriteAllText($file,($job|ConvertTo-Json -Depth 5),(New-Object Text.UTF8Encoding($false)))
Write-Output $file
