
del /Q "%~dp0\__pycache__"
rmdir "%~dp0\__pycache__"
xcopy "%~dp0\files" "%~dp0\dist\files" /y
del "%~dp0\dist\files\recent.txt"
xcopy "%~dp0\drizzle" "%~dp0\dist\drizzle" /y
pyinstaller --onefile main.py
del "%~dp0\dist\OGSCULEDITOR-PLUS.zip"
mkdir "%~dp0\dist\LevelEditorProjects"
del /S /Q "%~dp0\dist\LevelEditorProjects"
del /Q "%~dp0\dist\loadLog.txt"
del /Q "%~dp0\dist\crashLog.txt"
7z a -tzip "%~dp0\dist\OGSCULEDITOR-PLUS.zip" "%~dp0\dist\*"