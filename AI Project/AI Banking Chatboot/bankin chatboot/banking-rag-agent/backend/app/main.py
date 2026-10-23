"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import admin, auth, chat, documents, tickets
from app.config import get_settings
from app.database.mongodb import close_db, connect_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.vector_store_path, exist_ok=True)
    await connect_db()
    yield
    await close_db()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Banking RAG Agent API",
    description="AI-Powered Banking Customer Support with Retrieval-Augmented Generation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

settings = get_settings()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(tickets.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {
        "service": "Banking RAG Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
