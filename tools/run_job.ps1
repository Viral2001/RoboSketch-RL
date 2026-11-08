# run_job.ps1 <name> <script_args...>  - runs ONE sweep worker, records how it ended.
# Exit code 0  -> tools\done\<name>.done is written (watchdog never relaunches it).
# Exit code !=0 -> tools\fails\<name>.count is incremented (watchdog relaunches, up to 20 times).
param([string]$Name, [string]$ScriptArgs)

$root = 'D:\RoboSketch-RL'
$log  = "$root\tools\keepalive.log"
$env:OMP_NUM_THREADS = '1'      # same settings as AGENTS.md section 5 (thread count changes seeded results)
$env:MKL_NUM_THREADS = '1'
Set-Location $root

"$(Get-Date -Format s) START $Name : $ScriptArgs" | Add-Content $log
$conda = 'C:\Users\viral\New folder\Scripts\conda.exe'
New-Item -ItemType Directory -Force "$root\tools\job_logs" | Out-Null
$jl  = "$root\tools\job_logs\$Name.log"    # worker output goes to a file (a hidden console can block writes)
$cmd = "`"$conda`" run -n robosketch --no-capture-output python -u $ScriptArgs >> `"$jl`" 2>&1"
cmd /c $cmd
$code = $LASTEXITCODE
"$(Get-Date -Format s) END   $Name exit=$code" | Add-Content $log

if ($code -eq 0) {
    New-Item -ItemType Directory -Force "$root\tools\done" | Out-Null
    Set-Content "$root\tools\done\$Name.done" (Get-Date -Format s)
} else {
    New-Item -ItemType Directory -Force "$root\tools\fails" | Out-Null
    $f = "$root\tools\fails\$Name.count"
    $n = 0; if (Test-Path $f) { $n = [int](Get-Content $f) }
    Set-Content $f ($n + 1)
}
