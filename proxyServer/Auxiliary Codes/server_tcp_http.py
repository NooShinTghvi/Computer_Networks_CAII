import socket

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(("127.0.0.1", 8088))
serversocket.listen(1)

msg = """
HTTP/1.0
Content-Type: text/html

<html>
<body>
<b>Hello World</b>
</body>
</html>

"""

(clientsocket, address) = serversocket.accept()
sent = clientsocket.sendall(msg.encode('utf-8'))