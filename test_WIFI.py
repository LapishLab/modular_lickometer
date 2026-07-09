print("new message")

import wifi
wifi.connect_to_wifi("TP","",10)


# import http_server
# http_server.start_http_server()
import tcp
sock = tcp.connect_tcp("192.168.0.115", "5000")
if sock:
	tcp.send_data(sock, "Hey, how ya doin?")
	sock.close()