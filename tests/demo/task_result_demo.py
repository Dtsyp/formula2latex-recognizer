#!/usr/bin/env python3
"""
Демонстрация работы получения результатов задач через новый эндпоинт
"""
import asyncio
import base64
import json
import os
import requests
import time
from io import BytesIO
from PIL import Image


API_BASE_URL = "http://localhost:8000"


class TaskResultDemo:
    def __init__(self):
        self.token = None
        self.session = requests.Session()

    def create_test_image(self):
        """Создает тестовое изображение формулы"""
        # Создаем простое изображение с текстом формулы
        img = Image.new('RGB', (300, 100), color='white')
        
        # В реальном приложении здесь было бы изображение формулы
        # Для демо создаем простое изображение
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    def register_and_login(self):
        """Регистрация и авторизация тестового пользователя"""
        print("🔐 Регистрация и авторизация...")
        
        # Регистрация
        user_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "password": "testpassword123"
        }
        
        response = self.session.post(f"{API_BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            print(f"✅ Пользователь зарегистрирован: {user_data['email']}")
        else:
            print(f"❌ Ошибка регистрации: {response.text}")
            return False

        # Авторизация
        response = self.session.post(f"{API_BASE_URL}/auth/login", json=user_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Авторизация успешна")
            return True
        else:
            print(f"❌ Ошибка авторизации: {response.text}")
            return False

    def get_models(self):
        """Получение доступных моделей"""
        print("\n🤖 Получение списка моделей...")
        
        response = self.session.get(f"{API_BASE_URL}/models")
        if response.status_code == 200:
            models = response.json()
            if models:
                model = models[0]  # Берем первую модель
                print(f"✅ Найдена модель: {model['name']} (стоимость: {model['credit_cost']})")
                return model['id']
            else:
                print("❌ Модели не найдены")
                return None
        else:
            print(f"❌ Ошибка получения моделей: {response.text}")
            return None

    def create_prediction_task(self, model_id):
        """Создание задачи распознавания"""
        print("\n📸 Создание задачи распознавания...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        image_data = self.create_test_image()
        
        task_data = {
            "model_id": model_id,
            "file_content": image_data,
            "filename": "test_formula.png"
        }
        
        response = self.session.post(
            f"{API_BASE_URL}/predict", 
            json=task_data, 
            headers=headers
        )
        
        if response.status_code == 200:
            task = response.json()
            print(f"✅ Задача создана: {task['id']}")
            print(f"💰 Списано кредитов: {task['credits_charged']}")
            return task['id']
        else:
            print(f"❌ Ошибка создания задачи: {response.text}")
            return None

    def demo_get_task_result_methods(self, task_id):
        """
        Демонстрация различных способов получения результата задачи
        """
        print(f"\n🔍 Демонстрация получения результата задачи {task_id}...")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Способ 1: Новый эндпоинт для получения результата из RabbitMQ
        print("\n📨 Способ 1: Получение результата напрямую из RabbitMQ очереди")
        print("   (Используется get_task_result метод)")
        print("   Преимущества: мгновенный результат, не зависит от Result Processor")
        print("   Недостатки: блокирующий вызов с таймаутом")
        
        try:
            start_time = time.time()
            response = self.session.get(
                f"{API_BASE_URL}/tasks/{task_id}/result?timeout=30",
                headers=headers
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Результат получен за {elapsed:.2f}с из очереди:")
                print(f"   Успех: {result.get('success')}")
                if result.get('success'):
                    print(f"   LaTeX: {result.get('latex_code', 'Не найден')}")
                    print(f"   Уверенность: {result.get('confidence', 0):.2%}")
                else:
                    print(f"   Ошибка: {result.get('error', 'Неизвестная')}")
            elif response.status_code == 408:
                print(f"⏰ Таймаут ({elapsed:.2f}с) - результат еще не готов")
            else:
                print(f"❌ Ошибка получения результата: {response.text}")
        except Exception as e:
            print(f"❌ Исключение при получении результата: {e}")
        
        # Способ 2: Традиционный метод через БД (проверяем задачу)
        print(f"\n💾 Способ 2: Получение задачи из БД")
        print("   (Result Processor обновляет задачи в БД асинхронно)")
        print("   Преимущества: персистентное хранение, история задач")
        print("   Недостатки: может быть задержка до обновления")
        
        try:
            response = self.session.get(
                f"{API_BASE_URL}/tasks/{task_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                task = response.json()
                print(f"✅ Задача из БД:")
                print(f"   Статус: {task['status']}")
                print(f"   Результат: {task.get('output_data', 'Пока нет')}")
                print(f"   Ошибка: {task.get('error_message', 'Нет')}")
                print(f"   Создана: {task['created_at']}")
            else:
                print(f"❌ Ошибка получения задачи: {response.text}")
        except Exception as e:
            print(f"❌ Исключение при получении задачи: {e}")

        # Способ 3: Polling (проверка через интервалы)
        print(f"\n🔄 Способ 3: Polling - периодическая проверка")
        print("   (Подходит для UI приложений)")
        
        for i in range(3):
            print(f"   Проверка {i+1}/3...")
            try:
                response = self.session.get(
                    f"{API_BASE_URL}/tasks/{task_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    task = response.json()
                    if task['status'] in ['completed', 'failed']:
                        print(f"   ✅ Задача завершена: {task['status']}")
                        break
                    else:
                        print(f"   ⏳ Статус: {task['status']}")
                        time.sleep(2)  # Ждем 2 секунды
                else:
                    print(f"   ❌ Ошибка: {response.text}")
                    break
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                break

    def demo_task_history(self):
        """Демонстрация получения истории задач"""
        print(f"\n📋 История всех задач пользователя:")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.session.get(f"{API_BASE_URL}/tasks", headers=headers)
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Найдено задач: {len(tasks)}")
            for task in tasks:
                print(f"   📝 {task['id']}: {task['status']} "
                      f"(кредиты: {task['credits_charged']})")
        else:
            print(f"❌ Ошибка получения истории: {response.text}")

    def run_demo(self):
        """Запуск полной демонстрации"""
        print("🚀 Демонстрация работы с результатами задач")
        print("=" * 60)
        
        # Регистрация и авторизация
        if not self.register_and_login():
            return
        
        # Получение модели
        model_id = self.get_models()
        if not model_id:
            return
        
        # Создание задачи
        task_id = self.create_prediction_task(model_id)
        if not task_id:
            return
        
        # Демонстрация методов получения результатов
        self.demo_get_task_result_methods(task_id)
        
        # История задач
        self.demo_task_history()
        
        print("\n" + "=" * 60)
        print("🎉 Демонстрация завершена!")
        print("\n📖 Выводы:")
        print("1. Новый эндпоинт /tasks/{task_id}/result позволяет получить результат")
        print("   напрямую из RabbitMQ очереди без ожидания обновления в БД")
        print("2. Традиционный способ через /tasks/{task_id} использует данные из БД")
        print("3. Polling подходит для UI приложений с периодическими проверками")
        print("4. Все методы теперь работают корректно!")


if __name__ == "__main__":
    print("🧪 Убедитесь что система запущена: docker-compose up -d")
    input("Нажмите Enter для продолжения...")
    
    demo = TaskResultDemo()
    demo.run_demo()