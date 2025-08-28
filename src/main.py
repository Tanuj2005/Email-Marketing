from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.auth import router as auth_router

app = FastAPI(title="Email Marketing OAuth Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, tags=["authentication"])

@app.get("/")
async def root():
    return {"message": "Email Marketing OAuth Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}