#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования подключения к PostgreSQL
Запустите: python test_connection.py
"""

import sys
import os

# Добавляем текущую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_postgresql_connection():
    """Тестирует подключение к PostgreSQL"""
    print("=" * 50)
    print("    GenBot - Тест подключения к PostgreSQL")
    print("=" * 50)
    print()
    
    try:
        # Пытаемся импортировать модуль базы данных
        print("1. Импорт модуля базы данных...")
        from database import db
        print("   ✓ Модуль database импортирован успешно")
        print()
        
        # Проверяем подключение
        print("2. Проверка подключения к PostgreSQL...")
        conn = db.get_connection()
        
        if conn:
            print("   ✓ Подключение к PostgreSQL установлено")
            
            # Проверяем версию PostgreSQL
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"   ✓ Версия PostgreSQL: {version.split(',')[0]}")
            
            conn.close()
            print("   ✓ Соединение закрыто")
        else:
            print("   ❌ Не удалось подключиться к PostgreSQL")
            return False
        
        print()
        
        # Проверяем существование таблиц
        print("3. Проверка структуры базы данных...")
        conn = db.get_connection()
        
        if conn:
            with conn.cursor() as cursor:
                # Проверяем таблицу users
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'users'
                    );
                """)
                users_exists = cursor.fetchone()[0]
                print(f"   {'✓' if users_exists else '❌'} Таблица 'users': {'существует' if users_exists else 'не найдена'}")
                
                # Проверяем таблицу operations
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'operations'
                    );
                """)
                operations_exists = cursor.fetchone()[0]
                print(f"   {'✓' if operations_exists else '❌'} Таблица 'operations': {'существует' if operations_exists else 'не найдена'}")
                
                # Проверяем количество пользователей
                if users_exists:
                    cursor.execute("SELECT COUNT(*) FROM users;")
                    user_count = cursor.fetchone()[0]
                    print(f"   📊 Количество пользователей в базе: {user_count}")
            
            conn.close()
        
        print()
        print("=" * 50)
        print("    Тест подключения завершен успешно!")
        print("=" * 50)
        print()
        print("Теперь можете запустить бота:")
        print("python main.py")
        print()
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
        print()
        print("Убедитесь, что установлены все зависимости:")
        print("pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print()
        print("Возможные причины:")
        print("1. PostgreSQL не установлен или не запущен")
        print("2. Неверные параметры подключения в config.py")
        print("3. База данных не создана")
        print("4. Неверный пароль")
        print()
        print("Запустите скрипт настройки:")
        print("setup_database.bat (или setup_database.ps1)")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    
    if not success:
        print("❌ Тест не пройден. Проверьте настройки и попробуйте снова.")
        sys.exit(1)
    else:
        print("✅ Все тесты пройдены успешно!")
