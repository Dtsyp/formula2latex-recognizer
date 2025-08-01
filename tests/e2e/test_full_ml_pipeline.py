#!/usr/bin/env python3
import base64
import io
import json
import time
from PIL import Image, ImageDraw, ImageFont
import requests

def create_formula_image(formula_text: str = "x² + y² = r²") -> str:
    print(f"🖼️  Создаем изображение с формулой: {formula_text}")
    
    width, height = 400, 120
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), formula_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), formula_text, fill='black', font=font)
    
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    print("✅ Изображение создано")
    return image_data

def test_full_ml_pipeline():
    base_url = "http://localhost:8000"
    
    print("🚀 Запуск полного теста ML системы")
    print("=" * 60)
    
    test_image = create_formula_image("∫x²dx = x³/3 + C")
    print("👤 Регистрация тестового пользователя...")
    user_data = {
        "username": "ml_test_user",
        "email": "mltest@example.com",
        "password": "testpass123"
    }
    
    try:
        requests.post(f"{base_url}/auth/register", json=user_data)
        print("✅ Пользователь зарегистрирован")
    except Exception as e:
        print(f"⚠️  Ошибка регистрации (возможно уже существует): {e}")
    
    # 3. Авторизуемся
    print("🔐 Авторизация...")
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    login_response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Ошибка авторизации: {login_response.text}")
        return False
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ Авторизация успешна")
    
    # 4. Получаем список ML моделей
    print("🤖 Получение ML моделей...")
    models_response = requests.get(f"{base_url}/models", headers=headers)
    
    if models_response.status_code != 200:
        print(f"❌ Ошибка получения моделей: {models_response.text}")
        return False
    
    models = models_response.json()
    if not models:
        print("❌ Нет доступных ML моделей")
        return False
        
    model_id = models[0]['id']
    model_name = models[0]['name']
    model_cost = models[0]['credit_cost']
    print(f"✅ Выбрана модель: {model_name} (стоимость: {model_cost} кредитов)")
    
    # 5. Проверяем баланс кошелька
    print("💰 Проверка баланса...")
    wallet_response = requests.get(f"{base_url}/wallet", headers=headers)
    
    if wallet_response.status_code == 200:
        wallet = wallet_response.json()
        balance = float(wallet['balance'])
        print(f"💰 Текущий баланс: {balance} кредитов")
        
        if balance < float(model_cost):
            print("⚠️  Недостаточно кредитов, пополняем кошелек...")
            topup_data = {"amount": 50.0}
            requests.post(f"{base_url}/wallet/topup", json=topup_data, headers=headers)
            print("✅ Кошелек пополнен")
    
    # 6. Отправляем задачу на ML обработку
    print("🔬 Отправка задачи на ML обработку...")
    
    prediction_data = {
        "filename": "test_formula.png", 
        "file_content": test_image,
        "model_id": model_id
    }
    
    predict_response = requests.post(
        f"{base_url}/predict", 
        json=prediction_data,
        headers=headers
    )
    
    if predict_response.status_code != 200:
        print(f"❌ Ошибка отправки задачи: {predict_response.text}")
        return False
    
    task_data = predict_response.json()
    task_id = task_data["id"]
    print(f"✅ Задача отправлена в ML очередь: {task_id}")
    print(f"📊 Начальный статус: {task_data['status']}")
    
    # 7. Ожидаем обработки
    print("⏳ Ожидание обработки ML воркером...")
    max_wait_time = 60  # 60 секунд
    check_interval = 3   # проверяем каждые 3 секунды
    
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait_time:
        task_response = requests.get(f"{base_url}/tasks/{task_id}", headers=headers)
        
        if task_response.status_code == 200:
            task_info = task_response.json()
            status = task_info["status"]
            
            print(f"📊 Статус: {status}")
            
            if status == "completed":
                print("🎉 ML обработка завершена успешно!")
                print(f"📝 Результат LaTeX: {task_info['output_data']}")
                print(f"💰 Списано кредитов: {task_info['credits_charged']}")
                return True
                
            elif status == "failed":
                print(f"❌ ML обработка завершена с ошибкой: {task_info['error_message']}")
                print(f"💰 Списано кредитов: {task_info['credits_charged']}")
                return False
                
            elif status in ["pending", "in_progress"]:
                print("⏳ Задача обрабатывается...")
            else:
                print(f"⚠️  Неизвестный статус: {status}")
        
        time.sleep(check_interval)
    
    print("⏰ Таймаут ожидания ML обработки")
    return False

def check_system_status():
    """Проверка статуса всей системы"""
    print("🔍 Проверка статуса системы...")
    
    components = [
        ("Backend API", "http://localhost:8000/health"),
        ("RabbitMQ Management", "http://localhost:15672"),
    ]
    
    all_good = True
    
    for name, url in components:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: работает")
            else:
                print(f"⚠️  {name}: отвечает с кодом {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"❌ {name}: недоступен ({e})")
            all_good = False
    
    return all_good

def main():
    """Главная функция тестирования"""
    print("🧪 End-to-End тест ML системы Formula2LaTeX")
    print("=" * 60)
    
    # Проверяем статус системы
    if not check_system_status():
        print("\n❌ Не все компоненты системы работают")
        return 1
    
    print("\n" + "=" * 60)
    
    # Запускаем полный тест
    success = test_full_ml_pipeline()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ ML система работает корректно")
        print("✅ Взаимодействие API ↔ RabbitMQ ↔ ML Worker работает")
        print("✅ Обработка результатов работает")
        return 0
    else:
        print("❌ ТЕСТЫ НЕ ПРОШЛИ")
        print("🔧 Проверьте логи Docker контейнеров:")
        print("   docker-compose logs ml-worker-1")
        print("   docker-compose logs result-processor")
        return 1

if __name__ == "__main__":
    exit(main())