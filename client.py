import socket
import select
import errno
import re
import os
import signal
import sys
import pprint
import time
from helper import check_for_config, lobby_welcome, end_session, interpret_lobby_message

HEADER_LENGTH = 10

IP = "127.0.0.1"
CONNECTION_PORT = 9001

class Client:
    """
    TinyIRC client
    Establishes a TCP connection with server at specified IP and
    port 9001. Then sends messages and commands to the server after
    connection has been established.
    """
    def __init__(self):
        self.pp = pprint.PrettyPrinter(indent=4)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((IP, CONNECTION_PORT))
        self.client_socket.setblocking(False)
        self.username = ''
        self.entered = False
        self.entered_channel = ''
        self.ticker = 0
        self.config = {'username':'','rooms':[]}


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

    def send_message(self, message):
        """
        Basic send message mechanism. Allows client to send
        a fixed 10-byte header that contains the length of the
        following payload message.
        """
        message = message.encode('utf-8')
        header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(header + message)


    def receive_message(self):
        """
        Receive a message from a server socket
        First interprets the header of 10 bytes,
        which is telling the server the length of the following message
        """
        try:
            message_header = self.client_socket.recv(HEADER_LENGTH)

            if not len(message_header):
                return False

            message_length = int(message_header.decode("utf-8").strip())
            return {"header": message_header, "data":self.client_socket.recv(message_length)}

        except:
            return False

    def get_input(self):
        prompt = f"{self.username.decode('utf-8')} > "
        if self.entered:
            prompt += self.entered_channel + ' : '
        return input(prompt)


    def handle_message_to_send(self, message):
        if message == "$$$end":
            end_session(self)
            self.client_socket.close()
            sys.exit(0)

        client_analysis = interpret_lobby_message(self, message)
        
        if message == "$$exit":
            print(f"Exiting active mode in channel {self.entered_channel}")
            self.entered = False
            self.entered_channel = ''
            self.send_message(message)
        elif (self.entered and message) or client_analysis:
            split_message = message.split()
            # If user has entered a room, make sure their message is sent to that room
            # by replacing their input with the $$send command
            if self.entered and split_message[0:1] is not ['$$send', str(self.entered_channel)]:
                split_message.insert(0, '$$send ' + self.entered_channel)
                message = ' '.join(map(str, split_message))
            
            if split_message[0] == "$$enter":
                self.entered = True
                _room = split_message[1]
                self.entered_channel = _room
                print(f"Attempting to enter room {_room}")

            self.send_message(message)
            # Sleep slightly to allow IO
            time.sleep(0.1)


    def check_socket(self):
        while True:
            msg = self.receive_message()
            
            # Booted
            if msg and msg['data'].decode('utf-8').split()[0] == "Booting":
                print("Error! Server connection lost... Booted")
                end_session(self)
                self.client_socket.close()
                sys.exit(0)
            if msg:
                recvd = msg['data'].decode('utf-8')
                print(recvd)
                if recvd.split()[-1] == "NONACTIVE":
                    self.entered = False
                    self.entered_channel = ''
            if not msg:
                break


    def run(self):
        """
        Main routine, message processing
        """
        self.send_message(self.username.decode('utf-8'))
        lobby_welcome()
        while True:
            message = self.get_input()
            if message:
                self.handle_message_to_send(message)
                
            try:
                self.check_socket()
                        
            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error', str(e))
                    end_session(self)
                continue

            except Exception as e:
                print('General error', str(e))
                end_session(self)


c = Client()
signal.signal(signal.SIGINT, c.signal_handler)
c.run()
