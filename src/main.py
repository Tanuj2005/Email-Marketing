from fastapi import FastAPI, HTTPException
import os
from .routes.auth import router as auth_router  # type: ignore

app = FastAPI()

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


