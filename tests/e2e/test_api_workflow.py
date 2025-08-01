#!/usr/bin/env python3
"""
Быстрый тест API без ML части
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont

def create_test_image() -> str:
    """Создание тестового изображения"""
    image = Image.new('RGB', (200, 60), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 20), "x² + y² = r²", fill='black', font=font)
    
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_api():
    """Тестирование API"""
    base_url = "http://localhost:8000"
    
    # 1. Проверяем здоровье API
    print("🔍 Проверяем API...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ API отвечает: {response.status_code}")
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        return
    
    # 2. Регистрация пользователя
    print("📝 Регистрация пользователя...")
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/register", json=user_data)
        if response.status_code == 409:
            print("ℹ️  Пользователь уже существует")
        elif response.status_code == 201:
            print("✅ Пользователь зарегистрирован")
        else:
            print(f"⚠️  Неожиданный статус регистрации: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        return
    
    # 3. Авторизация
    print("🔐 Авторизация...")
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print("✅ Авторизация успешна")
        else:
            print(f"❌ Ошибка авторизации: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return
    
    # 4. Проверяем профиль пользователя
    print("👤 Получение профиля...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{base_url}/users/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Профиль получен: {user_info['username']}")
        else:
            print(f"❌ Ошибка получения профиля: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка получения профиля: {e}")
    
    # 5. Проверяем кошелек
    print("💰 Проверка кошелька...")
    try:
        response = requests.get(f"{base_url}/wallet", headers=headers)
        if response.status_code == 200:
            wallet_info = response.json()
            print(f"✅ Баланс кошелька: {wallet_info['balance']} кредитов")
        else:
            print(f"❌ Ошибка получения кошелька: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка получения кошелька: {e}")
    
    # 6. Получаем список моделей
    print("🤖 Получение списка ML моделей...")
    try:
        response = requests.get(f"{base_url}/models", headers=headers)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Найдено моделей: {len(models)}")
            if models:
                print(f"   Первая модель: {models[0]}")
        else:
            print(f"❌ Ошибка получения моделей: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка получения моделей: {e}")
    
    print("\n🎉 Базовое тестирование API завершено!")
    print(f"🌐 Документация API: {base_url}/docs")
    print(f"🌐 Frontend: http://localhost:5173")
    print(f"🐰 RabbitMQ Management: http://localhost:15672 (guest/guest)")

if __name__ == "__main__":
    test_api()