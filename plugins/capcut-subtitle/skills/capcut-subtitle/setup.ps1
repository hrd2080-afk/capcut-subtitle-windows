# One-time setup for the capcut-subtitle skill (Windows).
# Creates a Python venv at %USERPROFILE%\.capcut-subtitle\venv, installs deps,
# and pre-downloads the Whisper model. Safe to re-run.
#
# Usage: powershell -ExecutionPolicy Bypass -File setup.ps1 [model_name]
# Example: powershell -ExecutionPolicy Bypass -File setup.ps1 large-v3

param(
    [string]$Model = "medium"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HomeDir = Join-Path $env:USERPROFILE ".capcut-subtitle"
$Venv = Join-Path $HomeDir "venv"

Write-Host "▶ capcut-subtitle 설치 시작 (Windows)" -ForegroundColor Cyan

# 1. ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "✗ ffmpeg 가 없습니다. 먼저 설치하세요:" -ForegroundColor Red
    Write-Host "  winget install ffmpeg"
    Write-Host "  또는 https://ffmpeg.org/download.html 에서 Windows 빌드 다운로드 후 PATH에 추가"
    exit 1
}
Write-Host "✓ ffmpeg 확인" -ForegroundColor Green

# 2. python
$PythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") {
            $PythonCmd = $cmd
            break
        }
    }
}
if (-not $PythonCmd) {
    Write-Host "✗ Python 3 이 없습니다." -ForegroundColor Red
    Write-Host "  https://www.python.org 에서 설치 후 'Add Python to PATH'를 체크하세요."
    exit 1
}
$PyVersion = & $PythonCmd --version 2>&1
Write-Host "✓ Python 확인 ($PyVersion)" -ForegroundColor Green

# 3. venv + deps
if (-not (Test-Path $HomeDir)) {
    New-Item -ItemType Directory -Path $HomeDir | Out-Null
}

if (-not (Test-Path $Venv)) {
    Write-Host "▶ 가상환경 생성: $Venv"
    & $PythonCmd -m venv $Venv
}

$VenvPython = Join-Path $Venv "Scripts\python.exe"
$VenvPip = Join-Path $Venv "Scripts\pip.exe"

Write-Host "▶ 의존성 설치 (faster-whisper 등)…"
& $VenvPython -m pip install --upgrade pip -q
& $VenvPip install -q -r (Join-Path $ScriptDir "requirements.txt")
Write-Host "✓ 의존성 설치 완료" -ForegroundColor Green

# 4. pre-download the model (~1.5GB for medium)
Write-Host "▶ 음성인식 모델($Model) 다운로드 — 처음 한 번, 수백MB~1.5GB…"
$PyScript = @"
import sys
from faster_whisper import WhisperModel
WhisperModel(sys.argv[1], device='cpu', compute_type='int8')
print('✓ 모델 준비 완료')
"@
& $VenvPython -c $PyScript $Model

Write-Host ""
Write-Host "🎉 설치 완료! 이제 Claude Code 에서 이렇게 쓰세요:" -ForegroundColor Green
Write-Host "  `"이 영상에 자막 넣어줘 C:\경로\영상.mp4`" (대본이 있으면 함께 주세요)"
