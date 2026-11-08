# agent_run.ps1 - Task Scheduler runs this every 10 min. It starts ONE unattended `claude -p "continue"` session when it is safe.
# Skips (and tries again next cycle) when:  tools\STOP or tools\NOAGENT exists | an auto session is still running |
#   no internet | an interactive Claude session touched this project in the last 30 min (AGENTS.md rule: one agent at a time) |
#   last auto session started < 60 min ago | already 8 auto sessions today.
# A session that fails within 3 min (= usually no internet / API error) does not count and is retried next cycle.
param([switch]$Worker, [string]$PromptFile = 'D:\RoboSketch-RL\tools\agent_prompt.txt')

$root = 'D:\RoboSketch-RL'
$t    = "$root\tools"
$log  = "$t\agent.log"
$lock = "$t\agent.lock"
$last = "$t\agent.last"

function Log($m) { "$(Get-Date -Format s) $m" | Add-Content $log }

if (-not $Worker) {
    if ((Test-Path "$t\STOP") -or (Test-Path "$t\NOAGENT")) { exit 0 }
    if ((Test-Path $lock) -and (Get-Process -Id ([int](Get-Content $lock)) -ErrorAction SilentlyContinue)) { exit 0 }

    # internet: any HTTP answer = online; no answer = offline
    try { Invoke-WebRequest 'https://api.anthropic.com' -Method Head -TimeoutSec 8 -UseBasicParsing | Out-Null }
    catch { if (-not $_.Exception.Response) { Log 'SKIP no internet'; exit 0 } }

    $newest = Get-ChildItem "$env:USERPROFILE\.claude\projects\d--RoboSketch-RL" -Filter *.jsonl -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($newest -and ((Get-Date) - $newest.LastWriteTime).TotalMinutes -lt 30) { exit 0 }   # someone is working here
    if ((Test-Path $last) -and ((Get-Date) - [datetime](Get-Content $last)).TotalMinutes -lt 60) { exit 0 }
    $today = (Get-Date).ToString('yyyy-MM-dd')
    if (@(Select-String -Path $log -Pattern "^$today.* START" -ErrorAction SilentlyContinue).Count -ge 8) { exit 0 }

    Set-Content $last (Get-Date -Format s)
    Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$t\agent_run.ps1",'-Worker')
    exit 0
}

# ---- worker: runs the session, max 90 min ----
Set-Content $lock $PID
$exe = Get-ChildItem "$env:USERPROFILE\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe" |
       Sort-Object { [version]($_.FullName -replace '.*claude-code-([\d\.]+)-.*','$1') } -Descending |
       Select-Object -First 1 -ExpandProperty FullName
New-Item -ItemType Directory -Force "$t\agent_logs" | Out-Null
$out = "$t\agent_logs\$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"

$allowed = 'Read,Grep,Glob,Edit,Write,PowerShell(Get-Content:*),PowerShell(Get-ChildItem:*),PowerShell(Select-String:*),PowerShell(Get-Item:*),PowerShell(Get-CimInstance:*),PowerShell(Get-Date:*),PowerShell(conda run:*)'
$denied  = 'PowerShell(Remove-Item:*),PowerShell(Stop-Process:*),PowerShell(git:*),WebSearch,WebFetch'
$args2   = "-p --permission-mode acceptEdits --max-turns 150 --allowedTools `"$allowed`" --disallowedTools `"$denied`""

Log "START session -> $out"
Set-Location $root
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process $exe -ArgumentList $args2 -RedirectStandardInput $PromptFile -RedirectStandardOutput $out `
        -RedirectStandardError "$out.err" -WindowStyle Hidden -PassThru
$null = $p.Handle    # cache the handle, otherwise ExitCode is empty after WaitForExit
if (-not $p.WaitForExit(90 * 60 * 1000)) { $p.Kill(); $p.WaitForExit(); Log 'KILLED after 90 min timeout' }
$code = $p.ExitCode
Log "END   session exit=$code secs=$([int]$sw.Elapsed.TotalSeconds)"
if ($code -ne 0 -and $sw.Elapsed.TotalSeconds -lt 180) { Remove-Item $last -ErrorAction SilentlyContinue; Log 'quick failure (internet/API?) - will retry next cycle' }
Remove-Item $lock -ErrorAction SilentlyContinue
