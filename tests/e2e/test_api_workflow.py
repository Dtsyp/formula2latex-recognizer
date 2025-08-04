import pytest
import json
import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_services():
    with patch('api.dependencies.get_user_service') as mock_user_service, \
         patch('api.dependencies.get_wallet_service') as mock_wallet_service, \
         patch('api.dependencies.get_task_service') as mock_task_service:
        
        yield {
            'user_service': mock_user_service,
            'wallet_service': mock_wallet_service,
            'task_service': mock_task_service
        }


class TestUserWorkflow:
    
    def test_user_registration_workflow(self, client, mock_services):
        from domain.user import User
        from uuid import uuid4
        
        user_id = uuid4()
        mock_user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hashed_password",
            role="user"
        )
        
        mock_services['user_service'].return_value.register_user.return_value = mock_user
        
        response = client.post("/api/users/register", json={
            "email": "test@example.com",
            "password": "strongpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"
        assert "password" not in data

    def test_user_registration_duplicate_email(self, client, mock_services):
        mock_services['user_service'].return_value.register_user.side_effect = \
            ValueError("Пользователь с email test@example.com уже существует")
        
        response = client.post("/api/users/register", json={
            "email": "test@example.com", 
            "password": "strongpassword123"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "уже существует" in data["detail"]

    def test_user_login_workflow(self, client, mock_services):
        from domain.user import User
        from uuid import uuid4
        
        user_id = uuid4()
        mock_user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hashed_password",
            role="user"
        )
        
        mock_services['user_service'].return_value.authenticate_user.return_value = mock_user
        
        with patch('api.auth.create_access_token') as mock_create_token:
            mock_create_token.return_value = "test_jwt_token"
            
            response = client.post("/api/auth/login", data={
                "username": "test@example.com",
                "password": "correctpassword"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_jwt_token"
        assert data["token_type"] == "bearer"

    def test_user_login_invalid_credentials(self, client, mock_services):
        mock_services['user_service'].return_value.authenticate_user.return_value = None
        
        response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "Неверные учетные данные" in data["detail"]


class TestWalletWorkflow:
    
    def test_wallet_topup_workflow(self, client, mock_services):
        from domain.wallet import TopUpTransaction
        from uuid import uuid4
        
        transaction_id = uuid4()
        wallet_id = uuid4()
        
        mock_transaction = TopUpTransaction(
            id=transaction_id,
            wallet_id=wallet_id,
            amount=Decimal("100.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("150.00")
        )
        
        mock_services['wallet_service'].return_value.top_up_wallet.return_value = mock_transaction
        
        with patch('api.auth.get_current_user') as mock_get_user:
            from domain.user import User
            mock_user = User(
                id=uuid4(),
                email="test@example.com",
                password_hash="hash",
                role="user"
            )
            mock_get_user.return_value = mock_user
            
            response = client.post(
                "/api/wallet/topup",
                json={"amount": 100.00, "description": "Test topup"},
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "100.00"
        assert data["post_balance"] == "150.00"

    def test_wallet_get_balance(self, client, mock_services):
        from domain.wallet import Wallet
        from uuid import uuid4
        
        wallet_id = uuid4()
        user_id = uuid4()
        
        mock_wallet = Wallet(
            id=wallet_id,
            owner_id=user_id,
            balance=Decimal("250.50")
        )
        
        mock_services['wallet_service'].return_value.get_user_wallet.return_value = mock_wallet
        
        with patch('api.auth.get_current_user') as mock_get_user:
            from domain.user import User
            mock_user = User(
                id=user_id,
                email="test@example.com", 
                password_hash="hash",
                role="user"
            )
            mock_get_user.return_value = mock_user
            
            response = client.get(
                "/api/wallet/balance",
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == "250.50"

    def test_wallet_transaction_history(self, client, mock_services):
        from domain.wallet import TopUpTransaction, SpendTransaction  
        from uuid import uuid4
        
        wallet_id = uuid4()
        user_id = uuid4()
        
        transactions = [
            TopUpTransaction(
                id=uuid4(),
                wallet_id=wallet_id,
                amount=Decimal("100.00"),
                timestamp=datetime.datetime.utcnow(),
                post_balance=Decimal("100.00")
            ),
            SpendTransaction(
                id=uuid4(),
                wallet_id=wallet_id,
                amount=Decimal("25.00"),
                timestamp=datetime.datetime.utcnow(),
                post_balance=Decimal("75.00")
            )
        ]
        
        mock_services['wallet_service'].return_value.get_transaction_history.return_value = transactions
        
        with patch('api.auth.get_current_user') as mock_get_user:
            from domain.user import User
            mock_user = User(
                id=user_id,
                email="test@example.com",
                password_hash="hash",  
                role="user"
            )
            mock_get_user.return_value = mock_user
            
            response = client.get(
                "/api/wallet/transactions",
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 2
        assert data["transactions"][0]["amount"] == "100.00"
        assert data["transactions"][1]["amount"] == "25.00"


class TestTaskWorkflow:
    
    def test_create_task_workflow(self, client, mock_services):
        from domain.task import RecognitionTask
        from domain.file import File  
        from domain.model import MLModel
        from uuid import uuid4
        
        task_id = uuid4()
        user_id = uuid4()
        model_id = uuid4()
        
        mock_file = File(path="test.png", content_type="image/png")
        mock_model = MLModel(id=model_id, name="Test Model", credit_cost=Decimal("5.00"))
        
        mock_task = RecognitionTask(
            id=task_id,
            user_id=user_id,
            file=mock_file,
            model=mock_model
        )
        
        mock_services['task_service'].return_value.create_recognition_task.return_value = mock_task
        
        with patch('api.auth.get_current_user') as mock_get_user:
            from domain.user import User
            mock_user = User(
                id=user_id,
                email="test@example.com",
                password_hash="hash",
                role="user"
            )
            mock_get_user.return_value = mock_user
            
            response = client.post(
                "/api/tasks/create",
                json={
                    "image_data": "base64_image_data",
                    "filename": "test.png",
                    "model_id": str(model_id)
                },
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task_id)
        assert data["status"] == "pending"

    def test_create_task_insufficient_funds(self, client, mock_services):
        mock_services['task_service'].return_value.create_recognition_task.side_effect = \
            ValueError("Недостаточно средств для выполнения задачи")
        
        with patch('api.auth.get_current_user') as mock_get_user:
            from domain.user import User
            from uuid import uuid4
            mock_user = User(
                id=uuid4(),
                email="test@example.com",
                password_hash="hash",
                role="user"
            )
            mock_get_user.return_value = mock_user
            
            response = client.post(
                "/api/tasks/create",
                json={
                    "image_data": "base64_image_data",
                    "filename": "test.png", 
                    "model_id": str(uuid4())
                },
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "Недостаточно средств" in data["detail"]

    def test_get_user_tasks(self, client, mock_services):
        from domain.task import RecognitionTask
        from domain.file import File
        from domain.model import MLModel
        from uuid import uuid4
        
        user_id = uuid4()
        
        mock_tasks = [
            RecognitionTask(
                id=uuid4(),
                user_id=user_id,
                file=File("test1.png", "image/png"),
                model=MLModel(uuid4(), "Model1", Decimal("5.00"))
            ),
            RecognitionTask(
                id=uuid4(),
                user_id=user_id,
                file=File("test2.png", "image/png"),
                model=MLModel(uuid4(), "Model2", Decimal("3.00"))
            )
        ]
        
        mock_services['task_service'].return_value.get_user_tasks.return_value = mock_tasks
        
        with patch('api.auth.get_current_user') as mock_get_user:
            from domain.user import User
            mock_user = User(
                id=user_id,
                email="test@example.com",
                password_hash="hash",
                role="user"
            )
            mock_get_user.return_value = mock_user
            
            response = client.get(
                "/api/tasks/",
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["status"] == "pending"
        assert data["tasks"][1]["status"] == "pending"