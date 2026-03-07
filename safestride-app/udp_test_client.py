import socket
import time

TARGET_IP = "192.168.178.16"
TARGET_PORT = 9000

status_cycle = ["Slow", "Medium", "Fast", "Stopped"]
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"UDP Test Client starting. Blasting to {TARGET_IP}:{TARGET_PORT}")

# We separate the "State" from the "Network Broadcast"
current_status = "Stopped"
last_state_change_time = time.time()
i = 0

try:
    while True:
        # 1. Check if 5 seconds have passed to change the state
        if time.time() - last_state_change_time > 5.0:
            i += 1
            current_status = status_cycle[i % len(status_cycle)]
            last_state_change_time = time.time()
            print(f"--- STATE CHANGED TO: {current_status} ---")

        # 2. BLAST the current state constantly!
        # The watch will pick this up almost instantly when opened
        sock.sendto(current_status.encode(), (TARGET_IP, TARGET_PORT))

        # Wait just 0.5 seconds before broadcasting again
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nClient stopped by user.")
finally:
    sock.close()