from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for APPA (Analisa Pasar Pintar & Akurat)",
    version="1.0.0"
)

# Configure CORS Middleware
# Allows frontend Next.js running on another port (e.g. 3000) or host to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production for security, but allow all for competition/hackathon local deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(api_router, tags=["API"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # When run directly, start the server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
