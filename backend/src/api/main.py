from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.users import router as users_router
from api.wallet import router as wallet_router
from api.models import router as models_router
from api.tasks import router as tasks_router

app = FastAPI(
    title="Formula2LaTeX Recognizer API",
    description="REST API для распознавания математических формул с аутентификацией",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router)
app.include_router(wallet_router)
app.include_router(models_router)
app.include_router(tasks_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Formula2LaTeX Recognizer API", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "formula2latex-backend"}