#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs
)

$ErrorActionPreference = 'Stop'

# Ensure TLS 1.2+ for any HTTPS downloads on Windows PowerShell 5.1
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
} catch {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$VenvDir = Join-Path $ProjectRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$ReqFile = Join-Path $ProjectRoot 'requirements.txt'
$ReqHashFile = Join-Path $VenvDir '.requirements.sha256'
$PkgJsonFile = Join-Path $ProjectRoot 'package.json'
$PkgLockFile = Join-Path $ProjectRoot 'package-lock.json'
$NodeModulesDir = Join-Path $ProjectRoot 'node_modules'
$PkgHashFile = Join-Path $NodeModulesDir '.package.sha256'
$SetupStateFile = Join-Path $VenvDir '.setup_state.json'

# Parse CLI flags (supports both --flag and -Flag styles)
$Opt = @{
    InstallOnly  = $false
    Reinstall    = $false
    Check        = $false
    SkipOptional = $false
    InstallAll   = $false
    Shortcut     = $false
    Help         = $false
}

foreach ($arg in @($CliArgs)) {
    if ([string]::IsNullOrWhiteSpace($arg)) {
        continue
    }
    switch ($arg.ToLowerInvariant()) {
        '--install-only'  { $Opt.InstallOnly  = $true }
        '-installonly'    { $Opt.InstallOnly  = $true }
        '--reinstall'     { $Opt.Reinstall    = $true }
        '-reinstall'      { $Opt.Reinstall    = $true }
        '--check'         { $Opt.Check        = $true }
        '-check'          { $Opt.Check        = $true }
        '--skip-optional' { $Opt.SkipOptional = $true }
        '-skipoptional'   { $Opt.SkipOptional = $true }
        '--install-all'   { $Opt.InstallAll   = $true }
        '-installall'     { $Opt.InstallAll   = $true }
        '--shortcut'      { $Opt.Shortcut     = $true }
        '-shortcut'       { $Opt.Shortcut     = $true }
        '--help'          { $Opt.Help         = $true }
        '-help'           { $Opt.Help         = $true }
        '-h'              { $Opt.Help         = $true }
        '/?'              { $Opt.Help         = $true }
        default {
            Write-Host "[!] Unknown option: $arg" -ForegroundColor Yellow
            $Opt.Help = $true
        }
    }
}

function Write-Info($Message) {
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-Ok($Message) {
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-Warn($Message) {
    Write-Host "[!] $Message" -ForegroundColor Yellow
}

function Write-Err($Message) {
    Write-Host "[-] $Message" -ForegroundColor Red
}

function Show-Help {
    Write-Host ""
    Write-Host "MCPTool Windows One-Click Installer & Launcher" -ForegroundColor Cyan
    Write-Host "Usage: MCPTool.bat [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  (none)           Install missing dependencies if needed and launch MCPTool"
    Write-Host "  --check          Check installed runtimes and dependencies without modifying anything"
    Write-Host "  --install-only   Install/verify dependencies without launching MCPTool"
    Write-Host "  --install-all    Auto-install optional tools (Java 21, Nmap) without prompting"
    Write-Host "  --skip-optional  Skip optional tool prompts (Java, Nmap)"
    Write-Host "  --reinstall      Recreate .venv and reinstall Python & Node dependencies"
    Write-Host "  --shortcut       Create a Desktop shortcut for MCPTool.bat"
    Write-Host "  --help           Show this help message"
    Write-Host ""
}

function Refresh-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $combined = @($machinePath, $userPath) | Where-Object { $_ }
    $env:Path = ($combined -join ';')
}

function Add-ToSessionPath([string]$Dir) {
    if ([string]::IsNullOrWhiteSpace($Dir) -or -not (Test-Path -LiteralPath $Dir)) {
        return
    }
    $currentEntries = $env:Path -split ';' | Where-Object { $_ }
    if ($currentEntries -notcontains $Dir) {
        $env:Path = "$Dir;$env:Path"
    }
}

function Test-WingetAvailable {
    return [bool](Get-Command winget.exe -ErrorAction SilentlyContinue)
}

function Install-WingetPackage([string]$PackageId, [string]$DisplayName) {
    if (-not (Test-WingetAvailable)) {
        return $false
    }
    Write-Info "Installing $DisplayName via winget ($PackageId)..."
    & winget.exe install -e --id $PackageId --accept-package-agreements --accept-source-agreements
    $code = $LASTEXITCODE
    Refresh-SessionPath
    if ($code -eq 0) {
        Write-Ok "$DisplayName installed."
        return $true
    }
    Write-Warn "winget returned exit code $code for $DisplayName."
    return $false
}

function Test-PythonCandidate([string]$ExePath) {
    if ([string]::IsNullOrWhiteSpace($ExePath) -or -not (Test-Path -LiteralPath $ExePath)) {
        return $false
    }
    # Skip Microsoft Store execution alias stubs
    if ($ExePath -like '*\Microsoft\WindowsApps\*') {
        return $false
    }
    try {
        $null = & $ExePath -c "import sys, venv; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Find-SystemPython {
    $candidates = New-Object System.Collections.Generic.List[string]

    # 1. Python Launcher (py -3)
    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            $resolved = (& $pyLauncher.Source -3 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
            if ($LASTEXITCODE -eq 0 -and $resolved) {
                $candidates.Add($resolved.Trim())
            }
        } catch {}
    }

    # 2. PATH python / python3 (excluding .venv and WindowsApps)
    foreach ($cmdName in @('python', 'python3')) {
        $found = Get-Command $cmdName -All -ErrorAction SilentlyContinue
        foreach ($item in $found) {
            if ($item.Source -and ($item.Source -notlike "$VenvDir*")) {
                $candidates.Add($item.Source)
            }
        }
    }

    # 3. Standard Windows installation directories
    $searchGlobs = @(
        "$env:LocalAppData\Programs\Python\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe",
        'C:\Python3*\python.exe'
    )
    foreach ($glob in $searchGlobs) {
        $foundFiles = Get-ChildItem -Path $glob -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
        foreach ($file in $foundFiles) {
            $candidates.Add($file.FullName)
        }
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-PythonCandidate $candidate) {
            return $candidate
        }
    }

    return $null
}

function Install-PythonFallback {
    $installerUrl = 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe'
    $installerPath = Join-Path $env:TEMP 'mcptool-python-installer.exe'
    try {
        Write-Info "Downloading Python 3.12.8 installer from python.org..."
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        Write-Info "Running silent Python installation..."
        $proc = Start-Process -FilePath $installerPath -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_test=0' -Wait -PassThru
        Refresh-SessionPath
        return ($proc.ExitCode -eq 0)
    } catch {
        Write-Err "Python download/install failed: $($_.Exception.Message)"
        return $false
    } finally {
        if (Test-Path -LiteralPath $installerPath) {
            Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Find-NodeInfo {
    $nodeExe = $null
    $npmCmd = $null

    $nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($nodeCmd) {
        $nodeExe = $nodeCmd.Source
    } else {
        foreach ($dir in @("$env:ProgramFiles\nodejs", "${env:ProgramFiles(x86)}\nodejs")) {
            $candidate = Join-Path $dir 'node.exe'
            if (Test-Path -LiteralPath $candidate) {
                $nodeExe = $candidate
                Add-ToSessionPath $dir
                break
            }
        }
    }

    if ($nodeExe) {
        $nodeDir = Split-Path -Parent $nodeExe
        $localNpmCmd = Join-Path $nodeDir 'npm.cmd'
        if (Test-Path -LiteralPath $localNpmCmd) {
            $npmCmd = $localNpmCmd
        } else {
            $foundNpm = Get-Command npm.cmd -ErrorAction SilentlyContinue
            if (-not $foundNpm) {
                $foundNpm = Get-Command npm -ErrorAction SilentlyContinue
            }
            if ($foundNpm) {
                $npmCmd = $foundNpm.Source
            }
        }
    }

    return [PSCustomObject]@{
        Node = $nodeExe
        Npm  = $npmCmd
    }
}

function Install-NodeFallback {
    $msiPath = Join-Path $env:TEMP 'mcptool-nodejs-lts.msi'
    try {
        Write-Info "Fetching latest Node.js LTS version..."
        $releases = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json' -UseBasicParsing
        $lts = $releases | Where-Object { $_.lts } | Select-Object -First 1
        if (-not $lts) {
            return $false
        }
        $ver = $lts.version
        $arch = if ([Environment]::Is64BitOperatingSystem) { 'x64' } else { 'x86' }
        $msiUrl = "https://nodejs.org/dist/$ver/node-$ver-$arch.msi"
        Write-Info "Downloading Node.js $ver ($arch)..."
        Invoke-WebRequest -Uri $msiUrl -OutFile $msiPath -UseBasicParsing
        Write-Info "Installing Node.js $ver..."
        $proc = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/i', "`"$msiPath`"", '/qn', '/norestart' -Wait -PassThru
        Refresh-SessionPath
        return ($proc.ExitCode -eq 0)
    } catch {
        Write-Err "Node.js download/install failed: $($_.Exception.Message)"
        return $false
    } finally {
        if (Test-Path -LiteralPath $msiPath) {
            Remove-Item -LiteralPath $msiPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Find-JavaInfo {
    $javaExe = $null
    $cmd = Get-Command java.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $javaExe = $cmd.Source
    } else {
        $globs = @(
            "$env:ProgramFiles\Eclipse Adoptium\jdk-*\bin\java.exe",
            "$env:ProgramFiles\Microsoft\jdk-*\bin\java.exe",
            "$env:ProgramFiles\Java\jdk-*\bin\java.exe"
        )
        foreach ($glob in $globs) {
            $match = Get-ChildItem -Path $glob -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
            if ($match) {
                $javaExe = $match.FullName
                Add-ToSessionPath (Split-Path -Parent $javaExe)
                break
            }
        }
    }

    if (-not $javaExe) {
        return $null
    }

    $major = $null
    try {
        $verOutput = & cmd.exe /c "`"$javaExe`" -version 2>&1" | Out-String
        if ($verOutput -match 'version "(\d+)(?:\.(\d+))?') {
            $first = [int]$Matches[1]
            if ($first -eq 1 -and $Matches[2]) {
                $major = [int]$Matches[2]
            } else {
                $major = $first
            }
        }
    } catch {}

    return [PSCustomObject]@{
        Path  = $javaExe
        Major = $major
    }
}

function Install-JavaFallback {
    $msiPath = Join-Path $env:TEMP 'mcptool-temurin-21.msi'
    try {
        $url = 'https://api.adoptium.net/v3/installer/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse'
        Write-Info "Downloading Eclipse Temurin JDK 21..."
        Invoke-WebRequest -Uri $url -OutFile $msiPath -UseBasicParsing
        Write-Info "Installing Eclipse Temurin JDK 21..."
        $proc = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/i', "`"$msiPath`"", 'ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome', '/qn', '/norestart' -Wait -PassThru
        Refresh-SessionPath
        return ($proc.ExitCode -eq 0)
    } catch {
        Write-Err "Java download/install failed: $($_.Exception.Message)"
        return $false
    } finally {
        if (Test-Path -LiteralPath $msiPath) {
            Remove-Item -LiteralPath $msiPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Find-NmapPath {
    $cmd = Get-Command nmap.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    foreach ($dir in @("${env:ProgramFiles(x86)}\Nmap", "$env:ProgramFiles\Nmap")) {
        $candidate = Join-Path $dir 'nmap.exe'
        if (Test-Path -LiteralPath $candidate) {
            Add-ToSessionPath $dir
            return $candidate
        }
    }
    return $null
}

function Find-BundledOrPathTool([string]$ExeName) {
    $localPath = Join-Path $ProjectRoot $ExeName
    if (Test-Path -LiteralPath $localPath) {
        return $localPath
    }
    $cmd = Get-Command $ExeName -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    return $null
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Read-TrimmedFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return ''
    }
    $content = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) {
        return ''
    }
    return ([string]$content).Trim()
}

function Get-SetupState {
    if (Test-Path -LiteralPath $SetupStateFile) {
        try {
            return (Get-Content -LiteralPath $SetupStateFile -Raw -Encoding UTF8 | ConvertFrom-Json)
        } catch {}
    }
    return [PSCustomObject]@{
        skipJava = $false
        skipNmap = $false
    }
}

function Save-SetupState($State) {
    if (Test-Path -LiteralPath $VenvDir) {
        $State | ConvertTo-Json | Set-Content -LiteralPath $SetupStateFile -Encoding UTF8
    }
}

function Read-YesNo([string]$Prompt, [bool]$DefaultYes) {
    $suffix = if ($DefaultYes) { '[Y/n]' } else { '[y/N]' }
    $answer = Read-Host "$Prompt $suffix"
    if ([string]::IsNullOrWhiteSpace($answer)) {
        return $DefaultYes
    }
    return $answer.Trim().ToLowerInvariant() -in @('y', 'yes')
}

function Test-NodeModulesPopulated {
    if (-not (Test-Path -LiteralPath $PkgJsonFile) -or -not (Test-Path -LiteralPath $NodeModulesDir)) {
        return $false
    }
    try {
        $pkg = Get-Content -LiteralPath $PkgJsonFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $pkg.dependencies) {
            return $true
        }
        foreach ($prop in $pkg.dependencies.PSObject.Properties) {
            $depPath = Join-Path $NodeModulesDir $prop.Name
            if (-not (Test-Path -LiteralPath $depPath)) {
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

function New-DesktopShortcut {
    $desktopDir = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktopDir 'MCPTool.lnk'
    $batPath = Join-Path $ProjectRoot 'MCPTool.bat'

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $batPath
    $shortcut.WorkingDirectory = $ProjectRoot
    $shortcut.Description = 'MCPTool - Pentesting tool for Minecraft'
    $shortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
    $shortcut.Save()

    Write-Ok "Desktop shortcut created: $shortcutPath"
}

function Show-StatusReport {
    $sysPython = Find-SystemPython
    $nodeInfo = Find-NodeInfo
    $javaInfo = Find-JavaInfo
    $nmapPath = Find-NmapPath
    $ngrokPath = Find-BundledOrPathTool 'ngrok.exe'
    $masscanPath = Find-BundledOrPathTool 'masscan.exe'

    Write-Host ""
    Write-Host "=== MCPTool Environment Status ===" -ForegroundColor Cyan

    if ($sysPython) {
        $pyVer = (& $sysPython --version 2>&1) -join ' '
        Write-Ok "Python       : $pyVer ($sysPython)"
    } else {
        Write-Err "Python 3.9+  : Not found"
    }

    if (Test-Path -LiteralPath $VenvPython) {
        $reqHash = Get-FileSha256 $ReqFile
        $savedHash = Read-TrimmedFile $ReqHashFile
        if ($reqHash -eq $savedHash) {
            Write-Ok "VirtualEnv   : Ready (.venv, requirements up to date)"
        } else {
            Write-Warn "VirtualEnv   : Present (.venv), requirements need sync"
        }
    } else {
        Write-Warn "VirtualEnv   : Not created yet (.venv)"
    }

    if ($nodeInfo.Node -and $nodeInfo.Npm) {
        $nodeVer = (& $nodeInfo.Node --version 2>&1) -join ' '
        Write-Ok "Node.js      : $nodeVer ($($nodeInfo.Node))"
    } else {
        Write-Err "Node.js/npm  : Not found"
    }

    if (Test-NodeModulesPopulated) {
        Write-Ok "Node Modules : Installed"
    } else {
        Write-Warn "Node Modules : Missing or incomplete"
    }

    if ($javaInfo) {
        $majorText = if ($javaInfo.Major) { "Java $($javaInfo.Major)" } else { "Java" }
        if ($javaInfo.Major -and $javaInfo.Major -lt 21) {
            Write-Warn "Java (Opt.)  : $majorText ($($javaInfo.Path)) - Java 21+ recommended"
        } else {
            Write-Ok "Java (Opt.)  : $majorText ($($javaInfo.Path))"
        }
    } else {
        Write-Warn "Java (Opt.)  : Not found (needed for Waterfall/Velocity proxies & QuboScanner)"
    }

    if ($nmapPath) {
        Write-Ok "Nmap (Opt.)  : $nmapPath"
    } else {
        Write-Warn "Nmap (Opt.)  : Not found (optional scanner)"
    }

    if ($ngrokPath) {
        Write-Ok "Ngrok (Opt.) : $ngrokPath"
    } else {
        Write-Warn "Ngrok (Opt.) : Not found"
    }

    if ($masscanPath) {
        Write-Ok "Masscan      : $masscanPath"
    } else {
        Write-Warn "Masscan      : Not found"
    }
    Write-Host ""
}

# --- Main flow ---

if ($Opt.Help) {
    Show-Help
    exit 0
}

if ($Opt.Shortcut) {
    New-DesktopShortcut
    if (-not $Opt.InstallOnly -and -not $Opt.Check -and -not $Opt.Reinstall) {
        exit 0
    }
}

if ($Opt.Check) {
    Show-StatusReport
    exit 0
}

$FirstTimeVenv = -not (Test-Path -LiteralPath $VenvPython)

# 1. Ensure Python 3.9+
$SystemPython = Find-SystemPython
if (-not $SystemPython) {
    Write-Warn "Python 3.9+ was not found on your system."
    $installed = Install-WingetPackage -PackageId 'Python.Python.3.12' -DisplayName 'Python 3.12'
    if (-not $installed) {
        $installed = Install-PythonFallback
    }
    $SystemPython = Find-SystemPython
    if (-not $SystemPython) {
        Write-Err "Could not locate Python after installation. Please install Python 3.10+ from https://www.python.org/downloads/ (check 'Add Python to PATH') and try again."
        exit 1
    }
}

# 2. Ensure Node.js & npm
$NodeInfo = Find-NodeInfo
if (-not $NodeInfo.Node -or -not $NodeInfo.Npm) {
    Write-Warn "Node.js / npm was not found on your system."
    $installed = Install-WingetPackage -PackageId 'OpenJS.NodeJS.LTS' -DisplayName 'Node.js LTS'
    if (-not $installed) {
        $installed = Install-NodeFallback
    }
    $NodeInfo = Find-NodeInfo
    if (-not $NodeInfo.Node -or -not $NodeInfo.Npm) {
        Write-Err "Could not locate Node.js/npm after installation. Please install Node.js LTS from https://nodejs.org/ and try again."
        exit 1
    }
}

# 3. Create or recreate Python virtual environment (.venv)
if ($Opt.Reinstall -and (Test-Path -LiteralPath $VenvDir)) {
    Write-Info "Removing existing .venv for clean reinstall..."
    Remove-Item -LiteralPath $VenvDir -Recurse -Force
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Info "Creating Python virtual environment (.venv)..."
    & $SystemPython -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $VenvPython)) {
        Write-Err "Failed to create Python virtual environment at $VenvDir."
        exit 1
    }
    Write-Ok "Virtual environment created."
}

# 4. Install/sync Python requirements
if (Test-Path -LiteralPath $ReqFile) {
    $currentReqHash = Get-FileSha256 $ReqFile
    $savedReqHash = Read-TrimmedFile $ReqHashFile

    if ($Opt.Reinstall -or ($currentReqHash -ne $savedReqHash)) {
        Write-Info "Installing Python dependencies from requirements.txt..."
        & $VenvPython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "pip self-upgrade returned non-zero exit code; continuing with package installation..."
        }
        & $VenvPython -m pip install -r $ReqFile
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to install Python dependencies from requirements.txt."
            exit 1
        }
        Set-Content -LiteralPath $ReqHashFile -Value $currentReqHash -Encoding UTF8
        Write-Ok "Python dependencies installed."
    }
}

# 5. Install/sync Node.js dependencies
if (Test-Path -LiteralPath $PkgJsonFile) {
    $currentPkgHash = Get-FileSha256 $PkgJsonFile
    $savedPkgHash = Read-TrimmedFile $PkgHashFile
    $modulesOk = Test-NodeModulesPopulated

    if ($Opt.Reinstall -or (-not $modulesOk) -or ($savedPkgHash -and ($currentPkgHash -ne $savedPkgHash))) {
        Write-Info "Installing Node.js dependencies..."
        if ($Opt.Reinstall -and (Test-Path -LiteralPath $NodeModulesDir)) {
            Remove-Item -LiteralPath $NodeModulesDir -Recurse -Force
        }
        if (-not (Test-Path -LiteralPath $NodeModulesDir) -and (Test-Path -LiteralPath $PkgLockFile)) {
            & $NodeInfo.Npm ci --no-audit --no-fund
        } else {
            & $NodeInfo.Npm install --no-audit --no-fund
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to install Node.js dependencies."
            exit 1
        }
        if (Test-Path -LiteralPath $NodeModulesDir) {
            Set-Content -LiteralPath $PkgHashFile -Value $currentPkgHash -Encoding UTF8
        }
        Write-Ok "Node.js dependencies installed."
    } elseif (-not $savedPkgHash -and $modulesOk) {
        # Record hash for pre-existing node_modules so subsequent runs track package.json changes
        Set-Content -LiteralPath $PkgHashFile -Value $currentPkgHash -Encoding UTF8
    }
}

# 6. Optional dependencies (Java 21+, Nmap)
if (-not $Opt.SkipOptional) {
    $state = Get-SetupState
    $stateChanged = $false

    $javaInfo = Find-JavaInfo
    if (-not $javaInfo -and ($Opt.InstallAll -or $Opt.Reinstall -or -not $state.skipJava)) {
        $installJava = $Opt.InstallAll -or (Read-YesNo 'Java 21+ is recommended for Waterfall/Velocity proxies & QuboScanner. Install now?' $true)
        if ($installJava) {
            $ok = Install-WingetPackage -PackageId 'EclipseAdoptium.Temurin.21.JDK' -DisplayName 'Eclipse Temurin JDK 21'
            if (-not $ok) {
                $ok = Install-JavaFallback
            }
            $null = Find-JavaInfo
            if (-not $ok) {
                Write-Warn "Java installation did not complete. You can still use all non-proxy/non-Qubo features."
            }
        } else {
            $state.skipJava = $true
            $stateChanged = $true
        }
    }

    $nmapPath = Find-NmapPath
    if (-not $nmapPath -and ($Opt.InstallAll -or $Opt.Reinstall -or -not $state.skipNmap)) {
        $installNmap = $Opt.InstallAll -or (Read-YesNo 'Nmap is optional (used for Nmap port scanning). Install now?' $false)
        if ($installNmap) {
            $ok = Install-WingetPackage -PackageId 'Insecure.Nmap' -DisplayName 'Nmap'
            $null = Find-NmapPath
            if (-not $ok) {
                Write-Warn "Nmap installation did not complete. You can still use QuboScanner or Masscan."
            }
        } else {
            $state.skipNmap = $true
            $stateChanged = $true
        }
    }

    if ($stateChanged) {
        Save-SetupState $state
    }
} else {
    # Still refresh PATH with any standard locations for Java/Nmap if already installed
    $null = Find-JavaInfo
    $null = Find-NmapPath
}

if ($FirstTimeVenv -and -not $Opt.Shortcut) {
    Write-Info 'Tip: Run "MCPTool.bat --shortcut" anytime to create a Desktop shortcut.'
}

if ($Opt.InstallOnly) {
    Write-Ok "Setup complete. Double-click MCPTool.bat to launch."
    exit 0
}

# 7. Launch MCPTool using the isolated .venv Python with the refreshed session PATH
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

& $VenvPython (Join-Path $ProjectRoot 'main.py')
exit $LASTEXITCODE
