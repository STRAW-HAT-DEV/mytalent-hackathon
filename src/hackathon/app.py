from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MyTalent API")


@app.get("/")
def read_root():
    return {"Message": "Welcome to the backend API for MyTalent"}


class HealthCheck(BaseModel):
    status: str = "OK"


@app.get("/health", response_model=HealthCheck)
def get_health():
    return HealthCheck(status="OK")
