@echo off
echo Starting AMU Registration System...

start "Certificate Service" cmd /k "cd certificate && uvicorn main:app --port 8001 --reload"
start "Main Backend" cmd /k "cd backend && uvicorn main:app --port 8000 --reload"
start "Frontend" cmd /k "cd frontend && streamlit run app.py"

echo All services started!