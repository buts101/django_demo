@echo off
cd /d "%~dp0"
git pull
echo Git pull executed at %date% %time% >> git_pull_log.txt
