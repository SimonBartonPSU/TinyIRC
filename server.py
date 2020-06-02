import socket
import select
import signal
import sys
import os
import json
import jsonpickle
import pprint

HEADER_LENGTH = 10
IP = "127.0.0.1"
LISTENING_PORT = 9001
CLIENT_NO = 0
ROOM_NO = 0

class Room:
    """
    Core abstraction of this program. Connecting clients want to
    exchange messages with each other in rooms.
    """
    def __init__(self, creator, name='Linux', topic='Default'):
        self.name = name
        self.socket = None
        self.room_attrbts = {'topic' : topic, 
                        'creator': creator,
                        'members': { creator },
                        'active': set(),
                        'admins': [creator]}

class Server:
    def __init__(self):
        """
        Funny little chat server that asynchronosly handles client connections
        and manages a list of Room objects based on user commands.
        """
        self.pp = pprint.PrettyPrinter(indent=4)
        self.rooms = []
        self.clients = {}
        self.name_list = []
        self.server_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_listen_socket.bind((IP, LISTENING_PORT))
        self.server_listen_socket.listen()
        self.sockets_list = [self.server_listen_socket]

        def load_config(self):
            """
            If a config file exists, load it always on server.
            Must manually delete config to start clean or 
            load, make changes and re-save for changes.
            """
            try:
                path = os.environ.get('HOME') + '/.tinyserver'
                if os.path.exists(path):
                    with open(path) as f:
                        JSON = json.load(f)
                        self.rooms = jsonpickle.decode(JSON)
                print('Rooms config loaded...')
                
            except Exception as e:
                print("Error while loading server config {0}".format(e))

        load_config(self)

    def save_config(self):
        """
        Save and print server room state.
        """
        try:
            print("Clearing active users")
            for room in self.rooms:
                room.room_attrbts['active'].clear()
            print('Saving config...')
            print("Known clients:")
            self.pp.pprint(self.clients)
            print("Known rooms:")
            for room in self.rooms: 
                self.pp.pprint(room.name)
                self.pp.pprint(room.room_attrbts)
            path = os.environ.get('HOME') + '/.tinyserver'
            roomJSON = jsonpickle.encode(self.rooms)
            with open(path, 'w') as f:
                json.dump(roomJSON, f)
        except Exception as e:
            print("Error saving config!! {0}".format(e))

    def signal_handler(self, sig, frame):
        """
        Save state, allow server operator to kick, or shutdown server
        on CTRL+C signal.
        """
        print('You pressed Ctrl+C!')
        response = input("Would you like to terminate a user session? [y/n] ")
        if response.lower() == 'exit':
            print("fast exiting..")
            sys.exit(0)


        if response.lower() == 'y':
            trying = 'y'
            while trying.lower() == 'y':
                print("Choose a user to remove:\n")
                user_list = []
                for client in self.clients:
                    user_list.append(self.clients[client]['data'].decode('utf-8'))
                for user in user_list: print(user)
                response = input("Enter user to remove: ")
                for client in self.clients:
                    if self.clients[client]['data'].decode('utf-8') == response:
                        msg = f"Booting client {self.clients[client]} from server..."
                        self.log_and_send(client, msg)
                        print("Closing socket...")
                        #client.close()
                        self.sockets_list.remove(client)
                        del self.clients[client]
                        client.shutdown(socket.SHUT_RDWR)

                        
                        print(f"Client {response} booted. Returning to listening...")
                        return
                trying = input("No matching client found. Try again? [y/n] ")

        response = input("Save config? [y/n] ")

        if response.lower() == 'y' or response == '\n':
            print('Saving config and closing all sockets...')
            for _socket in self.clients:
                self.pp.pprint(_socket)
                _socket.close()
            self.save_config()
        
        response = input("Terminate server session? [y/n] ")
        if response.lower() == 'y':
            print('Exiting, good')
            sys.exit(0)


    def handle_exceptions(self, exception_sockets):
        """
        For now if a client socket has errored, simply drop it
        """
        for notified_socket in exception_sockets:
            print("Dropping socket {0} due to exception".format(repr(notified_socket)))
            self.sockets_list.remove(notified_socket)
            del self.clients[notified_socket]


    def receive_message(self, client_socket):
        """
        Receive a message from a client socket
        First interprets the header of 10 bytes,
        which is telling the server the length of the actual message
        """
        try:
            message_header = client_socket.recv(HEADER_LENGTH)

            if not len(message_header):
                return False

            message_length = int(message_header.decode("utf-8").strip())
            return {"header": message_header, "data":client_socket.recv(message_length)}

        except:
            return False


    def log_and_send(self, client_socket, msg):
        print(msg)
        client_socket.send(bytes(msg, 'utf-8'))
        return


    def handle_conns(self, read_sockets):
        """
        Main messaging processing method
        """
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
                try:
                    message = self.receive_message(notified_socket)
                    print(f"We received message {message}")

                    # User quits
                    if message is False:
                        print("Closed connection from {0}".format(self.clients[notified_socket]['data'].decode('utf-8')))
                        self.sockets_list.remove(notified_socket)
                        del self.clients[notified_socket]
                        continue

                    print("Accepted message: {0}".format(message['data'].decode('utf-8')))
                    # User's socket sent us something in lobby
                    user = self.clients[notified_socket]
                    print("Received message from {0}: {1}".format(user['data'].decode('utf-8'), message['data'].decode('utf-8')))
                    print("Interpreting... {0}".format(message['data']))
                    self.handle_lobby_command(message['data'], notified_socket)
                except Exception as e:
                    print(f"Error handling message from socket {e}")
                    print("Possibly booted client")


    def handle_lobby_command(self, lobby_command, client_socket):
        lobby_command = lobby_command.decode('utf-8')
        words = lobby_command.split()
        first = words[0]

        # Catch initial errors
        if len(words) == 1:
            msg = ''
            if first == "$$create" or first == "$$delete":
                msg = "Must specify a room name argument to execute $$create or $$delete! [E.g. $$create pokemon]"
                print("User did not specify roomname to create or delete")
            elif first == "$$send":
                msg = "Must specify a room to send your message for $$send [E.g. $$send pokemon]!"
                print("User did not specify a room to send a message to")
            elif first == "$$join" or first == "$$leave":
                msg = "Must specify a room name argument to execute $$join or $$leave! [E.g. $$join pokemon]"
                print("User did not specify roomname to join or leave")
            elif first == "$$enter":
                msg = "Must specify a room name argument to execute $$enter! [E.g. $$enter pokemon]"
                print("User did not specify roomname to enter")
            elif msg != '':
                print("Error catching failed ...")
                client_socket.send(bytes(msg, 'utf-8'))
                return

        if first == "$$create":
            self.handle_create_room(lobby_command, client_socket)
        elif first == "$$delete":
            self.handle_delete_room(lobby_command, client_socket)
        elif first == "$$join":
            self.handle_join_room(lobby_command, client_socket)
        elif first == "$$leave":
            self.handle_leave_room(lobby_command, client_socket)
        elif first == "$$list":
            self.handle_list_room(lobby_command, client_socket)
        elif first == "$$send":
            self.handle_send_to_room(lobby_command, client_socket)
        elif first == "$$enter":
            self.handle_enter_room_session(lobby_command, client_socket)
        elif first == "$$exit":
            self.handle_exit_room_session(lobby_command, client_socket)
        elif first == "$$whoami":
            self.handle_whoami(client_socket)
        else:
            print("Not sure how this lobby command got to server. Should have been filtered by client filter")

    def handle_whoami(self, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        print(f'User {user} queried their identity')
        msg = f'You are currently user {user}'
        client_socket.send(bytes(msg, 'utf-8'))

    def handle_create_room(self, lobby_command, client_socket):
        msg = "Handling room creation of {0}".format(lobby_command)
        print(msg)
        user = self.clients[client_socket]['data'].decode('utf-8')
        roomname = lobby_command.split()[1]

        if roomname == "mine":
            msg = f'Client {user} error! "mine" is a reserved word that cannot be a room name.'
            self.log_and_send(client_socket, msg)
            return

        for room in self.rooms:
            if room.name == roomname:
                msg = f"Invalid request from client: {roomname} already exists!"
                self.log_and_send(client_socket, msg)
                return

        self.rooms.append(Room(name=roomname, creator=user))
        msg = f"Room {roomname} created for client {user} (creator/Admin)."
        self.log_and_send(client_socket, msg)
        return
    

    def handle_delete_room(self, lobby_command, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        roomname = lobby_command.split()[1]
        msg = f"Handling room deletion of {roomname} by {user}"
        print(msg)
        for _room in self.rooms:
            if _room.name == roomname and user in _room.room_attrbts['admins']:
                msg = f"Room {roomname} is being deleted by admin {user}"
                self.rooms.remove(_room)
                self.log_and_send(client_socket, msg)
                return
        msg = f"Room {roomname} was not found or user is not permitted to delete"
        self.log_and_send(client_socket, msg)



    def handle_join_room(self, lobby_command, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        words = lobby_command.split()
        roomname = words[1]
        print(f"Handling join room {roomname} for {user}")
        for _room in self.rooms:
            if _room.name == roomname:
                print("Requested roomname found..")
                if user in _room.room_attrbts['members']:
                    msg = f"Client {user} is already a member of room {_room.name}"
                    self.log_and_send(client_socket, msg)
                    return
                else:
                    _room.room_attrbts['members'].add(user)
                    msg = f"{user} successfully joined membership of room {roomname}"
                    self.log_and_send(client_socket, msg)
                    return
        msg = f'Client {user} passed invalid room. Could not join room {roomname}'
        self.log_and_send(client_socket, msg)
        return


    def handle_leave_room(self, lobby_command, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        words = lobby_command.split()
        roomname = words[1]
        print(f"Handling leave room {roomname} for {user}")
        for _room in self.rooms:
            if _room.name == roomname:
                print("Requested roomname found..")
                if user not in _room.room_attrbts['members']:
                    msg = f"Client {user} is already NOT a member of room {_room.name}"
                    self.log_and_send(client_socket, msg)
                    return
                else:
                    _room.room_attrbts['members'].remove(user)
                    msg = f"User {user} successfully removed from room {roomname}"
                    self.log_and_send(client_socket, msg)
                    return
        msg = f'Client {user} passed invalid room. Could not join room {roomname}'
        self.log_and_send(client_socket, msg)
        return


    def handle_list_room(self, lobby_command, client_socket):
        print("Handling list command...")
        msg = ''
        words = lobby_command.split()
        # List all rooms
        if len(words) == 1:
            msg = 'Available Rooms:\n'
            for room in self.rooms:
                msg += f'\t\t{room.name}\n'
            client_socket.send(bytes(msg, 'utf-8'))
            return
        else:
            # List all rooms and members
            roomname = words[1]
            if roomname == "all":
                user = self.clients[client_socket]['data'].decode('utf-8')
                msg = f'All rooms and users:\n'
                for room in self.rooms:
                    msg += f'Room: {room.name}\nUsers: '
                    for user in room.room_attrbts['members']:
                        msg += f'\t{user}'
                        if user in room.room_attrbts['admins']:
                            msg += ' - Admin'
                        msg += '\n'
                    msg += '\n'
                client_socket.send(bytes(msg, 'utf-8'))
                return

            # List user's room membership
            if roomname == "mine":
                user = self.clients[client_socket]['data'].decode('utf-8')
                msg = f'Rooms user {user} has joined:\n'
                for room in self.rooms:
                    if user in room.room_attrbts['members']:
                        msg += f'\t\t{room.name}'
                        if user in room.room_attrbts['admins']:
                            msg += ' - Admin'
                        msg += '\n'
                client_socket.send(bytes(msg, 'utf-8'))
                return
            
            # List membership and active users of a room
            for _room in self.rooms:
                if _room.name == roomname:
                    print("Request roomname found..")
                    msg = f'User members of room {roomname}:\n'
                    for member in _room.room_attrbts['members']:
                        msg += f'\t\t{member}\n'
                    msg+= '\n'
                    client_socket.send(bytes(msg, 'utf-8'))
                    
                    msg = 'Users active in room:\n'
                    for active_user in _room.room_attrbts['active']:
                        msg += f'\t\t{active_user}\n'
                    client_socket.send(bytes(msg, 'utf-8'))
                    return
            if msg == '':
                msg = f'Client passed an invalid room to list members of {roomname}\n'
                self.log_and_send(client_socket, msg)
                return
    
    def handle_send_to_room(self, lobby_command, client_socket):
        """
        Fundamental algorithm for distributing messages to other clients.
        Look for the matching room, then send the message to any users who
        are members of that room.
        """
        words = lobby_command.split()
        sent_name = words[1]
        user = self.clients[client_socket]['data'].decode('utf-8')
        for room in self.rooms:
            if room.name == sent_name:
                actual_words = words[2:]
                actual_words = ' '.join(actual_words)
                actual_words += '\n'
                msg = f"[{sent_name}] {user}: {actual_words}"
                for client in self.clients:
                    found_user = self.clients[client]['data'].decode('utf-8')
                    if found_user != user and found_user in room.room_attrbts['members']:
                        client.send(bytes(msg, 'utf-8'))
                print(f"Successfully sent message to all members of {sent_name}")
                return
        msg = f"Could not find room {sent_name} requested by {user}"
        self.log_and_send(client_socket, msg)
        msg = f"format for command is $$send [roomname] message"
        client.send(bytes(msg, 'utf-8'))
        return

    def handle_enter_room_session(self, lobby_command, client_socket):
        words = lobby_command.split()
        sent_name = words[1]
        user = self.clients[client_socket]['data'].decode('utf-8')
        for room in self.rooms:
            if room.name == sent_name and user in room.room_attrbts['members']:
                room.room_attrbts['active'].add(user)
                msg = f'User {user} is a member of room {sent_name}. Entering user into active mode for this room. ACTIVE'
                print(msg)
                return
        msg = f'Room {sent_name} not found or user {user} is not yet a member. NONACTIVE'
        self.log_and_send(client_socket, msg)
        return

    def handle_exit_room_session(self, lobby_command, client_socket):
        user = self.clients[client_socket]['data'].decode('utf-8')
        for room in self.rooms:
            if user in room.room_attrbts['active']:
                room.room_attrbts['active'].remove(user)
                msg = f'User {user} is no longer active in room {room.name}.'
                print(msg)
                return
        msg = f'Room {room.name} not found or user {user} is not yet a member. NONACTIVE'
        self.log_and_send(client_socket, msg)
        return

    def run(self):
        print("Central server now listening...")
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            self.handle_conns(read_sockets)
            self.handle_exceptions(exception_sockets)


s = Server()
signal.signal(signal.SIGINT, s.signal_handler)
s.run()
