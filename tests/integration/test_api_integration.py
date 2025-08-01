import base64
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
from infrastructure.repositories import UserRepository, WalletRepository, MLModelRepository


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def demo_user_data():
    """Demo user data for testing"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


class TestAuthentication:
    
    def test_register_user(self, client, test_db, demo_user_data):
        response = client.post("/auth/register", json=demo_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == demo_user_data["email"]
        assert "id" in data
    
    def test_register_duplicate_email(self, client, test_db, demo_user_data):
        client.post("/auth/register", json=demo_user_data)
        
        response = client.post("/auth/register", json=demo_user_data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"
    
    def test_login_success(self, client, test_db, demo_user_data):
        client.post("/auth/register", json=demo_user_data)
        
        response = client.post("/auth/login", json=demo_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_db):
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_get_current_user(self, client, test_db, demo_user_data):
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == demo_user_data["email"]
    
    def test_unauthorized_access(self, client, test_db):
        response = client.get("/auth/me")
        assert response.status_code == 403


class TestWallet:
    
    def test_get_wallet(self, client, test_db, demo_user_data):
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/wallet", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "balance" in data
        assert data["balance"] == "0.00"
    
    def test_get_transactions_empty(self, client, test_db, demo_user_data):
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/wallet/transactions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestMLModels:
    
    def test_get_models(self, client, test_db):
        db = test_db
        model_repo = MLModelRepository(db)
        model_repo.create_model("Test Model", Decimal("5.00"))
        model_repo.create_model("Advanced Model", Decimal("10.00"))
        
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        
        model = data[0]
        assert "id" in model
        assert "name" in model
        assert "credit_cost" in model
        assert "is_active" in model


class TestPredictions:
    
    def setup_user_with_credits(self, client, test_db, user_data, credits_amount=100):
        client.post("/auth/register", json=user_data)
        login_response = client.post("/auth/login", json=user_data)
        token = login_response.json()["access_token"]
        
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        user = user_repo.get_by_email(user_data["email"])
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        transaction = wallet.top_up(Decimal(str(credits_amount)))
        wallet_repo.add_transaction(transaction)
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        return token
    
    def setup_demo_model(self, test_db):
        model_repo = MLModelRepository(test_db)
        model = model_repo.create_model("Test Model", Decimal("5.00"))
        return model
    
    def test_create_prediction_insufficient_credits(self, client, test_db, demo_user_data):
        token = self.setup_user_with_credits(client, test_db, demo_user_data, credits_amount=0)
        model = self.setup_demo_model(test_db)
        headers = {"Authorization": f"Bearer {token}"}
        
        dummy_image = base64.b64encode(b"dummy image content").decode()
        request_data = {
            "model_id": str(model.id),
            "file_content": dummy_image,
            "filename": "test_formula.png"
        }
        
        response = client.post("/predict", json=request_data, headers=headers)
        assert response.status_code == 402
        assert "Insufficient credits" in response.json()["detail"]
    
    def test_create_prediction_invalid_model(self, client, test_db, demo_user_data):
        token = self.setup_user_with_credits(client, test_db, demo_user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        dummy_image = base64.b64encode(b"dummy image content").decode()
        request_data = {
            "model_id": "00000000-0000-0000-0000-000000000000",
            "file_content": dummy_image,
            "filename": "test_formula.png"
        }
        
        response = client.post("/predict", json=request_data, headers=headers)
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]


class TestAPIIntegration:
    
    def test_complete_user_workflow(self, client, test_db):
        user_data = {"email": "workflow@example.com", "password": "workflow123"}
        
        # Register
        reg_response = client.post("/auth/register", json=user_data)
        assert reg_response.status_code == 200
        
        # Login
        login_response = client.post("/auth/login", json=user_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check wallet
        wallet_response = client.get("/wallet", headers=headers)
        assert wallet_response.status_code == 200
        assert wallet_response.json()["balance"] == "0.00"
        
        # Get models
        models_response = client.get("/models")
        assert models_response.status_code == 200
        
        # Check empty task history
        tasks_response = client.get("/tasks", headers=headers)
        assert tasks_response.status_code == 200
        assert len(tasks_response.json()) == 0
        
        # Check empty transaction history
        transactions_response = client.get("/wallet/transactions", headers=headers)
        assert transactions_response.status_code == 200
        assert len(transactions_response.json()) == 0