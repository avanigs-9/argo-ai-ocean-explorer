from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.query import router as query_router


app = FastAPI(
    title="ARGO Ocean Explorer API",
    description="Backend API for the ARGO AI Ocean Explorer",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTES
# =========================================================

app.include_router(
    query_router,
    prefix="/api/argo"
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "ARGO Ocean Explorer Backend is running!"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }