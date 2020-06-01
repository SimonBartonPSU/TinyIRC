import re
import sys
import os
import json

accepted_commands = ["$$whoami", "$$create", "$$delete", "$$join", "$$leave", "$$list", "$$enter", "$$exit", "$$send"]

# Validate input client side to save server work
def interpret_lobby_message(message):
    if len(message) == 0:
        return None

    message = message.strip()
    words = message.split()
    command = words[0]
    if len(words) > 1:
        room = words[1]
    # not special message
    if command[:2] != '$$':
        print("Unknown lobby input, please enter a valid command.")
        print("$$help can display available commands.\n")
        #Debugging print(f"We received command {command}\n")
        return None
    elif command == "$$help":
        print("Available commands:")
        print("$$whoami -- Echo your current identity")
        print("$$create [room name] -- Creates a new chat room with specified name")
        print("$$delete [room name] -- Allows a room Admin to delete a specified room")
        print("$$join [room name] -- Add yourself to room membership, if possible")
        print("$$leave [room name] -- Remove yourself from room membership, if possible")
        print("$$list [room name|mine|all] -- Without an argument, lists available rooms\nwith an argument, list users in specified room or \nrooms you've joined or all rooms with members")
        print("$$enter [room name] -- Enter an active session in a room, all messages will be directed to this room")
        print("$$exit -- Exit an active room session, messages will default to lobby")
        print("$$$end -- Note three dollar signs, this will end the client session entirely\n")
        return None
    elif command in accepted_commands:
        if command == "$$create":
            if len(room) > 48 or not room.isalpha():
                print("Invalid! Room names must be 48 characters or less and alphabetical")
        return True
    else:
        print("Hmmm, you were close to a valid command with $$, are you sure this wasn't a typo?\n")
        return None

def lobby_welcome():
    print("Welcome back to your lobby. Enter a valid $$ command or $$help if you need help.\n")

def end_session(Client):
    r = input('Would you like to save local config? [y/n] ')
    if r.lower() == 'y':
        print("Saving config for current user...")
        save_config(Client)
    else:
        print("NOT saving current config")
    r = input("Would you like to delete local config? [y/n] ")
    if r.lower() == 'y':
        path = os.environ.get('HOME') + '/.tiny'
        if os.path.exists(path):
            print("Deleting existing local config...")
            os.system('rm ' + path)
        else:
            print("No local config exists to delete.")
    sys.exit(0)

def check_for_config(Client):
    try:
        path = os.environ.get('HOME') + '/.tiny'
        if os.path.exists(path):
            with open(path) as f:
                Client.config = json.load(f)
            Client.username = Client.config['username']
            return True
        else:
            return False
    except Exception as e:
        print(f"Exception occured while loading client config... {e}")

def save_config(Client):
        try:
            path = os.environ.get('HOME') + '/.tiny'
            with open(path, 'w') as f:
                json.dump(Client.config, f)
        except Exception as e:
            print(f"Error saving config!! {e}")