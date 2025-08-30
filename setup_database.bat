@echo off
echo ========================================
echo    GenBot - Настройка базы данных
echo ========================================
echo.

echo Проверка подключения к PostgreSQL...
echo.

REM Проверяем, установлен ли PostgreSQL
where psql >nul 2>nul
if %errorlevel% neq 0 (
    echo ОШИБКА: PostgreSQL не найден в PATH!
    echo.
    echo Убедитесь, что PostgreSQL установлен и добавлен в PATH
    echo Обычно это: C:\Program Files\PostgreSQL\15\bin
    echo.
    echo Если PostgreSQL не установлен:
    echo 1. Скачайте с https://www.postgresql.org/download/windows/
    echo 2. Установите, запомнив пароль для пользователя postgres
    echo 3. Перезапустите командную строку
    echo.
    pause
    exit /b 1
)

echo PostgreSQL найден!
echo.

REM Запрашиваем пароль
set /p DB_PASSWORD="Введите пароль для пользователя postgres: "

echo.
echo Создание базы данных genbot...

REM Создаем базу данных
psql -U postgres -h localhost -p 6200 -c "CREATE DATABASE genbot;" 2>nul
if %errorlevel% equ 0 (
    echo База данных genbot создана успешно!
) else (
    echo База данных genbot уже существует или произошла ошибка
)

echo.
echo Подключение к базе данных genbot...

REM Подключаемся к базе данных и выполняем SQL скрипт
psql -U postgres -h localhost -p 6200 -d genbot -f database_setup.sql
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    База данных настроена успешно!
    echo ========================================
    echo.
    echo Теперь можете запустить бота командой:
    echo python main.py
    echo.
) else (
    echo.
    echo ========================================
    echo    ОШИБКА при настройке базы данных!
    echo ========================================
    echo.
    echo Возможные причины:
    echo 1. Неверный пароль для пользователя postgres
    echo 2. PostgreSQL не запущен
    echo 3. Порт 6200 занят или заблокирован
    echo.
    echo Проверьте:
    echo 1. Службу PostgreSQL в services.msc
    echo 2. Пароль в config.py
    echo 3. Порт подключения
    echo.
)

pause
