@echo off
REM ============================================================
REM  One-time fix: temporarily disable the hosts entry that maps
REM  github.com -> 127.0.0.1 (Steam++/Watt Toolkit acceleration).
REM  Backup is saved as hosts.bak-20260903-push automatically.
REM  Run this file AS ADMINISTRATOR (right-click -> Run as admin).
REM ============================================================
set "H=%SystemRoot%\System32\drivers\etc\hosts"
copy /y "%H%" "%H%.bak-20260903-push" >nul
powershell -NoProfile -Command "$enc=[Text.Encoding]::GetEncoding('ISO-8859-1'); $h='%H%'; $b=[IO.File]::ReadAllBytes($h); $s=$enc.GetString($b); $n=([regex]::Matches($s,'(?m)^127\.0\.0\.1[ \t]+github\.com[ \t]*\r?$')).Count; $s=[regex]::Replace($s,'(?m)^127\.0\.0\.1[ \t]+github\.com[ \t]*\r?$','# 127.0.0.1 github.com   (temp-disabled 2026-09-03 for git push)'); [IO.File]::WriteAllBytes($h,$enc.GetBytes($s)); Write-Host ('commented github.com lines: ' + $n)"
echo.
echo Done. Backup saved. If it says "commented github.com lines: 1", tell the assistant to push.
pause
