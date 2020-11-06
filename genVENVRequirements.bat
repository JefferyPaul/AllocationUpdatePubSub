cd %~dp0
cd "venv\Scripts"
call activate.bat

pip freeze > "..\..\requirements.txt"

pause