<# 
.SYNOPSIS
    Complete automated setup for AI Horror/Anime/Thriller YouTube Channel
    Run this AFTER adding API keys to .env and placing client_secret.json
#>

param(
    [switch]$SkipTests,
    [switch]$InstallScheduler
)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  AI HORROR CHANNEL - AUTOMATED SETUP" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectPath = "E:\ai-horror-channel"
Set-Location $ProjectPath

# ===========================================
# STEP 1: Verify Prerequisites
# ===========================================
Write-Host "[1/8] Checking prerequisites..." -ForegroundColor Yellow

$Checks = @{
    Python = (Get-Command python -ErrorAction SilentlyContinue)
    FFmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue)
    Node   = (Get-Command node -ErrorAction SilentlyContinue)
    Git    = (Get-Command git -ErrorAction SilentlyContinue)
}

$CheckNames = @("Python", "FFmpeg", "Node", "Git")
foreach ($check in $CheckNames) {
    if ($Checks[$check]) {
        Write-Host "  ✓ $check found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $check MISSING - install with: winget install $($check.ToLower())" -ForegroundColor Red
    }
}

# ===========================================
# STEP 2: Verify .env Configuration
# ===========================================
Write-Host ""
Write-Host "[2/8] Checking .env configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    $geminiOk = $envContent -match 'GEMINI_API_KEY=AIza'
    $pexelsOk = $envContent -match 'PEXELS_API_KEY=[A-Za-z0-9]'
    
    if ($geminiOk) { Write-Host "  ✓ GEMINI_API_KEY configured" -ForegroundColor Green }
    else { Write-Host "  ✗ GEMINI_API_KEY missing or invalid" -ForegroundColor Red }
    
    if ($pexelsOk) { Write-Host "  ✓ PEXELS_API_KEY configured" -ForegroundColor Green }
    else { Write-Host "  ✗ PEXELS_API_KEY missing" -ForegroundColor Red }
} else {
    Write-Host "  ✗ .env file not found" -ForegroundColor Red
}

# ===========================================
# STEP 3: Verify Google OAuth
# ===========================================
Write-Host ""
Write-Host "[3/8] Checking Google OAuth..." -ForegroundColor Yellow

if (Test-Path "client_secret.json") {
    Write-Host "  ✓ client_secret.json found" -ForegroundColor Green
    if (Test-Path "token.json") {
        Write-Host "  ✓ token.json exists (already authorized)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ token.json missing - run 'python authorize.py' after this" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ client_secret.json missing - download from Google Cloud Console" -ForegroundColor Red
}

# ===========================================
# STEP 4: Verify Assets
# ===========================================
Write-Host ""
Write-Host "[4/8] Checking assets..." -ForegroundColor Yellow

if (Test-Path "assets\background_music.mp3") {
    $size = (Get-Item "assets\background_music.mp3").Length
    Write-Host "  ✓ background_music.mp3 (${size} bytes)" -ForegroundColor Green
} else {
    Write-Host "  ✗ background_music.mp3 missing" -ForegroundColor Red
}

if (Test-Path "assets\font.ttf") {
    Write-Host "  ✓ font.ttf found" -ForegroundColor Green
} else {
    Write-Host "  ✗ font.ttf missing" -ForegroundColor Red
}

# ===========================================
# STEP 5: Python Dependencies
# ===========================================
Write-Host ""
Write-Host "[5/8] Verifying Python dependencies..." -ForegroundColor Yellow

try {
    python -c "import edge_tts, requests, google.api_core, google.auth, googleapiclient.discovery; print('All packages OK')"
    Write-Host "  ✓ All Python packages installed" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Some packages missing - installing..." -ForegroundColor Yellow
    pip install -r requirements.txt -q
    Write-Host "  ✓ Packages installed" -ForegroundColor Green
}

# ===========================================
# STEP 6: Remotion (React Renderer)
# ===========================================
Write-Host ""
Write-Host "[6/8] Checking Remotion renderer..." -ForegroundColor Yellow

if (Test-Path "remotion\node_modules") {
    Write-Host "  ✓ Remotion installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Remotion not installed - installing..." -ForegroundColor Yellow
    cd remotion; npm install; cd ..
    Write-Host "  ✓ Remotion installed" -ForegroundColor Green
}

# ===========================================
# STEP 7: Run Tests
# ===========================================
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "[7/8] Running pipeline tests..." -ForegroundColor Yellow
    
    Write-Host "  Test 1: Dry run (no upload)..." -ForegroundColor Cyan
    $dryRun = python run_daily.py --no-upload 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Dry run successful" -ForegroundColor Green
        if (Test-Path "output") {
            $videos = Get-ChildItem output -Filter *.mp4
            Write-Host "    Generated $($videos.Count) video(s) in output/" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  ✗ Dry run failed:" -ForegroundColor Red
        Write-Host "    $($dryRun[-5..-1] -join '`n')" -ForegroundColor Red
    }
    
    Write-Host "  Test 2: Weekly long-form (dry run)..." -ForegroundColor Cyan
    $weeklyRun = python run_weekly.py --no-upload 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Weekly dry run successful" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Weekly dry run failed:" -ForegroundColor Red
        Write-Host "    $($weeklyRun[-5..-1] -join '`n')" -ForegroundColor Red
    }
}

# ===========================================
# STEP 8: Install Task Scheduler
# ===========================================
if ($InstallScheduler) {
    Write-Host ""
    Write-Host "[8/8] Installing Windows Task Scheduler..." -ForegroundColor Yellow
    
    # Check admin
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "  ✗ Must run as Administrator for Task Scheduler" -ForegroundColor Red
        Write-Host "    Right-click PowerShell → 'Run as Administrator' → re-run with -InstallScheduler" -ForegroundColor Yellow
    } else {
        .\setup_scheduler.ps1
        Write-Host "  ✓ Scheduler installed" -ForegroundColor Green
        
        # Verify tasks
        $daily = Get-ScheduledTask -TaskName "AIHorrorChannel_Daily" -ErrorAction SilentlyContinue
        $weekly = Get-ScheduledTask -TaskName "AIHorrorChannel_Weekly" -ErrorAction SilentlyContinue
        if ($daily -and $weekly) {
            Write-Host "    Daily: $($daily.Triggers[0].StartBoundary)" -ForegroundColor Cyan
            Write-Host "    Weekly: $($weekly.Triggers[0].StartBoundary)" -ForegroundColor Cyan
        }
    }
}

# ===========================================
# SUMMARY
# ===========================================
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "NEXT STEPS (if not done):" -ForegroundColor Yellow
Write-Host "1. Edit .env with your API keys:" -ForegroundColor White
Write-Host "   notepad $ProjectPath\.env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Authorize YouTube channel:" -ForegroundColor White
Write-Host "   cd $ProjectPath; python authorize.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test full upload (private):" -ForegroundColor White
Write-Host "   python run_daily.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Install scheduler (Run as Admin):" -ForegroundColor White
Write-Host "   powershell -ExecutionPolicy Bypass -File $ProjectPath\setup_all.ps1 -InstallScheduler" -ForegroundColor Gray
Write-Host ""

Write-Host "LOGS: $ProjectPath\logs\" -ForegroundColor Cyan
Write-Host "OUTPUT: $ProjectPath\output\" -ForegroundColor Cyan
Write-Host "CONFIG: $ProjectPath\config.json" -ForegroundColor Cyan