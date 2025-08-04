import pytest
from unittest.mock import Mock, patch
import json
import base64
import io
from PIL import Image

with patch.dict('sys.modules', {
    'transformers': Mock(),
    'torch': Mock(),
    'torchvision': Mock(),
    'pika': Mock()
}):
    import sys
    import os
    ml_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml')
    sys.path.insert(0, ml_path)
    
    from worker import FormulaWorker
    from messaging import RabbitMQManager


class TestMLWorkerIntegration:
    
    @patch('worker.get_rabbitmq_manager')
    @patch('worker.get_model')
    def test_worker_initialization(self, mock_get_model, mock_get_rabbitmq):
        mock_rabbitmq = Mock()
        mock_model = Mock()
        mock_get_rabbitmq.return_value = mock_rabbitmq
        mock_get_model.return_value = mock_model
        
        worker = FormulaWorker("test-worker-1")
        worker.initialize()
        
        assert worker.worker_id == "test-worker-1"
        assert worker.rabbitmq_manager == mock_rabbitmq
        assert worker.ml_model == mock_model

    def test_task_validation_success(self):
        worker = FormulaWorker("test-worker")
        worker.ml_model = Mock()
        worker.ml_model.validate_image.return_value = {'valid': True, 'width': 100, 'height': 100}
        
        task_data = {
            'task_id': 'test-task-id',
            'user_id': 'test-user-id',
            'image_data': 'valid_base64_data'
        }
        
        result = worker.validate_task_data(task_data)
        
        assert result['valid'] is True
        assert 'image_info' in result

    def test_task_validation_missing_fields(self):
        worker = FormulaWorker("test-worker")
        
        task_data = {
            'task_id': 'test-task-id'
            # Missing user_id and image_data
        }
        
        result = worker.validate_task_data(task_data)
        
        assert result['valid'] is False
        assert 'Отсутствует обязательное поле' in result['error']

    def test_task_validation_invalid_image(self):
        worker = FormulaWorker("test-worker")
        worker.ml_model = Mock()
        worker.ml_model.validate_image.return_value = {'valid': False, 'error': 'Invalid image'}
        
        task_data = {
            'task_id': 'test-task-id',
            'user_id': 'test-user-id', 
            'image_data': 'invalid_base64_data'
        }
        
        result = worker.validate_task_data(task_data)
        
        assert result['valid'] is False
        assert 'Невалидное изображение' in result['error']

    @patch('worker.time')
    def test_process_task_success(self, mock_time):
        mock_time.time.side_effect = [0, 1.5]  # start_time, end_time
        
        worker = FormulaWorker("test-worker")
        worker.rabbitmq_manager = Mock()
        worker.ml_model = Mock()
        
        # Mock validation success
        worker.ml_model.validate_image.return_value = {'valid': True, 'width': 100, 'height': 100}
        
        # Mock prediction success  
        worker.ml_model.predict.return_value = {
            'success': True,
            'latex_code': 'x^2 + y^2 = r^2',
            'confidence': 0.95,
            'error': None
        }
        
        task_data = {
            'task_id': 'test-task-id',
            'user_id': 'test-user-id',
            'image_data': 'valid_base64_data'
        }
        
        worker.process_task("delivery-tag", task_data)
        
        # Verify result was published
        worker.rabbitmq_manager.publish_result.assert_called_once()
        result_call = worker.rabbitmq_manager.publish_result.call_args[0][0]
        
        assert result_call['task_id'] == 'test-task-id'
        assert result_call['success'] is True
        assert result_call['latex_code'] == 'x^2 + y^2 = r^2'
        assert result_call['processing_time'] == 1.5
        
        # Verify message was acknowledged
        worker.rabbitmq_manager.ack_message.assert_called_once_with("delivery-tag")

    def test_process_task_validation_failure(self):
        worker = FormulaWorker("test-worker")
        worker.rabbitmq_manager = Mock()
        worker.ml_model = Mock()
        
        # Mock validation failure
        worker.ml_model.validate_image.return_value = {'valid': False, 'error': 'Invalid image'}
        
        task_data = {
            'task_id': 'test-task-id',
            'user_id': 'test-user-id',
            'image_data': 'invalid_base64_data'
        }
        
        worker.process_task("delivery-tag", task_data)
        
        # Verify error result was published
        worker.rabbitmq_manager.publish_result.assert_called_once()
        result_call = worker.rabbitmq_manager.publish_result.call_args[0][0]
        
        assert result_call['task_id'] == 'test-task-id'
        assert result_call['success'] is False
        assert 'Invalid image' in result_call['error']
        
        # Verify message was acknowledged
        worker.rabbitmq_manager.ack_message.assert_called_once_with("delivery-tag")

    def test_process_task_prediction_failure(self):
        worker = FormulaWorker("test-worker")
        worker.rabbitmq_manager = Mock()
        worker.ml_model = Mock()
        
        # Mock validation success but prediction failure
        worker.ml_model.validate_image.return_value = {'valid': True, 'width': 100, 'height': 100}
        worker.ml_model.predict.return_value = {
            'success': False,
            'latex_code': None,
            'confidence': 0.0,
            'error': 'Prediction failed'
        }
        
        task_data = {
            'task_id': 'test-task-id',
            'user_id': 'test-user-id',
            'image_data': 'valid_base64_data'
        }
        
        worker.process_task("delivery-tag", task_data)
        
        # Verify error result was published
        worker.rabbitmq_manager.publish_result.assert_called_once()
        result_call = worker.rabbitmq_manager.publish_result.call_args[0][0]
        
        assert result_call['task_id'] == 'test-task-id'
        assert result_call['success'] is False
        assert result_call['error'] == 'Prediction failed'


class TestRabbitMQIntegration:
    
    @patch('messaging.pika')
    def test_rabbitmq_connection(self, mock_pika):
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        manager = RabbitMQManager()
        manager.connect()
        
        assert manager.connection == mock_connection
        assert manager.channel == mock_channel
        
        # Verify queues were declared
        mock_channel.exchange_declare.assert_called()
        mock_channel.queue_declare.assert_called()

    @patch('messaging.pika')
    def test_publish_task(self, mock_pika):
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        manager = RabbitMQManager()
        manager.connect()
        
        task_data = {
            'task_id': 'test-task-id',
            'user_id': 'test-user-id',
            'image_data': 'base64_data'
        }
        
        task_id = manager.publish_task(task_data)
        
        # Verify message was published
        mock_channel.basic_publish.assert_called()
        publish_call = mock_channel.basic_publish.call_args
        
        assert publish_call[1]['exchange'] == manager.config.task_exchange
        assert publish_call[1]['routing_key'] == manager.config.task_queue
        
        # Verify task_id was returned
        assert task_id is not None

    @patch('messaging.pika')
    def test_publish_result(self, mock_pika):
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        manager = RabbitMQManager()
        manager.connect()
        
        result_data = {
            'task_id': 'test-task-id',
            'success': True,
            'latex_code': 'x^2 + y^2'
        }
        
        manager.publish_result(result_data)
        
        # Verify result was published
        mock_channel.basic_publish.assert_called()
        publish_call = mock_channel.basic_publish.call_args
        
        assert publish_call[1]['exchange'] == manager.config.result_exchange
        assert publish_call[1]['routing_key'] == manager.config.result_queue