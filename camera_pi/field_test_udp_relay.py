import socket

# 1. Listen for Windows (Tailscale) on Port 9001
LISTEN_IP = "0.0.0.0"  
LISTEN_PORT = 9001 

# 2. Blast to the Watch (Phone Hotspot) on Port 9000
WATCH_PORT = 9000
BROADCAST_IP = "255.255.255.255" #double check with watches ip config on hotspot network!

receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_sock.bind((LISTEN_IP, LISTEN_PORT))

sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# THE MAGIC LINE: Enable shouting to the whole hotspot network
sender_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) 

print(f"[PI RELAY] Field Test Mode Active!")
print(f"[*] Listening for Windows on Port {LISTEN_PORT}...")
print(f"[*] Broadcasting to Physical Watch on Port {WATCH_PORT}...")

while True:
    data, addr = receiver_sock.recvfrom(1024)
    msg = data.decode()
    print(f"[RELAY] Caught '{msg}' from Campus -> Blasting to Watch!")
    
    # Shout to the entire local hotspot network
    sender_sock.sendto(data, (BROADCAST_IP, WATCH_PORT))