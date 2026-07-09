import socket
import time

# SERVER_HOST = "192.168.1.100" # your server IP
# SERVER_PORT = 5000  # your server TCP port

# HTTP POST

def connect_tcp(SERVER_HOST: str, SERVER_PORT: int) -> socket.socket | None:
    print("Starting TCP connection attempts to {}:{}".format(SERVER_HOST, SERVER_PORT))
    try:
        addr_info = socket.getaddrinfo(SERVER_HOST, SERVER_PORT)[0][-1]
    except Exception as e:
        print("Failed to resolve address {}:{}: {}".format(SERVER_HOST, SERVER_PORT, e))
        return None
    for attempt in range(5):
        s = socket.socket()
        s.settimeout(5)
        try:
            print("Attempting connection to {}:{} (attempt {})".format(SERVER_HOST, SERVER_PORT, attempt+1))
            s.connect(addr_info)
            print("TCP connection successful")
            return s
        except Exception as e:
            print("TCP connection failed on attempt {}: {}".format(attempt+1, e))
            s.close()
            if attempt < 4:   # Don't sleep after the last attempt
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

def test(SERVER_HOST: str, SERVER_PORT: int, file_path: str | None = None) -> None:
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
    # Support both regular Python and MicroPython execution environments.
	host = "192.168.0.115"
	port = 5000
	file_path = "/test for tcp.csv"  # Path to the file you want to send
	test(host, port, file_path)