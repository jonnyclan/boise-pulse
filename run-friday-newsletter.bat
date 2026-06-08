@echo off
REM ============================================================
REM   The Boise Pulse — one-click publish
REM ============================================================
REM   Double-click this file Friday (or Tue/Thu) morning to:
REM     1. Fetch raw news from sources
REM     2. Have Claude curate + write in 10 distinct voices
REM     3. Run automated quality checks (lint + signatures)
REM     4. Render HTML magazine
REM     5. Open the finished issue in your browser
REM
REM   Exit 0 (green) = GO, ship it.
REM   Exit 1 (red)   = NO-GO, problem will be printed below.
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   Boise Pulse — running pre-publish check...
echo ============================================================
echo.

python pre_publish_check.py --preview 2>&1

echo.
echo ============================================================
echo   Done. Press any key to close this window.
echo ============================================================
pause >nul
