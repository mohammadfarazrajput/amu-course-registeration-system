@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

echo Running setup scripts...
python scripts/setup_all.py

pause
