import re

accepted_commands = ["$$create", "$$join", "$$leave", "$$list", "$$enter", "$$exit"]

def print_response(response):
    if response == 1:
        print("Unknown lobby input, please enter a valid command.")
        print("$$help can display available commands.")
        print("$$new is recommended for new users.")
    elif response == 2:
        pass
        #TODO write a guide for braaand new peeps if they want it
    elif response == 3:
        print("Available commands:")
        # TODO all of these
        print("$$create [room name] -- Creates a new chat room with specified name")
        print("$$join [room name] -- Add room to your remembered room list")
        print("$$leave -- Remove room from your remembered room list")
        print("$$list [room name] -- Without a room name argument, lists available rooms\nwith a room name argument, list users in specified room")
        print("$$enter [room name] -- Enter an active session in a room")
        print("$$exit -- Exit an active room session")
    elif response == 4:
        print("Hmmm, you were close to a valid command with $$, are you sure this wasn't a typo?")

def interpret_lobby_message(message):
    message = message.strip()
    # normal message
    if message[:2] != '$$':
        return 1
    elif message == "$$new":
        return 2
    elif message == "$$help":
        return 3
    elif message.split()[0] in accepted_commands:
        return message
    else:
        return 4

def handle_lobby_command(lobby_command):
    first = lobby_command.split()[0]
    if first == "$$create":
        handle_room_create(lobby_command)
    elif first == 

def handle_room_create(lobby_command):
    pass

def handle_join_room(lobby_command):
    pass

def handle_leave_room(lobby_command):
    pass

def handle_list_room(lobby_command):
    pass

def handle_active_room_session(lobby_command):
    #BIG TODO
    pass

def lobby_welcome():
    print("Welcome back to your lobby. Enter a valid $$ command or $$help if you need help.")