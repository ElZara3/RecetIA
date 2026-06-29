"""Punto de entrada de la API RecetIA (FastAPI).

Fase 0: auth (register/login/me) + creación de tablas SQLite al arrancar.
Levantar en dev:  uvicorn app.main:app --reload   (desde la carpeta backend/)
Docs interactivas: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  — registra los modelos en Base.metadata
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.db import Base, engine
from app.routers.admin import router as admin_router
from app.routers.comercio import router as comercio_router
from app.routers.hogar import router as hogar_router
from app.routers.notifications import router as notifications_router
from app.routers.pantry import router as pantry_router
from app.routers.plan import router as plan_router
from app.routers.recipes import router as recipes_router
from app.routers.savings import router as savings_router
from app.routers.subscription import router as subscription_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev (Fase 0): crea las tablas al arrancar.
    # En producción esto se reemplaza por migraciones (Alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# CORS — origenes desde settings (dev: "*"; prod: fijar CORS_ORIGINS). Usamos auth por
# Bearer token (no cookies), así que no necesitamos allow_credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(hogar_router)
app.include_router(pantry_router)
app.include_router(recipes_router)
app.include_router(admin_router)
app.include_router(comercio_router)
app.include_router(plan_router)
app.include_router(savings_router)
app.include_router(notifications_router)
app.include_router(subscription_router)


@app.get("/health", tags=["meta"], summary="Healthcheck")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.environment}
