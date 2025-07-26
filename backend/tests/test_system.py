#!/usr/bin/env python3
import sys
import os
from decimal import Decimal
from uuid import uuid4

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_domain_models():
    print("🧪 Тестирование доменных моделей...")
    
    from domain.user import User, Admin
    from domain.wallet import Wallet
    from domain.file import File
    from domain.model import MLModel
    from domain.task import RecognitionTask
    
    class DemoMLModel(MLModel):
        def preprocess(self, file):
            return f"preprocessed_{file.path}"
        
        def predict(self, data):
            return "\\sum_{i=1}^{n} x_i^2"
    
    try:
        # Тест создания пользователя и кошелька
        wallet = Wallet(uuid4(), uuid4(), Decimal("0"))
        user = User(uuid4(), "test@example.com", "password_hash", wallet)
        
        print(f"✅ Пользователь создан: {user.email}")
        print(f"✅ Баланс кошелька: {user.wallet.balance}")
        
        # Тест пополнения баланса
        top_up_amount = Decimal("100.00")
        txn = user.wallet.top_up(top_up_amount)
        print(f"✅ Пополнение на {top_up_amount}: новый баланс {user.wallet.balance}")
        
        # Тест создания задачи
        model = DemoMLModel(uuid4(), "TestModel", Decimal("5.00"))
        file = File("/path/to/test.png", "image/png")
        task = RecognitionTask(uuid4(), user.id, file, model)
        
        print(f"✅ Задача создана: {task.id}")
        print(f"✅ Стоимость: {task.credits_charged}")
        
        # Тест выполнения задачи
        user.execute_task(file, model)
        print(f"✅ Задача выполнена, новый баланс: {user.wallet.balance}")
        print(f"✅ Количество транзакций: {len(user.wallet.transactions)}")
        print(f"✅ Количество задач в истории: {len(user.tasks)}")
        
        # Тест создания админа
        admin_wallet = Wallet(uuid4(), uuid4(), Decimal("0"))
        admin = Admin(uuid4(), "admin@example.com", "admin_hash", admin_wallet)
        
        # Админ пополняет баланс пользователя
        admin_top_up = admin.top_up_user(user, Decimal("50.00"))
        print(f"✅ Админ пополнил баланс пользователя на 50.00")
        print(f"✅ Финальный баланс пользователя: {user.wallet.balance}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в доменных моделях: {e}")
        return False

def test_sqlalchemy_models():
    """Тестируем SQLAlchemy модели"""
    print("\n🧪 Тестирование SQLAlchemy моделей...")
    
    try:
        from infrastructure.models import (
            UserModel, WalletModel, TransactionModel, 
            MLModelModel, FileModel, TaskModel,
            UserRole, TaskStatus, TransactionType
        )
        
        # Создаем объекты моделей (без сохранения в БД)
        user_model = UserModel(
            email="test@example.com",
            password_hash="hash123",
            role=UserRole.USER
        )
        
        wallet_model = WalletModel(
            owner_id=user_model.id,
            balance=Decimal("100.00")
        )
        
        model_model = MLModelModel(
            name="TestModel",
            credit_cost=Decimal("5.00")
        )
        
        print("✅ SQLAlchemy модели созданы успешно")
        print(f"✅ Пользователь: {user_model.email}")
        print(f"✅ Роль: {user_model.role}")
        print(f"✅ Баланс кошелька: {wallet_model.balance}")
        print(f"✅ ML модель: {model_model.name}, стоимость: {model_model.credit_cost}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в SQLAlchemy моделях: {e}")
        return False

def test_imports():
    """Тестируем импорты всех модулей"""
    print("\n🧪 Тестирование импортов...")
    
    modules_to_test = [
        'infrastructure.database',
        'infrastructure.models',
        'infrastructure.repositories',
        'domain.user',
        'domain.wallet',
        'domain.task',
        'domain.file',
        'domain.model'
    ]
    
    success_count = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    print(f"\n📊 Успешно импортировано: {success_count}/{len(modules_to_test)} модулей")
    return success_count == len(modules_to_test)

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования системы formula2latex-recognizer")
    print("=" * 60)
    
    tests = [
        ("Импорты модулей", test_imports),
        ("Доменные модели", test_domain_models),
        ("SQLAlchemy модели", test_sqlalchemy_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        if test_func():
            passed += 1
            print(f"✅ {test_name}: ПРОШЕЛ")
        else:
            print(f"❌ {test_name}: ПРОВАЛЕН")
    
    print("\n" + "=" * 60)
    print(f"🎯 РЕЗУЛЬТАТ: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Система готова к использованию.")
        print("\n📝 Следующие шаги:")
        print("1. Запустите Docker Compose для БД: docker-compose up -d database")
        print("2. Инициализируйте БД: python src/infrastructure/init_db.py")
        print("3. Запустите тесты: pytest tests/")
        return True
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте ошибки выше.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)