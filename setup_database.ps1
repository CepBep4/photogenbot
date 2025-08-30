# GenBot - PowerShell скрипт для настройки PostgreSQL
# Запустите от имени администратора: PowerShell -> "Запуск от имени администратора"

param(
    [string]$Port = "6200",
    [string]$DatabaseName = "genbot",
    [string]$UserName = "postgres"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    GenBot - Настройка базы данных" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем, запущен ли PowerShell от имени администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ОШИБКА: Запустите PowerShell от имени администратора!" -ForegroundColor Red
    Write-Host "Правый клик на PowerShell -> 'Запуск от имени администратора'" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "PowerShell запущен от имени администратора ✓" -ForegroundColor Green
Write-Host ""

# Проверяем, установлен ли PostgreSQL
try {
    $psqlPath = Get-Command psql -ErrorAction Stop
    Write-Host "PostgreSQL найден: $($psqlPath.Source)" -ForegroundColor Green
} catch {
    Write-Host "ОШИБКА: PostgreSQL не найден в PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Убедитесь, что PostgreSQL установлен и добавлен в PATH" -ForegroundColor Yellow
    Write-Host "Обычно это: C:\Program Files\PostgreSQL\15\bin" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Если PostgreSQL не установлен:" -ForegroundColor Yellow
    Write-Host "1. Скачайте с https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "2. Установите, запомнив пароль для пользователя $UserName" -ForegroundColor Yellow
    Write-Host "3. Перезапустите PowerShell" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""

# Проверяем службу PostgreSQL
try {
    $service = Get-Service -Name "*postgresql*" -ErrorAction Stop
    Write-Host "Служба PostgreSQL найдена: $($service.Name)" -ForegroundColor Green
    
    if ($service.Status -eq "Running") {
        Write-Host "Служба PostgreSQL запущена ✓" -ForegroundColor Green
    } else {
        Write-Host "Служба PostgreSQL остановлена. Запускаем..." -ForegroundColor Yellow
        Start-Service $service
        Start-Sleep -Seconds 3
        if ((Get-Service $service.Name).Status -eq "Running") {
            Write-Host "Служба PostgreSQL запущена ✓" -ForegroundColor Green
        } else {
            Write-Host "ОШИБКА: Не удалось запустить службу PostgreSQL!" -ForegroundColor Red
            Read-Host "Нажмите Enter для выхода"
            exit 1
        }
    }
} catch {
    Write-Host "ОШИБКА: Служба PostgreSQL не найдена!" -ForegroundColor Red
    Write-Host "Убедитесь, что PostgreSQL установлен корректно" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""

# Запрашиваем пароль
$securePassword = Read-Host "Введите пароль для пользователя $UserName" -AsSecureString
$password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword))

Write-Host ""
Write-Host "Создание базы данных $DatabaseName..."

# Создаем базу данных
try {
    $env:PGPASSWORD = $password
    $createDbResult = psql -U $UserName -h localhost -p $Port -c "CREATE DATABASE $DatabaseName;" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "База данных $DatabaseName создана успешно! ✓" -ForegroundColor Green
    } else {
        # Проверяем, не существует ли уже база данных
        if ($createDbResult -match "already exists") {
            Write-Host "База данных $DatabaseName уже существует ✓" -ForegroundColor Yellow
        } else {
            Write-Host "Предупреждение: $createDbResult" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "ОШИБКА при создании базы данных: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Подключение к базе данных $DatabaseName..."

# Подключаемся к базе данных и выполняем SQL скрипт
try {
    if (Test-Path "database_setup.sql") {
        $env:PGPASSWORD = $password
        $setupResult = psql -U $UserName -h localhost -p $Port -d $DatabaseName -f "database_setup.sql" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "    База данных настроена успешно!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Теперь можете запустить бота командой:" -ForegroundColor Cyan
            Write-Host "python main.py" -ForegroundColor White
            Write-Host ""
            
            # Обновляем config.py с правильным паролем
            Write-Host "Обновление config.py с правильным паролем..." -ForegroundColor Yellow
            $configContent = Get-Content "config.py" -Raw
            $configContent = $configContent -replace 'DB_PASSWORD = .*', "DB_PASSWORD = '$password'"
            Set-Content "config.py" $configContent -Encoding UTF8
            Write-Host "config.py обновлен ✓" -ForegroundColor Green
            
        } else {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Red
            Write-Host "    ОШИБКА при настройке базы данных!" -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Red
            Write-Host ""
            Write-Host "Детали ошибки:" -ForegroundColor Yellow
            Write-Host $setupResult -ForegroundColor Red
            Write-Host ""
            Write-Host "Возможные причины:" -ForegroundColor Yellow
            Write-Host "1. Неверный пароль для пользователя $UserName" -ForegroundColor Yellow
            Write-Host "2. PostgreSQL не запущен" -ForegroundColor Yellow
            Write-Host "3. Порт $Port занят или заблокирован" -ForegroundColor Yellow
            Write-Host ""
        }
    } else {
        Write-Host "ОШИБКА: Файл database_setup.sql не найден!" -ForegroundColor Red
        Write-Host "Убедитесь, что файл находится в текущей папке" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ОШИБКА при выполнении SQL скрипта: $_" -ForegroundColor Red
}

# Очищаем переменную окружения
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
