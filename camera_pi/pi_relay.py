import socket

LISTEN_IP = "0.0.0.0"  
LISTEN_PORT = 9000

# CHANGE THIS: Use the Watch's actual Wi-Fi IP
WATCH_IP = "192.168.178.49" 
WATCH_PORT = 9000 # The port your Android app is listening on

receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_sock.bind((LISTEN_IP, LISTEN_PORT))
sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[RELAY] Forwarding traffic DIRECTLY to Watch at {WATCH_IP}:{WATCH_PORT}")

while True:
    data, addr = receiver_sock.recvfrom(1024)
    print(f"[RELAY] Caught '{data.decode()}' | Sending to Physical Watch...")
    sender_sock.sendto(data, (WATCH_IP, WATCH_PORT))