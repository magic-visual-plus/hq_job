@echo off 
cd /d "%~dp0" 
python -m hq_job.server >> "%~dp0hq_job.log" 2>&1 
