@echo off
echo Resetting history...
if exist history.csv (
    del history.csv
    echo History cleared.
) else (
    echo No history found.
)
pause
