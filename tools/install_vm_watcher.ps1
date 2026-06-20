#Requires -Version 5.1
# Run this script ONCE in the VM as the logged-in user.
# It installs a "run-drop watcher" as a Task Scheduler logon task.
#
# Usage after install:
#   Drop any .ps1 file into  \\vmware-host\Shared Folders\wsp_tools\run\
#   The watcher picks it up within 2 seconds and launches it interactively
#   in your user session (visible window, correct desktop).
#
# The task starts automatically at every logon.
# To start it immediately without rebooting:
#   Start-ScheduledTask -TaskName "WSP-Run-Watcher"

Set-StrictMode -Off
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Watcher script (written to LocalAppData so it survives reboots)
# ---------------------------------------------------------------------------
$WatcherCode = @'
Set-StrictMode -Off
$DropFolder = "\\vmware-host\Shared Folders\wsp_tools\run"
$LogFile    = "\\vmware-host\Shared Folders\wsp_tools\watcher_log.txt"
$LocalTemp  = "$env:TEMP\wsp_runner"

if (-not (Test-Path $LocalTemp)) {
    New-Item -ItemType Directory -Path $LocalTemp -Force | Out-Null
}

function WLog($msg) {
    $entry = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $entry
    try { Add-Content $LogFile $entry -Encoding ASCII -ErrorAction SilentlyContinue } catch {}
}

WLog "=== WSP Run-Watcher started  user=$env:USERNAME  session=$env:SESSIONNAME ==="

# Wait up to 30 s for shared folders to mount after logon
$waited = 0
while ($waited -lt 30 -and -not (Test-Path "\\vmware-host\Shared Folders")) {
    Start-Sleep -Seconds 2; $waited += 2
}
if (Test-Path "\\vmware-host\Shared Folders") {
    WLog "Shared folders available after ${waited}s"
} else {
    WLog "WARNING: shared folders not found after 30 s - polling anyway"
}

# Ensure drop folder exists
if (-not (Test-Path $DropFolder)) {
    try { New-Item -ItemType Directory -Path $DropFolder -Force | Out-Null } catch {}
}

while ($true) {
    try {
        $files = Get-ChildItem "$DropFolder\*.ps1" -ErrorAction SilentlyContinue
        foreach ($f in $files) {
            # Copy to local temp so PowerShell doesn't execute from a UNC path
            $localCopy = "$LocalTemp\$(Get-Date -Format 'yyyyMMdd_HHmmss')_$($f.Name)"
            Copy-Item $f.FullName $localCopy -Force
            # Remove from drop folder so it doesn't run again on next poll
            Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue
            WLog "Launching: $($f.Name) -> $localCopy"
            Start-Process powershell.exe `
                -ArgumentList "-ExecutionPolicy Bypass -File `"$localCopy`"" `
                -WindowStyle Normal
        }
    } catch {
        WLog "Watcher error: $_"
    }
    Start-Sleep -Seconds 2
}
'@

$WatcherPath = "$env:LOCALAPPDATA\wsp_watcher.ps1"
$WatcherCode | Out-File $WatcherPath -Encoding UTF8 -Force
Write-Host "Watcher script written to: $WatcherPath"

# ---------------------------------------------------------------------------
# Create the run drop folder on the shared side (best-effort)
# ---------------------------------------------------------------------------
$RunDir = "\\vmware-host\Shared Folders\wsp_tools\run"
if (-not (Test-Path $RunDir)) {
    try { New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
          Write-Host "Created drop folder: $RunDir" }
    catch { Write-Host "Note: could not create drop folder now - it will be created on first watcher start" }
}

# ---------------------------------------------------------------------------
# Register the Task Scheduler task
# ---------------------------------------------------------------------------
$taskName = "WSP-Run-Watcher"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -File `"$WatcherPath`""

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([System.TimeSpan]::Zero) `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host ""
Write-Host "Task '$taskName' installed successfully."
Write-Host ""
Write-Host "Starting watcher now (no reboot needed)..."
Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 2

$state = (Get-ScheduledTask -TaskName $taskName).State
Write-Host "Task state: $state"
Write-Host ""
Write-Host "Drop folder (from VM):   $RunDir"
Write-Host "Drop folder (from host): H:\Users\Leo1\SpeechRecognition\tools\run\"
Write-Host "Watcher log:             \\vmware-host\Shared Folders\wsp_tools\watcher_log.txt"
Write-Host ""
Write-Host "To deploy vm_install_test.ps1, copy it to the run\ folder from the host."
Write-Host "The watcher will pick it up within 2 seconds and launch it visibly."
