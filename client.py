import socket
import select
import errno
import re
import os
import signal
import sys
import json
import pprint
from helper import lobby_welcome, print_response

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
        def check_for_config(self):
            try:
                path = os.environ.get('HOME') + '/.tiny'
                if os.path.exists(path):
                    with open(path) as f:
                        self.config = json.load(f)
                    self.username = self.config['username']
                    return True
                else:
                    return False
            except Exception as e:
                print("Exception occured while loading client config... {0}".format(e))

        if check_for_config(self):
            print("Config file detected and loaded successfully. Welcome back, {0}".format(self.username))
        else:
            print("No config file detected... Please setup your name.")
            while not self.username.isalpha():
                self.username = input("Please enter alphabetical username: ").encode('utf-8')
            self.config['username'] = self.username.decode('utf-8')
    

    def save_config(self):
        try:
            path = os.environ.get('HOME') + '/.tiny'
            with open(path, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print("Error saving config!! {0}".format(e))

    # Handle ctrl+C crash
    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C! Saving config to $HOME/.tiny')
        self.save_config()
        sys.exit(0)


    def run(self):
        # Tell server our username len
        username_header = f"{len(self.username):<{HEADER_LENGTH}}"
        self.client_socket.send(username_header.encode('utf-8') + self.username)
        lobby_welcome()
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
                    print(f"{username}: {message}")

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error', str(e))
                    sys.exit()
                continue

            except Exception as e:
                print('General error', str(e))
                sys.exit

#try:
c = Client()
signal.signal(signal.SIGINT, c.signal_handler)
c.run()
#except Exception as e:
 #   print("Exception occured during client operation... {0}".format(e))