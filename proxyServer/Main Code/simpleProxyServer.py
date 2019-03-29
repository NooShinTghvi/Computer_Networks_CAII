import os,sys,_thread,socket
import logging
#********* CONSTANT VARIABLES *********
BACKLOG = 50            # how many pending connections queue will hold
MAX_DATA_RECV = 4096    # max number of bytes we receive at once
DEBUG = False           # set to True to see the debug msgs

#********* MAIN PROGRAM ***************
def main():
    # host and port info.
    host = '127.0.0.1'                # blank for localhost
    #print(socket.gethostname())    #the socket would be visible to the outside world
    port = 8088                       # port from argument

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
        #print('Connection address:', client_addr)
        logging.info('Connection address:' + str(client_addr))
        # create a thread to handle request
        _thread.start_new_thread(proxy_thread, (conn, client_addr))

    s.close()

def proxy_thread(conn, client_addr):

    # get the request from browser
    while(1):
        request = conn.recv(MAX_DATA_RECV)
        if not request :
            print("data not exist")
            break
        print("received data:",request)
        conn.send(request)  # echo

    conn.close()

if __name__ == '__main__':
    # ********* log file *********
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)-21s %(levelname)-8s %(message)s',
        datefmt='[%y/%m/%d %H:%M:%S]:',
        filename='myapp2.log',
        filemode='w'
    )
    logging.info('Hi')
    main()