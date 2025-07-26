import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from decimal import Decimal
import base64

from api.main import app
from infrastructure.database import SessionLocal, Base, engine
from infrastructure.repositories import UserRepository, WalletRepository, MLModelRepository
from infrastructure.models import *

@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

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

@pytest.fixture
def demo_admin_data():
    """Demo admin data for testing"""
    return {
        "email": "admin@example.com", 
        "password": "adminpassword123"
    }

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self, client, test_db, demo_user_data):
        """Test user registration"""
        response = client.post("/auth/register", json=demo_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == demo_user_data["email"]
        assert "id" in data
    
    def test_register_duplicate_email(self, client, test_db, demo_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/auth/register", json=demo_user_data)
        
        # Try to register with same email
        response = client.post("/auth/register", json=demo_user_data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"
    
    def test_login_success(self, client, test_db, demo_user_data):
        """Test successful login"""
        # Register user first
        client.post("/auth/register", json=demo_user_data)
        
        # Login
        response = client.post("/auth/login", json=demo_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_db):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_get_current_user(self, client, test_db, demo_user_data):
        """Test getting current user info"""
        # Register and login
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == demo_user_data["email"]
    
    def test_unauthorized_access(self, client, test_db):
        """Test unauthorized access to protected endpoint"""
        response = client.get("/auth/me")
        assert response.status_code == 403

class TestWallet:
    """Test wallet endpoints"""
    
    def test_get_wallet(self, client, test_db, demo_user_data):
        """Test getting wallet information"""
        # Register, login, get token
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get wallet
        response = client.get("/wallet", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "balance" in data
        assert data["balance"] == "0.00"  # New user starts with 0 balance
    
    def test_get_transactions_empty(self, client, test_db, demo_user_data):
        """Test getting empty transaction history"""
        # Register, login, get token
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get transactions
        response = client.get("/wallet/transactions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

class TestMLModels:
    """Test ML models endpoints"""
    
    def test_get_models(self, client, test_db):
        """Test getting available ML models"""
        # First create some demo models
        db = test_db
        model_repo = MLModelRepository(db)
        model_repo.create_model("Test Model", Decimal("5.00"))
        model_repo.create_model("Advanced Model", Decimal("10.00"))
        
        # Get models
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        
        # Check model structure
        model = data[0]
        assert "id" in model
        assert "name" in model
        assert "credit_cost" in model
        assert "is_active" in model

class TestPredictions:
    """Test prediction endpoints"""
    
    def setup_user_with_credits(self, client, test_db, user_data, credits_amount=100):
        """Helper to create user with credits"""
        # Register user
        client.post("/auth/register", json=user_data)
        login_response = client.post("/auth/login", json=user_data)
        token = login_response.json()["access_token"]
        
        # Add credits directly through repository
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        user = user_repo.get_by_email(user_data["email"])
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        transaction = wallet.top_up(Decimal(str(credits_amount)))
        wallet_repo.add_transaction(transaction)
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        return token
    
    def setup_demo_model(self, test_db):
        """Helper to create demo model"""
        model_repo = MLModelRepository(test_db)
        model = model_repo.create_model("Test Model", Decimal("5.00"))
        return model
    
    def test_create_prediction_success(self, client, test_db, demo_user_data):
        """Test successful prediction creation"""
        # Setup user with credits and model
        token = self.setup_user_with_credits(client, test_db, demo_user_data)
        model = self.setup_demo_model(test_db)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create prediction request
        # Simple base64 encoded string representing an image
        dummy_image = base64.b64encode(b"dummy image content").decode()
        request_data = {
            "model_id": str(model.id),
            "file_content": dummy_image,
            "filename": "test_formula.png"
        }
        
        response = client.post("/predict", json=request_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "done"
        assert "credits_charged" in data
        assert "output_data" in data
    
    def test_create_prediction_insufficient_credits(self, client, test_db, demo_user_data):
        """Test prediction with insufficient credits"""
        # Setup user with NO credits
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
        """Test prediction with invalid model ID"""
        token = self.setup_user_with_credits(client, test_db, demo_user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        dummy_image = base64.b64encode(b"dummy image content").decode()
        request_data = {
            "model_id": "00000000-0000-0000-0000-000000000000",  # Non-existent model
            "file_content": dummy_image,
            "filename": "test_formula.png"
        }
        
        response = client.post("/predict", json=request_data, headers=headers)
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]

class TestTasks:
    """Test task endpoints"""
    
    def test_get_user_tasks_empty(self, client, test_db, demo_user_data):
        """Test getting empty task history"""
        # Register, login, get token
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get tasks
        response = client.get("/tasks", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_nonexistent_task(self, client, test_db, demo_user_data):
        """Test getting non-existent task"""
        # Register, login, get token
        client.post("/auth/register", json=demo_user_data)
        login_response = client.post("/auth/login", json=demo_user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get non-existent task
        fake_task_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/tasks/{fake_task_id}", headers=headers)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "formula2latex-backend"

class TestAPIIntegration:
    """Integration tests for complete API workflows"""
    
    def test_complete_user_workflow(self, client, test_db):
        """Test complete user workflow: register -> login -> predict -> view history"""
        user_data = {"email": "workflow@example.com", "password": "workflow123"}
        
        # 1. Register
        reg_response = client.post("/auth/register", json=user_data)
        assert reg_response.status_code == 200
        
        # 2. Login
        login_response = client.post("/auth/login", json=user_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Check wallet (should be empty)
        wallet_response = client.get("/wallet", headers=headers)
        assert wallet_response.status_code == 200
        assert wallet_response.json()["balance"] == "0.00"
        
        # 4. Get models (should exist from other tests or demo data)
        models_response = client.get("/models")
        assert models_response.status_code == 200
        
        # 5. Check empty task history
        tasks_response = client.get("/tasks", headers=headers)
        assert tasks_response.status_code == 200
        assert len(tasks_response.json()) == 0
        
        # 6. Check empty transaction history
        transactions_response = client.get("/wallet/transactions", headers=headers)
        assert transactions_response.status_code == 200
        assert len(transactions_response.json()) == 0