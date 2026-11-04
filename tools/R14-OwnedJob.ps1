#Requires -Version 7
# Native job membership is established before the trusted gate can start payloads.
if (-not ('R14OwnedJob' -as [type])) {
    $compileEnvironment=@{}
    $compilePresent=@{}
    foreach ($name in @('TEMP','TMP','TMPDIR')) {
        $compilePresent[$name]=Test-Path -LiteralPath ('Env:'+$name)
        $compileEnvironment[$name]=[Environment]::GetEnvironmentVariable($name,'Process')
        [Environment]::SetEnvironmentVariable($name,'D:\a14\tmp','Process')
    }
    try {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
public sealed class R14OwnedJob : IDisposable {
    [StructLayout(LayoutKind.Sequential)] struct BasicLimits {
        public long ProcessTime, JobTime;
        public uint Flags;
        public UIntPtr MinWorkingSet, MaxWorkingSet;
        public uint ActiveProcesses;
        public UIntPtr Affinity;
        public uint PriorityClass, SchedulingClass;
    }
    [StructLayout(LayoutKind.Sequential)] struct IoCounters {
        public ulong ReadOperations, WriteOperations, OtherOperations;
        public ulong ReadBytes, WriteBytes, OtherBytes;
    }
    [StructLayout(LayoutKind.Sequential)] struct ExtendedLimits {
        public BasicLimits Basic;
        public IoCounters Io;
        public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateJobObjectW(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool SetInformationJobObject(IntPtr job, int kind, ref ExtendedLimits data, uint size);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool member);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool TerminateJobObject(IntPtr job, uint exitCode);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr OpenJobObjectW(uint access, bool inherit, string name);
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct StartupInfo {
        public uint Size;
        public string Reserved, Desktop, Title;
        public uint X, Y, XSize, YSize, XCountChars, YCountChars, FillAttribute, Flags;
        public ushort ShowWindow, ReservedBytes;
        public IntPtr ReservedData, Input, Output, Error;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInformation {
        public IntPtr Process, Thread;
        public uint ProcessId, ThreadId;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool CreateProcessW(string application, StringBuilder commandLine,
        IntPtr processSecurity, IntPtr threadSecurity, bool inheritHandles, uint flags,
        IntPtr environment, string directory, ref StartupInfo startup, out ProcessInformation process);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(IntPtr process, uint exitCode);
    [DllImport("kernel32.dll")] static extern IntPtr GetStdHandle(int handle);
    IntPtr handle;
    public string Name { get; private set; }
    public R14OwnedJob() {
        Name="Local\\R14-"+Guid.NewGuid().ToString("N");
        handle=CreateJobObjectW(IntPtr.Zero,Name);
        if (handle==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        var limits=new ExtendedLimits();
        limits.Basic.Flags=0x2000 | 0x20;
        limits.Basic.PriorityClass=0x40;
        if (!SetInformationJobObject(handle,9,ref limits,(uint)Marshal.SizeOf<ExtendedLimits>())) {
            int error=Marshal.GetLastWin32Error();
            CloseHandle(handle); handle=IntPtr.Zero;
            throw new Win32Exception(error);
        }
    }
    public void Assign(IntPtr process) {
        if (handle==IntPtr.Zero) throw new ObjectDisposedException("owned job");
        if (!AssignProcessToJobObject(handle,process)) throw new Win32Exception(Marshal.GetLastWin32Error());
    }
    public bool Contains(IntPtr process) {
        bool member;
        if (!IsProcessInJob(process,handle,out member)) throw new Win32Exception(Marshal.GetLastWin32Error());
        return member;
    }
    public void Dispose() {
        if (handle!=IntPtr.Zero) {
            IntPtr closing=handle; handle=IntPtr.Zero;
            bool terminated=TerminateJobObject(closing,70);
            int error=Marshal.GetLastWin32Error();
            bool closed=CloseHandle(closing);
            if (!terminated) throw new Win32Exception(error);
            if (!closed) throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }
    static string Quote(string value) {
        var result=new StringBuilder("\"");
        int slashes=0;
        foreach (char ch in value) {
            if (ch=='\\') { slashes++; continue; }
            if (ch=='\"') result.Append('\\',slashes*2+1);
            else result.Append('\\',slashes);
            slashes=0; result.Append(ch);
        }
        result.Append('\\',slashes*2); result.Append('"');
        return result.ToString();
    }
    public static uint RunAssigned(string jobName, string executable, string[] arguments) {
        IntPtr job=OpenJobObjectW(0x0001 | 0x0004,false,jobName);
        if (job==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        var command=new StringBuilder(Quote(executable));
        foreach (string argument in arguments) command.Append(' ').Append(Quote(argument));
        if (command.Length>=32767) { CloseHandle(job); throw new ArgumentException("Command exceeds native limit"); }
        var startup=new StartupInfo();
        startup.Size=(uint)Marshal.SizeOf<StartupInfo>();
        startup.Flags=0x100;
        startup.Input=GetStdHandle(-10); startup.Output=GetStdHandle(-11); startup.Error=GetStdHandle(-12);
        ProcessInformation process=new ProcessInformation();
        bool resumed=false;
        try {
            // A suspended payload cannot create a descendant before explicit membership.
            if (!CreateProcessW(executable,command,IntPtr.Zero,IntPtr.Zero,true,0x08000004,
                                IntPtr.Zero,"D:\\a14",ref startup,out process))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            bool member;
            if (!IsProcessInJob(process.Process,job,out member)) throw new Win32Exception(Marshal.GetLastWin32Error());
            if (!member && !AssignProcessToJobObject(job,process.Process)) throw new Win32Exception(Marshal.GetLastWin32Error());
            CloseHandle(job); job=IntPtr.Zero;
            if (ResumeThread(process.Thread)==0xffffffff) throw new Win32Exception(Marshal.GetLastWin32Error());
            resumed=true;
            if (WaitForSingleObject(process.Process,0xffffffff)!=0) throw new Win32Exception(Marshal.GetLastWin32Error());
            uint exitCode;
            if (!GetExitCodeProcess(process.Process,out exitCode)) throw new Win32Exception(Marshal.GetLastWin32Error());
            return exitCode;
        } finally {
            if (!resumed && process.Process!=IntPtr.Zero) TerminateProcess(process.Process,76);
            if (process.Thread!=IntPtr.Zero) CloseHandle(process.Thread);
            if (process.Process!=IntPtr.Zero) CloseHandle(process.Process);
            if (job!=IntPtr.Zero) CloseHandle(job);
        }
    }
}
'@
    } finally {
        foreach ($name in $compileEnvironment.Keys) {
            if ($compilePresent[$name]) { [Environment]::SetEnvironmentVariable($name,$compileEnvironment[$name],'Process') }
            else { [Environment]::SetEnvironmentVariable($name,$null,'Process') }
        }
    }
}

function Initialize-R14JobChild($Child,[string]$RunDirectory,[string]$Executable,[string[]]$Arguments) {
    $job=[R14OwnedJob]::new()
    $manifest=Join-Path $RunDirectory 'child-command.json'
    $payload=@{executable=$Executable;arguments=$Arguments;job=$job.Name} | ConvertTo-Json -Depth 3
    [IO.File]::WriteAllText($manifest,$payload,[Text.UTF8Encoding]::new($false))
    $Child.StartInfo.FileName=Join-Path $PSHOME 'pwsh.exe'
    $Child.StartInfo.ArgumentList.Clear()
    foreach ($argument in @('-NoProfile','-File','D:\a14\tools\R14-ChildGate.ps1','-Manifest',$manifest)) {
        $Child.StartInfo.ArgumentList.Add($argument)
    }
    $Child.StartInfo.RedirectStandardInput=$true
    return $job
}

function Release-R14JobChild($Job,$Child) {
    $Job.Assign($Child.Handle)
    $Child.StandardInput.WriteLine('R14_READY')
    $Child.StandardInput.Flush()
    $Child.StandardInput.Close()
}

function Complete-R14JobCapture($Job,$Child,[object[]]$Tasks,[scriptblock]$Guard) {
    # Closing the job kills all owned descendants, even after the direct gate exits.
    if ($Job) { $Job.Dispose() }
    $deadline=[Diagnostics.Stopwatch]::StartNew()
    while (@($Tasks | Where-Object { $_ -and -not $_.IsCompleted }).Count) {
        if ($deadline.Elapsed.TotalSeconds -ge 5) { throw 'PIPE_DRAIN_TIMEOUT' }
        if ($Guard) { & $Guard }
        Start-Sleep -Milliseconds 50
    }
    foreach ($task in $Tasks) {
        if ($task) { $null=$task.GetAwaiter().GetResult() }
    }
}

function Stop-R14JobChild($Job,$Child,[bool]$Started) {
    if ($Job) { $Job.Dispose() }
    if ($Started -and -not $Child.HasExited -and -not $Child.WaitForExit(1000)) {
        # Assignment can fail before gate release. That gate has no payload yet.
        try { $Child.Kill($true) } catch { if (-not $Child.HasExited) { throw } }
        if (-not $Child.WaitForExit(1000)) { throw 'CHILD_EXIT_TIMEOUT' }
    }
}
