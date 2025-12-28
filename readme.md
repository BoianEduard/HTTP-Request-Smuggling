# HTTP Request Smuggling PoC — Overview

```md
# HTTP Request Smuggling PoC — Overview
Proof-of-concept demonstrating HTTP Request Smuggling vulnerability where a backend application trusts its reverse proxy for authorization, leading to privilege escalation and data exposure.The Vulnerability ExplainedNormal Request Flow

User sends request → nginx reverse proxy
nginx validates authorization (checks session, role, permissions)
If authorized → nginx forwards request to Flask backend
Backend processes request (trusts nginx already validated it)
HTTP Request Smuggling Attack
The vulnerability exploits disagreement between nginx and Flask on where one HTTP request ends and another begins.The Desync:

nginx uses Transfer-Encoding: chunked header to parse request
Flask uses Content-Length header to parse request
Attacker crafts request with BOTH headers (ambiguous)
What Happens:

Attacker logs in as alice (normal user) with valid session
Attacker sends ONE malformed HTTP request containing TWO requests:

nginx reads first request: POST / (public endpoint, allowed)
Flask reads first request: POST / + leftover bytes

The leftover bytes form a second request: GET /users/admin
This smuggled request is processed by Flask on the same TCP connection
Flask thinks: "This came from nginx on our trusted connection → must be authorized"
Flask serves admin data WITHOUT checking if alice is actually an admin
Why It Works:

nginx checked authorization for POST / only
The smuggled GET /users/admin never passed through nginx's security checks
Backend blindly trusts anything from nginx
Result: Normal user accesses admin-only passwords
The Trust Issue
Many production systems use this architecture:

Reverse proxy handles authentication/authorization (edge security)
Internal services trust requests from the proxy
"If nginx forwarded it, it's authorized"
This is common in microservices where an API gateway protects multiple internal services. If one service has this vulnerability, the entire security boundary collapses.Technical DetailsCL.TE Desync

CL = Content-Length (Flask uses this)
TE = Transfer-Encoding (nginx uses this)
nginx 1.18.0 is vulnerable to ambiguous header combinations
Modern nginx versions (1.21+) reject such requests
Session Storage

Sessions stored in Redis database (industry standard)
Format: session:TOKEN → {"username": "alice", "role": "user"}
nginx checks if session cookie exists
Backend SHOULD check role from Redis, but doesn't (trusts nginx)
```
```

---

## Normal Request Flow

1. Client → nginx reverse proxy  
2. nginx checks authentication/authorization (session + role)  
3. nginx forwards validated request → Flask backend  
4. Backend processes request, assuming proxy already enforced auth  

---

## HRS Attack (Request Desync)

- **nginx parses using** `Transfer‑Encoding: chunked`
- **Flask parses using** `Content‑Length`
- Attacker sends **both headers** → ambiguous body size → desync
- Hidden request bypasses nginx validation but is executed by backend

**Impact in PoC**
- Attacker logs in as `alice` (role: `user`)
- Smuggles a second request: `GET /users/admin`
- Flask executes it on a trusted internal socket
- Admin data + passwords are returned despite missing privileges

---

## Root Cause (Trust Boundary Failure)

> Reverse proxy enforced security only on the first request.  
> Backend accepted the second one because it arrived via an internal upstream connection assumed to be trusted.

This mirrors real microservice architectures where API gateways handle auth and internal services do not re‑validate it.

---

## Technical Context

- CL.TE desync works on **nginx 1.18.0**
- Newer nginx versions block ambiguous headers
- Sessions stored in **Redis** as `session:TOKEN → {username, role}`

---

# Setup Instructions

### Prerequisites
```sh
sudo apt update
sudo apt install nginx redis-server python3-pip -y
pip3 install flask redis --break-system-packages
redis-cli ping  # expect: PONG
```

### Verify nginx version
```sh
nginx -v  # must show 1.18.0
```

### Backend server (Terminal 1)
```sh
cd server
python3 server.py
```

### Launch attack (Terminal 2)
```sh
cd attack
python3 http_smuggler.py
```

---

## Expected PoC Result

If smuggling works, backend logs will show:

```
POST /
GET /users/admin  ← smuggled request
```

And the attacker will receive admin data without passing nginx role validation.

---