import requests
from fastapi import FastAPI
from .auth import check_auth
from .database import query_db

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "running"}
