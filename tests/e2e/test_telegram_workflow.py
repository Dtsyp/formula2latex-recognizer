#!/usr/bin/env python3
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
import base64
import io
from PIL import Image

# Mock telegram components
with patch.dict('sys.modules', {
    'aiogram': Mock(),
    'aiohttp': Mock(),
    'requests': Mock()
}):
    import sys
    import os
    bot_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src', 'telegram_bot')
    sys.path.insert(0, bot_path)
    
    from handlers import FormulaBotHandlers
    from api_client import APIClient


class TestTelegramWorkflow:
    
    def create_test_image(self):
        """Создание тестового изображения"""
        image = Image.new('RGB', (200, 100), 'white')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @pytest.mark.asyncio
    async def test_start_command(self):
        """Тест команды /start"""
        # Mock message and bot
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.from_user.first_name = "Test User"
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        
        await handlers.start_handler(mock_message)
        
        # Проверяем что отправлено приветственное сообщение
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Добро пожаловать" in call_args
        assert "Test User" in call_args

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Тест команды /help"""
        mock_message = Mock()
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        
        await handlers.help_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Команды бота" in call_args
        assert "/register" in call_args
        assert "/upload" in call_args

    @pytest.mark.asyncio
    @patch('handlers.APIClient')
    async def test_register_command_success(self, mock_api_client):
        """Тест успешной регистрации"""
        # Mock API client
        mock_client = Mock()
        mock_client.register_user = AsyncMock(return_value={
            'success': True,
            'user_id': 'test-user-id',
            'token': 'test-token'
        })
        mock_api_client.return_value = mock_client
        
        # Mock message
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.get_args.return_value = "user@example.com password123"
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        
        await handlers.register_handler(mock_message)
        
        # Проверяем что пользователь зарегистрирован
        mock_client.register_user.assert_called_once_with("user@example.com", "password123")
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "успешно зарегистрированы" in call_args

    @pytest.mark.asyncio
    @patch('handlers.APIClient')
    async def test_register_command_failure(self, mock_api_client):
        """Тест неудачной регистрации"""
        # Mock API client с ошибкой
        mock_client = Mock()
        mock_client.register_user = AsyncMock(return_value={
            'success': False,
            'error': 'Email already exists'
        })
        mock_api_client.return_value = mock_client
        
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.get_args.return_value = "user@example.com password123"
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        
        await handlers.register_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Ошибка регистрации" in call_args
        assert "Email already exists" in call_args

    @pytest.mark.asyncio
    @patch('handlers.APIClient')
    async def test_login_command_success(self, mock_api_client):
        """Тест успешного входа"""
        mock_client = Mock()
        mock_client.login_user = AsyncMock(return_value={
            'success': True,
            'token': 'test-token',
            'user_id': 'test-user-id'
        })
        mock_api_client.return_value = mock_client
        
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.get_args.return_value = "user@example.com password123"
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        
        await handlers.login_handler(mock_message)
        
        mock_client.login_user.assert_called_once_with("user@example.com", "password123")
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "успешно выполнен" in call_args

    @pytest.mark.asyncio
    @patch('handlers.APIClient')
    async def test_balance_command(self, mock_api_client):
        """Тест команды /balance"""
        mock_client = Mock()
        mock_client.get_wallet = AsyncMock(return_value={
            'success': True,
            'balance': '25.50',
            'currency': 'credits'
        })
        mock_api_client.return_value = mock_client
        
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        # Mock что пользователь авторизован
        handlers.user_sessions = {123456: {'token': 'test-token'}}
        
        await handlers.balance_handler(mock_message)
        
        mock_client.get_wallet.assert_called_once_with('test-token')
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "25.50" in call_args
        assert "кредитов" in call_args

    @pytest.mark.asyncio
    @patch('handlers.APIClient')
    async def test_photo_upload_success(self, mock_api_client):
        """Тест успешной загрузки и обработки фото"""
        # Mock API client
        mock_client = Mock()
        mock_client.get_models = AsyncMock(return_value={
            'success': True,
            'models': [{'id': 'model-1', 'name': 'Basic OCR', 'credit_cost': '2.50'}]
        })
        mock_client.predict_formula = AsyncMock(return_value={
            'success': True,
            'task_id': 'task-123',
            'latex_code': 'x^2 + y^2 = r^2',
            'confidence': 0.95,
            'credits_charged': '2.50'
        })
        mock_api_client.return_value = mock_client
        
        # Mock photo message
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.photo = [Mock()]
        mock_message.photo[-1].file_id = 'photo-file-id'
        mock_message.answer = AsyncMock()
        mock_message.bot.download_file = AsyncMock()
        
        # Mock file download
        test_image_data = self.create_test_image()
        mock_message.bot.download_file.return_value = base64.b64decode(test_image_data)
        
        handlers = FormulaBotHandlers()
        # Mock авторизованного пользователя
        handlers.user_sessions = {123456: {'token': 'test-token'}}
        
        await handlers.photo_handler(mock_message)
        
        # Проверяем что модели были получены
        mock_client.get_models.assert_called_once_with('test-token')
        
        # Проверяем что предикт был выполнен
        mock_client.predict_formula.assert_called_once()
        
        # Проверяем ответ пользователю
        assert mock_message.answer.call_count >= 2  # Минимум 2 сообщения
        
        # Проверяем что в одном из ответов есть LaTeX результат
        call_args_list = [call[0][0] for call in mock_message.answer.call_args_list]
        latex_found = any('x^2 + y^2 = r^2' in msg for msg in call_args_list)
        assert latex_found

    @pytest.mark.asyncio
    async def test_photo_upload_unauthorized(self):
        """Тест загрузки фото неавторизованным пользователем"""
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.photo = [Mock()]
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        # Пользователь не авторизован
        handlers.user_sessions = {}
        
        await handlers.photo_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "авторизуйтесь" in call_args.lower() or "войдите" in call_args.lower()

    @pytest.mark.asyncio
    @patch('handlers.APIClient')
    async def test_history_command(self, mock_api_client):
        """Тест команды /history"""
        mock_client = Mock()
        mock_client.get_tasks = AsyncMock(return_value={
            'success': True,
            'tasks': [
                {
                    'id': 'task-1',
                    'status': 'completed',
                    'output_data': 'x^2 + y^2',
                    'credits_charged': '2.50',
                    'created_at': '2024-01-01T12:00:00Z'
                },
                {
                    'id': 'task-2', 
                    'status': 'failed',
                    'error_message': 'Low image quality',
                    'credits_charged': '2.50',
                    'created_at': '2024-01-01T13:00:00Z'
                }
            ]
        })
        mock_api_client.return_value = mock_client
        
        mock_message = Mock()
        mock_message.from_user.id = 123456
        mock_message.answer = AsyncMock()
        
        handlers = FormulaBotHandlers()
        handlers.user_sessions = {123456: {'token': 'test-token'}}
        
        await handlers.history_handler(mock_message)
        
        mock_client.get_tasks.assert_called_once_with('test-token')
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        
        # Проверяем что в истории есть обе задачи
        assert 'x^2 + y^2' in call_args
        assert 'completed' in call_args
        assert 'failed' in call_args
        assert 'Low image quality' in call_args


class TestTelegramAPIClient:
    
    @pytest.mark.asyncio
    @patch('api_client.aiohttp.ClientSession')
    async def test_register_user_success(self, mock_session):
        """Тест успешной регистрации через API client"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'id': 'user-123',
            'email': 'test@example.com'
        })
        
        mock_session_instance = Mock()
        mock_session_instance.post = AsyncMock(return_value=mock_response)
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        client = APIClient("http://localhost:8000")
        result = await client.register_user("test@example.com", "password123")
        
        assert result['success'] is True
        assert result['user_id'] == 'user-123'
        
        # Проверяем что был сделан POST запрос
        mock_session_instance.post.assert_called_once()
        call_args = mock_session_instance.post.call_args
        assert '/auth/register' in call_args[0][0]

    @pytest.mark.asyncio 
    @patch('api_client.aiohttp.ClientSession')
    async def test_predict_formula_success(self, mock_session):
        """Тест успешного предикта через API client"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'id': 'task-123',
            'status': 'completed',
            'output_data': 'x^2 + y^2 = r^2',
            'credits_charged': '2.50'
        })
        
        mock_session_instance = Mock()
        mock_session_instance.post = AsyncMock(return_value=mock_response)
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        client = APIClient("http://localhost:8000")
        
        test_image_data = base64.b64encode(b"test image data").decode()
        result = await client.predict_formula(
            token="test-token",
            model_id="model-1", 
            image_data=test_image_data,
            filename="test.png"
        )
        
        assert result['success'] is True
        assert result['latex_code'] == 'x^2 + y^2 = r^2'
        assert result['task_id'] == 'task-123'
        assert result['credits_charged'] == '2.50'