from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.routes import router 

app = FastAPI(
    title="personalized Email marketing",
    description="mail marketing campaign service with Ai personalization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
