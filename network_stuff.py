import network
import time
import socket
import hashlib
import ubinascii




def connect_to_hotspot(HOTSPOT_SSID, HOTSPOT_PASSWORD, WIFI_CONNECT_TIMEOUT_S):
    sta = network.WLAN(network.STA_IF)
    ap  = network.WLAN(network.AP_IF)

    # Turn off AP mode (optional but recommended to avoid confusion)
    ap.active(False)

    sta.active(True)

    if not sta.isconnected():
        print("Connecting to hotspot:", HOTSPOT_SSID)
        sta.connect(HOTSPOT_SSID, HOTSPOT_PASSWORD)

        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > WIFI_CONNECT_TIMEOUT_S * 1000:
                print("ERROR: Hotspot connection timed out.")
                return None
            time.sleep_ms(250)

    ip = sta.ifconfig()[0]
    print("Connected to hotspot.")
    print("STA IP:", ip)
    return ip


def send_data_via_websocket(server_host, server_port, csv_file_path):
    """
    Send CSV data to websocket server after recording stops.
    Reads the entire CSV file and sends as batch.
    
    Args:
        server_host: IP or hostname of websocket server (e.g., "192.168.1.100")
        server_port: Port number (e.g., 8765)
        csv_file_path: Path to CSV file (e.g., "/sd/touch_log.csv")
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Connecting to websocket server at {server_host}:{server_port}...")
        
        # Read CSV data
        with open(csv_file_path, 'r') as f:
            csv_data = f.read()
        
        print(f"Read {len(csv_data)} bytes from {csv_file_path}")
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_host, server_port))
        
        # WebSocket handshake
        key = ubinascii.b2a_base64(b"esp32_client").decode().strip()
        handshake = (
            f"GET / HTTP/1.1\r\n"
            f"Host: {server_host}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"\r\n"
        )
        sock.send(handshake.encode())
        
        # Receive handshake response
        response = sock.recv(1024)
        print("Handshake response received")
        
        # Send CSV data as websocket frame
        data = csv_data.encode()
        frame = _create_websocket_frame(data)
        sock.send(frame)
        
        print("Data sent successfully!")
        sock.close()
        return True
        
    except Exception as e:
        print(f"ERROR sending data: {e}")
        return False


def _create_websocket_frame(data):
    """Create a WebSocket frame for text data."""
    frame = bytearray()
    frame.append(0x81)  # FIN + Text opcode
    
    length = len(data)
    if length < 126:
        frame.append(length)
    elif length < 65536:
        frame.append(126)
        frame.extend(length.to_bytes(2, 'big'))
    else:
        frame.append(127)
        frame.extend(length.to_bytes(8, 'big'))
    
    # No masking from server, so just append data
    frame.extend(data)
    return bytes(frame)
