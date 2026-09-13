@echo off
cd /d E:\ai-horror-channel
if not exist .venv (
    python -m venv .venv
    .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    .venv\Scripts\activate.bat
)
if not exist logs mkdir logs
python run_daily.py >> logs\daily_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%.log 2>&1