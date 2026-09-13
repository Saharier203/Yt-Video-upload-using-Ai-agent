@echo off
title Dark Archives - Horror Video Generator
cd /d E:\ai-horror-channel

:MENU
cls
echo ==========================================
echo   DARK ARCHIVES - HORROR VIDEO GENERATOR
echo ==========================================
echo.
echo Select video type:
echo.
echo   [1] Short (45 sec, vertical 9:16) - Posts to #Shorts
echo   [2] Long-form (8-10 min, horizontal 16:9) - Deep dive
echo   [3] Test run (dry run, no upload)
echo   [4] Exit
echo.
set /p CHOICE="Enter choice [1-4]: "

if "%CHOICE%"=="1" goto SHORT
if "%CHOICE%"=="2" goto LONG
if "%CHOICE%"=="3" goto TEST
if "%CHOICE%"=="4" goto END

echo Invalid choice. Press any key to try again.
pause
goto MENU

:SHORT
echo.
echo Generating SHORT video (45 sec, 9:16)...
echo.
python run_daily.py
echo.
echo Done. Press any key to return to menu.
pause
goto MENU

:LONG
echo.
echo Generating LONG-FORM video (8-10 min, 16:9)...
echo.
python run_weekly.py
echo.
echo Done. Press any key to return to menu.
pause
goto MENU

:TEST
echo.
echo Running DRY RUN (no upload)...
echo.
python run_daily.py --no-upload
echo.
echo Done. Press any key to return to menu.
pause
goto MENU

:END
echo.
echo Goodbye!
timeout /t 2 >nul