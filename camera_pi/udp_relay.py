import socket

LISTEN_IP = "0.0.0.0"  
LISTEN_PORT = 9000

#Laptop's Tailscale IP 
WATCH_IP = "100.126.172.47" 
WATCH_PORT = 9001

receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_sock.bind((LISTEN_IP, LISTEN_PORT))
sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[RELAY] Forwarding traffic to Emulator (via Laptop) at {WATCH_IP}:{WATCH_PORT}")

while True:
    data, addr = receiver_sock.recvfrom(1024)
    print(f"[RELAY] Caught '{data.decode()}' | Forwarding to Emulator...")
    sender_sock.sendto(data, (WATCH_IP, WATCH_PORT))