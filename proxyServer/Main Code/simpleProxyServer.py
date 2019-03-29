import os,sys,_thread,socket,logging,json
#********* CONSTANT VARIABLES *********
BACKLOG = 50            # how many pending connections queue will hold
MAX_DATA_RECV = 4096    # max number of bytes we receive at once
DEBUG = True           # set to True to see the debug msgs

#********* MAIN PROGRAM ***************
def main():
    # host and port info.
    host = '0.0.0.0'                          #localhost
    #print(socket.gethostname())                #the socket would be visible to the outside world
    port = config["port"]                       #Use from port of Json file

    # create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # associate the socket to host and port
    s.bind((host, port))

    # listenning
    s.listen(BACKLOG)

    logging.info('socket is listening')

    # get the connection from client
    while 1:
        conn, client_addr = s.accept()
        logging.info('new Connection from: ' + str(client_addr))
        # create a thread to handle request
        _thread.start_new_thread(proxy_thread, (conn, client_addr))

    s.close()

def proxy_thread(conn, client_addr):
    while (1):
        request = conn.recv(MAX_DATA_RECV).decode('utf-8')
        if not request:
            print("data not exist")
            break
        print("received data:", request)
        msg_send = input()
        conn.sendall(msg_send.encode('utf-8'))


def proxy_thread2(conn, client_addr):
    # get the request from browser
    request = conn.recv(MAX_DATA_RECV).decode('utf-8')
    print(request)
    # parse the first line
    first_line = request.split('n')[0]
    # get url
    url = first_line.split(' ')[1]
    if (DEBUG):
        print(first_line)
        print("URL:", url)

    # find the webserver and port
    http_pos = url.find("://")  # find pos of ://
    print("http_pos: ", http_pos)
    if (http_pos == -1):
        temp = url
    else:
        temp = url[(http_pos + 3):]  # get the rest of url
        print("temp: ", temp)

    port_pos = temp.find(":")  # find the port pos (if any)

    # find end of web server
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if (port_pos == -1 or webserver_pos < port_pos):  # default port
        port = 80
        webserver = temp[:webserver_pos]
    else:  # specific port
        port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
        webserver = temp[:port_pos]

    print("Connect to:", webserver, port)

    try:
        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(request)  # send request to webserver

        while 1:
            # receive data from web server
            data = s.recv(MAX_DATA_RECV)

            if (len(data) > 0):
                # send to browser
                conn.send(data)
            else:
                break
        s.close()
        conn.close()
    except (socket.error, (value, message)):
        if s:
            s.close()
        if conn:
            conn.close()
        print("Runtime Error:", message)
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(                                    #create log file
        level=logging.DEBUG,
        format='%(asctime)-21s %(levelname)-8s %(message)s',
        datefmt='[%y/%m/%d %H:%M:%S]:',
        filename='../log/logFile.log',
        filemode='w'
    )
    config = json.loads(open('../Json/config.json').read()) #Read json file
    main()