

import socket
import time
# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST,PORT))
server.listen(1)
print(f"Listening on Port: {PORT}")

# while True:
print(f"Waiting for client to connect")
conn, addr = server.accept()
print(f"Client connected from {addr}")


# data=conn.recv(1024)
# print("data received")
# # try:
while True:
    print("starting loop")

    # Currently, this function blocks the script and waits for data to be sent
    #  or for the connection be be closed by the client. 
    # If the connection is closed the first time we run this function,
    #  then we get empty bytes. But, if the connetion is closed the 
    # 2nd time we try reading this, we get an error (ConnectionResetError). Weird.
    try:
        data=conn.recv(1024)
    except ConnectionResetError:
        print("Client reset the connection")
        break
    print("data received")
    if data:
        print(f"Received {len(data)} bytes:", data)
        conn.sendall(b"ACK")
    else:
        print("client closed connection")
        break
# finally: # run this weather error or client closed connection
conn.close()
print(f"Server closed connection")



