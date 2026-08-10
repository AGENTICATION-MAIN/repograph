from .database import get_user

def check_auth(token: str):
    return get_user(token)

def validate_session(sess_id: str):
    return True
