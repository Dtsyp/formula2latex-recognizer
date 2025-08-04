from fastapi import APIRouter, Depends
from typing import List

from infrastructure.database import get_db
from api.schemas import MLModelResponse
from infrastructure.repositories import SQLAlchemyMLModelRepository

router = APIRouter(prefix="/models", tags=["ML Models"])

@router.get("", response_model=List[MLModelResponse])
async def get_models(db = Depends(get_db)):
    """Получение списка доступных ML моделей"""
    model_repo = SQLAlchemyMLModelRepository(db)
    models = model_repo.get_all_active()
    
    return [
        MLModelResponse(
            id=model.id,
            name=model.name,
            credit_cost=model.credit_cost,
            is_active=True
        )
        for model in models
    ]