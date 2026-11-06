@echo off
chcp 65001 >nul
cd /d "%~dp0.."
start "" pythonw -m icc_finder
if errorlevel 1 python -m icc_finder

