@echo off
chcp 65001 >nul
echo Установка необходимых библиотек...
pip install -r requirements.txt >nul 2>&1
echo Запуск переводчика...
python translator.py
pause