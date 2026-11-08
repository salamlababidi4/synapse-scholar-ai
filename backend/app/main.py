from fastapi import FastAPI

app = FastAPI(
    title="Synapse Scholar AI",
    description="AI-powered academic research intelligence platform",
    version="0.1.0"
)


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