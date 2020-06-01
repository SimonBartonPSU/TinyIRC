import socket
import select
import errno
import re
import os
import signal
import sys
import pprint
from helper import check_for_config, lobby_welcome, end_session, interpret_lobby_message

HEADER_LENGTH = 10

IP = "127.0.0.1"
CONNECTION_PORT = 9001

class Client: 
    def __init__(self):
        self.pp = pprint.PrettyPrinter(indent=4)
        # Setup connection
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((IP, CONNECTION_PORT))
        self.client_socket.setblocking(False)
        self.username = ''
        self.config = {'username':'','rooms':[]}

        # Look for config, or setup username if no config
        if check_for_config(self):
            print("Config file detected and loaded successfully. Welcome back, {0}".format(self.username))
        else:
            print("No config file detected... Please setup your name.")
            while not self.username.isalpha() or len(self.username) > 30:
                self.username = input("Please enter alphabetical username of 30 characters or less: ").encode('utf-8')
            self.config['username'] = self.username.decode('utf-8')
    

    # Handle ctrl+C crash
    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C! Config will not be saved!')
        sys.exit(0)


    def run(self):
        # Tell server our username len
        username_header = f"{len(self.username):<{HEADER_LENGTH}}"
        msg = username_header + self.username.decode('utf-8')
        self.client_socket.send(bytes(msg, 'utf-8'))
        lobby_welcome()
        while True:

            message = input(f"{self.username.decode('utf-8')} > ")

            # If user actually typed something in and it's a valid command, send it
            if message == "$$$end":
                end_session(self)
            elif interpret_lobby_message(message):
                message = message.encode('utf-8')
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                self.client_socket.send(message_header + message)
                
            # handle response 1K at a time
            try:
                while True:
                    data = self.client_socket.recv(1024)
                    # Lost conn to server
                    if not data:
                        sys.exit
                    print(data.decode('utf-8'))

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error', str(e))
                    sys.exit()
                continue

            except Exception as e:
                print('General error', str(e))
                sys.exit


c = Client()
signal.signal(signal.SIGINT, c.signal_handler)
c.run()
