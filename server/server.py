from flask import Flask, request, jsonify
import logging
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - BACKEND - %(message)s'
)

request_log = []

@app.route('/', methods=['GET','PUT','POST','DELETE'])
@app.route('/<path:path>', methods=['GET','PUT','POST','DELETE'])
def handle_request(path=''):
    timestamp = datetime.now().isoformat()
    request_info = {
        'timestamp': timestamp,
        'method': request.method,
        'path': f'/{path}' if path else '/',
        'headers': dict(request.headers),
        'body': request.get_data(as_text=True),
        'content-length': request.content_length,
        'remote_addr': request.remote_addr
    }

    request_log.append(request_info)
    logging.info(f"{request.method} /{path}")
    logging.info(f" Headers: {request_info['headers']}")
    logging.info(f" Body length:  {len(request.get_data())}" )
    logging.info(f" Content-Length header: {request.headers.get('Content-Length', 'Not Set')}")
    logging.info("-" * 60)

    if path == 'admin':
        return jsonify({
            'status': 'success',
            'message': 'ADMIN ACCESS - you have reached the admin panel!',
            'timestamp': timestamp
        }), 200

    elif path == 'api/user':
        return jsonify({
            'status': 'success',
            'user': 'victim_user',
            'session': 'abcda12345sessiontoken',
            'timestamp': timestamp
        }), 200
    
    else:
        return jsonify({
            'status': 'success',
            'message': f"Backend received {request.method} request to /{path}",
            'timestamp': timestamp
        }), 200
    
@app.route('/logs')
def show_logs():
    return jsonify({
        'total_requests': len(request_log),
        'requests': request_log[-10:]
    })

@app.route('/clear') 
def clear_logs():
    request_log.clear()
    return jsonify({
        'status': 'success',
        'message': 'Request logs cleared.'
    }), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port = 5000, debug=True)