import socket
import time

# ADB is listening on our Mac's localhost
TARGET_IP = "127.0.0.1" 
TARGET_PORT = 9000

# statuses we want to test
status_cycle = ["Slow", "Medium", "Fast", "Stopped"]

# Create a UDP socket
# AF_INET = IPv4, SOCK_DGRAM = UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"UDP Test Client starting. Blasting to {TARGET_IP}:{TARGET_PORT}")

i = 0
try:
    while True:
        status = status_cycle[i % len(status_cycle)]
        print(f"Sending status: {status}")
        
        # Convert string to bytes and send
        sock.sendto(status.encode(), (TARGET_IP, TARGET_PORT))
        
        i += 1
        time.sleep(5) # Wait 5 seconds before next status
        
except KeyboardInterrupt:
    print("\nClient stopped by user.")
finally:
    sock.close()