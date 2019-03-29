import os,sys,_thread,socket,logging,json
MAX_DATA_RECV = 4096    # max number of bytes we receive at once
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect('0.0.0.0')
while(1):
    msg_send = input()
    s.sendall(msg_send.encode('utf-8'))
    msg_recv = s.recv(MAX_DATA_RECV).decode('utf-8')
    print(msg_recv)