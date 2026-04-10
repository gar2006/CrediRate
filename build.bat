@echo off
echo Setting up virtual environment...
python -m venv --clear venv
venv\Scripts\python.exe -m pip install -r requirements.txt
echo Setup complete.

echo Make sure MySQL is running on localhost before continuing.
echo Initializing database...
venv\Scripts\python.exe db_setup.py
echo Build complete! You can now use run.bat
