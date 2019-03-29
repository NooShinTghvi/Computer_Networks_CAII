from socket import *
import base64
import time

#********* Connect to the server ***************
mailserver = ("mail.ut.ac.ir", 25) #Fill in start #Fill in end
# Telnet mail.ut.ac.ir 25
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(mailserver)
recv = clientSocket.recv(1024)
recv = recv.decode('utf-8')
print("1) Message after connection request:" + recv)
if recv[:3] != '220':
    print('220 reply not received from server.')
#********* Introducing to the server ***************
heloCommand = 'HELO local.domain.com\r\n'
#EHLO <nooshin> ---- EHLO NooShin --- local.domain.com
#HELO <nooshintaghavi@ut.ac.ir>
clientSocket.send(heloCommand.encode('utf-8'))
recv1 = clientSocket.recv(1024)
recv1 = recv1.decode('utf-8')
print("2) Message after EHLO command:" + recv1)
if recv1[:3] != '250':
    print('250 reply not received from server.')
#********* Authentication ***************
username = "nooshintaghavi"
password = "68177037Nt"
base64_str = ("\x00"+username+"\x00"+password).encode('utf-8')
base64_str = base64.b64encode(base64_str)   # base64
authMsg = "AUTH PLAIN ".encode('utf-8') + base64_str + "\r\n".encode('utf-8')
#authMsg = AUTH PLAIN AG5vb3NoaW50YWdoYXZpADY4MTc3MDM3TnQ=
#authMsg = AUTH LOGIN AG5vb3NoaW50YWdoYXZpADY4MTc3MDM3TnQ=
clientSocket.sendall(authMsg)
recv_auth = clientSocket.recv(1024)
print("3) ",recv_auth.decode('utf-8'))
#********* Specify the sender's address ***************
mailFrom = "MAIL FROM:<nooshintaghavi@ut.ac.ir>\r\n"
clientSocket.sendall(mailFrom.encode('utf-8'))
recv2 = clientSocket.recv(1024)
recv2 = recv2.decode('utf-8')
print("4) After MAIL FROM command: " + recv2)
#********* Specify the address of the recipient ***************
rcptTo = "RCPT TO:<nooshin.tghvi@gmail.com>\r\n"
clientSocket.send(rcptTo.encode('utf-8'))
recv3 = clientSocket.recv(1024)
recv3 = recv3.decode('utf-8')
print("5) After RCPT TO command: "+recv3)
#********* E-mail text ***************
data = "DATA\r\n"
clientSocket.send(data.encode('utf-8'))
recv4 = clientSocket.recv(1024)
recv4 = recv4.decode('utf-8')
print("6) After DATA command: "+recv4)
subject = "Subject: testing my client\r\n\r\n"      #Subject
clientSocket.send(subject.encode('utf-8'))
date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
date = date + "\r\n\r\n"
clientSocket.send(date.encode('utf-8'))
msg = "\r\n I love computer networks!"              #massage
clientSocket.send(msg.encode('utf-8'))
endmsg = "\r\n.\r\n"
clientSocket.send(endmsg.encode('utf-8'))
recv_msg = clientSocket.recv(1024)
print("7) Response after sending message body:" + recv_msg.decode('utf-8'))
quit = "QUIT\r\n"
clientSocket.send(quit.encode('utf-8'))
recv5 = clientSocket.recv(1024)
print(recv5.decode('utf-8'))
clientSocket.close()