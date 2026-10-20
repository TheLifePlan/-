@echo off
rem ws - open the WS desks (Windows Terminal WS desks profile, fixed GUID). 2026-10-21 ZARA: one word after reboot.
rem The profile runs ~/ai/bin/studio.sh (waits for the 58 windows, never creates an empty win).
start "" "%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe" -w 0 nt -p "{4ce7dd61-f5b5-5a52-9a9b-a2b8801eb0b6}"
