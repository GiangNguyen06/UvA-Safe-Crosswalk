import socket
import time

# --- CONFIGURATION ---
PI_TAILSCALE_IP = "100.119.133.35"  #Raspberry Pi's Tailscale IP
TARGET_PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[SENDER] Starting. Blasting UDP to Pi at {PI_TAILSCALE_IP}:{TARGET_PORT}")

status_cycle = ["> 30M AWAY", "15-30M AWAY", "< 15M AWAY", "STOPPED OR GONE"]
i = 0

try:
    while True:
        current_status = status_cycle[i % len(status_cycle)]
        
        # Send the string to the Pi
        sock.sendto(current_status.encode(), (PI_TAILSCALE_IP, TARGET_PORT))
        print(f"[SENDER] Sent out to Pi: {current_status}")
        
        i += 1
        time.sleep(3.0)  # Wait 3 seconds before sending the next one

except KeyboardInterrupt:
    print("\n[SENDER] Stopped by user.")
finally:
    sock.close()