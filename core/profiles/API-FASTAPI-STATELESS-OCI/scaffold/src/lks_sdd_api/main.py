from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class Status(BaseModel):
    service: str
    status: Literal["ok"]


app = FastAPI(
    title="LKS-SDD stateless API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def readiness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/status", response_model=Status, tags=["v1"])
def status() -> Status:
    return Status(service="lks-sdd-api", status="ok")
