#Requires -Version 5.1
# Automates the WSP Inno Setup installer wizard using UI Automation + Win32 API.
# Run on the VM after wsp_setup*.exe is present on the Desktop or shared folder.
# Writes a full log to Desktop\wsp_install_log.txt.
# ASCII-only: no em-dashes or box-drawing chars.

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# ---------------------------------------------------------------------------
# Win32 helpers.
# Radio buttons on custom Inno Setup pages (VCL TRadioButton) do not expose
# their caption via UIA NameProperty.  We use EnumChildWindows + BM_CLICK to
# click them directly.  The installer window is located by PID so we don't
# depend on a specific window title.
# ---------------------------------------------------------------------------
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Win32Helper {
    public delegate bool EnumWinProc(IntPtr hwnd, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWinProc fn, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern bool EnumChildWindows(IntPtr parent, EnumWinProc fn, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hwnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hwnd, StringBuilder sb, int n);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetClassName(IntPtr hwnd, StringBuilder sb, int n);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hwnd, uint msg, IntPtr wp, IntPtr lp);

    public const uint BM_CLICK = 0x00F5;

    // Find the main visible window owned by a given PID.
    public static IntPtr FindMainWindowByPid(uint pid) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((hwnd, lp) => {
            if (!IsWindowVisible(hwnd)) return true;
            uint winPid;
            GetWindowThreadProcessId(hwnd, out winPid);
            if (winPid == pid) { found = hwnd; return false; }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    // Find a child control whose caption contains 'text' (case-insensitive).
    public static IntPtr FindChildByText(IntPtr parent, string text) {
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(parent, (hwnd, lp) => {
            var sb = new StringBuilder(512);
            GetWindowText(hwnd, sb, 512);
            if (sb.ToString().IndexOf(text, StringComparison.OrdinalIgnoreCase) >= 0) {
                found = hwnd;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static string GetClass(IntPtr hwnd) {
        var sb = new StringBuilder(256);
        GetClassName(hwnd, sb, 256);
        return sb.ToString();
    }

    public static void Click(IntPtr hwnd) {
        SendMessage(hwnd, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
    }
}
"@

$LogFile         = "$env:USERPROFILE\Desktop\wsp_install_log.txt"
$ShareLog        = "\\vmware-host\Shared Folders\wsp_tools\install_progress.txt"
$ErrorCount      = 0
$script:InstPid  = 0   # installer process ID — set after Start-Process

"" | Out-File $LogFile   -Encoding ASCII
"" | Out-File $ShareLog  -Encoding ASCII -ErrorAction SilentlyContinue

function Log {
    param([string]$msg, [string]$level = "INFO")
    $entry = "[$(Get-Date -Format 'HH:mm:ss')] [$level] $msg"
    Write-Host $entry
    Add-Content $LogFile  $entry -Encoding ASCII
    Add-Content $ShareLog $entry -Encoding ASCII -ErrorAction SilentlyContinue
    if ($level -eq "ERROR") { $script:ErrorCount++ }
}

function Get-Root {
    return [System.Windows.Automation.AutomationElement]::RootElement
}

function Find-ByName {
    param(
        [string]$name,
        [string]$ctrlType   = "Button",
        [int]   $timeoutSec = 180
    )
    $type     = [System.Windows.Automation.ControlType]::$ctrlType
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        $nc = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty, $name)
        $tc = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty, $type)
        $el = (Get-Root).FindFirst(
            [System.Windows.Automation.TreeScope]::Descendants,
            (New-Object System.Windows.Automation.AndCondition($nc, $tc)))
        if ($el -and $el.Current.IsEnabled) { return $el }
        Start-Sleep -Milliseconds 400
    }
    return $null
}

function Get-AllVisibleText {
    $type = [System.Windows.Automation.ControlType]::Text
    $tc   = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty, $type)
    $texts = @()
    foreach ($el in (Get-Root).FindAll([System.Windows.Automation.TreeScope]::Descendants, $tc)) {
        $t = $el.Current.Name
        if ($t -and $t.Trim().Length -gt 3) { $texts += $t.Trim() }
    }
    return $texts -join " | "
}

function Invoke-Element {
    param([System.Windows.Automation.AutomationElement]$el, [string]$label)
    try {
        $p = $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        $p.Invoke()
        Log "Clicked: $label"
        Start-Sleep -Milliseconds 800
        return $true
    } catch {
        Log "Click failed on '$label': $_" "ERROR"
        return $false
    }
}

function Click-Button {
    param([string]$name, [int]$timeoutSec = 300)
    Log "Waiting for button '$name'..."
    $el = Find-ByName $name "Button" $timeoutSec
    if (-not $el) {
        Log "Button '$name' not found after ${timeoutSec}s" "ERROR"
        return $false
    }
    return Invoke-Element $el $name
}

# ---------------------------------------------------------------------------
# Click-ChildW32
# Finds any child control of the installer window whose caption contains
# $text, then sends BM_CLICK.  Works for radio buttons and checkboxes.
# Uses the installer PID stored in $script:InstPid so no window title needed.
# ---------------------------------------------------------------------------
function Click-ChildW32 {
    param([string]$text, [int]$timeoutSec = 20)
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        if ($script:InstPid -gt 0) {
            $hwnd = [Win32Helper]::FindMainWindowByPid([uint32]$script:InstPid)
            if ($hwnd -ne [IntPtr]::Zero) {
                $ctrl = [Win32Helper]::FindChildByText($hwnd, $text)
                if ($ctrl -ne [IntPtr]::Zero) {
                    [Win32Helper]::Click($ctrl)
                    Log "Clicked (W32): $text"
                    Start-Sleep -Milliseconds 400
                    return $true
                }
            }
        }
        Start-Sleep -Milliseconds 400
    }
    Log "Control '$text' not found after ${timeoutSec}s" "WARN"
    return $false
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Log "=== WSP Installer Automation Started ==="
Log "Host: $env:COMPUTERNAME  User: $env:USERNAME"

# Search Desktop first, then VMware shared folder
$installer = Get-ChildItem "$env:USERPROFILE\Desktop\wsp_setup*.exe" -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $installer) {
    $installer = Get-ChildItem "\\vmware-host\Shared Folders\wsp_installer\wsp_setup*.exe" `
                     -ErrorAction SilentlyContinue |
                 Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if (-not $installer) {
    Log "No wsp_setup*.exe found on Desktop or shared folder" "ERROR"
    exit 1
}
Log "Launching: $($installer.FullName)"
$proc            = Start-Process $installer.FullName -PassThru
$script:InstPid  = $proc.Id
Log "Installer PID: $($script:InstPid)"
Start-Sleep -Seconds 4

# Page 1: Welcome
Log "--- Page 1: Welcome ---"
if (-not (Click-Button "Next" 60)) { Log "Aborting" "ERROR"; exit 1 }

# Page 2: HuggingFace Licence
# Caption: "I accept the licence terms (speaker identification will be available)"
Log "--- Page 2: HuggingFace Licence ---"
Start-Sleep -Seconds 1
if (-not (Click-ChildW32 "I accept the licence terms")) {
    Log "Could not select Accept - continuing with Decline" "WARN"
}
if (-not (Click-Button "Next")) { Log "Aborting" "ERROR"; exit 1 }

# Page 3: Install Directory
Log "--- Page 3: Install Directory (default path) ---"
Start-Sleep -Seconds 1
if (-not (Click-Button "Next")) { Log "Aborting" "ERROR"; exit 1 }

# Page 4: Whisper Model
# Caption: "  Tiny    (~75 MB  -- fastest, lowest accuracy)"
Log "--- Page 4: Whisper Model (Tiny) ---"
Start-Sleep -Seconds 1
if (-not (Click-ChildW32 "Tiny")) {
    Log "Could not select Tiny - Medium will be used" "WARN"
}
if (-not (Click-Button "Next")) { Log "Aborting" "ERROR"; exit 1 }

# Page 5: Additional Tasks — check desktop shortcut before Next
# Checkbox caption resolves to "Create a &desktop icon" in English
Log "--- Page 5: Additional Tasks ---"
Start-Sleep -Seconds 1
if (-not (Click-ChildW32 "desktop icon")) {
    Log "Desktop icon checkbox not found - shortcut may not be created" "WARN"
}
if (-not (Click-Button "Next")) { Log "Aborting" "ERROR"; exit 1 }

# Page 6: Ready to Install
Log "--- Page 6: Ready to Install ---"
Start-Sleep -Seconds 1
if (-not (Click-Button "Install" 30)) { Log "Aborting" "ERROR"; exit 1 }

# ---------------------------------------------------------------------------
# Dialog loop: VLC + model downloads (up to 30 min)
# ---------------------------------------------------------------------------
Log "--- Waiting for downloads and installation (up to 30 min) ---"

$retryCounts = @{}
$deadline    = (Get-Date).AddMinutes(30)
$done        = $false

while ((Get-Date) -lt $deadline -and -not $done) {

    $finish = Find-ByName "Finish" "Button" 1
    if ($finish) {
        Log "Finish button found - installation complete"
        Invoke-Element $finish "Finish" | Out-Null
        $done = $true
        break
    }

    $yes = Find-ByName "Yes" "Button" 1
    $no  = Find-ByName "No"  "Button" 1
    if ($yes -and $no) {
        $text = Get-AllVisibleText
        Log "Yes/No dialog: $text"
        if ($text -match "retry|Retry") {
            $key = ($text -split '\|')[0].Trim() -replace '\s+', ' '
            $retryCounts[$key] = [int]$retryCounts[$key] + 1
            if ($retryCounts[$key] -le 2) {
                Log "Retry attempt $($retryCounts[$key]) for: $key"
                Invoke-Element $yes "Yes (retry)" | Out-Null
            } else {
                Log "Max retries reached - skipping: $key" "WARN"
                Invoke-Element $no "No (skip)" | Out-Null
            }
        } else {
            Log "Clicking Yes"
            Invoke-Element $yes "Yes" | Out-Null
        }
        Start-Sleep -Milliseconds 500
        continue
    }

    # OK button: only click if it belongs to a real MessageBox (#32770).
    # This prevents accidentally clicking OK in other windows (e.g. Windows Settings).
    $dlgHwnd = [Win32Helper]::FindWindow("#32770", $null)
    if ($dlgHwnd -ne [IntPtr]::Zero) {
        $okHwnd = [Win32Helper]::FindChildByText($dlgHwnd, "OK")
        if ($okHwnd -ne [IntPtr]::Zero) {
            $text = Get-AllVisibleText
            Log "OK dialog (MessageBox): $text" "WARN"
            [Win32Helper]::Click($okHwnd)
            Log "Clicked OK"
            Start-Sleep -Milliseconds 500
            continue
        }
    }

    Start-Sleep -Seconds 1
}

if (-not $done) {
    Log "TIMEOUT: installation did not finish within 30 minutes" "ERROR"
}

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

Log "=== Verifying installation ==="

$wspExe = "$env:LOCALAPPDATA\SpeechRecognitionProgram\wsp.exe"
if (Test-Path $wspExe) {
    Log "PASS: wsp.exe found at $wspExe"
} else {
    Log "FAIL: wsp.exe NOT found at $wspExe" "ERROR"
}

$cfg = "$env:LOCALAPPDATA\SpeechRecognitionProgram\config.json"
if (Test-Path $cfg) {
    Log "PASS: config.json found"
    Log "      $(Get-Content $cfg -Raw -Encoding UTF8)"
} else {
    Log "FAIL: config.json NOT found" "ERROR"
}

$shortcut = "$env:USERPROFILE\Desktop\Speech Recognition Program.lnk"
if (Test-Path $shortcut) {
    Log "PASS: Desktop shortcut created"
} else {
    Log "FAIL: Desktop shortcut missing" "ERROR"
}

Log "=== Done. Errors: $ErrorCount ==="
exit $ErrorCount
