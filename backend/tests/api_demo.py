#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования REST API
"""
import requests
import base64
import json
from decimal import Decimal

API_BASE = "http://localhost:8000"

def demo_api():
    """Полная демонстрация API функциональности"""
    print("🚀 ДЕМОНСТРАЦИЯ REST API")
    print("=" * 50)
    
    # 1. Регистрация пользователя
    print("\n1️⃣ РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ")
    user_data = {
        "email": "api_demo@example.com",
        "password": "demo123456"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code == 200:
        user_info = response.json()
        print(f"✅ Пользователь зарегистрирован: {user_info['email']}")
        print(f"   ID: {user_info['id']}")
    else:
        print(f"❌ Ошибка регистрации: {response.json()}")
        return
    
    # 2. Авторизация
    print("\n2️⃣ АВТОРИЗАЦИЯ")
    response = requests.post(f"{API_BASE}/auth/login", json=user_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print(f"✅ Авторизация успешна")
        print(f"   Токен: {token[:50]}...")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print(f"❌ Ошибка авторизации: {response.json()}")
        return
    
    # 3. Получение информации о пользователе
    print("\n3️⃣ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
    response = requests.get(f"{API_BASE}/auth/me", headers=headers)
    if response.status_code == 200:
        user_me = response.json()
        print(f"✅ ID: {user_me['id']}")
        print(f"   Email: {user_me['email']}")
    else:
        print(f"❌ Ошибка: {response.json()}")
    
    # 4. Проверка кошелька
    print("\n4️⃣ ИНФОРМАЦИЯ О КОШЕЛЬКЕ")
    response = requests.get(f"{API_BASE}/wallet", headers=headers)
    if response.status_code == 200:
        wallet = response.json()
        print(f"✅ ID кошелька: {wallet['id']}")
        print(f"   Баланс: {wallet['balance']} кредитов")
    else:
        print(f"❌ Ошибка: {response.json()}")
    
    # 5. Получение доступных моделей
    print("\n5️⃣ ДОСТУПНЫЕ ML МОДЕЛИ")
    response = requests.get(f"{API_BASE}/models")
    if response.status_code == 200:
        models = response.json()
        print(f"✅ Найдено моделей: {len(models)}")
        for i, model in enumerate(models, 1):
            print(f"   {i}. {model['name']} - {model['credit_cost']} кредитов")
        
        if models:
            selected_model = models[0]  # Выберем первую модель
    else:
        print(f"❌ Ошибка: {response.json()}")
        return
    
    # 6. Попытка создания предсказания (без кредитов)
    print("\n6️⃣ ПОПЫТКА ПРЕДСКАЗАНИЯ БЕЗ КРЕДИТОВ")
    dummy_image = base64.b64encode(b"dummy image content for testing").decode()
    prediction_data = {
        "model_id": selected_model["id"],
        "file_content": dummy_image,
        "filename": "test_formula.png"
    }
    
    response = requests.post(f"{API_BASE}/predict", json=prediction_data, headers=headers)
    if response.status_code == 402:
        print(f"✅ Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"❌ Неожиданный результат: {response.status_code} - {response.json()}")
    
    # 7. Проверка истории транзакций (пустая)
    print("\n7️⃣ ИСТОРИЯ ТРАНЗАКЦИЙ (ПУСТАЯ)")
    response = requests.get(f"{API_BASE}/wallet/transactions", headers=headers)
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Транзакций в истории: {len(transactions)}")
    else:
        print(f"❌ Ошибка: {response.json()}")
    
    # 8. Проверка истории задач (пустая)
    print("\n8️⃣ ИСТОРИЯ ЗАДАЧ (ПУСТАЯ)")
    response = requests.get(f"{API_BASE}/tasks", headers=headers)
    if response.status_code == 200:
        tasks = response.json()
        print(f"✅ Задач в истории: {len(tasks)}")
    else:
        print(f"❌ Ошибка: {response.json()}")
    
    # 9. Проверка несуществующей задачи
    print("\n9️⃣ ПРОВЕРКА НЕСУЩЕСТВУЮЩЕЙ ЗАДАЧИ")
    fake_task_id = "00000000-0000-0000-0000-000000000000"
    response = requests.get(f"{API_BASE}/tasks/{fake_task_id}", headers=headers)
    if response.status_code == 404:
        print(f"✅ Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"❌ Неожиданный результат: {response.status_code}")
    
    # 10. Проверка здоровья API
    print("\n🔟 ПРОВЕРКА ЗДОРОВЬЯ API")
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Статус: {health['status']}")
        print(f"   Сервис: {health['service']}")
    else:
        print(f"❌ Ошибка: {response.json()}")
    
    print("\n🎉 ДЕМОНСТРАЦИЯ API ЗАВЕРШЕНА!")
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("✅ Регистрация пользователей")
    print("✅ JWT аутентификация")
    print("✅ Защищенные эндпоинты")
    print("✅ Управление кошельком")
    print("✅ Получение ML моделей")
    print("✅ Валидация запросов на предсказания")
    print("✅ История транзакций и задач")
    print("✅ Обработка ошибок")
    print("✅ Health checks")
    
    print(f"\n📖 Документация API: {API_BASE}/docs")
    print(f"📚 ReDoc: {API_BASE}/redoc")

def test_api_security():
    """Тестирование безопасности API"""
    print("\n🔒 ТЕСТИРОВАНИЕ БЕЗОПАСНОСТИ")
    print("=" * 30)
    
    # Тест доступа без токена
    print("\n🔐 Тест доступа без авторизации")
    protected_endpoints = [
        "/auth/me",
        "/wallet", 
        "/wallet/transactions",
        "/predict",
        "/tasks"
    ]
    
    for endpoint in protected_endpoints:
        response = requests.get(f"{API_BASE}{endpoint}")
        if response.status_code == 403:
            print(f"✅ {endpoint}: защищен")
        else:
            print(f"❌ {endpoint}: НЕ защищен ({response.status_code})")
    
    # Тест с недействительным токеном
    print("\n🚫 Тест с недействительным токеном")
    fake_headers = {"Authorization": "Bearer fake_token"}
    response = requests.get(f"{API_BASE}/auth/me", headers=fake_headers)
    if response.status_code == 401:
        print("✅ Недействительный токен отклонен")
    else:
        print(f"❌ Недействительный токен принят ({response.status_code})")

if __name__ == "__main__":
    try:
        print("🔍 Проверка доступности API...")
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API доступен")
            demo_api()
            test_api_security()
        else:
            print(f"❌ API недоступен: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к API: {e}")
        print(f"💡 Убедитесь, что сервер запущен на {API_BASE}")
        print("   Запустите: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")