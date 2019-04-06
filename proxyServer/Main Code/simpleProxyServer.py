import os
import sys
import _thread
import socket
import logging
import json
import datetime
import re

# ********* CONSTANT VARIABLES *********
BACKLOG = 50            # how many pending connections queue will hold
MAX_DATA_RECV = 4096    # max number of bytes we receive at once
DEBUG = True           # set to True to see the debug msgs
DEBUG2 = False
DEBUG3 = False



# ********* MAIN PROGRAM ***************
class ProxyServer:
    def __init__(self, config, logging):
        # host and port info.
        self.host = '0.0.0.0'  # localhost
        # print(socket.gethostname())                #the socket would be visible to the outside world
        self.port = config["port"]  # Use from port of Json file

        # Create a TCP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # associate the socket to host and port
        self.s.bind((self.host, self.port))

        # listenning
        self.s.listen(BACKLOG)

        logging.info('socket is ready to listening')

        # users
        self.users = config["accounting"]["users"]
        self.writeDataUser(self.users)

        # get the connection from client
        while 1:
            conn, client_addr = self.s.accept()

            isUser = False

            for i in range(len(self.users)):
                if (client_addr[0] == self.users[i]["IP"]):
                    isUser = True

            if (isUser):
                logging.info('new Connection from: ' + str(client_addr))
                # create a thread to handle request
                _thread.start_new_thread(self.proxy_thread, (conn, client_addr, logging, config))

            else :
                conn.sendall("<html>you are not one of us</html>".encode('utf-8'))
                logging.info("Illegal access from: " + str(client_addr))


        self.s.close()

    def proxy_thread(self, conn, client_addr, logging, config):
        cache = self.readCacheFile()
        users,index = self.readDataUser(client_addr)
        # get the request from browser
        request = conn.recv(MAX_DATA_RECV)

        users[index]["volume"] = str(int(users[index]["volume"]) - len(request))

        # Convert HTTP/1.1 To HTTP/1.0
        request_str = request.decode('utf-8').replace("HTTP/1.1", "HTTP/1.0")

        # Delete Proxy-Connection: keep-alive
        #request_str = re.sub('Proxy-Connection: keep-alive\r\n', '', request_str)

        # Privacy
        if (config["privacy"]["enable"]):
            lines = request_str.split('\n')
            for line in range(len(lines)):
                if ('User-Agent' == lines[line].split(':')[0]):
                    lines[line] = 'User-Agent: ' + config["privacy"]["userAgent"] + '\r'
            request_str = '\n'.join(lines)

        if(DEBUG2):
            logging.info("* * * * received data from bowser * * * *")
            logging.info(request_str)

            new_request = request_str.encode('utf-8')
            #new_request = request

        # parse the first line
        first_line = request_str.split('\n')[0]
        # get url
        url = first_line.split(' ')[1]
        if (DEBUG3):
            logging.debug("first_line: " + str(first_line))
            logging.debug("URL:" + str(url))
        if(url in cache):
            conn.send(cache[url]['data'].encode('utf-8'))
            cacheData = cache[url]
            del cache[url]
            cache[url] = cacheData

            cacheFile = open('cached/cache.json', 'w')
            json.dump(cache, cacheFile, indent=4, separators=(", ", " : "))
            cacheFile.close()
            
            conn.close()
            sys.exit(0)

        # find the webserver and port
        http_pos = url.find("://")  # find pos of ://
        if (DEBUG3):
            logging.debug("http_pos: " + str(http_pos))
        if (http_pos == -1):
            temp = url
        else:
            temp = url[(http_pos + 3):]  # get the rest of url
            if (DEBUG2):
                logging.debug("temp: " + str(temp))

        port_pos = temp.find(":")  # find the port pos (if any)

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos == -1 or webserver_pos < port_pos):
            # default port
            port = 80
            webserver = temp[:webserver_pos]
        else:  # specific port
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        if (DEBUG2):
            logging.INFO("Connect to:" + str(webserver) + "   " + str(port))

        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(request)  # send request to webserver
        if (DEBUG):
            logging.warning("* * * * Send data To Server * * * *")
            logging.warning(new_request.decode('utf-8'))

        while 1:
            # receive data from web server
            data = s.recv(MAX_DATA_RECV)
            data_str = data.decode('utf-8')

            if (DEBUG):
                logging.critical("* * * * received data from server * * * *")
                logging.critical(data_str)

            cacheAble = 1
            cacheType = {'type': 'simple'}

            if (len(data) > 0):
                # send to browser
                conn.send(data)
                users[index]["volume"] = str(int(users[index]["volume"]) - len(data))
                self.writeDataUser(users)
                try:
                    cacheControl = str(data.decode('utf-8')).split('\n')[4]
                    cacheOptions = cacheControl.split(':')[1].split(',')
                    for option in cacheOptions:
                        option = option.strip()
                        if(option == "no-cach"):
                            cacheAble = 0
                        if(option == 'expire'):
                            cacheType = {'type': 'expire',
                                         'time': datetime.datetime.now()}

                    if(cacheAble == 1):
                        if(len(cache) < config["caching"]["size"]):
                            a = {}
                            a['data'] = data.decode('utf-8')
                            a['cacheConfig'] = cacheType
                            cache[url] = a
                        else:
                            del cache[list(cache.keys())[0]]
                            a = {}
                            a['data'] = data.decode('utf-8')
                            a['cacheConfig'] = cacheType
                            cache[url] = a

                    self.writeCacheFile(cache)

                except IndexError:
                    print("salam")
            else:
                break
        s.close()
        conn.close()
        # except (socket.error, (value, message)):
        #    if s:
        #        s.close()
        #    if conn:
        #        conn.close()
        #    print("Runtime Error:", message)
        #    sys.exit(1)

    def writeCacheFile(self,cache):
        cacheFile = open('cached/cache.json', 'w')
        json.dump(cache, cacheFile, indent=4,separators=(", ", " : "))
        cacheFile.close()

    def readCacheFile(self):
        # Read chache File
        cacheFile = open('cached/cache.json')
        cache = json.loads(cacheFile.read())
        cacheFile.close()
        return cache

    def writeDataUser(self, users):
        u = {}
        for i in range(len(users)):
            u[str(i)]=users[i]
        f = open('users.json', 'w')
        json.dump(u, f, indent=4, separators=(", ", " : "))
        f.close()

    def readDataUser(self,client_addr):
        f = open('users.json')
        u = json.loads(f.read())
        f.close()
        users = []
        index = 0
        for i in range(len(u)):
            users.append(u[str(i)])
            if (client_addr[0] == users[i]["IP"]):
                index = i
        return users,index

if __name__ == '__main__':
    config = json.loads(open('../Json/config.json').read())  # Read json file
    if (config["logging"]["enable"]):
        logging.basicConfig(  # create log file
            level=logging.DEBUG,
            format='%(asctime)-21s %(levelname)-8s %(message)s',
            datefmt='[%y/%m/%d %H:%M:%S]:',
            filename='../log/'+config["logging"]["logFile"],
            filemode='w'
        )
    # initial cache file and user data
    f = open('cached/cache.json', 'w')
    json.dump({}, f)
    f.close()

    f = open('users.json', 'w')
    json.dump({}, f)
    f.close()

    p = ProxyServer(config, logging)
