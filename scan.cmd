@echo off
:: Usage: scan.cmd [block_size] [offset_pct] [quality]
:: Defaults: block_size=40, offset_pct=10, quality=95

set BLOCK=%~1
set OFFSET=%~2
set QUALITY=%~3

if "%BLOCK%"=="" set BLOCK=40
if "%OFFSET%"=="" set OFFSET=10
if "%QUALITY%"=="" set QUALITY=95

mkdir Scans 2>nul
for %%f in (*.jpg *.jpeg *.png) do (
    echo Bearbeite %%f...
    "C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe" "%%f" -colorspace gray -negate -lat %BLOCK%x%BLOCK%+%OFFSET%%% -negate -quality %QUALITY% "Scans\%%~nf_scan.jpg"
)
echo Fertig!
pause
