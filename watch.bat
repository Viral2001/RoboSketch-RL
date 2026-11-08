@echo off
setlocal EnableDelayedExpansion
title RoboSketch-RL  -  watch the simulation
cd /d "%~dp0"

rem ===================================================================
rem  RoboSketch-RL  |  watch.bat
rem  Double-click me to watch a trained agent draw. No conda knowledge
rem  needed: this finds the `robosketch` environment itself and puts it
rem  on PATH the same way `conda activate` would (env, Library\bin,
rem  Scripts) - calling the env's python.exe WITHOUT that PATH fails,
rem  because pybullet and OpenCV load DLLs out of Library\bin.
rem
rem  Any argument is passed straight through to rl/watch.py, so
rem      watch.bat --shape circle --reward-mode vision --view both
rem  works exactly like the python command. With NO arguments you get
rem  the little menu below.
rem ===================================================================

rem --- 1. locate the environment -------------------------------------
set "ENVDIR="
if defined ROBOSKETCH_ENV if exist "%ROBOSKETCH_ENV%\python.exe" set "ENVDIR=%ROBOSKETCH_ENV%"
for %%D in (
  "%USERPROFILE%\New folder\envs\robosketch"
  "%USERPROFILE%\anaconda3\envs\robosketch"
  "%USERPROFILE%\miniconda3\envs\robosketch"
  "%USERPROFILE%\miniforge3\envs\robosketch"
  "%LOCALAPPDATA%\anaconda3\envs\robosketch"
  "%LOCALAPPDATA%\miniconda3\envs\robosketch"
  "C:\ProgramData\anaconda3\envs\robosketch"
  "C:\ProgramData\miniconda3\envs\robosketch"
) do (
  if not defined ENVDIR if exist "%%~D\python.exe" set "ENVDIR=%%~D"
)

if not defined ENVDIR (
  echo.
  echo   Could not find the 'robosketch' conda environment.
  echo.
  echo   Create it once with:
  echo       conda env create -f environment.yml
  echo.
  echo   Already have it somewhere unusual? Point this script at it:
  echo       setx ROBOSKETCH_ENV "C:\path\to\envs\robosketch"
  echo.
  pause
  exit /b 1
)

set "PATH=%ENVDIR%;%ENVDIR%\Library\mingw-w64\bin;%ENVDIR%\Library\usr\bin;%ENVDIR%\Library\bin;%ENVDIR%\Scripts;%ENVDIR%\bin;%PATH%"
set "PY=%ENVDIR%\python.exe"

rem --- 2. arguments given? just run ----------------------------------
if not "%~1"=="" (
  "%PY%" rl\watch.py %*
  echo.
  pause
  exit /b 0
)

rem --- 3. no arguments: the menu -------------------------------------
:menu
cls
echo.
echo   ====================================================
echo     RoboSketch-RL   -   watch the robot draw
echo   ====================================================
echo.
echo     What should it draw?
echo       1  line          3  square         5  all four
echo       2  circle        4  triangle
echo.
set "SHAPE="
set /p "S=  choice [1-5, Enter = 5]: "
if "%S%"=="" set "S=5"
if "%S%"=="1" set "SHAPE=line"
if "%S%"=="2" set "SHAPE=circle"
if "%S%"=="3" set "SHAPE=square"
if "%S%"=="4" set "SHAPE=triangle"
if "%S%"=="5" set "SHAPE=all"
if not defined SHAPE goto menu

echo.
echo     Which agent?
echo       t  trained on the GROUND-TRUTH reward   (the baseline)
echo       v  trained on the CAMERA reward         (H2 - the novelty)
echo       r  untrained RANDOM policy              (the "before" picture)
echo.
set "MODE=--reward-mode truth"
set /p "M=  choice [t/v/r, Enter = t]: "
if /i "%M%"=="v" set "MODE=--reward-mode vision"
if /i "%M%"=="r" set "MODE=--random"

echo.
echo     How do you want to see it?
echo       1  2D only        - target ^| live ink ^| what the camera sees
echo       2  2D + 3D robot  - also opens the PyBullet window with the arm
echo.
set "VIEW=--view canvas"
set /p "V=  choice [1/2, Enter = 1]: "
if "%V%"=="2" set "VIEW=--view both"

echo.
set "SAVE="
set /p "R=  Record it to output\watch\ as mp4 + PNGs? [y/N]: "
if /i "%R%"=="y" set "SAVE=--save"

echo.
echo   running:  python rl\watch.py --shape %SHAPE% %MODE% %VIEW% %SAVE%
echo.
"%PY%" rl\watch.py --shape %SHAPE% %MODE% %VIEW% %SAVE%

echo.
set /p "A=  Again? [y/N]: "
if /i "%A%"=="y" goto menu
endlocal
exit /b 0
