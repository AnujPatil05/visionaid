import socket
import re
import os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    ip = get_local_ip()
    print("Detected IPs:")
    hostname = socket.gethostname()
    _, _, ips = socket.gethostbyname_ex(hostname)
    
    # Try finding fallback IP if disconnected from 8.8.8.8
    if ip == "127.0.0.1" and ips:
        potentials = [i for i in ips if i.startswith("192.168.") or i.startswith("10.")]
        if potentials:
            ip = potentials[0]
            
    for i in ips:
        if i == ip:
            print(f" -> {i} (Local Network)")
        else:
            print(f"    {i}")
            
    print(f"\nUpdate api_service.dart baseUrl to: http://{ip}:8000")
    
    dart_path = "visionaid_app/lib/api_service.dart"
    if os.path.exists(dart_path):
        with open(dart_path, "r") as f:
            content = f.read()
            
        new_content = re.sub(
            r"static const String baseUrl = 'http://[^']+';", 
            f"static const String baseUrl = 'http://{ip}:8000';", 
            content
        )
                             
        with open(dart_path, "w") as f:
            f.write(new_content)
            
        print(f"Updated api_service.dart with IP: {ip}")
    else:
        print(f"File not found: {dart_path}")

if __name__ == "__main__":
    main()
