$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "          REVTRACE STARTUP                  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# FIND PROJECT FOLDERS
# ------------------------------------------------------------

function Find-Folder {
    param(
        [string[]]$Candidates
    )

    foreach ($candidate in $Candidates) {

        $fullPath = Join-Path $ROOT $candidate

        if (Test-Path $fullPath) {
            return $fullPath
        }
    }

    return $null
}


$CORE = Find-Folder @(
    "revtrace-core"
)

$PROSPECTING = Find-Folder @(
    "revtrace-prospecting"
)

$DEAL_DESK = Find-Folder @(
    "deal-desk",
    "Build-desk\Build-desk"
)

$PROPOSAL = Find-Folder @(
    "proposal-rfp",
    "pbst\pbst"
)

$DASHBOARD = Find-Folder @(
    "dashboard",
    "revtrace-dashboard-v2\revtrace-frontend-main"
)


# ------------------------------------------------------------
# VERIFY FOLDERS
# ------------------------------------------------------------

$missing = $false

if (-not $CORE) {
    Write-Host "ERROR: RevTrace Core folder not found." -ForegroundColor Red
    $missing = $true
}

if (-not $PROSPECTING) {
    Write-Host "ERROR: Prospecting folder not found." -ForegroundColor Red
    $missing = $true
}

if (-not $DEAL_DESK) {
    Write-Host "ERROR: Deal Desk folder not found." -ForegroundColor Red
    $missing = $true
}

if (-not $PROPOSAL) {
    Write-Host "ERROR: Proposal / RFP folder not found." -ForegroundColor Red
    $missing = $true
}

if (-not $DASHBOARD) {
    Write-Host "ERROR: Dashboard folder not found." -ForegroundColor Red
    $missing = $true
}

if ($missing) {

    Write-Host ""
    Write-Host "Fix the folder names and run this script again." -ForegroundColor Yellow

    Read-Host "Press Enter to exit"

    exit
}


Write-Host "Project folders detected:" -ForegroundColor Green

Write-Host "Core        : $CORE"
Write-Host "Prospecting : $PROSPECTING"
Write-Host "Deal Desk   : $DEAL_DESK"
Write-Host "Proposal    : $PROPOSAL"
Write-Host "Dashboard   : $DASHBOARD"

Write-Host ""


# ------------------------------------------------------------
# CREATE LOG DIRECTORY
# ------------------------------------------------------------

$LOG_DIR = Join-Path $ROOT "logs"

if (-not (Test-Path $LOG_DIR)) {
    New-Item `
        -ItemType Directory `
        -Path $LOG_DIR `
        | Out-Null
}


# ------------------------------------------------------------
# CHECK PORT
# ------------------------------------------------------------

function Test-Port {
    param(
        [int]$Port
    )

    $result = Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue

    return ($null -ne $result)
}


# ------------------------------------------------------------
# START PYTHON SERVICE
# ------------------------------------------------------------

function Start-PythonService {

    param(
        [string]$Name,
        [string]$Directory,
        [string[]]$Arguments,
        [int]$Port
    )

    if (Test-Port $Port) {

        Write-Host "$Name already running on port $Port" -ForegroundColor Yellow

        return
    }

    Write-Host "Starting $Name..." -ForegroundColor Cyan

    $outputLog = Join-Path $LOG_DIR "$Name-output.log"
    $errorLog = Join-Path $LOG_DIR "$Name-error.log"

    Start-Process `
        -FilePath "python" `
        -ArgumentList $Arguments `
        -WorkingDirectory $Directory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outputLog `
        -RedirectStandardError $errorLog

    Start-Sleep -Seconds 2

    Write-Host "$Name started." -ForegroundColor Green
}


# ------------------------------------------------------------
# START NODE SERVICE
# ------------------------------------------------------------

function Start-NodeService {

    param(
        [string]$Name,
        [string]$Directory,
        [int]$Port
    )

    if (Test-Port $Port) {

        Write-Host "$Name already running on port $Port" -ForegroundColor Yellow

        return
    }

    Write-Host "Starting $Name..." -ForegroundColor Cyan

    $outputLog = Join-Path $LOG_DIR "$Name-output.log"
    $errorLog = Join-Path $LOG_DIR "$Name-error.log"

    Start-Process `
        -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm.cmd run dev" `
        -WorkingDirectory $Directory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outputLog `
        -RedirectStandardError $errorLog

    Start-Sleep -Seconds 2

    Write-Host "$Name started." -ForegroundColor Green
}


# ============================================================
# 1. REVTRACE CORE
# ============================================================

Start-PythonService `
    -Name "core" `
    -Directory $CORE `
    -Arguments @(
        "-m",
        "uvicorn",
        "main:app",
        "--port",
        "8100"
    ) `
    -Port 8100


# ============================================================
# 2. PROSPECTING BACKEND
# ============================================================

Start-PythonService `
    -Name "prospecting-backend" `
    -Directory $PROSPECTING `
    -Arguments @(
        "-m",
        "uvicorn",
        "backend.main:app",
        "--port",
        "8000"
    ) `
    -Port 8000


# ============================================================
# 3. PROSPECTING UI
# ============================================================

Start-PythonService `
    -Name "prospecting-ui" `
    -Directory $PROSPECTING `
    -Arguments @(
        "-m",
        "streamlit",
        "run",
        "frontend.py",
        "--server.port",
        "8501",
        "--server.headless",
        "true"
    ) `
    -Port 8501


# ============================================================
# 4. DEAL DESK
# ============================================================

Start-NodeService `
    -Name "deal-desk" `
    -Directory $DEAL_DESK `
    -Port 3000


# ============================================================
# 5. PROPOSAL / RFP
# ============================================================

Start-PythonService `
    -Name "proposal-rfp" `
    -Directory $PROPOSAL `
    -Arguments @(
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        "8502",
        "--server.headless",
        "true"
    ) `
    -Port 8502


# ============================================================
# 6. DASHBOARD
# ============================================================

Start-NodeService `
    -Name "dashboard" `
    -Directory $DASHBOARD `
    -Port 5173


# ------------------------------------------------------------
# WAIT FOR SERVICES
# ------------------------------------------------------------

Write-Host ""
Write-Host "Waiting for RevTrace services..." -ForegroundColor Cyan

Start-Sleep -Seconds 8


# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "            SERVICE STATUS                  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan


$services = @(
    @{ Name = "RevTrace Core"; Port = 8100 },
    @{ Name = "Prospecting Backend"; Port = 8000 },
    @{ Name = "Prospecting UI"; Port = 8501 },
    @{ Name = "Deal Desk"; Port = 3000 },
    @{ Name = "Proposal / RFP"; Port = 8502 },
    @{ Name = "Dashboard"; Port = 5173 }
)


foreach ($service in $services) {

    if (Test-Port $service.Port) {

        Write-Host `
            "[RUNNING] $($service.Name) - Port $($service.Port)" `
            -ForegroundColor Green

    }
    else {

        Write-Host `
            "[FAILED]  $($service.Name) - Port $($service.Port)" `
            -ForegroundColor Red
    }
}


# ------------------------------------------------------------
# URLS
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "                 URLS                       " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "Core                 http://localhost:8100"
Write-Host "Prospecting Backend  http://localhost:8000"
Write-Host "Prospecting           http://localhost:8501"
Write-Host "Deal Desk             http://localhost:3000"
Write-Host "Proposal / RFP        http://localhost:8502"
Write-Host "Dashboard             http://localhost:5173"

Write-Host ""
Write-Host "Logs are available at:" -ForegroundColor DarkGray
Write-Host $LOG_DIR -ForegroundColor DarkGray


# ------------------------------------------------------------
# OPEN DASHBOARD
# ------------------------------------------------------------

if (Test-Port 5173) {

    Write-Host ""
    Write-Host "Opening RevTrace Dashboard..." -ForegroundColor Green

    Start-Process "http://localhost:5173"
}


Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "REVTRACE IS READY" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "You can close this launcher window."
Write-Host "The RevTrace services will continue running."
Write-Host ""