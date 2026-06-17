#Requires -Version 5.1
# Automates the WSP Inno Setup installer wizard using UI Automation + Win32 API.
# Run on the VM after wsp_setup*.exe is present on the Desktop or shared folder.
# Writes a full log to Desktop\wsp_install_log.txt.
# ASCII-only: no em-dashes or box-drawing chars.

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# ---------------------------------------------------------------------------
# Win32 helpers.
# ---------------------------------------------------------------------------
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Win32Helper {
    public delegate bool EnumWinProc(IntPtr hwnd, IntPtr lp);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWinProc fn, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern bool EnumChildWindows(IntPtr parent, EnumWinProc fn, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hwnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hwnd, StringBuilder sb, int n);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetClassName(IntPtr hwnd, StringBuilder sb, int n);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hwnd, uint msg, IntPtr wp, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern uint GetWindowLong(IntPtr hwnd, int nIndex);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern IntPtr FindWindow(string cls, string title);

    [DllImport("user32.dll")]
    public static extern IntPtr GetAncestor(IntPtr hwnd, uint gaFlags);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hwnd);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint flags, int dx, int dy, uint data, IntPtr extra);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hwnd, uint msg, IntPtr wp, IntPtr lp);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hwnd, int nCmdShow);

    [DllImport("kernel32.dll")]
    public static extern IntPtr GetConsoleWindow();

    public const uint GA_ROOT             = 2;
    public const uint BM_CLICK            = 0x00F5;
    public const uint WM_LBUTTONDOWN      = 0x0201;
    public const uint WM_LBUTTONUP        = 0x0202;
    public const uint MK_LBUTTON          = 0x0001;
    public const int  GWL_STYLE           = -16;
    public const int  SW_MINIMIZE         = 6;
    public const int  SW_RESTORE          = 9;
    public const uint BS_TYPEMASK         = 0x0000000F;
    public const uint BS_RADIOBUTTON      = 0x00000004;
    public const uint BS_AUTORADIOBUTTON  = 0x00000009;
    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP   = 0x0004;

    public static IntPtr FindWindowByTitle(string part) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((hwnd, lp) => {
            if (!IsWindowVisible(hwnd)) return true;
            var sb = new StringBuilder(512);
            GetWindowText(hwnd, sb, 512);
            if (sb.ToString().IndexOf(part, StringComparison.OrdinalIgnoreCase) >= 0) {
                found = hwnd; return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static IntPtr FindChildByText(IntPtr parent, string text) {
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(parent, (hwnd, lp) => {
            var sb = new StringBuilder(512);
            GetWindowText(hwnd, sb, 512);
            if (sb.ToString().IndexOf(text, StringComparison.OrdinalIgnoreCase) >= 0) {
                found = hwnd; return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static IntPtr FindChildByClass(IntPtr parent, string cls) {
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(parent, (hwnd, lp) => {
            var sb = new StringBuilder(256);
            GetClassName(hwnd, sb, 256);
            if (sb.ToString().Equals(cls, StringComparison.OrdinalIgnoreCase)) {
                found = hwnd; return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    // Find the Nth radio button (0-indexed) among VISIBLE descendants only.
    // IsWindowVisible checks the entire ancestor chain, so controls on hidden
    // pages (whose Surface has WS_VISIBLE cleared) are excluded automatically.
    // This ensures index 0 == first radio on the CURRENT page.
    public static IntPtr FindVisibleRadioByIndex(IntPtr parent, int index) {
        int[] cnt = { 0 };
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(parent, (hwnd, lp) => {
            if (!IsWindowVisible(hwnd)) return true;
            uint t = GetWindowLong(hwnd, GWL_STYLE) & BS_TYPEMASK;
            if (t == BS_RADIOBUTTON || t == BS_AUTORADIOBUTTON) {
                if (cnt[0] == index) { found = hwnd; return false; }
                cnt[0]++;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    // Count all radio buttons (any visibility) for diagnostics.
    public static int CountAllRadios(IntPtr parent) {
        int[] cnt = { 0 };
        EnumChildWindows(parent, (hwnd, lp) => {
            uint t = GetWindowLong(hwnd, GWL_STYLE) & BS_TYPEMASK;
            if (t == BS_RADIOBUTTON || t == BS_AUTORADIOBUTTON) cnt[0]++;
            return true;
        }, IntPtr.Zero);
        return cnt[0];
    }

    // Count visible radio buttons for diagnostics.
    public static int CountVisibleRadios(IntPtr parent) {
        int[] cnt = { 0 };
        EnumChildWindows(parent, (hwnd, lp) => {
            if (!IsWindowVisible(hwnd)) return true;
            uint t = GetWindowLong(hwnd, GWL_STYLE) & BS_TYPEMASK;
            if (t == BS_RADIOBUTTON || t == BS_AUTORADIOBUTTON) cnt[0]++;
            return true;
        }, IntPtr.Zero);
        return cnt[0];
    }

    // Return details about every control found by the BS_AUTORADIOBUTTON scan.
    public static string[] ListRadioCandidates(IntPtr parent) {
        var list = new System.Collections.Generic.List<string>();
        EnumChildWindows(parent, (hwnd, lp) => {
            uint sty = GetWindowLong(hwnd, GWL_STYLE);
            uint t   = sty & BS_TYPEMASK;
            if (t == BS_RADIOBUTTON || t == BS_AUTORADIOBUTTON) {
                var cls = new StringBuilder(256);
                var txt = new StringBuilder(256);
                GetClassName(hwnd, cls, 256);
                GetWindowText(hwnd, txt, 256);
                RECT r; GetWindowRect(hwnd, out r);
                bool vis = IsWindowVisible(hwnd);
                list.Add(String.Format(
                    "HWND=0x{0:X} cls={1} txt='{2}' vis={3} sty=0x{4:X} rect={5},{6},{7},{8}",
                    hwnd.ToInt64(), cls, txt, vis, sty,
                    r.Left, r.Top, r.Right, r.Bottom));
            }
            return true;
        }, IntPtr.Zero);
        return list.ToArray();
    }

    // Return unique class names of all descendant windows.
    public static string[] ListUniqueClasses(IntPtr parent) {
        var set = new System.Collections.Generic.HashSet<string>();
        EnumChildWindows(parent, (hwnd, lp) => {
            var cls = new StringBuilder(256);
            GetClassName(hwnd, cls, 256);
            set.Add(cls.ToString());
            return true;
        }, IntPtr.Zero);
        var list = new System.Collections.Generic.List<string>(set);
        list.Sort();
        return list.ToArray();
    }

    // Find Nth radio button regardless of visibility (all pages).
    public static IntPtr FindRadioByIndex(IntPtr parent, int index) {
        int[] cnt = { 0 };
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(parent, (hwnd, lp) => {
            uint t = GetWindowLong(hwnd, GWL_STYLE) & BS_TYPEMASK;
            if (t == BS_RADIOBUTTON || t == BS_AUTORADIOBUTTON) {
                if (cnt[0] == index) { found = hwnd; return false; }
                cnt[0]++;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    // Find all children whose Win32 class name matches cls.
    public static IntPtr[] FindAllByClass(IntPtr parent, string cls) {
        var list = new System.Collections.Generic.List<IntPtr>();
        EnumChildWindows(parent, (hwnd, lp) => {
            var sb = new StringBuilder(256);
            GetClassName(hwnd, sb, 256);
            if (sb.ToString().Equals(cls, StringComparison.OrdinalIgnoreCase))
                list.Add(hwnd);
            return true;
        }, IntPtr.Zero);
        return list.ToArray();
    }

    // Post WM_LBUTTONDOWN/UP directly to the control HWND.
    // Bypasses foreground/z-order requirements entirely.
    public static void PostClick(IntPtr hwnd) {
        RECT r;
        int cx = 5, cy = 5;
        if (GetWindowRect(hwnd, out r)) { cx = (r.Right - r.Left) / 2; cy = (r.Bottom - r.Top) / 2; }
        IntPtr lp = (IntPtr)(((cy & 0xFFFF) << 16) | (cx & 0xFFFF));
        PostMessage(hwnd, WM_LBUTTONDOWN, (IntPtr)MK_LBUTTON, lp);
        System.Threading.Thread.Sleep(60);
        PostMessage(hwnd, WM_LBUTTONUP, IntPtr.Zero, lp);
    }

    // Click the control's centre using the real mouse.
    // Minimises the console window first so clicks land on the installer,
    // then restores it after the click.
    public static void ClickCenter(IntPtr hwnd) {
        RECT r;
        if (!GetWindowRect(hwnd, out r)) return;

        IntPtr console = GetConsoleWindow();
        if (console != IntPtr.Zero) ShowWindow(console, SW_MINIMIZE);
        System.Threading.Thread.Sleep(250);

        IntPtr root = GetAncestor(hwnd, GA_ROOT);
        if (root == IntPtr.Zero) root = hwnd;
        for (int i = 0; i < 6; i++) {
            SetForegroundWindow(root);
            System.Threading.Thread.Sleep(80);
            if (GetForegroundWindow() == root) break;
        }

        int x = r.Left + (r.Right  - r.Left) / 2;
        int y = r.Top  + (r.Bottom - r.Top)  / 2;
        SetCursorPos(x, y);
        System.Threading.Thread.Sleep(120);
        mouse_event(MOUSEEVENTF_LEFTDOWN, x, y, 0, IntPtr.Zero);
        System.Threading.Thread.Sleep(80);
        mouse_event(MOUSEEVENTF_LEFTUP,   x, y, 0, IntPtr.Zero);
        System.Threading.Thread.Sleep(120);

        if (console != IntPtr.Zero) ShowWindow(console, SW_RESTORE);
    }

    // Click at an offset within hwnd using the real mouse (console minimised).
    public static void MouseClickOffset(IntPtr hwnd, int offsetX, int offsetY) {
        RECT r;
        if (!GetWindowRect(hwnd, out r)) return;

        IntPtr console = GetConsoleWindow();
        if (console != IntPtr.Zero) ShowWindow(console, SW_MINIMIZE);
        System.Threading.Thread.Sleep(250);

        IntPtr root = GetAncestor(hwnd, GA_ROOT);
        if (root == IntPtr.Zero) root = hwnd;
        for (int i = 0; i < 6; i++) {
            SetForegroundWindow(root);
            System.Threading.Thread.Sleep(80);
            if (GetForegroundWindow() == root) break;
        }

        int x = r.Left + offsetX;
        int y = r.Top  + offsetY;
        SetCursorPos(x, y);
        System.Threading.Thread.Sleep(120);
        mouse_event(MOUSEEVENTF_LEFTDOWN, x, y, 0, IntPtr.Zero);
        System.Threading.Thread.Sleep(80);
        mouse_event(MOUSEEVENTF_LEFTUP,   x, y, 0, IntPtr.Zero);
        System.Threading.Thread.Sleep(120);

        if (console != IntPtr.Zero) ShowWindow(console, SW_RESTORE);
    }

    public static void Click(IntPtr hwnd) {
        SendMessage(hwnd, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
    }

    public static string[] ListChildClasses(IntPtr parent) {
        var list = new System.Collections.Generic.List<string>();
        EnumChildWindows(parent, (hwnd, lp) => {
            var cls = new StringBuilder(256);
            var txt = new StringBuilder(256);
            GetClassName(hwnd, cls, 256);
            GetWindowText(hwnd, txt, 256);
            list.Add(cls.ToString() + "|" + txt.ToString());
            return true;
        }, IntPtr.Zero);
        return list.ToArray();
    }
}
"@

$LogFile    = "$env:USERPROFILE\Desktop\wsp_install_log.txt"
$ShareLog   = "\\vmware-host\Shared Folders\wsp_tools\install_progress.txt"
$ErrorCount = 0

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
        # IgnoreCase: covers installers where button name casing differs from Default.isl
        $nc = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty, $name,
            [System.Windows.Automation.PropertyConditionFlags]::IgnoreCase)
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

# Dump all UIA button elements visible anywhere on the desktop.
function Dump-UIAButtons {
    $type = [System.Windows.Automation.ControlType]::Button
    $tc   = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty, $type)
    $found = $false
    foreach ($b in (Get-Root).FindAll([System.Windows.Automation.TreeScope]::Descendants, $tc)) {
        try {
            $n = $b.Current.Name; $en = $b.Current.IsEnabled
            Log "  [DIAG-BTN] name='$n' enabled=$en"
            $found = $true
        } catch {}
    }
    if (-not $found) { Log "  [DIAG-BTN] No UIA buttons found on desktop" }
}

# Click the Next button via Win32 BM_CLICK on the installer HWND (fallback).
function Click-NextWin32 {
    param([string]$label = "Next")
    $hwnd = Get-InstallerHwnd
    if ($hwnd -eq [IntPtr]::Zero) {
        Log "  [W32] Installer window not found" "WARN"
        return $false
    }
    $btn = [Win32Helper]::FindChildByText($hwnd, $label)
    if ($btn -eq [IntPtr]::Zero) {
        Log "  [W32] '$label' child not found in HWND=$hwnd" "WARN"
        return $false
    }
    [Win32Helper]::Click($btn)
    Log "  [W32] BM_CLICK on '$label' HWND=$btn"
    Start-Sleep -Milliseconds 800
    return $true
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

function Get-InstallerHwnd {
    $hwnd = [Win32Helper]::FindWindowByTitle("Speech Recognition Program")
    if ($hwnd -ne [IntPtr]::Zero) { return $hwnd }
    return [Win32Helper]::FindWindowByTitle("Setup")
}

# ---------------------------------------------------------------------------
# Click-RadioIndexW32
# Strategy 1: find by class name "TNewRadioButton" (Inno Setup custom class).
# Strategy 2: find by BS_AUTORADIOBUTTON style (visible-only filter).
# Strategy 3: find by BS_AUTORADIOBUTTON style (any visibility).
# Each HWND found is clicked via PostClick then ClickCenter (console min'd).
# One-time diagnostic dump of child classes and radio candidates on first call.
# ---------------------------------------------------------------------------
function Click-RadioIndexW32 {
    param([int]$index = 0, [int]$timeoutSec = 20)
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    $dumped   = $false

    while ((Get-Date) -lt $deadline) {
        $hwnd = Get-InstallerHwnd
        if ($hwnd -ne [IntPtr]::Zero) {

            # One-time diagnostic dump
            if (-not $dumped) {
                $dumped = $true
                Log "  [dump] Unique child classes:"
                foreach ($c in [Win32Helper]::ListUniqueClasses($hwnd)) {
                    Log "    $c"
                }
                Log "  [dump] BS_AUTORADIOBUTTON candidates:"
                foreach ($c in [Win32Helper]::ListRadioCandidates($hwnd)) {
                    Log "    $c"
                }
            }

            # Strategy 1: class name "TNewRadioButton" (Inno Setup's actual class)
            $allRB = [Win32Helper]::FindAllByClass($hwnd, "TNewRadioButton")
            if ($allRB.Length -gt $index) {
                $ctrl = $allRB[$index]
                Log "  [S1] TNewRadioButton[$index] HWND=$ctrl vis=$([Win32Helper]::IsWindowVisible($ctrl))"
                [Win32Helper]::PostClick($ctrl)
                Start-Sleep -Milliseconds 400
                [Win32Helper]::ClickCenter($ctrl)
                Start-Sleep -Milliseconds 400
                Log "radio[$index] S1=TNewRadioButton HWND=$ctrl"
                return $true
            }

            # Strategy 2: visible radio by BS_AUTORADIOBUTTON
            $ctrl2 = [Win32Helper]::FindVisibleRadioByIndex($hwnd, $index)
            if ($ctrl2 -ne [IntPtr]::Zero) {
                Log "  [S2] visible BS_AUTORADIOBUTTON[$index] HWND=$ctrl2"
                [Win32Helper]::PostClick($ctrl2)
                Start-Sleep -Milliseconds 400
                [Win32Helper]::ClickCenter($ctrl2)
                Start-Sleep -Milliseconds 400
                Log "radio[$index] S2=VisibleBSAuto HWND=$ctrl2"
                return $true
            }

            # Strategy 3: any radio by BS_AUTORADIOBUTTON (all pages)
            $ctrl3 = [Win32Helper]::FindRadioByIndex($hwnd, $index)
            if ($ctrl3 -ne [IntPtr]::Zero) {
                $total   = [Win32Helper]::CountAllRadios($hwnd)
                $visible = [Win32Helper]::CountVisibleRadios($hwnd)
                Log "  [S3] BS_AUTORADIOBUTTON[$index] total=$total vis=$visible HWND=$ctrl3"
                [Win32Helper]::PostClick($ctrl3)
                Start-Sleep -Milliseconds 400
                [Win32Helper]::ClickCenter($ctrl3)
                Start-Sleep -Milliseconds 400
                Log "radio[$index] S3=AnyBSAuto HWND=$ctrl3"
                return $true
            }

            Log "  [diag] index $index not found by any strategy yet"
        }
        Start-Sleep -Milliseconds 400
    }
    Log "Radio[$index] not found after ${timeoutSec}s" "WARN"
    return $false
}

# ---------------------------------------------------------------------------
# Click-TaskCheckbox
# TNewCheckListBox is custom-drawn; use real mouse at the checkbox offset.
# Console is minimised before clicking so it does not intercept the event.
# ---------------------------------------------------------------------------
function Click-TaskCheckbox {
    param([int]$itemIndex = 0, [int]$timeoutSec = 20)
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    $classes  = @("TNewCheckListBox","ListBox","SysListView32","TListBox")

    while ((Get-Date) -lt $deadline) {
        $hwnd = Get-InstallerHwnd
        if ($hwnd -ne [IntPtr]::Zero) {
            foreach ($cls in $classes) {
                $listbox = [Win32Helper]::FindChildByClass($hwnd, $cls)
                if ($listbox -ne [IntPtr]::Zero) {
                    $offX = 8
                    $offY = 10 + ($itemIndex * 20)
                    [Win32Helper]::MouseClickOffset($listbox, $offX, $offY)
                    Log "Clicked task checkbox[$itemIndex] via mouse on '$cls' (offset $offX,$offY)"
                    Start-Sleep -Milliseconds 400
                    return $true
                }
            }
            Log "  [diag] task listbox not found yet; dumping child classes" "WARN"
            $entries = [Win32Helper]::ListChildClasses($hwnd)
            foreach ($e in ($entries | Sort-Object -Unique)) { Log "    child: $e" }
        }
        Start-Sleep -Milliseconds 400
    }
    Log "Task checkbox[$itemIndex] not found after ${timeoutSec}s" "WARN"
    return $false
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Log "=== WSP Installer Automation Started ==="
Log "Host: $env:COMPUTERNAME  User: $env:USERNAME"

# Uninstall any existing WSP installation so the wizard shows from the beginning.
$wspExe    = "$env:LOCALAPPDATA\SpeechRecognitionProgram\wsp.exe"
$uninstExe = "$env:LOCALAPPDATA\SpeechRecognitionProgram\unins000.exe"
if (Test-Path $wspExe) {
    Log "WSP already installed - uninstalling silently..."
    if (Test-Path $uninstExe) {
        Start-Process $uninstExe -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES" -Wait
        Start-Sleep -Seconds 3
        Log "Uninstall finished"
    } else {
        Log "Uninstaller not found - cannot proceed" "ERROR"
        exit 1
    }
}

# Find installer executable
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
# /model and /licence are custom params read by InitializeWizard() in the ISS script.
# /TASKS is built into Inno Setup and pre-checks the named task checkbox.
Start-Process $installer.FullName -ArgumentList '/model=tiny /licence=accept /TASKS="desktopicon"'
Start-Sleep -Seconds 4

function Click-PageNext {
    param([string]$page, [int]$timeoutSec = 300, [string]$label = "Next")
    Log "--- $page ---"
    Start-Sleep -Seconds 2
    # Quick probe: log installer window state and UIA buttons after 5s if not found
    $quick = Find-ByName $label "Button" 5
    if (-not $quick) {
        $hwnd = Get-InstallerHwnd
        if ($hwnd -eq [IntPtr]::Zero) {
            Log "  [DIAG] Installer window NOT found - wizard may have closed" "WARN"
        } else {
            Log "  [DIAG] Installer HWND=$hwnd"
        }
        Dump-UIAButtons
        # Win32 fallback: BM_CLICK directly on the button HWND
        if (Click-NextWin32 $label) {
            return $true
        }
    } else {
        return Invoke-Element $quick $label
    }
    # Still not found - wait full timeout using UIA
    Log "  [DIAG] Waiting for '$label' up to ${timeoutSec}s..."
    $el = Find-ByName $label "Button" $timeoutSec
    if (-not $el) {
        Log "Button '$label' not found after ${timeoutSec}s on '$page'" "ERROR"
        return $false
    }
    return Invoke-Element $el $label
}

# Page 1: Welcome (allow up to 10 min for 1.6 GB installer to extract to temp dir)
if (-not (Click-PageNext "Page 1: Welcome" 600)) { Log "Aborting" "ERROR"; exit 1 }

# Page 2: HuggingFace Licence (Accept pre-selected via /licence=accept)
if (-not (Click-PageNext "Page 2: HuggingFace Licence (Accept pre-selected)")) { Log "Aborting" "ERROR"; exit 1 }

# Page 3: Install Directory
if (-not (Click-PageNext "Page 3: Install Directory (default path)")) { Log "Aborting" "ERROR"; exit 1 }

# Page 4: Whisper Model (Tiny pre-selected via /model=tiny)
if (-not (Click-PageNext "Page 4: Whisper Model (Tiny pre-selected)")) { Log "Aborting" "ERROR"; exit 1 }

# Page 5: Additional Tasks (desktopicon pre-checked via /TASKS="desktopicon")
if (-not (Click-PageNext "Page 5: Additional Tasks (desktop icon pre-checked)")) { Log "Aborting" "ERROR"; exit 1 }

# Page 6: Ready to Install
if (-not (Click-PageNext "Page 6: Ready to Install" 30 "Install")) { Log "Aborting" "ERROR"; exit 1 }

# ---------------------------------------------------------------------------
# Dialog loop: VLC + model downloads (up to 30 min)
# ---------------------------------------------------------------------------
Log "--- Waiting for downloads and installation (up to 60 min) ---"

$retryCounts = @{}
$deadline    = (Get-Date).AddMinutes(60)
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
        if ($text -match "Exit Setup|exit now|installation will not") {
            Log "Detected Exit Setup dialog - clicking No to stay"
            Invoke-Element $no "No (stay in installer)" | Out-Null
        } elseif ($text -match "VLC media player|VLC") {
            # Skip VLC download - it is not needed to validate the installer.
            # Clicking No shows an informational MB_OK which the OK handler will dismiss.
            Log "VLC prompt - clicking No (skip VLC)"
            Invoke-Element $no "No (skip VLC)" | Out-Null
        } elseif ($text -match "retry|Retry") {
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

$wspExe2 = "$env:LOCALAPPDATA\SpeechRecognitionProgram\wsp.exe"
if (Test-Path $wspExe2) {
    Log "PASS: wsp.exe found at $wspExe2"
} else {
    Log "FAIL: wsp.exe NOT found at $wspExe2" "ERROR"
}

$cfg = "$env:LOCALAPPDATA\SpeechRecognitionProgram\config.json"
if (Test-Path $cfg) {
    Log "PASS: config.json found"
    $cfgRaw = Get-Content $cfg -Raw -Encoding UTF8
    Log "      $cfgRaw"
    try {
        $cfgObj = $cfgRaw | ConvertFrom-Json
        # CHK-123: whisper_model
        if ($cfgObj.whisper_model -eq "tiny") {
            Log "PASS: whisper_model = 'tiny'"
        } else {
            Log "FAIL: whisper_model = '$($cfgObj.whisper_model)' (expected 'tiny')" "ERROR"
        }
        # CHK-124: licence_accepted
        if ($cfgObj.licence_accepted -eq $true) {
            Log "PASS: licence_accepted = true"
        } else {
            Log "FAIL: licence_accepted = '$($cfgObj.licence_accepted)' (expected true)" "ERROR"
        }
    } catch {
        Log "FAIL: could not parse config.json: $_" "ERROR"
    }
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
