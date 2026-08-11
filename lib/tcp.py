import socket
import time
import wifi
import config

def connect_tcp(SERVER_HOST: str, SERVER_PORT: int) -> socket.socket | None:
    print("Starting TCP connection attempts to {}:{}".format(SERVER_HOST, SERVER_PORT))
    try:
        addr_info = socket.getaddrinfo(SERVER_HOST, SERVER_PORT)[0][-1]
    except Exception as e:
        print("Failed to resolve address {}:{}: {}".format(SERVER_HOST, SERVER_PORT, e))
        return None
    num_attempts = 2
    for attempt in range(num_attempts):
        s = socket.socket()
        s.settimeout(10)
        try:
            print("Attempting connection to {}:{} (attempt {})".format(SERVER_HOST, SERVER_PORT, attempt+1))
            s.connect(addr_info)
            print("TCP connection successful")
            return s
        except Exception as e:
            print("TCP connection failed on attempt {}: {}".format(attempt+1, e))
            s.close()
            if attempt < num_attempts-1:   # Don't sleep after the last attempt
                time.sleep(1)
    return None

def send_data(sock: socket.socket, data: bytes) -> bool:
    try:
        sock.sendall(data)
    except Exception as e:
        print("Send failed:", e)
        return False
    return True

def receive_reply(sock: socket.socket, max_len: int = 1024) -> bytes | None:
    try:
        reply = sock.recv(max_len)
        return reply
    except Exception as e:
        print("Receive failed:", e)
        return None


def send_file(sock: socket.socket, file_path: str, chunk_size: int = 1024) -> bool:
    """Send a file over an open socket in binary chunks.
    Returns True on success, False on failure.
    """
    import os
    try:
        filesize = os.stat(file_path)[6]
    except Exception as e:
        print("Failed to stat file {}: {}".format(file_path, e))
        return False

    try:
        with open(file_path, "rb") as f:
            sock.sendall(file_path.encode() + b"\n")  # Send the file name first
            sock.sendall(str(filesize).encode() + b"\n")  # Send the file size next
            sent = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                try:
                    sock.sendall(chunk)
                except Exception as e:
                    print("Failed sending chunk:", e)
                    return False
                sent += len(chunk)
        print("Finished sending file {} ({} bytes)".format(file_path, sent))
        return True
    except Exception as e:
        print("Error opening/sending file {}: {}".format(file_path, e))
        return False

def connect_to_server_and_send_file(file_path: str | None = None) -> None:
    wifi.connect_to_wifi(config.WIFI_SSID, config.WIFI_PASSWORD, 10) # Maybe this should be handled seperately

    sock = connect_tcp(SERVER_HOST, SERVER_PORT)
    if not sock:
        return

    if file_path:
        ok = send_file(sock, file_path)
        if not ok:
            print("Failed to send file")
    else:
        msg = b"Hello from ESP32"
        send_data(sock, msg)

    reply = receive_reply(sock)
    if reply is not None:
        print("Received reply:", reply)
    sock.close()


if __name__ == '__main__':
    file_path = "/test for tcp.csv"  # Path to the file you want to send
    connect_to_server_and_send_file(file_path = file_path)