import socket
import time

# TARGET_IP = "192.168.178.16"
TARGET_IP = ("172.20.10.3")
TARGET_PORT = 9000

# Updated the exact phrases broadcasted over UDP
status_cycle = ["> 30M AWAY", "15-30M AWAY", "< 15M AWAY", "STOPPED OR GONE"]
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"UDP Test Client starting. Blasting to {TARGET_IP}:{TARGET_PORT}")

current_status = "Waiting for camera connection..."
last_state_change_time = time.time()
i = 0

try:
    while True:
        if time.time() - last_state_change_time > 5.0:
            i += 1
            current_status = status_cycle[i % len(status_cycle)]
            last_state_change_time = time.time()
            print(f"--- STATE CHANGED TO: {current_status} ---")

        sock.sendto(current_status.encode(), (TARGET_IP, TARGET_PORT))
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nClient stopped by user.")
finally:
    sock.close()