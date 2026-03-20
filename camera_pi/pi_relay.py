import socket

WIN_IP = "100.126.172.47" 
WIN_PORT = 9001

receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_sock.bind(("0.0.0.0", 9000))

sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[PI] Relay Active! Listening on 9000 -> Bouncing back to Windows at {WIN_IP}:{WIN_PORT}")

while True:
    data, addr = receiver_sock.recvfrom(1024)
    print(f"[PI] Caught '{data.decode()}' | Bouncing back to Windows...")
    sender_sock.sendto(data, (WIN_IP, WIN_PORT))