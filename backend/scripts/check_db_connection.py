#!/usr/bin/env python3
import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_database_connection():
    """Проверка подключения к БД"""
    load_dotenv()
    
    # Попробуем разные варианты подключения
    urls_to_try = [
        os.getenv("DATABASE_URL"),
        "postgresql://app_user:SuperSecretPass123@localhost:5432/app_db",
        "postgresql://app_user:SuperSecretPass123@database:5432/app_db",
        "postgresql://postgres:postgres@localhost:5432/postgres"
    ]
    
    for i, url in enumerate(urls_to_try, 1):
        if not url:
            continue
            
        print(f"🔄 Попытка {i}: {url}")
        
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✅ Подключение успешно!")
                print(f"📊 PostgreSQL версия: {version}")
                return url, engine
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            continue
    
    print("💀 Не удалось подключиться ни к одной БД")
    return None, None

def test_create_tables():
    """Тест создания таблиц"""
    url, engine = check_database_connection()
    if not engine:
        return False
    
    try:
        from infrastructure.database import Base
        import infrastructure.models
        
        print("\n🛠️  Создание таблиц...")
        Base.metadata.create_all(engine)
        print("✅ Таблицы созданы успешно!")
        
        # Проверим, что таблицы действительно созданы
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
        expected_tables = ['users', 'wallets', 'transactions', 'ml_models', 'files', 'tasks']
        for table in expected_tables:
            if table in tables:
                print(f"✅ Таблица {table} создана")
            else:
                print(f"❌ Таблица {table} НЕ создана")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка подключения к базе данных")
    print("=" * 50)
    
    success = check_database_connection()[0] is not None
    if success:
        success = test_create_tables()
    
    if success:
        print("\n🎉 База данных готова к работе!")
        print("\n📝 Следующие шаги:")
        print("1. python src/infrastructure/init_db.py  # Инициализация с демо данными")
        print("2. pytest tests/ -v                      # Запуск тестов")
    else:
        print("\n💡 Инструкции по исправлению:")
        print("1. Убедитесь, что PostgreSQL запущен")
        print("2. Проверьте docker-compose up -d database")
        print("3. Проверьте переменные окружения в .env")