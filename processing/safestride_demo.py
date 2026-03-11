import socket
import time
import threading

PI_IP = "100.119.133.35"     # Pi Tailscale IP
LAPTOP_IP = "0.0.0.0"         # Listen on all interfaces
OUTGOING_PORT = 9000          # Sending to Pi
INCOMING_PORT = 9001          # Receiving from Pi
EMULATOR_PORT = 9000          # Shoving into Emulator

# Listen for Pi and shove to Emulator
def start_bridge():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_sock.bind((LAPTOP_IP, INCOMING_PORT))
    
    send_to_emu_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"[*] BRIDGE: Listening on {INCOMING_PORT}, forwarding to Emulator...")
    while True:
        data, addr = listen_sock.recvfrom(1024)
        # Shove to the telnet redir door
        send_to_emu_sock.sendto(data, ("127.0.0.1", EMULATOR_PORT))
        print(f"[*] BRIDGE: Relayed '{data.decode()}' to Emulator")

# Simulate AI sending to Pi
def start_sender():
    sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    status_cycle = ["> 30M AWAY", "15-30M AWAY", "< 15M AWAY", "STOPPED OR GONE"]
    
    print(f"[*] SENDER: Blasting to Pi at {PI_IP}:{OUTGOING_PORT}...")
    i = 0
    while True:
        msg = status_cycle[i % len(status_cycle)]
        sender_sock.sendto(msg.encode(), (PI_IP, OUTGOING_PORT))
        print(f"[!] SENDER: Sent '{msg}'")
        i += 1
        time.sleep(3)

if __name__ == "__main__":
    bridge_thread = threading.Thread(target=start_bridge, daemon=True)
    bridge_thread.start()
    
    try:
        start_sender()
    except KeyboardInterrupt:
        print("\nDemo stopped.")