@echo off
chcp 65001 >nul
echo Установка необходимых библиотек...
python -m pip install -r requirements.txt
echo =========================================
echo Запуск MineAI Translator...
python translator.py
pause
