from fastapi import FastAPI
from backend.app.core.database import check_database_connection
from backend.app.api.papers import router as papers_router


app = FastAPI(
    title="Synapse Scholar AI",
    description="AI-powered academic research intelligence platform",
    version="0.1.0"
)

app.include_router(papers_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Synapse Scholar AI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "synapse-scholar-backend"
    }

from fastapi import HTTPException


@app.get("/health/database")
def database_health():
    try:
        database_name = check_database_connection()

        return {
            "status": "connected",
            "database": database_name
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )

    