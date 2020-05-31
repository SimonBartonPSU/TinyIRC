import socket
import select
import errno
import re
import os
import signal
import sys
import pickle

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 9001

class Client: 
    def __init__(self):
        # Setup connection
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((IP, PORT))
        self.client_socket.setblocking(False)
        self.config = {}

        # Look for config, or setup username if no config
        def check_for_config(self):
            path = os.environ.get('HOME') + '/.tiny'
            if os.path.exists(path):

                # TODO this doesn't actually work cause save doesnt actually work yet
                def load_config(self):
                    with open('path','rb') as fp:
                        self.config = pickle.load(fp)

                try:
                    load_config(self)
                except Exception as e:
                    print("Exception occured while loading client config... {0}".format(e))

                return True
            else:
                return False
        
        if check_for_config(self):
            print("Config file detected and loaded successfully. Welcome back, {self.username}")
        else:
            print("No config file detected... Please setup your name.")
            def setup_username(self):
                my_username = ''
                while not my_username.isalpha():
                    my_username = input("Please enter alphabetical username: ")
                    username = my_username.encode('utf-8')
                return username
            self.username = setup_username(self)


    def run(self):
        username_header = f"{len(self.username):<{HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(username_header + self.username)
        while True:
            message = input(f"{self.username} > ")

            if message:
                message = message.encode('utf-8')
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                self.client_socket.send(message_header + message)

            try:
                while True:
                    username_header = self.client_socket.recv(HEADER_LENGTH)
                    if not len(username_header):
                        print("connection closed by the server")
                        sys.exit()

                    username_length = int(username_header.decode('utf-8'))
                    username = self.client_socket.recv(username_length).decode('utf-8')

                    message_header = self.client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')

                    print(f"{username} > {message}")

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error', str(e))
                    sys.exit()
                continue

            except Exception as e:
                print('General error', str(e))
                sys.exit

# Handle ctrl+C crash
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    print('We should probably save a config when ctrl c is hit huh///?')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
c = Client()
c.run()