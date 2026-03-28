@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name image2scan image2scan.py
echo.
echo Built: dist\image2scan.exe
pause
