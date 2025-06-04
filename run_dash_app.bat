@echo off
cd "C:\Users\internet\OneDrive - Hadassah Academic College\Desktop\Project"
start cmd /k "python app.py"
timeout /t 5
start "" http://localhost:8050
