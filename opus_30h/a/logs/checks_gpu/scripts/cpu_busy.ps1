# cpu_busy.ps1 [-Cpus "0,1"] [-Samples 5] - checks of the GPU-trained v2 nets (2026-11-04): the busy percentage of the
# given logical CPUs over Samples x 1 s (Windows performance counters; prints n/a when a counter cannot be read).
# -Cpus is a comma-separated string (powershell -File binds "0,1" as one string).
param([string]$Cpus = '0,1', [int]$Samples = 5)
foreach ($cs in $Cpus.Split(',')) {
    $c = [int]$cs.Trim()
    try {
        $s = Get-Counter -Counter "\Processor($c)\% Processor Time" -SampleInterval 1 -MaxSamples $Samples -ErrorAction Stop
        $vals = @($s.CounterSamples | ForEach-Object { $_.CookedValue })
        $avg = ($vals | Measure-Object -Average).Average
        'cpu{0} busy {1:N1} % (avg of {2} x 1 s)' -f $c, $avg, $vals.Count
    } catch {
        'cpu{0} busy n/a ({1})' -f $c, $_.Exception.Message
    }
}
