-- Создание базы данных для GenBot
-- Выполните эти команды в PostgreSQL

-- 1. Создание базы данных (выполнить от имени postgres)
-- CREATE DATABASE genbot;

-- 2. Подключиться к базе данных genbot и выполнить:

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    language VARCHAR(2) NOT NULL DEFAULT 'ru',
    balance DECIMAL(10,2) NOT NULL DEFAULT 10.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы для истории операций
CREATE TABLE IF NOT EXISTS operations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    balance_before DECIMAL(10,2) NOT NULL,
    balance_after DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_operations_user_id ON operations(user_id);
CREATE INDEX IF NOT EXISTS idx_operations_created_at ON operations(created_at);

-- Создание представления для статистики пользователей
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    u.user_id,
    u.language,
    u.balance,
    u.created_at,
    u.updated_at,
    COUNT(o.id) as total_operations,
    COALESCE(SUM(CASE WHEN o.operation_type = 'top_up' THEN o.amount ELSE 0 END), 0) as total_top_ups,
    COALESCE(SUM(CASE WHEN o.operation_type = 'deduct' THEN o.amount ELSE 0 END), 0) as total_deductions
FROM users u
LEFT JOIN operations o ON u.user_id = o.user_id
GROUP BY u.user_id, u.language, u.balance, u.created_at, u.updated_at;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Таблица пользователей бота';
COMMENT ON TABLE operations IS 'История операций с балансом пользователей';
COMMENT ON COLUMN users.user_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN users.language IS 'Язык интерфейса (ru/en)';
COMMENT ON COLUMN users.balance IS 'Баланс в кредитах';
COMMENT ON COLUMN operations.operation_type IS 'Тип операции: top_up/deduct';
COMMENT ON COLUMN operations.amount IS 'Сумма операции';
COMMENT ON COLUMN operations.balance_before IS 'Баланс до операции';
COMMENT ON COLUMN operations.balance_after IS 'Баланс после операции';
