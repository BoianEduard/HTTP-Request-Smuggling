#!/usr/bin/env python3
from flask import Flask, request, make_response, render_template
import logging
import auth

app = Flask(__name__, template_folder='../client')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SERVER - %(message)s')

@app.route('/', methods=['GET', 'POST'])
def home():
    logging.info(f"{request.method} /")
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    user = auth.authenticate(username, password)
    
    if not user:
        return render_template('login_failed.html'), 401
    
    session_token = auth.create_session(user['username'], user['role'])
    logging.info(f"Login: {username} ({user['role']})")
    
    response = make_response(render_template('login_success.html', username=user['username']))
    response.set_cookie('session', session_token, httponly=True)
    return response

@app.route('/users/list')
def users_list():
    session_token = request.cookies.get('session')
    session = auth.validate_session(session_token)
    
    if not session:
        return "Unauthorized", 401
    
    users = auth.get_users_safe()
    return render_template('users_list.html', users=users, user_count=len(users))

@app.route('/users/admin')
def users_admin():
    logging.warning("Backend trusts nginx - no role check")
    users = auth.get_all_users()
    return render_template('users_admin.html', users=users, user_count=len(users))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)