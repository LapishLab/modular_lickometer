import socket
import time

# SERVER_HOST = "192.168.1.100" # your server IP
# SERVER_PORT = 5000  # your server TCP port

# HTTP POST

def connect_tcp(SERVER_HOST,SERVER_PORT):
    print("Starting TCP connection attempts to {}:{}".format(SERVER_HOST, SERVER_PORT))
    try:
        addr_info = socket.getaddrinfo(SERVER_HOST, SERVER_PORT)[0][-1]
    except Exception as e:
        print("Failed to resolve address {}:{}: {}".format(SERVER_HOST, SERVER_PORT, e))
        return None
    for attempt in range(5):
        s = socket.socket()
        s.settimeout(4)
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

def send_data(sock, data):
    # try:
    sock.sendall(data)
#     except Exception as e:
#         print("Send failed:", e)
#         return False
#     return True

def receive_reply(sock, max_len=1024):
#     try:
    reply = sock.recv(max_len)
#         return reply
#     except Exception as e:
#         print("Receive failed:", e)
#         return None

def test(SERVER_HOST,SERVER_PORT):
    sock = connect_tcp(SERVER_HOST,SERVER_PORT)
    msg = b"Hello from ESP32"
    send_data(sock, msg)
    reply = receive_reply(sock)
    sock.close()