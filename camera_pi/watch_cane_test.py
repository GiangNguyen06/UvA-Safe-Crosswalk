import socket

# 1. Listen for Windows (Tailscale) on Port 9001
LISTEN_IP = "0.0.0.0"  
LISTEN_PORT = 9001 

# 2. The Smart Devices
WATCH_IP = "192.168.178.49" # always double check the Watch's IP address 
WATCH_PORT = 9000

CANE_IP = "192.168.178.178" # ESP32's IP address 
CANE_PORT = 9002        

receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_sock.bind((LISTEN_IP, LISTEN_PORT))
sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[PI RELAY] Multi-Device Field Test Mode Active!")
print(f"[*] Forwarding to Watch at {WATCH_IP}:{WATCH_PORT}")
print(f"[*] Forwarding to Cane at {CANE_IP}:{CANE_PORT}")

while True:
    data, addr = receiver_sock.recvfrom(1024)
    msg = data.decode()
    
    # Shoot the data to the Watch
    sender_sock.sendto(data, (WATCH_IP, WATCH_PORT))
    
    # Shoot the EXACT SAME data to the Smart Cane
    sender_sock.sendto(data, (CANE_IP, CANE_PORT))