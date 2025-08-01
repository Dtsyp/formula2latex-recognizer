#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ML системы распознавания формул
Тестирует REST API и интеграцию с RabbitMQ
"""

import requests
import base64
import json
import time
import io
from PIL import Image, ImageDraw, ImageFont
import argparse


def create_test_image() -> str:
    """Создание тестового изображения с формулой"""
    # Создаем простое изображение с текстом формулы
    width, height = 300, 100
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Рисуем простую формулу
    try:
        # Пытаемся использовать системный шрифт 
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # Если не получается, используем стандартный
        font = ImageFont.load_default()
    
    # Формула: x^2 + y^2 = r^2
    formula_text = "x² + y² = r²"
    
    # Получаем размер текста
    bbox = draw.textbbox((0, 0), formula_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Центрируем текст
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), formula_text, fill='black', font=font)
    
    # Конвертируем в base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return image_data


def test_rest_api(api_url: str, test_image: str) -> dict:
    """
    Тестирование REST API
    
    Args:
        api_url: URL API сервера
        test_image: Base64 encoded изображение
        
    Returns:
        Результат теста
    """
    print(f"🔍 Тестирование REST API: {api_url}")
    
    # Сначала нужно зарегистрироваться и получить токен
    # Для упрощения теста используем мок-данные
    
    # Тестовые данные пользователя
    test_user = {
        "username": "test_user",
        "email": "test@example.com", 
        "password": "test_password"
    }
    
    try:
        # 1. Регистрация пользователя
        print("📝 Регистрация тестового пользователя...")
        register_response = requests.post(
            f"{api_url}/auth/register",
            json=test_user,
            timeout=10
        )
        
        if register_response.status_code == 409:
            print("ℹ️  Пользователь уже существует")
        elif register_response.status_code != 201:
            print(f"❌ Ошибка регистрации: {register_response.status_code}")
            return {"success": False, "error": f"Registration failed: {register_response.status_code}"}
        
        # 2. Авторизация
        print("🔐 Авторизация...")
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        
        login_response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Ошибка авторизации: {login_response.status_code}")
            return {"success": False, "error": f"Login failed: {login_response.status_code}"}
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print("✅ Авторизация успешна")
        
        # 3. Создание задачи предикта
        print("🚀 Отправка задачи распознавания...")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        predict_data = {
            "filename": "test_formula.png",
            "file_content": test_image,
            "model_id": 1  # Предполагаем что есть модель с ID 1
        }
        
        predict_response = requests.post(
            f"{api_url}/tasks/predict",
            json=predict_data,
            headers=headers,
            timeout=30
        )
        
        if predict_response.status_code != 200:
            print(f"❌ Ошибка создания задачи: {predict_response.status_code}")
            print(f"Response: {predict_response.text}")
            return {"success": False, "error": f"Prediction failed: {predict_response.status_code}"}
        
        task_data = predict_response.json()
        task_id = task_data["id"]
        print(f"✅ Задача создана: {task_id}")
        
        # 4. Ожидание обработки задачи
        print("⏳ Ожидание обработки...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            task_response = requests.get(
                f"{api_url}/tasks/{task_id}",
                headers=headers,
                timeout=10
            )
            
            if task_response.status_code == 200:
                task_info = task_response.json()
                status = task_info["status"]
                
                print(f"📊 Статус задачи: {status}")
                
                if status == "completed":
                    print(f"🎉 Задача выполнена! Результат: {task_info['output_data']}")
                    return {
                        "success": True,
                        "task_id": task_id,
                        "result": task_info['output_data'],
                        "status": status
                    }
                elif status == "failed":
                    print(f"❌ Задача завершена с ошибкой: {task_info['error_message']}")
                    return {
                        "success": False,
                        "task_id": task_id,
                        "error": task_info['error_message'],
                        "status": status
                    }
            
            time.sleep(2)
            attempt += 1
        
        print("⏰ Таймаут ожидания результата")
        return {"success": False, "error": "Timeout waiting for result"}
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сетевого запроса: {e}")
        return {"success": False, "error": f"Network error: {e}"}
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def test_telegram_bot(bot_token: str) -> dict:
    """
    Тестирование Telegram бота
    
    Args:
        bot_token: Токен Telegram бота
        
    Returns:
        Результат теста
    """
    print(f"🤖 Тестирование Telegram бота...")
    
    try:
        # Проверяем что бот отвечает
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getMe",
            timeout=10
        )
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info["ok"]:
                print(f"✅ Бот активен: @{bot_info['result']['username']}")
                return {"success": True, "bot_info": bot_info["result"]}
            else:
                print("❌ Бот неактивен")
                return {"success": False, "error": "Bot is not active"}
        else:
            print(f"❌ Ошибка проверки бота: {response.status_code}")
            return {"success": False, "error": f"Bot check failed: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Ошибка тестирования бота: {e}")
        return {"success": False, "error": f"Bot test error: {e}"}


def main():
    """Главная функция тестирования"""
    parser = argparse.ArgumentParser(description='Тестирование ML системы')
    parser.add_argument('--api-url', default='http://localhost:8000', help='URL API сервера')
    parser.add_argument('--bot-token', help='Токен Telegram бота')
    parser.add_argument('--skip-bot', action='store_true', help='Пропустить тестирование бота')
    
    args = parser.parse_args()
    
    print("🧪 Запуск тестирования ML системы распознавания формул")
    print("=" * 60)
    
    # Создаем тестовое изображение
    print("🖼️  Создание тестового изображения...")
    test_image = create_test_image()
    print("✅ Тестовое изображение создано")
    
    # Тестируем REST API
    api_result = test_rest_api(args.api_url, test_image)
    
    # Тестируем Telegram бота
    bot_result = None
    if not args.skip_bot and args.bot_token:
        bot_result = test_telegram_bot(args.bot_token)
    elif not args.skip_bot:
        print("⚠️  Токен бота не предоставлен, пропускаем тестирование бота")
        bot_result = {"success": False, "error": "No bot token provided"}
    else:
        print("⚠️  Тестирование бота пропущено")
        bot_result = {"success": True, "skipped": True}
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    print(f"REST API: {'✅ УСПЕШНО' if api_result['success'] else '❌ НЕУСПЕШНО'}")
    if not api_result['success']:
        print(f"  Ошибка: {api_result['error']}")
    else:
        print(f"  Результат: {api_result.get('result', 'N/A')}")
    
    if not bot_result.get('skipped', False):
        print(f"Telegram Bot: {'✅ УСПЕШНО' if bot_result['success'] else '❌ НЕУСПЕШНО'}")
        if not bot_result['success']:
            print(f"  Ошибка: {bot_result['error']}")
    else:
        print("Telegram Bot: ⚠️  ПРОПУЩЕНО")
    
    overall_success = api_result['success'] and (bot_result['success'] or bot_result.get('skipped', False))
    print(f"\nОБЩИЙ РЕЗУЛЬТАТ: {'✅ УСПЕШНО' if overall_success else '❌ НЕУСПЕШНО'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit(main())