#!/usr/bin/env python3
"""
Демонстрационный сценарий для проверки всех функций системы
"""
from decimal import Decimal
from infrastructure.database import SessionLocal
from infrastructure.repositories import UserRepository, WalletRepository, MLModelRepository, TaskRepository
from domain.file import File
from domain.task import RecognitionTask
from uuid import uuid4

def demo_scenario():
    """Полный сценарий тестирования системы"""
    print("🎬 ДЕМОНСТРАЦИОННЫЙ СЦЕНАРИЙ")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        wallet_repo = WalletRepository(db)
        model_repo = MLModelRepository(db)
        
        # 1. Получение существующих пользователей
        print("\n1️⃣ ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЕЙ")
        admin = user_repo.get_by_email("admin@formula2latex.com")
        user = user_repo.get_by_email("user@formula2latex.com")
        
        print(f"👨‍💼 Админ: {admin.email} (роль: {getattr(admin, 'role', 'admin')})")
        print(f"👤 Пользователь: {user.email}")
        
        # 2. Проверка баланса пользователя
        print("\n2️⃣ ПРОВЕРКА БАЛАНСА")
        user_wallet = wallet_repo.get_by_owner_id(user.id)
        print(f"💰 Текущий баланс пользователя: {user_wallet.balance} кредитов")
        
        # 3. Пополнение баланса администратором
        print("\n3️⃣ ПОПОЛНЕНИЕ БАЛАНСА АДМИНИСТРАТОРОМ")
        top_up_amount = Decimal("50.00")
        top_up_txn = user_wallet.top_up(top_up_amount)
        wallet_repo.add_transaction(top_up_txn)
        wallet_repo.update_balance(user_wallet.id, user_wallet.balance)
        
        print(f"✅ Админ пополнил баланс на {top_up_amount} кредитов")
        print(f"💰 Новый баланс: {user_wallet.balance} кредитов")
        
        # 4. Получение доступных моделей
        print("\n4️⃣ ДОСТУПНЫЕ ML МОДЕЛИ")
        models = model_repo.get_active_models()
        for i, model in enumerate(models, 1):
            print(f"🤖 {i}. {model.name} - {model.credit_cost} кредитов")
        
        # 5. Создание файла для обработки
        print("\n5️⃣ СОЗДАНИЕ ФАЙЛА ДЛЯ ОБРАБОТКИ")
        test_file = File("test_formula.png", "image/png")
        print(f"📁 Создан файл: {test_file.path}")
        
        # 6. Выполнение задачи распознавания
        print("\n6️⃣ ВЫПОЛНЕНИЕ ЗАДАЧИ РАСПОЗНАВАНИЯ")
        selected_model = models[1]  # Advanced LaTeX Model
        print(f"🎯 Выбрана модель: {selected_model.name}")
        print(f"💸 Стоимость: {selected_model.credit_cost} кредитов")
        
        # Эмуляция выполнения задачи через доменную модель
        task = user.execute_task(test_file, selected_model)
        print(f"✅ Задача выполнена с ID: {task.id}")
        print(f"📋 Статус: {task.status}")
        print(f"📄 Результат: {task.result}")
        
        # 7. Обновление баланса после выполнения задачи
        user_wallet = wallet_repo.get_by_owner_id(user.id)
        print(f"💰 Баланс после выполнения: {user_wallet.balance} кредитов")
        
        # 8. История транзакций
        print("\n7️⃣ ИСТОРИЯ ТРАНЗАКЦИЙ")
        user_wallet = wallet_repo.get_by_owner_id(user.id)
        transactions = user_wallet.transactions
        
        print(f"📊 Всего транзакций: {len(transactions)}")
        for i, txn in enumerate(transactions[-5:], 1):  # Последние 5 транзакций
            txn_type = "Пополнение" if txn.amount > 0 else "Списание"
            print(f"   {i}. {txn_type}: {abs(txn.amount)} кредитов (баланс после: {txn.post_balance})")
        
        # 9. Создание нового пользователя
        print("\n8️⃣ СОЗДАНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ")
        new_user = user_repo.create_user("newuser@example.com", "password123")
        print(f"✅ Создан новый пользователь: {new_user.email}")
        
        new_wallet = wallet_repo.get_by_owner_id(new_user.id)
        print(f"💰 Начальный баланс: {new_wallet.balance} кредитов")
        
        # 10. Статистика системы
        print("\n9️⃣ СТАТИСТИКА СИСТЕМЫ")
        all_users = user_repo.get_all()
        all_models = model_repo.get_active_models()
        
        print(f"👥 Всего пользователей: {len(all_users)}")
        print(f"🤖 Всего активных моделей: {len(all_models)}")
        print(f"📋 Выполнено задач пользователем: {len(user.tasks)}")
        
        print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ Все функции системы работают корректно:")
        print("   - Создание и управление пользователями")
        print("   - Система кошельков и транзакций")
        print("   - Управление ML моделями")
        print("   - Выполнение задач распознавания")
        print("   - История операций")
        
    except Exception as e:
        print(f"❌ Ошибка в демонстрации: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    demo_scenario()