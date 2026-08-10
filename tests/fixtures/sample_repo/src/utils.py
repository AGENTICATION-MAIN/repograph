# Circular dependency back to auth!
from .auth import validate_session

def format_sql(query: str) -> str:
    validate_session("system")
    return query.strip().upper()
