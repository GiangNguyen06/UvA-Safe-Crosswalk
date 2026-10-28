import socket
import time

# 1. CHANGE TO BROADCAST IP (Shouts to the whole hotspot)
TARGET_IP = "192.168.178.49"
TARGET_PORT = 9000

status_cycle = ["> 30M AWAY", "15-30M AWAY", "< 15M AWAY", "STOPPED OR GONE"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 2. THE MAGIC LINE: Tell the socket it's allowed to broadcast
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

print(f"UDP Broadcast Test starting. Blasting to {TARGET_IP}:{TARGET_PORT}")

current_status = "Waiting for camera connection..."
last_state_change_time = time.time()
i = 0

try:
    while True:
        # Change status every 5 seconds
        if time.time() - last_state_change_time > 5.0:
            i += 1
            current_status = status_cycle[i % len(status_cycle)]
            last_state_change_time = time.time()
            print(f"--- BLASTING TO WATCH: {current_status} ---")

        # Send the broadcast over the Wi-Fi
        sock.sendto(current_status.encode(), (TARGET_IP, TARGET_PORT))
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nTest stopped.")
finally:
    sock.close()