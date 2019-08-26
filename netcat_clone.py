#!/usr/bin/python
### Netcat clone ###
import sys
import socket
import getopt
import threading
import subprocess
from termcolor import colored as c

# Define global variables
listen             = False
command            = False
upload             = False
execute            = ""
target             = ""
upload_Destination = ""
port               = 0

def usage():
    print c("[#] Netcat-like tool [#]","yellow") + "\r\n"
    print c("Usage: ","cyan") + c(sys.argv[0],"cyan") + c(" -t target_host -p port","cyan")
    print c("-l --listen             - listen on [host]:[port]","cyan")
    print c("-e --execute=file       - execute the given file upon receiving connection","cyan")
    print c("-c --command            - initialize a command shell","cyan")
    print c("-u --upload=destination - upload a file upon receiving connection","cyan")
    print "\r\n"
    print c("[#] Examples: ","yellow")
    print c(sys.argv[0],"cyan") + c(" -t 10.0.0.10 -p 5000 -l -c","cyan")
    print c(sys.argv[0],"cyan") + c(" -t 10.0.0.10 -p 5000 -l -u=c:\\target.exe","cyan")
    print c(sys.argv[0],"cyan") + c(" -t 10.0.0.10 -p 5000 -l -e'cat /etc/passwd'","cyan")
    sys.exit(0)

def client_sender(buffer):
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to target host
        client.connect((target,port))
        
        if len(buffer):
            client.send(buffer)
        
        while True:
            # Wait for data back
            recv_len = 1
            response = ""
            
            while recv_len:
                data     = client.recv(4096)
                recv_len = len(data)
                response += data
                
                if recv_len < 4096:
                    break
            print response,
            
            # Wait for more input
            buffer = raw_input("")
            buffer += "\n"
            
            # Send it off
            client.send(buffer)
    
    except:
        print c("[!] Exception! Exiting.","white","on_red")
        
        # Tear down connection
        client.close()

def server_loop():
    global target
    
    # If no target is defined, listen on all interfaces
    if not len(target):
        target = "0.0.0.0"
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    
    server.listen(5)
    
    while True:
        client_socket, addr = server.accept()
        
        # Spin off a thread to handle the new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    # Trim the newline
    command = command.rstrip()
    
    # Run the command and get the output back
    try:
        output = subprocess.check_output(command,stderr=subprocess.STDOUT, shell=True)
    except:
        output = "[!] Failed to execute command.\r\n"
        
    # Send the output back to the client
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command
    
    # Check for upload
    if len(upload_Destination):
        # Read in all of the bytes and write to destination
        file_buffer = ""
        
        # Keep reading data until none is available
        while True:
            data = client_socket.recv(1024)
            
            if not data:
                break
            
            else:
                file_buffer += data
        # Now we take those bytes and try to write them out
        try:
            file_descriptor = open(upload_Destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            
            # Acknowledge that we wrote the file out
            client_socket.send("[+] Successfully saved file to %s\r\n" % upload_Destination)
        except:
            client_socket.send("[!] Failed to save file to %s\r\n" % upload_Destination)
            
    # Check for command execution
    if len(execute):
        # Run the command
        output = run_command(execute)
        
        client_socket.send(output)
    
    # Now we go into another loop if a command shell was requested
    if command:
        while True:
            # Show a simple prompt
            client_socket.send("<FoxShell:#> ")
            
            # Now we receive until we see a linefeed (Enter key)
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
                
            # Send back the command output
            response = run_command(cmd_buffer)
            
            # Send back the response
            client_socket.send(response)


def main():
    global listen
    global port
    global execute
    global command
    global upload_Destination
    global target
    
    if not len(sys.argv[1:]):
        usage()
    # Read command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print c(str(err),"white","on_red")
        usage()
        
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execute"):
            execute = a
        elif o in ("-c","--commandshell"):
            command = True
        elif o in ("-u","--upload"):
            upload_Destination = a
        elif o in ("-t","--target"):
            target = a
        elif o in ("-p","--port"):
            port = int(a)
        else:
            assert False,"Unhandled Option"
            
    # Are we going to listen or just send data from stdin?
    if not listen and len(target) and port > 0:
        
        # Read in the buffer from commandline
        # this will block, so send CTRL-D if not sending input
        # to stdin
        buffer = sys.stdin.read()
        
        # Send data off
        client_sender(buffer)
        
    # We are going to listen ant potentially
    # upload things, execute commands, and drop a shell back
    # depending on our command line options above
    if listen:
        server_loop()
        
main()