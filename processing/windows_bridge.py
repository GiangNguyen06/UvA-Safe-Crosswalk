import socket

# Stand outside and listen to Tailscale on Port 9001
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listen_sock.bind(("0.0.0.0", 9001)) 

# Setup the pipe to the Emulator
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("[BRIDGE] Standing by. Catching Pi packets and shoving them into Emulator...")

try:
    while True:
        data, addr = listen_sock.recvfrom(1024)
        message = data.decode()
        print(f"[BRIDGE] Caught '{message}' from Pi! Shoving to Emulator...")
        
        # Shove it into the Telnet door of the Emulator (localhost:9000)
        send_sock.sendto(data, ("127.0.0.1", 9000))
except KeyboardInterrupt:
    print("\n[BRIDGE] Stopped.")
finally:
    listen_sock.close()
    send_sock.close()