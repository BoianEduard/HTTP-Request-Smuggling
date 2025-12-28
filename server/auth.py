import secrets
import redis
import json
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

USERS = [
    {'id': 1, 'username': 'alice', 'email': 'alice@company.com', 'password': 'alice123', 'role': 'user'},
    {'id': 2, 'username': 'bob', 'email': 'bob@company.com', 'password': 'bob456', 'role': 'user'},
    {'id': 3, 'username': 'admin', 'email': 'admin@company.com', 'password': 'admin_secret', 'role': 'admin'},
    {'id': 4, 'username': 'john', 'email': 'john@company.com', 'password': 'john789', 'role': 'user'},
]

def authenticate(username, password):
    return next((u for u in USERS if u['username'] == username and u['password'] == password), None)

def create_session(username, role):
    session_token = secrets.token_hex(32)
    session_data = {'username': username, 'role': role, 'created': datetime.now().isoformat()}
    r.setex(f"session:{session_token}", 3600, json.dumps(session_data))
    return session_token

def validate_session(session_token):
    if not session_token:
        return None
    session_data = r.get(f"session:{session_token}")
    return json.loads(session_data) if session_data else None

def get_all_users():
    return USERS

def get_users_safe():
    return [{'id': u['id'], 'username': u['username'], 'email': u['email'], 'role': u['role']} for u in USERS]