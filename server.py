import socket
import select
import signal
import sys
import pprint
from helper import *

HEADER_LENGTH = 10
IP = "127.0.0.1"
LISTENING_PORT = 9001
CLIENT_NO = 0
ROOM_NO = 0

class Room:
    def __init__(self, name='Linux', topic='Default', creator='Auto'):
        self.name = name
        self.room_attrbts = {'topic' : topic, 
                        'creator': creator,
                        'members': set(),
                        'admins': [creator]}

class Server:
    def __init__(self):
        # this is where load file could happen
        self.pp = pprint.PrettyPrinter(indent=4)
        self.rooms = []
        self.clients = {}
        self.name_list = []
        # Setup client acceptance over TCP on 127.0.0.1:9001
        # UDP would be SOCK_DGRAM
        self.server_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_listen_socket.bind((IP, LISTENING_PORT))
        self.server_listen_socket.listen()
        self.sockets_list = [self.server_listen_socket]

    def receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(HEADER_LENGTH)

            if not len(message_header):
                return False

            message_length = int(message_header.decode("utf-8").strip())
            return {"header": message_header, "data":client_socket.recv(message_length)}

        except:
            return False

    def send_message(self, message, client_socket):
        pass


    # Handle ctrl+C crash
    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C! Woow')
        print('need to save a config when ctrlC hit by server ...')
        print("Known clients, rooms:")
        self.pp.pprint(self.clients)
        self.pp.pprint(self.rooms)
        sys.exit(0)

    def handle_exceptions(self, exception_sockets):
        for notified_socket in exception_sockets:
            self.sockets_list.remove(notified_socket)
            del self.clients[notified_socket]


    def handle_new_conns(self, read_sockets):
        for notified_socket in read_sockets:
            # Accept and handle new clients on TCP 9001
            if notified_socket == self.server_listen_socket:
                self.latest_client_socket, self.latest_client_address = self.server_listen_socket.accept()
                print("Accepted new connection from {0}:{1}".format(self.latest_client_address[0], self.latest_client_address[1]))
                user = self.receive_message(self.latest_client_socket)
                if user is False:
                    continue

                self.sockets_list.append(self.latest_client_socket)
                self.clients[self.latest_client_socket] = user

                print("Accepted new user: {0}".format(user['data'].decode('utf-8')))
            
            # If already a client conn, show lobby
            else:
                message = self.receive_message(notified_socket)

                # User quits
                if message is False:
                    print("Closed connection from {0}".format(self.clients[notified_socket]['data'].decode('utf-8')))
                    self.sockets_list.remove(notified_socket)
                    del self.clients[notified_socket]
                    continue

                # User's socket sent us something
                user = self.clients[notified_socket]
                print("Received message from {0}: {1}".format(user['data'].decode('utf-8'), message['data'].decode('utf-8')))
                print("Sending response to {0}".format(user['data'].decode('utf-8')))
                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                print("Interpreting...")
                lobby_action = interpret_lobby_message(message)
                if lobby_action == 1:
                    # send unknown response 1
                    pass
                elif lobby_action == 2:
                    # send new response of 2
                    pass
                elif lobby_action == 3:
                    #sned help response 3
                    pass
                elif lobby_action == 4:
                    # send close error response 4
                else:
                    handle_lobby_command(lobby_action)

                # broadcast to all in a room in some way
                #for client_socket in self.clients:
                 #   if client_socket != notified_socket:
                  #      client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
    

    def run(self):
        print("Central server now listening...")
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            self.handle_new_conns(read_sockets)
            self.handle_exceptions(exception_sockets)

try:
    s = Server()
    signal.signal(signal.SIGINT, s.signal_handler)
    s.run()
except Exception as e:
    print("Exception occured during server operation... {0}".format(e))