@echo off
echo Starting Chrome with remote debugging...
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --no-first-run --user-data-dir="%TEMP%\spotify_chrome" https://open.spotify.com
echo.
echo Chrome started. Press Ctrl+C to stop.
pause
