import socket

LISTEN_IP = "0.0.0.0"  
LISTEN_PORT = 9000

LAPTOP_TAILSCALE_IP = "100.126.172.47" # laptop's Tailscale IP 
LAPTOP_PORT = 9000

receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_sock.bind((LISTEN_IP, LISTEN_PORT))

sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[RELAY] Active. Listening on {LISTEN_PORT}...")
print(f"[RELAY] Bouncing traffic back to Laptop at {LAPTOP_TAILSCALE_IP}:{LAPTOP_PORT}")

try:
    while True:
        data, addr = receiver_sock.recvfrom(1024)
        message = data.decode()
        
        print(f"[RELAY] Caught '{message}' from {addr[0]} | Bouncing back...")
        
        sender_sock.sendto(data, (LAPTOP_TAILSCALE_IP, LAPTOP_PORT))

except KeyboardInterrupt:
    print("\n[RELAY] Stopped by user.")
finally:
    receiver_sock.close()
    sender_sock.close()