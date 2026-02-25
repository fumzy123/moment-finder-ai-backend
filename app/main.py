from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize the FastAPI application
app = FastAPI(
    title="Moment Finder API Backend",
    description="API for uploading and semantically searching videos for specific character moments.",
    version="1.0.0"
)

# Configure CORS so the frontend can communicate with this API
origins = [
    "http://localhost:3000",  # Example React/Next.js frontend port
    "http://127.0.0.1:3000",
]

# Import routers
from app.api import video

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(video.router, prefix="/api")

# --- Core MVP Endpoints ---
@app.get("/", tags=["System"])
def health_check():
    """
    Health check endpoint to verify the API server is running successfully.
    """
    return {"status": "ok", "message": "Moment Finder AI API is operational"}
