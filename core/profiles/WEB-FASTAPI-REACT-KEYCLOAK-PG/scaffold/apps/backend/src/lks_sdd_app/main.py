from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import Engine

from .config import Settings
from .database import create_database_engine, create_item, ensure_items, list_items
from .security import decode_access_token

app = FastAPI(
    title="LKS-SDD reference API",
    version="0.1.0",
    openapi_version="3.1.0",
)
bearer = HTTPBearer(auto_error=True)


class ItemInput(BaseModel):
    label: str = Field(min_length=1, max_length=200)


def current_settings() -> Settings:
    return Settings.from_environment()


def database(settings: Annotated[Settings, Depends(current_settings)]) -> Engine:
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        )
    engine = create_database_engine(settings.database_url)
    ensure_items(engine)
    return engine
def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    settings: Annotated[Settings, Depends(current_settings)],
) -> dict[str, Any]:
    return decode_access_token(credentials, settings)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def readiness() -> dict[str, object]:
    return {"status": "ready", "checks": [{"name": "api", "status": "ready"}]}


@app.get("/api/v1/me", tags=["identity"])
def me(user: Annotated[dict[str, Any], Depends(current_user)]) -> dict[str, str | None]:
    return {
        "subject": str(user["sub"]),
        "username": user.get("preferred_username"),
    }


@app.get("/api/v1/items", tags=["items"])
def read_items(
    _: Annotated[dict[str, Any], Depends(current_user)],
    engine: Annotated[Engine, Depends(database)],
) -> list[dict[str, str]]:
    return list_items(engine)


@app.post("/api/v1/items", status_code=201, tags=["items"])
def add_item(
    payload: ItemInput,
    response: Response,
    _: Annotated[dict[str, Any], Depends(current_user)],
    engine: Annotated[Engine, Depends(database)],
    correlation_id: Annotated[str | None, Header(alias="X-Correlation-ID")] = None,
) -> dict[str, str]:
    observed = correlation_id or "generated-by-api"
    response.headers["X-Correlation-ID"] = observed
    return create_item(engine, payload.label)
