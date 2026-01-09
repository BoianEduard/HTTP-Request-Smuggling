from flask import Flask, request, make_response
import secrets
import logging
import sys

app = Flask(__name__)

# Enable logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

USERS = [
    {'id': 1, 'username': 'alice', 'email': 'alice@company.com', 'password': 'alice123', 'role': 'user'},
    {'id': 2, 'username': 'bob', 'email': 'bob@company.com', 'password': 'bob456', 'role': 'user'},
    {'id': 3, 'username': 'admin', 'email': 'admin@company.com', 'password': 'admin_secret', 'role': 'admin'},
]

SESSIONS = {}

@app.before_request
def log_request():
    logger.info(f">>> REQUEST: {request.method} {request.path}")
    logger.info(f">>> Headers: {dict(request.headers)}")
    request.environ['wsgi.input_terminated'] = True

@app.after_request
def log_response(response):
    logger.info(f"<<< RESPONSE: {response.status}")
    return response

@app.route('/', methods=['GET', 'POST'])
def home():
    logger.info("HOME endpoint")
    return 'Home Page'

@app.route('/login', methods=['POST'])
def login():
    logger.info("LOGIN endpoint")
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = next((u for u in USERS if u['username'] == username and u['password'] == password), None)
    
    if not user:
        return 'Login failed', 401
    
    prefix = 'admin_' if user['role'] == 'admin' else 'user_'
    token = prefix + secrets.token_hex(16)
    SESSIONS[token] = user
    
    logger.info(f"LOGIN SUCCESS: {username} ({user['role']}) -> {token[:20]}...")
    
    resp = make_response(f'Login OK - {username}')
    resp.set_cookie('session', token, httponly=True)
    return resp

@app.route('/users/admin', methods=['GET', 'POST'])
def users_admin():
    logger.info("Admin endpoint accessed ")
    
    rows = '<br>'.join([f"{u['id']} | {u['username']} | {u['email']} | <b>{u['password']}</b> | {u['role']}" for u in USERS])
    
    return f"<h1>ADMIN PANEL</h1><p>All users with passwords:</p>{rows}"

if __name__ == '__main__':
    app.run(port=5001, debug=True)