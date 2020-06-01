import socket
import select
import signal
import sys
import pprint

HEADER_LENGTH = 10
IP = "127.0.0.1"
LISTENING_PORT = 9001
CLIENT_NO = 0
ROOM_NO = 0

class Room:
    def __init__(self, creator, name='Linux', topic='Default'):
        self.name = name
        self.socket = None
        self.room_attrbts = {'topic' : topic, 
                        'creator': creator,
                        'members': { creator },
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


    # Handle ctrl+C crash
    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C! Woow')
        print('need to save a config when ctrlC hit by server ...')
        print("Known clients:")
        self.pp.pprint(self.clients)
        print("Known rooms:")
        for room in self.rooms: 
            self.pp.pprint(room.name)
            self.pp.pprint(room.room_attrbts)
        sys.exit(0)


    def handle_exceptions(self, exception_sockets):
        for notified_socket in exception_sockets:
            print("Dropping socket {0} due to exception".format(repr(notified_socket)))
            self.sockets_list.remove(notified_socket)
            del self.clients[notified_socket]


    def handle_conns(self, read_sockets):
        for notified_socket in read_sockets:
            print("Checking sockets...")
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

                # User's socket sent us something in lobby
                user = self.clients[notified_socket]
                print("Received message from {0}: {1}".format(user['data'].decode('utf-8'), message['data'].decode('utf-8')))
                print("Interpreting... {0}".format(message['data']))
                self.handle_lobby_command(message['data'], notified_socket)


    def handle_lobby_command(self, lobby_command, client_socket):
        lobby_command = lobby_command.decode('utf-8')
        words = lobby_command.split()
        first = words[0]

        # Catch initial errors
        if len(words) == 1:
            msg = ''
            if first == "$$create":
                msg = "Must specify a room name argument to execute $$create! [E.g. $$create pokemon]"
                print("User did not specify roomname to create")
            if first == "$$join":
                msg = "Must specify a room name argument to execute $$join! [E.g. $$join pokemon]"
                print("User did not specify roomname to join")
            if first == "$$leave":
                msg = "Must specify a room name argument to execute $$leave! [E.g. $$leave pokemon]"
                print("User did not specify roomname to leave")
            if first == "$$enter":
                msg = "Must specify a room name argument to execute $$enter! [E.g. $$enter pokemon]"
                print("User did not specify roomname to enter")
            if msg != '':
                client_socket.send(bytes(msg, 'utf-8'))
                return

        if first == "$$create":
            self.handle_room_create(lobby_command, client_socket)
        elif first == "$$join":
            self.handle_join_room(lobby_command, client_socket)
        elif first == "$$leave":
            self.handle_leave_room(lobby_command, client_socket)
        elif first == "$$list":
            self.handle_list_room(lobby_command, client_socket)
        elif first == "$$enter":
            self.handle_enter_room_session(lobby_command, client_socket)
        elif first == "$$whoami":
            self.handle_whoami(client_socket)
        else:
            print("Not sure how this lobby command got to server. Should have been filtered by client filter")

    def handle_whoami(self, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        print('User {0} queried their identity'.format(user))
        msg = 'You are currently user {0}'.format(user)
        client_socket.send(bytes(msg, 'utf-8'))

    def handle_room_create(self, lobby_command, client_socket):
        msg = "Handling room creation of {0}".format(lobby_command)
        print(msg)
        roomname = lobby_command.split()[1]
        for room in self.rooms:
            if room.name == roomname:
                msg = "Invalid request from client: {0} already exists!".format(roomname)
                client_socket.send(bytes(msg, 'utf-8'))
                print(msg)
                return
        
        user = self.clients[client_socket]['data'].decode('utf-8')
        print("Creator of room will be {0}".format(user))
        self.rooms.append(Room(name=roomname, creator=user))
        client_socket.send(bytes("Room {0} created!".format(roomname), 'utf-8'))
        print("Created room for client. Response sent.")
        return


    def handle_join_room(self, lobby_command, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        words = lobby_command.split()
        roomname = words[1]
        print("Handling join room {0} for {1}".format(roomname, user))
        for _room in self.rooms:
            if _room.name == roomname:
                print("Requested roomname found..")
                if user in _room.room_attrbts['members']:
                    msg = "Client {0} is already a member of room {1}".format(user, _room.name)
                    print(msg)
                    client_socket.send(bytes(msg, 'utf-8'))
                    return
                else:
                    _room.room_attrbts['members'].add(user)
                    msg = "{0} successfully joined membership of room {1}".format(user,roomname)
                    print(msg)
                    client_socket.send(bytes(msg, 'utf-8'))
                    return
        msg = 'Client {0} passed invalid room. Could not join room {1}'.format(user, roomname)
        print(msg)
        client_socket.send(bytes(msg, 'utf-8'))
        return


    def handle_leave_room(self, lobby_command, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        words = lobby_command.split()
        roomname = words[1]
        print("Handling leave room {0} for {1}".format(roomname, user))
        for _room in self.rooms:
            if _room.name == roomname:
                print("Requested roomname found..")
                if user not in _room.room_attrbts['members']:
                    msg = "Client {0} is already NOT a member of room {1}".format(user, _room.name)
                    print(msg)
                    client_socket.send(bytes(msg, 'utf-8'))
                    return
                else:
                    _room.room_attrbts['members'].remove(user)
                    msg = "User successfully removed from room {0}...".format(roomname)
                    print (msg)
                    msg = "You've successfully left membership of room {0}".format(roomname)
                    client_socket.send(bytes(msg, 'utf-8'))
                    return
        msg = 'Client {0} passed invalid room. Could not join room {1}'.format(user, roomname)
        print(msg)
        client_socket.send(bytes(msg, 'utf-8'))
        return


    def handle_list_room(self, lobby_command, client_socket):
        print("Handling list command...")
        msg = ''
        words = lobby_command.split()
        if len(words) == 1:
            msg = 'Available Rooms: '
            for room in self.rooms:
                msg += '{0}, '.format(room.name)
        else:
            roomname = words[1]
            if roomname == "mine":
                msg = 'Rooms user {0} has joined'
            for _room in self.rooms:
                if _room.name == roomname:
                    print("Request roomname found..")
                    msg = 'Users in room {0}: '.format(roomname)
                    for member in _room.room_attrbts['members']:
                        msg += '{0}, '.format(member)
            if msg == '':
                raise print('Client passed an invalid room to list members of {0}'.format(roomname))
        
        msg.rstrip(',')
        client_socket.send(bytes(msg, 'utf-8'))


    def handle_enter_room_session(self, lobby_command, client_socket):
        #BIG TODO
        pass


    def run(self):
        print("Central server now listening...")
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            self.handle_conns(read_sockets)
            self.handle_exceptions(exception_sockets)


s = Server()
signal.signal(signal.SIGINT, s.signal_handler)
s.run()
