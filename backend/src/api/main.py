from fastapi import FastAPI

app = FastAPI(
    title="Formula2LaTeX Recognizer",
    description="API 4;O @0A?>7=020=8O <0B5<0B8G5A:8E D>@<C;",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Formula2LaTeX Recognizer API"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "formula2latex-backend"}