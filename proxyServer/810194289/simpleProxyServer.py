import os
import sys
import _thread
import socket
import logging
import json
import datetime
import base64
import time
import re

# ********* CONSTANT VARIABLES *********
BACKLOG = 50            # how many pending connections queue will hold
MAX_DATA_RECV = 4096    # max number of bytes we receive at once
DEBUG = True           # set to True to see the debug msgs
DEBUG_requests = False
DEBUG_checking = False
DEBUG_Mail = False         



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

        if (DEBUG_requests):
            logging.info("* * * * received data from bowser * * * *")
            logging.info(request.decode('utf-8'))

        users[index]["volume"] = str(int(users[index]["volume"]) - len(request))

        # Convert HTTP/1.1 To HTTP/1.0
        request_str = request.decode('utf-8').replace("HTTP/1.1", "HTTP/1.0")

        # Delete Proxy-Connection: keep-alive
        #request_str = re.sub('Proxy-Connection: keep-alive\r\n', '', request_str)

        # Privacy
        request_str = self.Privacy(request_str,config)

        new_request = request_str.encode('utf-8')
        #new_request = request

        url, webserver, port = self.FindDataFromUrl(logging,request_str)

        self.isUrlInCache(url, cache, conn)

        self.Restriction(config, webserver, conn)

        if (DEBUG_requests):
            logging.warning("* * * * Send data To Server * * * *")
            logging.warning(new_request.decode('utf-8'))

        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(new_request)  # send request to webserver

        while 1:
            # receive data from web server
            data = s.recv(MAX_DATA_RECV)
            data_str = data.decode('utf-8')

            if (DEBUG_requests):
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
                    logging.warning("BlahhhBlahhh")
            else:
                break
        s.close()
        conn.close()

    def writeCacheFile(self,cache):
        cacheFile = open('cache.json', 'w')
        json.dump(cache, cacheFile, indent=4,separators=(", ", " : "))
        cacheFile.close()

    def readCacheFile(self):
        # Read chache File
        cacheFile = open('cache.json')
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

    def sendEmail(self, logging):
        mailserver = ("mail.ut.ac.ir", 25)  # Fill in start #Fill in end
        # Telnet mail.ut.ac.ir 25
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(mailserver)
        recv = clientSocket.recv(1024)
        recv = recv.decode('utf-8')
        if(DEBUG_Mail):
            logging.info("1) Message after connection request:" + str(recv))
        if recv[:3] != '220':
            logging.error('220 reply not received from server.')
        # ********* Introducing to the server ***************
        heloCommand = 'HELO local.domain.com\r\n'
        # EHLO <nooshin> ---- EHLO NooShin --- local.domain.com
        # HELO <nooshintaghavi@ut.ac.ir>
        clientSocket.send(heloCommand.encode('utf-8'))
        recv1 = clientSocket.recv(1024)
        recv1 = recv1.decode('utf-8')
        if (DEBUG_Mail):
            logging.info("2) Message after EHLO command:" + str(recv1))
        if recv1[:3] != '250':
            logging.error('250 reply not received from server.')
        # ********* Authentication ***************
        username = "nooshintaghavi"
        password = "68177037Nt"
        base64_str = ("\x00" + username + "\x00" + password).encode('utf-8')
        base64_str = base64.b64encode(base64_str)  # base64
        authMsg = "AUTH PLAIN ".encode('utf-8') + base64_str + "\r\n".encode('utf-8')
        # authMsg = AUTH PLAIN AG5vb3NoaW50YWdoYXZpADY4MTc3MDM3TnQ=
        # authMsg = AUTH LOGIN AG5vb3NoaW50YWdoYXZpADY4MTc3MDM3TnQ=
        clientSocket.sendall(authMsg)
        recv_auth = clientSocket.recv(1024)
        if (DEBUG_Mail):
            logging.info("3) " + str(recv_auth.decode('utf-8')))
        # ********* Specify the sender's address ***************
        mailFrom = "MAIL FROM:<nooshintaghavi@ut.ac.ir>\r\n"
        clientSocket.sendall(mailFrom.encode('utf-8'))
        recv2 = clientSocket.recv(1024)
        recv2 = recv2.decode('utf-8')
        if (DEBUG_Mail):
            logging.info("4) After MAIL FROM command: " + str(recv2))
        # ********* Specify the address of the recipient ***************
        rcptTo = "RCPT TO:<nooshin.tghvi@gmail.com>\r\n"
        clientSocket.send(rcptTo.encode('utf-8'))
        recv3 = clientSocket.recv(1024)
        recv3 = recv3.decode('utf-8')
        if (DEBUG_Mail):
            logging.info("5) After RCPT TO command: " + str(recv3))
        # ********* E-mail text ***************
        data = "DATA\r\n"
        clientSocket.send(data.encode('utf-8'))
        recv4 = clientSocket.recv(1024)
        recv4 = recv4.decode('utf-8')
        if (DEBUG_Mail):
            logging.info("6) After DATA command: " + str(recv4))
        subject = "Subject: testing my client\r\n\r\n"  # Subject
        clientSocket.send(subject.encode('utf-8'))
        date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        date = date + "\r\n\r\n"
        clientSocket.send(date.encode('utf-8'))
        msg = "\r\n I love computer networks!"  # massage
        clientSocket.send(msg.encode('utf-8'))
        endmsg = "\r\n.\r\n"
        clientSocket.send(endmsg.encode('utf-8'))
        recv_msg = clientSocket.recv(1024)
        if (DEBUG_Mail):
            logging.info("7) Response after sending message body:" + str(recv_msg.decode('utf-8')))
        quit = "QUIT\r\n"
        clientSocket.send(quit.encode('utf-8'))
        recv5 = clientSocket.recv(1024)
        print(recv5.decode('utf-8'))
        clientSocket.close()

    def FindDataFromUrl(self,logging,request_str ):
        # parse the first line
        first_line = request_str.split('\n')[0]
        # get url
        url = first_line.split(' ')[1]
        if (DEBUG_checking):
            logging.debug("first_line: " + str(first_line))
            logging.debug("URL:" + str(url))
        # find the webserver and port
        http_pos = url.find("://")  # find pos of ://
        if (DEBUG_checking):
            logging.debug("http_pos: " + str(http_pos))
        if (http_pos == -1):
            temp = url
        else:
            temp = url[(http_pos + 3):]  # get the rest of url
            if (DEBUG_checking):
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

        if (DEBUG_checking):
            logging.INFO("Connect to:" + str(webserver) + "   " + str(port))

        return url,webserver,port

    def Privacy(self,request_str,config):
        if (config["privacy"]["enable"]):
            lines = request_str.split('\n')
            for line in range(len(lines)):
                if ('User-Agent' == lines[line].split(':')[0]):
                    lines[line] = 'User-Agent: ' + config["privacy"]["userAgent"] + '\r'
            request_str = '\n'.join(lines)
        return request_str

    def Restriction(self,config, webserver, conn):
        if (config["restriction"]["enable"]):
            targets = config["restriction"]["targets"]
            for t in range(len(targets)):
                if (webserver == targets[t]["URL"]):
                    if (targets[t]["notify"]):
                        self.sendEmail(logging)
                    conn.close()
                    sys.exit(0)

    def isUrlInCache(self, url, cache, conn):
        if (url in cache):
            conn.send(cache[url]['data'].encode('utf-8'))
            cacheData = cache[url]
            del cache[url]
            cache[url] = cacheData
            self.writeCacheFile(cache)
            conn.close()
            sys.exit(0)

if __name__ == '__main__':
    config = json.loads(open('config.json').read())  # Read json file
    if (config["logging"]["enable"]):
        logging.basicConfig(  # create log file
            level=logging.DEBUG,
            format='%(asctime)-21s %(levelname)-8s %(message)s',
            datefmt='[%y/%m/%d %H:%M:%S]:',
            filename=config["logging"]["logFile"],
            filemode='w'
        )
    # initial cache file and user data
    f = open('cache.json', 'w')
    json.dump({}, f)
    f.close()

    f = open('users.json', 'w')
    json.dump({}, f)
    f.close()

    p = ProxyServer(config, logging)
