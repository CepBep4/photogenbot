import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Tuple
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class PostgreSQLDatabase:
    def __init__(self):
        # Параметры подключения к PostgreSQL
        self.db_params = {
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
        self.init_database()
    
    def get_connection(self):
        """Получает соединение с базой данных"""
        try:
            return psycopg2.connect(**self.db_params)
        except psycopg2.Error as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            return None
    
    def init_database(self):
        """Инициализирует базу данных и создает таблицы"""
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cursor:
                # Создаем таблицу пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        language VARCHAR(2) NOT NULL DEFAULT 'ru',
                        balance DECIMAL(10,2) NOT NULL DEFAULT 10.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Создаем таблицу для истории операций
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operations (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        operation_type VARCHAR(50) NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        balance_before DECIMAL(10,2) NOT NULL,
                        balance_after DECIMAL(10,2) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                conn.commit()
                print("База данных PostgreSQL инициализирована успешно")
                
        except psycopg2.Error as e:
            print(f"Ошибка инициализации базы данных: {e}")
        finally:
            conn.close()
    
    def is_new_user(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь новым"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (user_id,))
                count = cursor.fetchone()[0]
                return count == 0
        except psycopg2.Error as e:
            print(f"Ошибка проверки нового пользователя: {e}")
            return False
        finally:
            conn.close()
    
    def add_user(self, user_id: int, language: str) -> bool:
        """Добавляет нового пользователя"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (user_id, language, balance) 
                    VALUES (%s, %s, 10.0)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id, language))
                conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_language(self, user_id: int) -> str:
        """Получает язык пользователя"""
        conn = self.get_connection()
        if not conn:
            return 'ru'
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT language FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 'ru'
        except psycopg2.Error as e:
            print(f"Ошибка получения языка пользователя: {e}")
            return 'ru'
        finally:
            conn.close()
    
    def update_user_language(self, user_id: int, language: str) -> bool:
        """Обновляет язык пользователя"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET language = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = %s
                """, (language, user_id))
                conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Ошибка обновления языка пользователя: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_balance(self, user_id: int) -> float:
        """Получает баланс пользователя"""
        conn = self.get_connection()
        if not conn:
            return 0.0
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                return float(result[0]) if result else 0.0
        except psycopg2.Error as e:
            print(f"Ошибка получения баланса пользователя: {e}")
            return 0.0
        finally:
            conn.close()
    
    def add_balance(self, user_id: int, amount: float) -> float:
        """Пополняет баланс пользователя"""
        conn = self.get_connection()
        if not conn:
            return 0.0
        
        try:
            with conn.cursor() as cursor:
                # Получаем текущий баланс
                cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                current_balance = float(result[0])
                new_balance = current_balance + amount
                
                # Обновляем баланс
                cursor.execute("""
                    UPDATE users 
                    SET balance = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = %s
                """, (new_balance, user_id))
                
                # Записываем операцию
                cursor.execute("""
                    INSERT INTO operations (user_id, operation_type, amount, balance_before, balance_after)
                    VALUES (%s, 'top_up', %s, %s, %s)
                """, (user_id, amount, current_balance, new_balance))
                
                conn.commit()
                return new_balance
                
        except psycopg2.Error as e:
            print(f"Ошибка пополнения баланса: {e}")
            return 0.0
        finally:
            conn.close()
    
    def deduct_credits(self, user_id: int, amount: float) -> Tuple[bool, float]:
        """Списывает кредиты с баланса пользователя"""
        conn = self.get_connection()
        if not conn:
            return False, 0.0
        
        try:
            with conn.cursor() as cursor:
                # Получаем текущий баланс
                cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return False, 0.0
                
                current_balance = float(result[0])
                
                # Проверяем достаточность средств
                if current_balance < amount:
                    return False, current_balance
                
                new_balance = current_balance - amount
                
                # Обновляем баланс
                cursor.execute("""
                    UPDATE users 
                    SET balance = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = %s
                """, (new_balance, user_id))
                
                # Записываем операцию
                cursor.execute("""
                    INSERT INTO operations (user_id, operation_type, amount, balance_before, balance_after)
                    VALUES (%s, 'deduct', %s, %s, %s)
                """, (user_id, amount, current_balance, new_balance))
                
                conn.commit()
                return True, new_balance
                
        except psycopg2.Error as e:
            print(f"Ошибка списания кредитов: {e}")
            return False, 0.0
        finally:
            conn.close()
    
    def get_user_stats(self, user_id: int) -> dict:
        """Получает статистику пользователя"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Получаем основную информацию о пользователе
                cursor.execute("""
                    SELECT user_id, language, balance, created_at, updated_at
                    FROM users WHERE user_id = %s
                """, (user_id,))
                user_info = cursor.fetchone()
                
                if not user_info:
                    return {}
                
                # Получаем статистику операций
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_operations,
                        SUM(CASE WHEN operation_type = 'top_up' THEN amount ELSE 0 END) as total_top_ups,
                        SUM(CASE WHEN operation_type = 'deduct' THEN amount ELSE 0 END) as total_deductions
                    FROM operations 
                    WHERE user_id = %s
                """, (user_id,))
                stats = cursor.fetchone()
                
                return {
                    'user_info': dict(user_info),
                    'stats': dict(stats) if stats else {}
                }
                
        except psycopg2.Error as e:
            print(f"Ошибка получения статистики пользователя: {e}")
            return {}
        finally:
            conn.close()

# Создаем глобальный экземпляр базы данных
db = PostgreSQLDatabase()
