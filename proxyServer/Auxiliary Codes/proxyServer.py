import os,sys,socket,signal,_thread
class proxyServer:
    from threading import Thread
    def __init__(self, config):
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)
        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # bind the socket to a public host, and a port
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))

        self.serverSocket.listen(10)  # become a server socket
        self.__clients = {}


while True:
    # Establish the connection
    (clientSocket, client_address) = self.serverSocket.accept()

    d = threading.Thread(name=self._getClientName(client_address),
                         target=self.proxy_thread, args=(clientSocket, client_address))
    d.setDaemon(True)
    d.start()