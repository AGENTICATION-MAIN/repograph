import pydantic
from .utils import format_sql

def query_db(q: str):
    return format_sql(q)

def get_user(uid: str):
    return {"id": uid, "role": "admin"}
