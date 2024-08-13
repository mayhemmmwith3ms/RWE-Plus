rmdir /S /Q "%~dp0\dist"
del /Q "%~dp0\__pycache__"
rmdir /S /Q "%~dp0\__pycache__"
pyinstaller --onefile --icon="%~dp0\files\icon.ico" main.py
xcopy "%~dp0\files" "%~dp0\dist\files" /y /i /s
del "%~dp0\dist\files\recent.txt"
xcopy "%~dp0\drizzle" "%~dp0\dist\drizzle" /y /i /s
del "%~dp0\dist\OGSCULEDITOR-PLUS.zip"
mkdir "%~dp0\dist\LevelEditorProjects"
del /S /Q "%~dp0\dist\LevelEditorProjects"
del /Q "%~dp0\dist\loadLog.txt"
del /Q "%~dp0\dist\crashLog.txt"
7z a -tzip "%~dp0\dist\OGSCULEDITOR-PLUS.zip" "%~dp0\dist\*"