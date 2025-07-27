from fastapi import APIRouter, Depends
from typing import List

from api.auth import get_db
from api.schemas import MLModelResponse
from infrastructure.repositories import MLModelRepository

router = APIRouter(prefix="/models", tags=["ML Models"])

@router.get("", response_model=List[MLModelResponse])
async def get_models(db = Depends(get_db)):
    """Получение списка доступных ML моделей"""
    model_repo = MLModelRepository(db)
    models = model_repo.get_active_models()
    
    return [
        MLModelResponse(
            id=model.id,
            name=model.name,
            credit_cost=model.credit_cost,
            is_active=True
        )
        for model in models
    ]